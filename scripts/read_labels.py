"""
read_labels.py — Laptop par encrypted labels padhne ke liye
Usage: python scripts/read_labels.py
"""
import json, pathlib
from cryptography.fernet import Fernet

KEY_FILE   = pathlib.Path(__file__).parent.parent / "local" / "config.key"
LABELS_DIR = pathlib.Path(__file__).parent.parent / "output_labels_enc"

fernet = Fernet(KEY_FILE.read_bytes().strip())

files = sorted(LABELS_DIR.glob("*.json.enc"))
if not files:
    print("No encrypted label files found in output_labels_enc/")
else:
    for f in files:
        data = json.loads(fernet.decrypt(f.read_bytes()).decode())
        labels = data["labels"]
        print(f"\n{data['original_filename']}")
        print(f"  Persona : {labels.get('compound_persona')}")
        print(f"  Folder  : {labels.get('folder_path')}")
        print(f"  Tags    : {labels.get('combo_tags', [])[:6]}")
