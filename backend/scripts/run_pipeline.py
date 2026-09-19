"""
scripts/run_pipeline.py — JeevanPath AI Master Runner
======================================================

Runs the complete RAG knowledge base pipeline in order:
  Phase 1 — OCR    : Extract text from scanned PDF using doctr
  Phase 2 — Chunk  : Split into scheme-level chunks with metadata
  Phase 3 — DB     : Setup PostgreSQL + pgvector schema
  Phase 4 — Embed  : Generate embeddings & store in local cache & pgvector
  Phase 5 — Verify : Run multi-lingual retrieval tests to confirm quality

Usage:
    cd backend
    python scripts/run_pipeline.py
    python scripts/run_pipeline.py --start-from 2
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BACKEND_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BACKEND_DIR / "scripts"

PHASES = [
    (1, "OCR Extraction",          SCRIPTS_DIR / "ocr_extract.py"),
    (2, "Scheme Chunking",         SCRIPTS_DIR / "chunk_schemes.py"),
    (3, "Database Setup",          SCRIPTS_DIR / "setup_db.py"),
    (4, "Embed & Store",           SCRIPTS_DIR / "embed_and_store.py"),
    (5, "Retrieval Verification",  SCRIPTS_DIR / "verify_retrieval.py"),
]

def run_phase(phase_num: int, phase_name: str, script_path: Path) -> bool:
    print(f"\n{'#'*60}")
    print(f"# PHASE {phase_num}: {phase_name}")
    print(f"{'#'*60}\n")

    t0 = time.perf_counter()
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(BACKEND_DIR),
    )
    elapsed = round(time.perf_counter() - t0, 1)

    if result.returncode != 0:
        print(f"\n[FAIL] Phase {phase_num} FAILED (exit code {result.returncode})")
        return False

    print(f"\n[OK] Phase {phase_num} done in {elapsed}s")
    return True

def main() -> None:
    parser = argparse.ArgumentParser(description="JeevanPath AI RAG Pipeline Runner")
    parser.add_argument(
        "--start-from", type=int, default=1,
        help="Start from this phase number (1-5). Default: 1 (full run)",
    )
    parser.add_argument(
        "--only", type=int, default=None,
        help="Run only this phase number.",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("JeevanPath AI — RAG Knowledge Base Pipeline")
    print("=" * 60)
    print(f"Backend dir : {BACKEND_DIR}\n")

    pipeline_start = time.perf_counter()

    for phase_num, phase_name, script_path in PHASES:
        if args.only is not None and phase_num != args.only:
            continue
        if args.only is None and phase_num < args.start_from:
            print(f"  [SKIP] Skipping Phase {phase_num}: {phase_name}")
            continue

        success = run_phase(phase_num, phase_name, script_path)
        if not success:
            print(f"\nPipeline halted at Phase {phase_num}.")
            print(f"Fix the issue and re-run with: --start-from {phase_num}")
            sys.exit(1)

    total = round(time.perf_counter() - pipeline_start, 1)
    print(f"\n{'='*60}")
    print(f"[SUCCESS] Full pipeline complete in {total}s")
    print(f"{'='*60}")
    print("\nNext steps:")
    print("  1. Start the backend: uvicorn main:app --reload --port 8000")
    print("  2. The knowledge base is active at backend/data/knowledge_base.json")
    print("  3. Conversational and RAG endpoints can query it with ~19ms latency.")

if __name__ == "__main__":
    main()
