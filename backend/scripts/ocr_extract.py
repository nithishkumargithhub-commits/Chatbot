"""
scripts/ocr_extract.py — JeevanPath AI
Phase 1: OCR all pages of the scanned PDF using python-doctr.

python-doctr is a pure Python deep learning OCR (no system binaries needed).
It uses DBNet for text detection and CRNN for recognition, running on GPU if available.

Output: backend/data/raw_ocr.json
  [{ "page": 1, "text": "...", "word_count": 120 }, ...]

Run:
    cd backend
    python scripts/ocr_extract.py
"""

import json
import sys
import os
import io
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent
PDF_PATH    = PROJECT_DIR / "Skill-Development-Scheme_11zon.pdf"
OUT_DIR     = BACKEND_DIR / "data"
OUT_PATH    = OUT_DIR / "raw_ocr.json"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def run_ocr() -> None:
    print("=" * 60)
    print("JeevanPath AI — Phase 1: OCR Extraction (python-doctr)")
    print("=" * 60)

    # ── Check dependencies ────────────────────────────────────────────────────
    try:
        import fitz  # PyMuPDF — for rendering PDF pages as images
    except ImportError:
        print("ERROR: PyMuPDF not installed. Run: pip install pymupdf")
        sys.exit(1)

    try:
        import numpy as np
        from PIL import Image
        from doctr.models import ocr_predictor
        from doctr.io import DocumentFile
    except ImportError as e:
        print(f"ERROR: {e}")
        print("Run: pip install python-doctr[torch] pymupdf pillow numpy")
        sys.exit(1)

    # ── Check PDF ─────────────────────────────────────────────────────────────
    if not PDF_PATH.exists():
        print(f"ERROR: PDF not found at {PDF_PATH}")
        sys.exit(1)

    print(f"PDF    : {PDF_PATH}")
    print(f"Output : {OUT_PATH}")
    print()

    # ── Load doctr OCR predictor ──────────────────────────────────────────────
    # pretrained=True downloads DBNet + CRNN models from HuggingFace (~100MB)
    print("Loading doctr OCR model (first run downloads ~100MB)...")
    predictor = ocr_predictor(
        det_arch="db_resnet50",
        reco_arch="crnn_vgg16_bn",
        pretrained=True,
        assume_straight_pages=True,  # document pages are straight (not photos)
    )
    print("  [OK] OCR model ready\n")

    # ── Open PDF & render pages ───────────────────────────────────────────────
    doc = fitz.open(str(PDF_PATH))
    total_pages = len(doc)
    print(f"PDF has {total_pages} pages. Starting OCR...\n")

    results = []
    total_words = 0

    for page_num in range(total_pages):
        page = doc[page_num]

        # Render at 2x for sharper text recognition
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")

        # Convert to numpy RGB array for doctr
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img_np = np.array(img)

        # Run OCR — doctr expects a list of pages (numpy arrays)
        doc_result = predictor([img_np])

        # Extract text from all blocks on this page
        page_words = []
        for page_res in doc_result.pages:
            for block in page_res.blocks:
                for line in block.lines:
                    line_words = [w.value for w in line.words if w.value.strip()]
                    page_words.extend(line_words)

        page_text = " ".join(page_words).strip()
        word_count = len(page_words)
        total_words += word_count

        results.append({
            "page"      : page_num + 1,
            "text"      : page_text,
            "word_count": word_count,
        })

        preview = page_text[:65].replace("\n", " ") if page_text else "(empty)"
        print(f"  Page {page_num + 1:3d}/{total_pages} | words={word_count:4d} | {preview}...")

    doc.close()

    # ── Save ──────────────────────────────────────────────────────────────────
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    non_empty = sum(1 for r in results if r["word_count"] > 5)

    print(f"\n{'='*60}")
    print(f"OCR complete!")
    print(f"  Total pages      : {total_pages}")
    print(f"  Pages with text  : {non_empty}")
    print(f"  Total words      : {total_words}")
    print(f"  Output saved     : {OUT_PATH}")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_ocr()
