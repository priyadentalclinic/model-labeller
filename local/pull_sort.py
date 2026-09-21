"""
pull_sort.py — Pull label files from GitHub and sort photos into folders.
Run via pull_sort.bat  (or: python pull_sort.py)
"""
import os, sys, json, shutil, pathlib, subprocess, urllib.parse

BASE         = pathlib.Path(__file__).parent.parent
TO_UPLOAD    = BASE / "to_upload"
OUTPUT_DIR   = BASE / "output_labels"
SORTED_DIR   = BASE / "sorted_photos"
SORTED_DIR.mkdir(exist_ok=True)

def main():
    print("=" * 55)
    print("  ModelBot — Pull Labels and Sort Photos")
    print("=" * 55)

    # Git pull
    print("\n[1/3] Pulling latest labels from GitHub...")
    os.chdir(BASE)
    r = subprocess.run("git pull", shell=True, capture_output=True, text=True)
    print(f"  {r.stdout.strip() or r.stderr.strip()}")

    # Find label files
    label_files = sorted(OUTPUT_DIR.glob("*_labels.json"))
    if not label_files:
        print()
        print("[INFO] No label files yet. GitHub Actions may still be running.")
        print("       Check: GitHub Repo -> Actions tab")
        input("Press Enter to exit...")
        return

    print(f"\n[2/3] Found {len(label_files)} label file(s).\n")
    sorted_count  = 0
    missing_count = 0

    for lf in label_files:
        try:
            data = json.loads(lf.read_text(encoding="utf-8"))
            original_name = data["original_filename"]
            labels        = data["labels"]
            folder_name   = labels["folder"]  # e.g. "bhabhi/curvy"
            compound      = labels["compound_persona"]
            tags          = labels["combo_tags"]

            # Find the original photo in to_upload/
            photo_path = TO_UPLOAD / original_name
            if not photo_path.exists():
                print(f"  [NOT FOUND] {original_name} — already moved or not in to_upload/")
                missing_count += 1
                continue

            # Create destination folder
            dest_dir = SORTED_DIR / folder_name
            dest_dir.mkdir(parents=True, exist_ok=True)

            # Move photo to sorted folder
            dest = dest_dir / original_name
            if dest.exists():
                # Add number suffix if collision
                stem  = photo_path.stem
                ext   = photo_path.suffix
                n     = 1
                while dest.exists():
                    dest = dest_dir / f"{stem}_{n}{ext}"
                    n   += 1

            shutil.move(str(photo_path), str(dest))
            sorted_count += 1
            print(f"  [SORTED] {original_name}")
            print(f"           Folder  : sorted_photos/{folder_name}/")
            print(f"           Persona : {compound}")
            print(f"           Tags    : {tags[:6]}...")
            print()

        except Exception as e:
            print(f"  [ERROR] Processing {lf.name}: {e}")

    print("[3/3] Summary")
    print(f"  Sorted  : {sorted_count} photo(s)")
    print(f"  Missing : {missing_count} photo(s) (already moved)")
    print()
    print(f"  Find sorted photos in:")
    print(f"  {SORTED_DIR}")
    print("=" * 55)
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
