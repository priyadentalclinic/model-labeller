"""
pull_report.py — Pulls labels from GitHub and displays individual detailed reports for every photo labeled by Qwen 2.5-VL.
Run via pull_report.bat  (or: python pull_report.py)
"""
import os, sys, json, pathlib, subprocess

BASE        = pathlib.Path(__file__).parent.parent
OUTPUT_DIR  = BASE / "output_labels"


def print_photo_report(idx: int, total: int, data: dict):
    orig_name = data.get("original_filename", "Unknown")
    model     = data.get("model_used", "qwen2.5vl:7b")
    labels    = data.get("labels", {})
    raw       = labels.get("llava_raw", {})

    print("=" * 75)
    print(f"  PHOTO [{idx}/{total}]: {orig_name}")
    print(f"  Model: {model}  |  Labeled at: {data.get('labeled_at', 'N/A')}")
    print("=" * 75)

    print(f"  [ARCHETYPE]        : {labels.get('archetype', 'N/A')}")
    print(f"  [TARGET FOLDER]    : sorted_photos/{labels.get('folder', 'N/A')}/")
    print(f"  [COMPOUND PERSONA] : {labels.get('compound_persona', 'N/A')}")
    print("-" * 75)

    age_val = f"{labels.get('age_years', 'N/A')} yrs ({labels.get('age_group', 'N/A')})"
    print(f"  Age                : {age_val:<25} Skin Tone     : {labels.get('skin_tone', 'N/A')}")
    
    body_val = f"{labels.get('body_type', 'N/A')} ({raw.get('BODY_DETAIL', labels.get('body_type', 'N/A'))})"
    print(f"  Body Build         : {body_val:<25} Mood          : {labels.get('mood', 'N/A')}")

    is_desi_str = "YES (Indian)" if labels.get('is_desi', False) else "NO"
    eth_val = f"{labels.get('regional_type', 'N/A')} [Desi: {is_desi_str}]"
    print(f"  Ethnicity/Region   : {eth_val:<25} Pose          : {labels.get('pose', 'N/A')}")

    print(f"  Clothing           : {labels.get('clothing_type', 'N/A'):<25} Hair Length   : {labels.get('hair_length', 'N/A')}")
    print(f"  Boldness Level     : {labels.get('boldness', 'N/A')}")

    print("-" * 75)
    tags = labels.get("combo_tags", [])
    print(f"  Tags ({len(tags)})         : {', '.join(tags)}")

    queries = [q for q in labels.get("query_matches", []) if q.get("match_pct", 0) >= 50]
    if queries:
        q_strs = [f"{q['query']} ({q['match_pct']}%)" for q in queries[:4]]
        print(f"  Matched Searches   : {', '.join(q_strs)}")

    print("=" * 75)
    print()


def main():
    print("=" * 75)
    print("  ModelBot — Qwen 2.5-VL Individual Photo Inspection Reports")
    print("=" * 75)

    print("\n[1/2] Pulling latest labels from GitHub...")
    os.chdir(BASE)
    r = subprocess.run("git pull --rebase origin main", shell=True, capture_output=True, text=True)
    print(f"  {r.stdout.strip() or r.stderr.strip()}")

    # Collect Qwen label files first, fallback to all label files
    qwen_files = sorted(OUTPUT_DIR.glob("*_qwen2.5vl.json"))
    if not qwen_files:
        qwen_files = sorted(OUTPUT_DIR.glob("*.json"))

    # Filter out empty or gitkeep
    valid_reports = []
    for jf in qwen_files:
        if jf.name == ".gitkeep":
            continue
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
            if "labels" in data:
                valid_reports.append(data)
        except Exception:
            pass

    if not valid_reports:
        print("\n[INFO] No label reports found yet. GitHub Actions may still be running.")
        print("       Check: GitHub Repo -> Actions tab")
        input("Press Enter to exit...")
        return

    print(f"\n[2/2] Generated Individual Reports for {len(valid_reports)} Photo(s):\n")

    for i, report in enumerate(valid_reports, 1):
        print_photo_report(i, len(valid_reports), report)

    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
