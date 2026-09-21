# ModelBot Photo Labeler

Automated Indian photo labeling system using LLaVA-Phi3 AI.

## How It Works

1. Photos are encrypted locally with AES-256
2. Encrypted photos push to GitHub (unreadable to anyone)
3. GitHub Actions runs LLaVA-Phi3 to label each photo
4. Label files commit back to the repo
5. Local script sorts photos into folders based on labels

## Setup (Run Once)

Double-click: `local/setup_labeler.bat`

## Daily Use

1. Put photos in `to_upload/` folder
2. Double-click `local/encrypt_push.bat`
3. Wait 10-15 min (check GitHub Actions tab)
4. Double-click `local/pull_sort.bat`
5. Find sorted photos in `sorted_photos/`

## Labels Generated Per Photo

- `compound_persona` (e.g. `prime_desi_curvy (bhabhi)`)
- `archetype` (college_girl / bhabhi / desi_glam / south_indian_beauty / punjabi_kudi / etc.)
- `combo_tags` (full searchable tag list)
- `folder` (auto sort destination)
- `skin_tone`, `body_type`, `boldness`, `regional_type`, `mood`
