#!/usr/bin/env python3
"""
UJET Animated Profile Picture Generator

Takes a photo of you and produces a 480x480 animated GIF that loops:
  your photo -> UJET blue background -> ujet.cx logo -> back to your photo

Branding (logo, color, durations) is locked to UJET. Just point it at a photo.
The exact ujet.cx brand wordmark is embedded (base64), so the script is a
fully self-contained single file with no asset folder to clone. Pass --logo
to override with a different white-on-black logo PNG. If the embedded image
ever fails to decode, the wordmark is re-rendered from a system font.

Usage:
    python make_profile.py path/to/your_photo.jpg
    python make_profile.py photo.jpg --output my_avatar.gif
    python make_profile.py photo.jpg --logo assets/ujet_logo.png

Requires: Pillow, numpy
    pip install Pillow numpy
"""
import argparse
import base64
import os
import sys
from pathlib import Path

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
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
WORDMARK_TEXT = "ujet.cx"

# Exact ujet.cx brand wordmark (white on black), embedded as base64 so the
# script is a single self-contained file with no asset folder to clone.
EMBEDDED_LOGO_B64 = (
    "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"
)

SCRIPT_DIR = Path(__file__).parent.resolve()
# Optional bundled asset. If present, it takes precedence over the embedded logo.
DEFAULT_LOGO_PATH = SCRIPT_DIR / "assets" / "ujet_logo.png"

# Candidate bold fonts, in preference order. macOS paths first (this is an
# internal Mac fleet tool), then common Linux locations, then PIL fallback.
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Helvetica.ttc",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/SFNSDisplay.ttf",
    "/System/Library/Fonts/SFNS.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/google-fonts/Poppins-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def smoothstep(x: float) -> float:
    """Ease-in-out curve."""
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def load_bold_font(px: int) -> ImageFont.FreeTypeFont:
    """
    Load the first available bold TrueType font at the given pixel size.

    Falls back to PIL's bitmap default if no system font is found (the
    wordmark still renders, just less crisply).
    """
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, px)
            except Exception:
                continue
    return ImageFont.load_default()


def render_wordmark() -> Image.Image:
    """
    Render the 'ujet.cx' wordmark as white text on a black background.

    Returns an RGB image (white text on black) matching the format the
    rest of the pipeline expects, where grayscale doubles as the alpha
    channel. Rendered large so downstream resizing stays crisp.
    """
    render_px = 400
    font = load_bold_font(render_px)

    # Measure the text so we can size a tight canvas with a little padding.
    tmp = Image.new("RGB", (10, 10))
    bbox = ImageDraw.Draw(tmp).textbbox((0, 0), WORDMARK_TEXT, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    pad_x = int(render_px * 0.12)
    pad_y = int(render_px * 0.12)
    canvas = Image.new("RGB", (text_w + 2 * pad_x, text_h + 2 * pad_y), (0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    # Offset by the bbox origin so the glyphs sit inside the padding.
    draw.text((pad_x - bbox[0], pad_y - bbox[1]), WORDMARK_TEXT,
              font=font, fill=(255, 255, 255))
    return canvas


def load_embedded_logo() -> "Image.Image":
    """Decode the embedded ujet.cx brand wordmark (white on black)."""
    import io
    raw = base64.b64decode(EMBEDDED_LOGO_B64)
    return Image.open(io.BytesIO(raw))


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


def prepare_logo_screen(logo_img: Image.Image) -> tuple[np.ndarray, np.ndarray]:
    """
    Build the logo screen: UJET blue background with white logo centered.

    Accepts a PIL image of white text/logo on a black background (either a
    loaded PNG asset or the rendered wordmark).

    Returns:
        (logo_screen_arr, logo_white_mask) - both float32 numpy arrays.
        The mask is 1.0 where the logo is white, 0.0 where the background shows.
    """
    logo_raw = logo_img.convert("RGB")

    # White text on black -> use grayscale as the alpha channel.
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

    Loop phases (sequential, no crossfade - prevents ghosting):
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
    parser.add_argument("--logo", type=Path, default=None,
                        help="Optional white-on-black logo PNG. If omitted, the "
                             "embedded ujet.cx brand wordmark is used.")
    args = parser.parse_args()

    if not args.photo.exists():
        print(f"ERROR: Photo not found: {args.photo}")
        sys.exit(1)

    print(f"Loading photo: {args.photo}")
    face_arr = prepare_photo(args.photo)

    # Resolve the logo source: explicit --logo, then an optional bundled asset,
    # then the embedded brand wordmark, then a text render as a final fallback.
    if args.logo is not None:
        if not args.logo.exists():
            print(f"ERROR: Logo not found: {args.logo}")
            sys.exit(1)
        print(f"Loading logo: {args.logo}")
        logo_img = Image.open(args.logo)
    elif DEFAULT_LOGO_PATH.exists():
        print(f"Loading logo: {DEFAULT_LOGO_PATH}")
        logo_img = Image.open(DEFAULT_LOGO_PATH)
    else:
        try:
            logo_img = load_embedded_logo()
            print("Using embedded ujet.cx brand wordmark")
        except Exception as exc:
            print(f"Embedded logo unavailable ({exc}); rendering {WORDMARK_TEXT} from text")
            logo_img = render_wordmark()

    _, logo_mask = prepare_logo_screen(logo_img)

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
