"""
generate_push.py — Encrypts reference photo from to_generate/ and pushes to GitHub.
Run via generate_push.bat
"""
import os, sys, pathlib, shutil, subprocess, urllib.parse

BASE            = pathlib.Path(__file__).parent.parent
TO_GENERATE     = BASE / "to_generate"
GEN_INPUT       = BASE / "generate_input"
KEY_FILE        = BASE / "local" / "config.key"

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def main():
    print("=" * 55)
    print("  ModelBot — Encrypt & Push Reference Photo for Ad")
    print("=" * 55)

    if not KEY_FILE.exists():
        print("[ERROR] config.key not found. Run setup_labeler.bat first.")
        input("Press Enter to exit...")
        sys.exit(1)

    from cryptography.fernet import Fernet
    key    = KEY_FILE.read_bytes()
    fernet = Fernet(key)

    photos = [f for f in TO_GENERATE.iterdir()
              if f.is_file() and f.suffix.lower() in SUPPORTED]

    if not photos:
        print("[INFO] No reference photo found in to_generate/ folder.")
        print("       Put a girl's face photo in to_generate/ and run again.")
        input("Press Enter to exit...")
        return

    print(f"\nFound {len(photos)} reference photo(s) to encrypt and push.\n")

    encrypted_count = 0
    for photo in photos:
        safe_name = urllib.parse.quote(photo.name, safe="")
        enc_path  = GEN_INPUT / f"{safe_name}.enc"

        if enc_path.exists():
            print(f"  [SKIP] Already encrypted: {photo.name}")
            continue

        print(f"  [ENCRYPT] {photo.name} ...")
        img_bytes = photo.read_bytes()
        encrypted = fernet.encrypt(img_bytes)
        enc_path.write_bytes(encrypted)
        print(f"            -> {enc_path.name} ({len(encrypted)//1024} KB)")
        encrypted_count += 1

    # Check for optional custom prompt file
    custom_prompt = TO_GENERATE / "prompt.txt"
    if custom_prompt.exists():
        shutil.copy(str(custom_prompt), str(GEN_INPUT / "prompt.txt"))
        print("  [PROMPT] Custom prompt included.")

    if encrypted_count == 0:
        print("\n[INFO] All reference photos already encrypted. Nothing new to push.")
        input("Press Enter to exit...")
        return

    print(f"\nEncrypted {encrypted_count} photo(s). Pushing to GitHub...\n")

    os.chdir(BASE)

    # 1. Pull latest changes first
    subprocess.run("git pull --rebase origin main", shell=True, capture_output=True, text=True)

    # 2. Add encrypted files
    subprocess.run("git add generate_input/", shell=True, capture_output=True, text=True)

    # 3. Commit
    subprocess.run(f'git commit -m "Add {encrypted_count} encrypted reference photo for ad generation"', shell=True, capture_output=True, text=True)

    # 4. Push with auto-sync retry
    pushed = False
    for attempt in range(1, 4):
        print(f"  $ git push")
        r = subprocess.run("git push origin main", shell=True, capture_output=True, text=True)
        if r.returncode == 0:
            pushed = True
            break
        print("  [SYNC] Remote updated, syncing with git pull --rebase...")
        subprocess.run("git pull --rebase origin main", shell=True, capture_output=True, text=True)

    if not pushed:
        print("  [GIT ERROR] Push failed. Check internet connection.")
        input("Press Enter to exit...")
        sys.exit(1)

    print()
    print("=" * 55)
    print(f"  DONE! Reference photo pushed to GitHub (100% Encrypted).")
    print()
    print("  GitHub Actions is now generating the UGC Sunscreen Ad.")
    print("  Check progress at: GitHub Repo -> Actions tab")
    print("  (Takes ~3-4 minutes on GitHub runner)")
    print()
    print("  When done, double-click: pull_generated.bat")
    print("=" * 55)
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
