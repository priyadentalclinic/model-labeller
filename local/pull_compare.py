"""
pull_compare.py — Pulls labels from GitHub and displays a side-by-side comparison of all 3 models.
Run via pull_compare.bat
"""
import os, sys, json, pathlib, subprocess

BASE        = pathlib.Path(__file__).parent.parent
OUTPUT_DIR  = BASE / "output_labels"


def main():
    print("=" * 75)
    print("  ModelBot — 3-Model Side-by-Side Comparison (LLaVA vs MiniCPM vs Qwen)")
    print("=" * 75)

    print("\n[1/2] Pulling latest labels from GitHub...")
    os.chdir(BASE)
    r = subprocess.run("git pull --rebase origin main", shell=True, capture_output=True, text=True)
    print(f"  {r.stdout.strip() or r.stderr.strip()}")

    json_files = sorted(OUTPUT_DIR.glob("*.json"))
    if not json_files:
        print("\n[INFO] No label files found yet. GitHub Actions may still be running.")
        print("       Check: GitHub Repo -> Actions tab")
        input("Press Enter to exit...")
        return

    # Group by original photo name
    photo_models = {}
    for jf in json_files:
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
            orig = data.get("original_filename", "unknown")
            model = data.get("model_used", "unknown")
            if orig not in photo_models:
                photo_models[orig] = {}
            photo_models[orig][model] = data.get("labels", {})
        except Exception:
            pass

    print(f"\n[2/2] Comparison for {len(photo_models)} photo(s):\n")

    for photo_name, models in photo_models.items():
        print("=" * 75)
        print(f"PHOTO: {photo_name}")
        print("=" * 75)

        model_names = sorted(models.keys())
        if not model_names:
            continue

        # Header
        header = f"{'Attribute':<18} | " + " | ".join([f"{m:<18}" for m in model_names])
        print(header)
        print("-" * len(header))

        attributes = [
            ("Archetype",     lambda l: l.get("archetype", "-")),
            ("Folder",        lambda l: l.get("folder", "-")),
            ("Age",           lambda l: f"{l.get('age_years', '-')} ({l.get('age_group', '-')})"),
            ("Body Build",    lambda l: l.get("body_type", "-")),
            ("Ethnicity",     lambda l: f"{l.get('regional_type', '-')} (desi={l.get('is_desi', '-')})"),
            ("Clothing",      lambda l: l.get("clothing_type", "-")),
            ("Pose",          lambda l: l.get("pose", "-")),
            ("Mood",          lambda l: l.get("mood", "-")),
            ("Hair",          lambda l: l.get("hair_length", "-")),
            ("Top Tags",      lambda l: ", ".join(l.get("combo_tags", [])[:5])),
        ]

        for attr_title, extractor in attributes:
            row_vals = []
            for m in model_names:
                val = str(extractor(models[m]))
                if len(val) > 18:
                    val = val[:16] + ".."
                row_vals.append(f"{val:<18}")
            print(f"{attr_title:<18} | " + " | ".join(row_vals))

        print("=" * 75)
        print()

    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
