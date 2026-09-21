"""
encrypt_push.py — Encrypts photos from to_upload/ and pushes to GitHub.
Run via encrypt_push.bat  (or: python encrypt_push.py)
"""
import os, sys, pathlib, shutil, subprocess, urllib.parse

BASE = pathlib.Path(__file__).parent.parent  # ModelBotLabeler/
TO_UPLOAD   = BASE / "to_upload"
ENC_DIR     = BASE / "input_encrypted"
KEY_FILE    = BASE / "local" / "config.key"

SUPPORTED = {".jpg",".jpeg",".png",".webp",".bmp"}

def main():
    print("=" * 55)
    print("  ModelBot — Encrypt & Push Photos to GitHub")
    print("=" * 55)

    # Load key
    if not KEY_FILE.exists():
        print("[ERROR] config.key not found. Run setup_labeler.py first.")
        input("Press Enter to exit...")
        sys.exit(1)

    from cryptography.fernet import Fernet
    key    = KEY_FILE.read_bytes()
    fernet = Fernet(key)

    # Find photos
    photos = [f for f in TO_UPLOAD.iterdir()
              if f.is_file() and f.suffix.lower() in SUPPORTED]

    if not photos:
        print(f"[INFO] No photos found in to_upload/ folder.")
        print(f"       Put .jpg/.png photos there and run again.")
        input("Press Enter to exit...")
        return

    print(f"\nFound {len(photos)} photo(s) to encrypt and push.\n")

    encrypted_count = 0
    for photo in photos:
        # URL-encode filename to make it git-safe
        safe_name = urllib.parse.quote(photo.name, safe="")
        enc_path  = ENC_DIR / f"{safe_name}.enc"

        if enc_path.exists():
            print(f"  [SKIP] Already encrypted: {photo.name}")
            continue

        print(f"  [ENCRYPT] {photo.name} ...")
        img_bytes = photo.read_bytes()
        encrypted = fernet.encrypt(img_bytes)
        enc_path.write_bytes(encrypted)
        print(f"            -> {enc_path.name} ({len(encrypted)//1024} KB)")
        encrypted_count += 1

    if encrypted_count == 0:
        print("\n[INFO] All photos already encrypted. Nothing new to push.")
        input("Press Enter to exit...")
        return

    print(f"\nEncrypted {encrypted_count} photo(s). Pushing to GitHub...\n")

    # Git add + commit + push
    os.chdir(BASE)
    cmds = [
        "git add input_encrypted/",
        f'git commit -m "Add {encrypted_count} encrypted photos for labeling"',
        "git push",
    ]
    for cmd in cmds:
        print(f"  $ {cmd}")
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if r.stdout: print("   ", r.stdout.strip())
        if r.stderr and "error" in r.stderr.lower():
            print(f"  [GIT ERROR] {r.stderr.strip()}")
            input("Press Enter to exit...")
            sys.exit(1)

    print()
    print("=" * 55)
    print(f"  DONE! {encrypted_count} photo(s) pushed to GitHub.")
    print()
    print("  Now wait for GitHub Actions to label them.")
    print("  Check progress at: GitHub Repo -> Actions tab")
    print("  (Usually takes 10-15 minutes per batch)")
    print()
    print("  When done, run: pull_sort.bat")
    print("=" * 55)
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
