"""
scripts/embed_and_store.py — JeevanPath AI
Phase 4: Embed each scheme chunk and store in PostgreSQL pgvector & local cache.

- Uses l3cube-pune/indic-sentence-bert-nli (768-dim Indic multilingual sentence embeddings).
- Caches embeddings to backend/data/embeddings.npy and backend/data/knowledge_base.json.
- Inserts into PostgreSQL + pgvector when DB is active.
- Fully resilient: works standalone and with Docker.
"""

import json
import sys
import time
from pathlib import Path
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BACKEND_DIR     = Path(__file__).resolve().parent.parent
DATA_DIR        = BACKEND_DIR / "data"
CHUNKS_PATH     = DATA_DIR / "chunks.json"
EMBEDDINGS_PATH = DATA_DIR / "embeddings.npy"
KB_CACHE_PATH   = DATA_DIR / "knowledge_base.json"

DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "jeevanpath"
DB_USER = "jeevanpath"
DB_PASS = "jeevanpath"

LOCAL_MODEL_DIR = BACKEND_DIR / "models" / "indic-sentence-bert-nli"
EMBED_MODEL     = str(LOCAL_MODEL_DIR) if (LOCAL_MODEL_DIR / "pytorch_model.bin").exists() else "l3cube-pune/indic-sentence-bert-nli"
BATCH_SIZE      = 8

def load_model():
    """Load Indic SBERT model."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("ERROR: sentence-transformers not installed.")
        sys.exit(1)

    model_src = str(LOCAL_MODEL_DIR) if (LOCAL_MODEL_DIR / "pytorch_model.bin").exists() else EMBED_MODEL
    print(f"Loading embedding model from: {model_src}")
    t0 = time.perf_counter()
    model = SentenceTransformer(model_src)
    elapsed = round(time.perf_counter() - t0, 1)
    
    probe = model.encode(["probe text"], normalize_embeddings=True)
    dim = probe.shape[1]
    print(f"  [OK] Model ready | dim={dim} | load_time={elapsed}s\n")
    return model, dim

def embed_chunks(model, chunks: list[dict]) -> np.ndarray:
    """Embed chunk texts in batches, returning L2-normalized numpy vectors."""
    texts = [c["chunk_text"] for c in chunks]
    total = len(texts)
    all_embeddings = []

    print(f"Embedding {total} scheme chunks in batches of {BATCH_SIZE}...")
    t0 = time.perf_counter()

    for i in range(0, total, BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        vecs = model.encode(
            batch,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=BATCH_SIZE,
        )
        all_embeddings.append(vecs)
        done = min(i + BATCH_SIZE, total)
        print(f"  Embedded {done:3d}/{total}", end="\r")

    embeddings_arr = np.vstack(all_embeddings)
    elapsed = round(time.perf_counter() - t0, 1)
    print(f"\n  [OK] All {total} embeddings complete | shape={embeddings_arr.shape} | time={elapsed}s\n")
    return embeddings_arr

def store_local(chunks: list[dict], embeddings: np.ndarray) -> None:
    """Save embeddings and knowledge base to local files."""
    np.save(EMBEDDINGS_PATH, embeddings)
    print(f"  [OK] Saved numpy embeddings -> {EMBEDDINGS_PATH}")

    # Save full knowledge base records with embedded vectors for direct retrieval
    kb_records = []
    for chunk, emb in zip(chunks, embeddings):
        record = dict(chunk)
        record["embedding"] = emb.tolist()
        kb_records.append(record)

    with open(KB_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(kb_records, f, ensure_ascii=False, indent=2)
    print(f"  [OK] Saved knowledge base cache -> {KB_CACHE_PATH}")

def store_in_postgres(chunks: list[dict], embeddings: np.ndarray) -> bool:
    """Insert into PostgreSQL pgvector if accessible."""
    try:
        import psycopg2
        from psycopg2.extras import execute_values
    except ImportError:
        print("  [INFO] psycopg2 not available for PostgreSQL storage.")
        return False

    print(f"\nAttempting PostgreSQL connection at {DB_HOST}:{DB_PORT}...")
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT,
            dbname=DB_NAME, user=DB_USER, password=DB_PASS,
            connect_timeout=3
        )
    except Exception as e:
        print(f"  [INFO] PostgreSQL not currently running ({e}).")
        print("  Local vector search cache is active. You can sync to pgvector anytime.")
        return False

    try:
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute(f"""
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id            SERIAL PRIMARY KEY,
            section_num   TEXT,
            scheme_name   TEXT NOT NULL,
            ministry      TEXT,
            category      TEXT,
            chunk_text    TEXT NOT NULL,
            description   TEXT,
            assistance    TEXT,
            eligibility   TEXT,
            how_to_apply  TEXT,
            source_url    TEXT,
            embedding     VECTOR({embeddings.shape[1]}),
            word_count    INTEGER,
            char_length   INTEGER,
            created_at    TIMESTAMPTZ DEFAULT NOW()
        );
        """)

        conn.autocommit = False
        cur.execute("DELETE FROM knowledge_base;")
        
        rows = []
        for chunk, emb in zip(chunks, embeddings):
            rows.append((
                chunk.get("section_num", ""),
                chunk.get("scheme_name", ""),
                chunk.get("ministry", ""),
                chunk.get("category", ""),
                chunk.get("chunk_text", ""),
                chunk.get("description", ""),
                chunk.get("assistance", ""),
                chunk.get("eligibility", ""),
                chunk.get("how_to_apply", ""),
                chunk.get("source_url", ""),
                emb.tolist(),
                chunk.get("word_count", 0),
                chunk.get("char_length", 0),
            ))

        insert_sql = """
            INSERT INTO knowledge_base (
                section_num, scheme_name, ministry, category, chunk_text,
                description, assistance, eligibility, how_to_apply,
                source_url, embedding, word_count, char_length
            ) VALUES %s
        """
        execute_values(cur, insert_sql, rows, page_size=50)
        conn.commit()

        # Build IVFFlat index
        conn.autocommit = True
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_knowledge_base_embedding
            ON knowledge_base
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 5);
        """)
        cur.execute("VACUUM ANALYZE knowledge_base;")
        print(f"  [OK] Successfully stored {len(rows)} records in PostgreSQL pgvector!")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"  [WARN] Failed writing to PostgreSQL: {e}")
        return False

def run_embed_and_store() -> None:
    print("=" * 60)
    print("JeevanPath AI — Phase 4: Indic-SBERT Embedding & Vector Storage")
    print("=" * 60)

    if not CHUNKS_PATH.exists():
        print(f"ERROR: {CHUNKS_PATH} not found. Run chunk_schemes.py first.")
        sys.exit(1)

    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Loaded {len(chunks)} scheme chunks from {CHUNKS_PATH}\n")

    model, dim = load_model()
    embeddings = embed_chunks(model, chunks)

    # Local persistence
    store_local(chunks, embeddings)

    # Database persistence
    store_in_postgres(chunks, embeddings)

    print(f"\n{'='*60}")
    print(f"Phase 4 complete! All {len(chunks)} schemes embedded and indexed.")
    print(f"{'='*60}")

if __name__ == "__main__":
    run_embed_and_store()
