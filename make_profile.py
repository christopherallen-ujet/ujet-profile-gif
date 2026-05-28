#!/usr/bin/env python3
"""
UJET Animated Profile Picture Generator

Takes a photo of you and produces a 480x480 animated GIF that loops:
  your photo -> UJET blue background -> ujet.cx logo -> back to your photo

Branding (logo, color, durations) is locked to UJET. Just point it at a photo.

Usage:
    python make_profile.py path/to/your_photo.jpg
    python make_profile.py photo.jpg --output my_avatar.gif

Requires: Pillow, numpy
    pip install Pillow numpy
"""
import argparse
import os
import sys
from pathlib import Path

try:
    import numpy as np
    from PIL import Image
except ImportError:
    print("ERROR: Missing dependencies. Install with:")
    print("    pip install Pillow numpy")
    sys.exit(1)

# ---- Locked UJET branding ----
UJET_BLUE = (16, 159, 255)
SIZE = 480
FPS = 10
FADE_DUR = 0.9       # seconds per fade
FACE_HOLD = 4.8      # seconds your photo is held
LOGO_HOLD = 1.2      # seconds the logo is held
BLUE_HOLD = 0.3      # brief beat on solid blue between fade and logo
LOGO_WIDTH_PCT = 0.72  # logo width as fraction of canvas

SCRIPT_DIR = Path(__file__).parent.resolve()
DEFAULT_LOGO_PATH = SCRIPT_DIR / "assets" / "ujet_logo.png"


def smoothstep(x: float) -> float:
    """Ease-in-out curve."""
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def prepare_photo(photo_path: Path) -> np.ndarray:
    """
    Load a photo, square-crop centered, and resize to 480x480.

    Handles any aspect ratio. The photo is used as-is (no color filters).
    Returns the photo as a float32 numpy array (H, W, 3).
    """
    img = Image.open(photo_path).convert("RGB")
    w, h = img.size

    # Center-crop to a square (use the shorter dimension)
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))

    # Resize to canvas
    img = img.resize((SIZE, SIZE), Image.LANCZOS)
    return np.array(img, dtype=np.float32)


