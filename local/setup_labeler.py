"""
setup_labeler.py — Run ONCE on your laptop to configure everything.
===================================================================
"""
import os, sys, subprocess, pathlib

BASE = pathlib.Path(__file__).parent.parent  # ModelBotLabeler/

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def main():
    print("=" * 60)
    print("  ModelBot Labeler — One-Time Setup")
    print("=" * 60)

    # 1. Install cryptography
    print("\n[1/4] Checking Python dependencies...")
    try:
        from cryptography.fernet import Fernet
        print("  OK: cryptography installed")
    except ImportError:
        print("  Installing cryptography...")
        subprocess.run([sys.executable, "-m", "pip", "install", "cryptography"], check=True)
        from cryptography.fernet import Fernet
        print("  OK: cryptography installed")

    # 2. Generate encryption key
    print("\n[2/4] Generating AES encryption key...")
    from cryptography.fernet import Fernet
    key = Fernet.generate_key()
    key_str = key.decode()

    key_file = BASE / "local" / "config.key"
    key_file.write_bytes(key)
    print(f"  Key saved to: {key_file}")
    print()
    print("  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("  !! IMPORTANT — ADD THIS TO GITHUB SECRETS     !!")
    print("  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print()
    print("  1. Go to: GitHub Repo → Settings → Secrets and variables → Actions")
    print("  2. Click: New repository secret")
    print("  3. Name:  PHOTO_DECRYPT_KEY")
    print(f"  4. Value: {key_str}")
    print()
    input("  Press ENTER after you have added the secret to GitHub...")

    # 3. Check git
    print("\n[3/4] Checking git setup...")
    r = run("git --version")
    if r.returncode != 0:
        print("  ERROR: git not found. Install git from https://git-scm.com/")
        sys.exit(1)
    print(f"  OK: {r.stdout.strip()}")

    r = run(f"git -C {BASE} remote -v")
    if "origin" not in r.stdout:
        print()
        print("  No GitHub remote found. Please:")
        print("  1. Create a new GitHub repo (can be public or private)")
        print("  2. Run these commands in ModelBotLabeler/ folder:")
        print(f"     git init")
        print(f"     git remote add origin https://github.com/YOURUSERNAME/YOURREPO.git")
        print(f"     git add .")
        print(f"     git commit -m Initial commit")
        print(f"     git push -u origin main")
    else:
        print(f"  OK: Remote found:\n{r.stdout.strip()}")

    # 4. Create local folders
    print("\n[4/4] Creating local folders...")
    for folder in ["to_upload", "sorted_photos", "input_encrypted", "output_labels"]:
        (BASE / folder).mkdir(exist_ok=True)
        print(f"  Created: {folder}/")

    print()
    print("=" * 60)
    print("  SETUP COMPLETE!")
    print()
    print("  HOW TO USE:")
    print("  1. Put photos in:     ModelBotLabeler/to_upload/")
    print("  2. Double-click:      local/encrypt_push.bat")
    print("     (Encrypts photos and pushes to GitHub)")
    print("  3. Wait ~10-15 min for GitHub Actions to finish")
    print("     (Check progress at: GitHub Repo → Actions tab)")
    print("  4. Double-click:      local/pull_sort.bat")
    print("     (Downloads labels and sorts photos into folders)")
    print("  5. Find sorted photos in: sorted_photos/")
    print("=" * 60)

if __name__ == "__main__":
    main()
