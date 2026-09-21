"""
decrypt_and_label.py  — runs inside GitHub Actions runner
==========================================================
1. Reads all .enc files from input_encrypted/
2. Decrypts using DECRYPT_KEY env variable (Fernet/AES)
3. Sends each photo to local LLaVA-Phi3 (Ollama)
4. Parses structured labels from response
5. Saves label JSON to output_labels/
"""
import os, sys, json, base64, time, pathlib, traceback
from datetime import datetime

try:
    from cryptography.fernet import Fernet
except ImportError:
    print("[ERROR] cryptography package not installed.")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("[ERROR] requests package not installed.")
    sys.exit(1)

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from indian_prompts import LLAVA_PROMPT, parse_llava_response, map_to_indian_labels

# ── Config ───────────────────────────────────────────────────────────
DECRYPT_KEY  = os.environ.get("DECRYPT_KEY", "").strip().encode()
OLLAMA_URL   = os.environ.get("OLLAMA_URL", "http://localhost:11434")
BASE         = pathlib.Path(__file__).parent.parent
INPUT_DIR    = BASE / "input_encrypted"
OUTPUT_DIR   = BASE / "output_labels"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OLLAMA_MODEL = "llava-phi3"
MAX_RETRIES  = 3
TIMEOUT_SEC  = 180  # 3 min per image


def decrypt_photo(enc_path: pathlib.Path, fernet: Fernet) -> bytes:
    """Decrypt a .enc file and return raw image bytes."""
    encrypted = enc_path.read_bytes()
    return fernet.decrypt(encrypted)


def call_llava(image_bytes: bytes, ext: str) -> str:
    """Send image to Ollama LLaVA and return raw text response."""
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "model":  OLLAMA_MODEL,
        "prompt": LLAVA_PROMPT,
        "images": [b64],
        "stream": False,
        "options": {
            "temperature": 0.1,   # Low temp for consistent structured output
            "num_predict": 400,
        },
    }
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json=payload,
                timeout=TIMEOUT_SEC,
            )
            r.raise_for_status()
            return r.json().get("response", "")
        except Exception as e:
            print(f"  [Attempt {attempt}/{MAX_RETRIES}] Ollama error: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(10)
    return ""


def process_one(enc_path: pathlib.Path, fernet: Fernet) -> bool:
    """Decrypt, label, and save JSON for one .enc file. Returns True on success."""
    # Derive the original filename from the .enc filename
    # enc filename format: urlencoded_originalname.ext.enc
    import urllib.parse
    enc_name = enc_path.stem   # e.g.  "photo%20name.jpg"
    original_name = urllib.parse.unquote(enc_name)  # e.g. "photo name.jpg"
    ext = pathlib.Path(original_name).suffix.lower()

    # Output JSON path
    safe_stem = enc_path.stem.replace("%", "_")
    out_json = OUTPUT_DIR / f"{safe_stem}_labels.json"

    if out_json.exists():
        print(f"  [SKIP] Already labeled: {original_name}")
        return True

    print(f"  [DECRYPT] {original_name} ...")
    try:
        img_bytes = decrypt_photo(enc_path, fernet)
    except Exception as e:
        print(f"  [ERROR] Decryption failed for {enc_path.name}: {e}")
        return False

    print(f"  [LLAVA]   Sending to LLaVA ({len(img_bytes)//1024} KB) ...")
    raw_response = call_llava(img_bytes, ext)

    if not raw_response.strip():
        print(f"  [ERROR] Empty response from LLaVA for {original_name}")
        return False

    print(f"  [PARSE]   Parsing response ...")
    raw_dict = parse_llava_response(raw_response)
    labels   = map_to_indian_labels(raw_dict)

    result = {
        "original_filename": original_name,
        "enc_filename":      enc_path.name,
        "labeled_at":        datetime.utcnow().isoformat() + "Z",
        "model_used":        OLLAMA_MODEL,
        "labels":            labels,
    }

    out_json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  [DONE]    Saved: {out_json.name}")
    print(f"            Persona : {labels['compound_persona']}")
    print(f"            Tags    : {labels['combo_tags']}")
    print(f"            Folder  : {labels['folder']}")
    return True


def main():
    print("=" * 60)
    print("  ModelBot LLaVA Labeler — GitHub Actions Runner")
    print("=" * 60)

    if not DECRYPT_KEY:
        print("[ERROR] DECRYPT_KEY environment variable is not set!")
        print("        Add PHOTO_DECRYPT_KEY to your GitHub Secrets.")
        sys.exit(1)

    try:
        fernet = Fernet(DECRYPT_KEY)
    except Exception as e:
        print(f"[ERROR] Invalid DECRYPT_KEY: {e}")
        sys.exit(1)

    enc_files = sorted(INPUT_DIR.glob("*.enc"))
    if not enc_files:
        print("[INFO] No .enc files found in input_encrypted/. Nothing to do.")
        sys.exit(0)

    print(f"\nFound {len(enc_files)} encrypted photo(s) to label.\n")

    success_count = 0
    fail_count    = 0

    for i, enc_path in enumerate(enc_files, 1):
        print(f"[{i}/{len(enc_files)}] Processing: {enc_path.name}")
        try:
            ok = process_one(enc_path, fernet)
            if ok:
                success_count += 1
            else:
                fail_count += 1
        except Exception:
            print(f"  [FATAL] Unexpected error:")
            traceback.print_exc()
            fail_count += 1
        print()

    print("=" * 60)
    print(f"  Labeled: {success_count} success  |  {fail_count} failed")
    print("=" * 60)

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
