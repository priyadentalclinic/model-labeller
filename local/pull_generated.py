"""
pull_generated.py — Pulls encrypted generated ads from GitHub, decrypts them locally.
Run via pull_generated.bat
"""
import os, sys, pathlib, subprocess, urllib.parse

BASE            = pathlib.Path(__file__).parent.parent
GEN_OUTPUT      = BASE / "generate_output"
FINAL_DIR       = BASE / "generated_photos"
KEY_FILE        = BASE / "local" / "config.key"
FINAL_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("=" * 55)
    print("  ModelBot — Pull & Decrypt Generated UGC Ads")
    print("=" * 55)

    if not KEY_FILE.exists():
        print("[ERROR] config.key not found. Run setup_labeler.bat first.")
        input("Press Enter to exit...")
        sys.exit(1)

    from cryptography.fernet import Fernet
    key    = KEY_FILE.read_bytes()
    fernet = Fernet(key)

    print("\n[1/2] Pulling latest generated ads from GitHub...")
    os.chdir(BASE)
    r = subprocess.run("git pull --rebase origin main", shell=True, capture_output=True, text=True)
    print(f"  {r.stdout.strip() or r.stderr.strip()}")

    enc_files = sorted(GEN_OUTPUT.glob("*.enc"))
    if not enc_files:
        print("\n[INFO] No generated ad files found yet. GitHub Actions may still be running.")
        print("       Check: GitHub Repo -> Actions tab")
        input("Press Enter to exit...")
        return

    print(f"\n[2/2] Found {len(enc_files)} encrypted ad file(s). Decrypting locally...\n")

    decrypted_count = 0
    for ef in enc_files:
        try:
            # clean output filename: e.g. ref_ad.png.enc -> ref_ad.png
            clean_name = ef.stem
            if not clean_name.lower().endswith(".png"):
                clean_name += ".png"

            dest_path = FINAL_DIR / clean_name

            if dest_path.exists():
                print(f"  [SKIP] Already decrypted: {clean_name}")
                continue

            enc_bytes = ef.read_bytes()
            png_bytes = fernet.decrypt(enc_bytes)
            dest_path.write_bytes(png_bytes)
            print(f"  [DECRYPTED] {clean_name} -> generated_photos/{clean_name}")
            decrypted_count += 1
        except Exception as e:
            print(f"  [ERROR] Failed to decrypt {ef.name}: {e}")

    print()
    print("=" * 55)
    print(f"  DONE! {decrypted_count} new UGC ad photo(s) decrypted.")
    print(f"  Folder: {FINAL_DIR}")
    print("=" * 55)

    # Open folder in Windows Explorer
    try:
        os.startfile(str(FINAL_DIR))
    except Exception:
        pass

    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
