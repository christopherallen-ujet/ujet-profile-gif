#!/usr/bin/env python3
"""
make_icon.py - Generate icon.png (1024x1024 app icon) at build time.

Draws a UJET-blue rounded-square tile with the embedded ujet.cx wordmark
centered on it. Reusing the wordmark already embedded in ujet_profile_app.py
means there is no binary asset to commit - the repo stays all text.
"""
import numpy as np
from PIL import Image, ImageDraw

from ujet_profile_app import load_embedded_logo, UJET_BLUE

SIZE = 1024
WORDMARK_WIDTH_PCT = 0.62
CORNER_RADIUS_PCT = 0.225


def main():
    icon = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    radius = int(SIZE * CORNER_RADIUS_PCT)
    draw.rounded_rectangle([0, 0, SIZE, SIZE], radius=radius, fill=UJET_BLUE + (255,))

    logo = load_embedded_logo().convert("L")
    rgba = np.zeros((*np.array(logo).shape, 4), dtype=np.uint8)
    rgba[..., :3] = 255            # white wordmark
    rgba[..., 3] = np.array(logo)  # grayscale doubles as alpha
    white = Image.fromarray(rgba)

    target_w = int(SIZE * WORDMARK_WIDTH_PCT)
    target_h = int(target_w * logo.size[1] / logo.size[0])
    white = white.resize((target_w, target_h), Image.LANCZOS)

    icon.paste(white, ((SIZE - target_w) // 2, (SIZE - target_h) // 2), white)
    icon.save("icon.png")
    print(f"Wrote icon.png {icon.size}")


if __name__ == "__main__":
    main()
