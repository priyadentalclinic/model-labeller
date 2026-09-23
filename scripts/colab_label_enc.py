"""
colab_label_enc.py
==================
Colab T4 GPU ke liye — same Qwen model, same photos,
lekin OUTPUT LABELS bhi encrypted (Fernet) save hote hain.
Google ko input bhi nahi dikhta, output bhi nahi.

Env vars needed:
  DECRYPT_KEY   — Fernet key (same as config.key content)
  OLLAMA_URL    — http://localhost:11434
  ALBUM_START   — 200 (default)
  ALBUM_END     — 210 (default)
"""
import os, sys, re, json, base64, time, pathlib, traceback, urllib.parse
from datetime import datetime

from cryptography.fernet import Fernet
import requests

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from indian_prompts import LLAVA_PROMPT, parse_llava_response, map_to_indian_labels

# ── Config ────────────────────────────────────────────────────────────
KEY_BYTES    = os.environ["DECRYPT_KEY"].strip().encode()
FERNET       = Fernet(KEY_BYTES)
OLLAMA_URL   = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5vl:7b")
ALBUM_START  = float(os.environ.get("ALBUM_START", "200"))
ALBUM_END    = float(os.environ.get("ALBUM_END",   "300"))
MAX_RETRIES  = 3
TIMEOUT_SEC  = 180   # GPU is fast, 3 min is enough

BASE         = pathlib.Path(__file__).parent.parent
INPUT_DIR    = BASE / "input_encrypted"
OUTPUT_DIR   = BASE / "output_labels_enc"   # ← encrypted output
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def album_num(filename: str):
    decoded = urllib.parse.unquote(filename)
    m = re.search(r'album[\s_]*(\d+(?:\.\d+)?)', decoded, re.I)
    return float(m.group(1)) if m else None


def call_qwen(image_bytes: bytes) -> str:
    b64 = base64.b64encode(image_bytes).decode()
    payload = {"model": OLLAMA_MODEL, "prompt": LLAVA_PROMPT,
                "images": [b64], "stream": False,
                "options": {"temperature": 0.1, "num_predict": 400}}
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.post(f"{OLLAMA_URL}/api/generate",
                              json=payload, timeout=TIMEOUT_SEC)
            r.raise_for_status()
            return r.json().get("response", "")
        except Exception as e:
            print(f"  [Attempt {attempt}/{MAX_RETRIES}] Error: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(5)
    return ""


def process_one(enc_path: pathlib.Path) -> bool:
    enc_name      = enc_path.stem
    original_name = urllib.parse.unquote(enc_name)

    # Output path — encrypted JSON
    safe_stem = enc_name.replace("%", "_")
    out_path  = OUTPUT_DIR / f"{safe_stem}.json.enc"
    if out_path.exists():
        print(f"  [SKIP] Already done: {original_name}")
        return True

    print(f"  [DECRYPT] {original_name}")
    try:
        img_bytes = FERNET.decrypt(enc_path.read_bytes())
    except Exception as e:
        print(f"  [ERROR] Decrypt failed: {e}")
        return False

    print(f"  [QWEN]    Sending ({len(img_bytes)//1024} KB)...")
    raw = call_qwen(img_bytes)
    if not raw.strip():
        print("  [ERROR]   Empty response from Qwen")
        return False

    labels = map_to_indian_labels(parse_llava_response(raw))
    result = {
        "original_filename": original_name,
        "labeled_at":        datetime.utcnow().isoformat() + "Z",
        "model_used":        OLLAMA_MODEL,
        "labels":            labels,
    }

    # Encrypt the output JSON before saving
    encrypted_out = FERNET.encrypt(json.dumps(result, ensure_ascii=False).encode())
    out_path.write_bytes(encrypted_out)
    print(f"  [DONE]    Persona: {labels['compound_persona']}")
    print(f"            Tags:    {labels['combo_tags'][:5]}...")
    return True


def main():
    print("=" * 60, flush=True)
    print(f"  Colab Encrypted Label Runner", flush=True)
    print(f"  Album Range: {ALBUM_START:.0f} – {ALBUM_END:.0f}", flush=True)
    print(f"  Model: {OLLAMA_MODEL}", flush=True)
    print("=" * 60, flush=True)

    enc_files = sorted([
        f for f in INPUT_DIR.glob("*.enc")
        if f.name != ".gitkeep"
        and (n := album_num(f.name)) is not None
        and ALBUM_START <= n <= ALBUM_END
    ], key=lambda f: album_num(f.name))

    if not enc_files:
        print("[WARN] No matching .enc files found in input_encrypted/", flush=True)
        sys.exit(1)

    print(f"\nFound {len(enc_files)} files to process.\n", flush=True)
    ok, fail = 0, 0
    for i, f in enumerate(enc_files, 1):
        print(f"[{i}/{len(enc_files)}]", flush=True)
        try:
            if process_one(f): ok += 1
            else: fail += 1
        except Exception:
            traceback.print_exc()
            fail += 1
        print("", flush=True)

    print("=" * 60, flush=True)
    print(f"  Done: {ok}  |  Failed: {fail}", flush=True)
    print(f"  Encrypted labels saved to: output_labels_enc/", flush=True)
    print("=" * 60, flush=True)
    if ok == 0 and fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
