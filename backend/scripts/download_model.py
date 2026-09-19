import os
import sys
import time
import requests
from pathlib import Path

# Target file in huggingface cache or local models dir
LOCAL_MODEL_DIR = (Path(__file__).resolve().parent.parent / "models" / "indic-sentence-bert-nli").resolve()
LOCAL_MODEL_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://huggingface.co/l3cube-pune/indic-sentence-bert-nli/resolve/main"

FILES = [
    "config.json",
    "config_sentence_transformers.json",
    "modules.json",
    "sentence_bert_config.json",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.txt",
    "1_Pooling/config.json",
    "pytorch_model.bin",
]

def download_file_with_resume(filename: str):
    target_path = LOCAL_MODEL_DIR / filename
    target_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"{BASE_URL}/{filename}"

    temp_path = target_path.with_suffix(target_path.suffix + ".part")
    
    # Check if target already fully downloaded
    if target_path.exists() and not filename.endswith(".bin"):
        print(f"  [OK] Already exists: {filename}")
        return

    existing_size = temp_path.stat().st_size if temp_path.exists() else 0

    headers = {"User-Agent": "Mozilla/5.0"}
    if existing_size > 0:
        headers["Range"] = f"bytes={existing_size}-"
        print(f"  Resuming {filename} from {round(existing_size / (1024*1024), 2)} MB...")
    else:
        print(f"  Downloading {filename}...")

    max_retries = 10
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(url, headers=headers, stream=True, timeout=20)
            if r.status_code in [200, 206]:
                mode = "ab" if existing_size > 0 and r.status_code == 206 else "wb"
                if mode == "wb":
                    existing_size = 0
                
                total_size = int(r.headers.get("content-length", 0)) + existing_size
                downloaded = existing_size

                with open(temp_path, mode) as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            mb_done = round(downloaded / (1024 * 1024), 1)
                            mb_total = round(total_size / (1024 * 1024), 1) if total_size > 0 else "?"
                            pct = f"({round(100*downloaded/total_size, 1)}%)" if total_size > 0 else ""
                            print(f"    {filename}: {mb_done}MB / {mb_total}MB {pct}", end="\r")

                print(f"\n  [OK] Completed: {filename}")
                if target_path.exists():
                    target_path.unlink()
                temp_path.rename(target_path)
                return
            else:
                print(f"  [WARN] Status {r.status_code} on {filename}, retrying ({attempt}/{max_retries})...")
                time.sleep(2)
        except Exception as e:
            print(f"  [WARN] Exception on {filename}: {e}, retrying ({attempt}/{max_retries})...")
            time.sleep(3)
            # Update resume offset
            if temp_path.exists():
                existing_size = temp_path.stat().st_size
                headers["Range"] = f"bytes={existing_size}-"

    print(f"ERROR: Failed to download {filename} after {max_retries} attempts.")
    sys.exit(1)

def main():
    print("=" * 60)
    print("Downloading Indic-SBERT model with resilient resume...")
    print(f"Destination: {LOCAL_MODEL_DIR}")
    print("=" * 60)

    for f in FILES:
        download_file_with_resume(f)

    print("\n[SUCCESS] All model files downloaded locally!")

if __name__ == "__main__":
    main()
