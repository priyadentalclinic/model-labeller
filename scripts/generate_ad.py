"""
generate_ad.py — Runs inside GitHub Actions runner.
===================================================
1. Decrypts reference photo in memory (never written to disk unencrypted).
2. Uses Stable Diffusion 1.5 + IP-Adapter Plus Face to generate consistent-character UGC ad.
3. Encrypts generated image in memory before saving to disk.
4. Saves to generate_output/*.png.enc.
"""
import os, sys, io, pathlib, traceback
from PIL import Image

try:
    from cryptography.fernet import Fernet
except ImportError:
    print("[ERROR] cryptography not installed.")
    sys.exit(1)

import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler

# ── Paths ─────────────────────────────────────────────────────────────
BASE            = pathlib.Path(__file__).parent.parent
INPUT_DIR       = BASE / "generate_input"
OUTPUT_DIR      = BASE / "generate_output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DECRYPT_KEY     = os.environ.get("DECRYPT_KEY", "").strip().encode()

DEFAULT_PROMPT = (
    "authentic UGC selfie of a beautiful 22-year-old Indian girl applying sunscreen cream on her cheek, "
    "glowing hydrated clear skin, soft natural smile, holding sunscreen tube, natural warm morning sunlight, "
    "casual top, front-camera smartphone review photo, high resolution, photorealistic, natural skin texture"
)

DEFAULT_NEGATIVE = (
    "ugly, deformed, disfigured, poor details, bad anatomy, bad eyes, extra fingers, cartoon, 3d, "
    "render, illustration, blurry, dark, oversaturated, painting, drawing"
)


def crop_to_square(img: Image.Image) -> Image.Image:
    """Smart crop to focus on face for IP-Adapter."""
    w, h = img.size
    if h > w:
        # In portrait photos, face is in the top section
        top = int(h * 0.03)
        bottom = min(h, top + w)
        crop_h = bottom - top
        return img.crop((0, top, w, top + crop_h)).resize((512, 512), Image.Resampling.LANCZOS)
    else:
        # In landscape photos, center crop
        min_dim = min(w, h)
        left = (w - min_dim) // 2
        top = (h - min_dim) // 2
        return img.crop((left, top, left + min_dim, top + min_dim)).resize((512, 512), Image.Resampling.LANCZOS)


def main():
    print("=" * 60)
    print("  ModelBot — Encrypted UGC Ad Generator (IP-Adapter FaceID)")
    print("=" * 60)

    if not DECRYPT_KEY:
        print("[ERROR] DECRYPT_KEY environment variable is not set!")
        sys.exit(1)

    try:
        fernet = Fernet(DECRYPT_KEY)
    except Exception as e:
        print(f"[ERROR] Invalid DECRYPT_KEY: {e}")
        sys.exit(1)

    enc_files = sorted(INPUT_DIR.glob("*.enc"))
    if not enc_files:
        print("[INFO] No .enc files found in generate_input/. Nothing to do.")
        sys.exit(0)

    # Check for custom prompt
    prompt_file = INPUT_DIR / "prompt.txt"
    if prompt_file.exists():
        prompt = prompt_file.read_text(encoding="utf-8").strip()
        print(f"[PROMPT] Using custom prompt:\n  {prompt}\n")
    else:
        prompt = DEFAULT_PROMPT
        print(f"[PROMPT] Using default UGC sunscreen ad prompt:\n  {prompt}\n")

    print("[1/3] Loading Stable Diffusion 1.5 + IP-Adapter FaceID...")
    model_id = "runwayml/stable-diffusion-v1-5"

    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float32,
        safety_checker=None,
    )
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)

    print("      Loading IP-Adapter weights...")
    pipe.load_ip_adapter(
        "h94/IP-Adapter",
        subfolder="models",
        weight_name="ip-adapter-plus-face_sd15.bin",
    )
    pipe.set_ip_adapter_scale(0.85)
    pipe.to("cpu")
    print("      Model loaded successfully on CPU!")

    print(f"\n[2/3] Processing {len(enc_files)} reference photo(s)...\n")

    for i, enc_path in enumerate(enc_files, 1):
        stem = enc_path.stem
        out_enc_path = OUTPUT_DIR / f"{stem}_ad.png.enc"

        print(f"[{i}/{len(enc_files)}] Decrypting reference: {enc_path.name} in memory...")
        enc_bytes = enc_path.read_bytes()
        try:
            raw_bytes = fernet.decrypt(enc_bytes)
            ref_image = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
            face_image = crop_to_square(ref_image)
        except Exception as e:
            print(f"  [ERROR] Decryption or image loading failed: {e}")
            continue

        print("      Generating new UGC ad image (20 steps)...")
        generated = pipe(
            prompt=prompt,
            negative_prompt=DEFAULT_NEGATIVE,
            ip_adapter_image=face_image,
            num_inference_steps=20,
            guidance_scale=7.0,
            height=512,
            width=512,
        ).images[0]

        print("      Encrypting generated image in memory before writing to disk...")
        buf = io.BytesIO()
        generated.save(buf, format="PNG")
        png_bytes = buf.getvalue()
        encrypted_output = fernet.encrypt(png_bytes)

        out_enc_path.write_bytes(encrypted_output)
        print(f"      [DONE] Saved encrypted ad: {out_enc_path.name} ({len(encrypted_output)//1024} KB)")
        print()

    print("=" * 60)
    print("  Generation complete! All outputs encrypted.")
    print("=" * 60)


if __name__ == "__main__":
    main()