def prepare_logo_screen(logo_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """
    Build the logo screen: UJET blue background with white logo centered.

    Returns:
        (logo_screen_arr, logo_white_mask) — both float32 numpy arrays.
        The mask is 1.0 where the logo is white, 0.0 where the background shows.
    """
    logo_raw = Image.open(logo_path).convert("RGB")

    # The logo file is white text on black. Use grayscale as the alpha channel.
    arr = np.array(logo_raw)
    gray = arr.mean(axis=-1)
    alpha = (gray / 255.0 * 255).astype(np.uint8)
    rgba = np.zeros((*arr.shape[:2], 4), dtype=np.uint8)
    rgba[..., :3] = 255   # white text
    rgba[..., 3] = alpha
    logo_white = Image.fromarray(rgba)

    # Resize logo to target width, preserving aspect
    target_w = int(SIZE * LOGO_WIDTH_PCT)
    aspect = logo_raw.size[1] / logo_raw.size[0]
    target_h = int(target_w * aspect)
    logo_sized = logo_white.resize((target_w, target_h), Image.LANCZOS)

    # Composite onto a UJET-blue canvas
    canvas = Image.new("RGB", (SIZE, SIZE), UJET_BLUE)
    paste_x = (SIZE - target_w) // 2
    paste_y = (SIZE - target_h) // 2
    canvas.paste(logo_sized, (paste_x, paste_y), logo_sized)

    logo_screen_arr = np.array(canvas, dtype=np.float32)

    # Build white-pixel mask (where logo text is, vs background blue)
    diff = np.abs(logo_screen_arr - np.array(UJET_BLUE)).sum(axis=-1)
    white_mask = np.clip(diff / 100, 0, 1)[..., None]

    return logo_screen_arr, white_mask


def build_frames(face_arr: np.ndarray,
                 logo_white_mask: np.ndarray) -> list[Image.Image]:
    """
    Build the full sequence of frames.

    Loop phases (sequential, no crossfade — prevents ghosting):
      face_hold -> fade_to_blue -> blue_hold -> fade_logo_in
      -> logo_hold -> fade_logo_out -> blue_hold -> fade_to_face
    """
    total_dur = FACE_HOLD + 4 * FADE_DUR + LOGO_HOLD + 2 * BLUE_HOLD
    n_frames = int(total_dur * FPS)

    blue_arr = np.full_like(face_arr, 0, dtype=np.float32)
    blue_arr[..., 0] = UJET_BLUE[0]
    blue_arr[..., 1] = UJET_BLUE[1]
    blue_arr[..., 2] = UJET_BLUE[2]
    white_field = np.full_like(face_arr, 255.0)

    # Absolute time boundaries (in seconds) for each phase end
    b = [0.0]
    for d in [FACE_HOLD, FADE_DUR, BLUE_HOLD, FADE_DUR, LOGO_HOLD, FADE_DUR, BLUE_HOLD, FADE_DUR]:
        b.append(b[-1] + d)

    frames = []
    for f in range(n_frames):
        t = f / FPS

        # Determine face->blue blend (fb) and logo opacity (lo) at this time
        if t < b[1]:
            fb, lo = 0.0, 0.0
        elif t < b[2]:
            fb, lo = smoothstep((t - b[1]) / FADE_DUR), 0.0
        elif t < b[3]:
            fb, lo = 1.0, 0.0
        elif t < b[4]:
            fb, lo = 1.0, smoothstep((t - b[3]) / FADE_DUR)
        elif t < b[5]:
            fb, lo = 1.0, 1.0
        elif t < b[6]:
            fb, lo = 1.0, 1.0 - smoothstep((t - b[5]) / FADE_DUR)
        elif t < b[7]:
            fb, lo = 1.0, 0.0
        elif t < b[8]:
            fb, lo = 1.0 - smoothstep((t - b[7]) / FADE_DUR), 0.0
        else:
            fb, lo = 0.0, 0.0

        # Stage 1: blend face <-> solid blue
        bg = face_arr * (1 - fb) + blue_arr * fb
        # Stage 2: composite white logo on top
        a = logo_white_mask * lo
        out = bg * (1 - a) + white_field * a

        frames.append(Image.fromarray(out.clip(0, 255).astype(np.uint8)))

    return frames


def save_gif(frames: list[Image.Image], output_path: Path, num_colors: int = 96) -> None:
    """Quantize and save the frames as an animated GIF."""
    quantized = [fr.quantize(colors=num_colors, method=2, dither=0) for fr in frames]
    quantized[0].save(
        output_path,
        save_all=True,
        append_images=quantized[1:],
        duration=int(1000 / FPS),
        loop=0,
        optimize=True,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate an animated UJET profile GIF from a photo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example:\n"
            "  python make_profile.py headshot.jpg\n"
            "  python make_profile.py headshot.jpg --output my_avatar.gif\n\n"
            "The output is a 480x480 square GIF. When you upload it as your\n"
            "Google profile photo, Google will let you crop a circle from it."
        ),
    )
    parser.add_argument("photo", type=Path, help="Path to your photo (JPG, PNG, etc).")
    parser.add_argument("-o", "--output", type=Path, default=Path("ujet_profile.gif"),
                        help="Output GIF path (default: ujet_profile.gif).")
    parser.add_argument("--logo", type=Path, default=DEFAULT_LOGO_PATH,
                        help="Path to logo PNG (default: bundled ujet.cx logo).")
    args = parser.parse_args()

    if not args.photo.exists():
        print(f"ERROR: Photo not found: {args.photo}")
        sys.exit(1)

    if not args.logo.exists():
        print(f"ERROR: Logo not found: {args.logo}")
        print("       Make sure you cloned the full repo (assets/ujet_logo.png).")
        sys.exit(1)

    print(f"Loading photo: {args.photo}")
    face_arr = prepare_photo(args.photo)

    print(f"Loading logo: {args.logo}")
    _, logo_mask = prepare_logo_screen(args.logo)

    total_dur = FACE_HOLD + 4 * FADE_DUR + LOGO_HOLD + 2 * BLUE_HOLD
    n_frames = int(total_dur * FPS)
    print(f"Rendering {n_frames} frames ({total_dur:.1f}s loop at {FPS} fps)...")
    frames = build_frames(face_arr, logo_mask)

    print(f"Saving to: {args.output}")
    save_gif(frames, args.output)

    size_kb = os.path.getsize(args.output) / 1024
    print(f"Done! {args.output} ({size_kb:.0f} KB)")
    print()
    print("Upload tip: when setting this as your Google profile picture,")
    print("Google's upload UI will let you crop a circle from the square.")


if __name__ == "__main__":
    main()
