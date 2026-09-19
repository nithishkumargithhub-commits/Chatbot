"""
scripts/setup_db.py — JeevanPath AI
Phase 3: Set up PostgreSQL + pgvector schema for the knowledge base.

- Connects to PostgreSQL and verifies pgvector extension.
- Creates the `knowledge_base` table with a vector(768) column.
- Creates an IVFFlat index for fast cosine similarity search.
- Gracefully detects if PostgreSQL/Docker is inactive and allows local vector search to proceed.
"""

import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "jeevanpath"
DB_USER = "jeevanpath"
DB_PASS = "jeevanpath"
EMBED_DIM = 768

def check_db():
    try:
        import psycopg2
    except ImportError:
        print("psycopg2 not installed. Skipping DB setup.")
        return False

    print(f"Testing PostgreSQL connection at {DB_HOST}:{DB_PORT}...")
    for attempt in range(1, 4):
        try:
            conn = psycopg2.connect(
                host=DB_HOST, port=DB_PORT,
                dbname=DB_NAME, user=DB_USER, password=DB_PASS,
                connect_timeout=2,
            )
            conn.close()
            print(f"  [OK] PostgreSQL is reachable (attempt {attempt})")
            return True
        except Exception as e:
            time.sleep(1)

    print(f"  [INFO] PostgreSQL not currently running.")
    print("  Local disk vector cache will be used for retrieval.")
    print("  When you start Docker Desktop, re-run: python scripts/setup_db.py")
    return False

def setup_schema():
    import psycopg2
    print("Setting up pgvector schema in PostgreSQL...")
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        dbname=DB_NAME, user=DB_USER, password=DB_PASS,
    )
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    print("  [OK] Extension 'vector' enabled")

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
        embedding     VECTOR({EMBED_DIM}),
        word_count    INTEGER,
        char_length   INTEGER,
        created_at    TIMESTAMPTZ DEFAULT NOW()
    );
    """)
    print("  [OK] Table 'knowledge_base' ready")

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_knowledge_base_embedding
        ON knowledge_base
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 5);
    """)
    print("  [OK] IVFFlat index created")

    cur.close()
    conn.close()
    print("  [OK] Database schema initialized successfully.\n")

def main():
    print("=" * 60)
    print("JeevanPath AI — Phase 3: Database Setup")
    print("=" * 60)

    if check_db():
        setup_schema()
    else:
        print("\nSkipping PostgreSQL setup (local vector storage active).")
    print("=" * 60)

if __name__ == "__main__":
    main()
