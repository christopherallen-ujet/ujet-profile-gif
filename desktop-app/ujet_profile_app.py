#!/usr/bin/env python3
"""
UJET Profile GIF - desktop app

A double-click GUI front end for the UJET animated profile picture generator.
Pick a photo, click Generate, and get a 480x480 animated GIF that loops your
photo to the ujet.cx logo on UJET blue. The brand wordmark is embedded, so
the app is fully self-contained with no asset files to ship alongside it.

Run directly during development:
    python3 ujet_profile_app.py

Packaged into a .app with PyInstaller (see build_app.sh) for distribution.
"""
import base64
import io
import os
import sys
import threading
from pathlib import Path

import numpy as np
from PIL import Image

# ---- Locked UJET branding ----
UJET_BLUE = (16, 159, 255)
UJET_BLUE_HEX = "#109FFF"
UJET_BLUE_DARK_HEX = "#0B7FCC"
SIZE = 480
FPS = 10
FADE_DUR = 0.9       # seconds per fade
FACE_HOLD = 4.8      # seconds the photo is held
LOGO_HOLD = 1.2      # seconds the logo is held
BLUE_HOLD = 0.3      # brief beat on solid blue between fade and logo
LOGO_WIDTH_PCT = 0.72

# Exact ujet.cx brand wordmark (white on black), embedded as base64 so the
# app is a single self-contained file with no asset folder to ship.
EMBEDDED_LOGO_B64 = (
    "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"
)

DEFAULT_OUTPUT = Path.home() / "Downloads" / "ujet_profile.gif"


def smoothstep(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def load_embedded_logo() -> Image.Image:
    """Decode the embedded ujet.cx brand wordmark (white on black)."""
    return Image.open(io.BytesIO(base64.b64decode(EMBEDDED_LOGO_B64)))


def prepare_photo(photo_path) -> np.ndarray:
    """Load a photo, center-crop to a square, and resize to the canvas."""
    img = Image.open(photo_path).convert("RGB")
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    img = img.resize((SIZE, SIZE), Image.LANCZOS)
    return np.array(img, dtype=np.float32)


def prepare_logo_mask(logo_img: Image.Image) -> np.ndarray:
    """Build the white-pixel mask for the centered logo on UJET blue."""
    logo_raw = logo_img.convert("RGB")
    arr = np.array(logo_raw)
    gray = arr.mean(axis=-1)
    alpha = (gray / 255.0 * 255).astype(np.uint8)
    rgba = np.zeros((*arr.shape[:2], 4), dtype=np.uint8)
    rgba[..., :3] = 255
    rgba[..., 3] = alpha
    logo_white = Image.fromarray(rgba)

    target_w = int(SIZE * LOGO_WIDTH_PCT)
    aspect = logo_raw.size[1] / logo_raw.size[0]
    target_h = int(target_w * aspect)
    logo_sized = logo_white.resize((target_w, target_h), Image.LANCZOS)

    canvas = Image.new("RGB", (SIZE, SIZE), UJET_BLUE)
    paste_x = (SIZE - target_w) // 2
    paste_y = (SIZE - target_h) // 2
    canvas.paste(logo_sized, (paste_x, paste_y), logo_sized)

    screen = np.array(canvas, dtype=np.float32)
    diff = np.abs(screen - np.array(UJET_BLUE)).sum(axis=-1)
    return np.clip(diff / 100, 0, 1)[..., None]


def build_frames(face_arr: np.ndarray, logo_mask: np.ndarray) -> list:
    total_dur = FACE_HOLD + 4 * FADE_DUR + LOGO_HOLD + 2 * BLUE_HOLD
    n_frames = int(total_dur * FPS)

    blue_arr = np.zeros_like(face_arr)
    blue_arr[..., 0], blue_arr[..., 1], blue_arr[..., 2] = UJET_BLUE
    white_field = np.full_like(face_arr, 255.0)

    b = [0.0]
    for d in [FACE_HOLD, FADE_DUR, BLUE_HOLD, FADE_DUR, LOGO_HOLD, FADE_DUR, BLUE_HOLD, FADE_DUR]:
        b.append(b[-1] + d)

    frames = []
    for f in range(n_frames):
        t = f / FPS
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

        bg = face_arr * (1 - fb) + blue_arr * fb
        a = logo_mask * lo
        out = bg * (1 - a) + white_field * a
        frames.append(Image.fromarray(out.clip(0, 255).astype(np.uint8)))
    return frames


def save_gif(frames: list, output_path, num_colors: int = 96) -> None:
    quantized = [fr.quantize(colors=num_colors, method=2, dither=0) for fr in frames]
    quantized[0].save(
        output_path,
        save_all=True,
        append_images=quantized[1:],
        duration=int(1000 / FPS),
        loop=0,
        optimize=True,
    )


def generate_profile_gif(photo_path, output_path=DEFAULT_OUTPUT) -> Path:
    """Full pipeline: photo in, animated UJET profile GIF out. Returns the path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    face_arr = prepare_photo(photo_path)
    logo_mask = prepare_logo_mask(load_embedded_logo())
    frames = build_frames(face_arr, logo_mask)
    save_gif(frames, output_path)
    return output_path


# --------------------------------------------------------------------------
# GUI (CustomTkinter). Imported lazily so the generation logic above can be
# imported and tested headlessly without a display.
# --------------------------------------------------------------------------
def main():
    import tkinter as tk
    from tkinter import filedialog
    import customtkinter as ctk

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.title("UJET Profile GIF")
    app.geometry("520x640")
    app.minsize(520, 640)

    state = {"photo": None, "busy": False}

    # ---- Header ----
    header = ctk.CTkFrame(app, fg_color=UJET_BLUE_HEX, corner_radius=0, height=110)
    header.pack(fill="x")
    header.pack_propagate(False)
    ctk.CTkLabel(
        header, text="ujet.cx", font=ctk.CTkFont(size=34, weight="bold"),
        text_color="white",
    ).pack(pady=(22, 0))
    ctk.CTkLabel(
        header, text="Animated Profile Picture Generator",
        font=ctk.CTkFont(size=13), text_color="white",
    ).pack()

    body = ctk.CTkFrame(app, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=28, pady=24)

    # ---- Photo preview ----
    preview = ctk.CTkLabel(
        body, text="No photo selected", width=300, height=300,
        fg_color=("#e6e6e6", "#2b2b2b"), corner_radius=16,
        font=ctk.CTkFont(size=14),
    )
    preview.pack(pady=(4, 18))

    def render_preview(path):
        img = Image.open(path).convert("RGB")
        w, h = img.size
        side = min(w, h)
        img = img.crop(((w - side) // 2, (h - side) // 2,
                        (w - side) // 2 + side, (h - side) // 2 + side))
        img = img.resize((300, 300), Image.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(300, 300))
        preview.configure(image=ctk_img, text="")
        preview.image = ctk_img  # keep a reference

    status = ctk.CTkLabel(body, text="Choose a photo to get started.",
                          font=ctk.CTkFont(size=13), text_color=("gray30", "gray70"))

    generate_btn = ctk.CTkButton(
        body, text="Generate GIF", height=46,
        font=ctk.CTkFont(size=16, weight="bold"),
        fg_color=UJET_BLUE_HEX, hover_color=UJET_BLUE_DARK_HEX,
    )

    progress = ctk.CTkProgressBar(body, mode="indeterminate", height=8)

    def set_busy(busy, message=None):
        state["busy"] = busy
        if busy:
            generate_btn.configure(state="disabled", text="Generating...")
            choose_btn.configure(state="disabled")
            progress.pack(fill="x", pady=(6, 0))
            progress.start()
        else:
            generate_btn.configure(state="normal", text="Generate GIF")
            choose_btn.configure(state="normal")
            progress.stop()
            progress.pack_forget()
        if message:
            status.configure(text=message)

    def choose_photo():
        path = filedialog.askopenfilename(
            title="Choose a photo",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.heic *.tif *.tiff *.bmp"),
                       ("All files", "*.*")],
        )
        if not path:
            return
        state["photo"] = path
        try:
            render_preview(path)
        except Exception:
            preview.configure(text=os.path.basename(path), image=None)
        status.configure(text=f"Selected: {os.path.basename(path)}")
        generate_btn.configure(state="normal")

    def on_done(output_path, error=None):
        if error:
            set_busy(False, f"Error: {error}")
            return
        set_busy(False, f"Saved to {output_path}")
        reveal_btn.pack(pady=(14, 0))
        try:
            import subprocess
            subprocess.run(["open", "-R", str(output_path)], check=False)
        except Exception:
            pass

    def run_generation():
        if state["busy"] or not state["photo"]:
            return
        set_busy(True, "Rendering frames...")
        reveal_btn.pack_forget()

        def worker():
            try:
                out = generate_profile_gif(state["photo"], DEFAULT_OUTPUT)
                app.after(0, lambda: on_done(out))
            except Exception as exc:
                app.after(0, lambda e=exc: on_done(None, str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def reveal():
        import subprocess
        subprocess.run(["open", "-R", str(DEFAULT_OUTPUT)], check=False)

    choose_btn = ctk.CTkButton(
        body, text="Choose Photo...", height=40,
        font=ctk.CTkFont(size=14), command=choose_photo,
        fg_color=("gray75", "gray25"), hover_color=("gray65", "gray35"),
        text_color=("black", "white"),
    )
    reveal_btn = ctk.CTkButton(
        body, text="Reveal in Finder", height=36,
        font=ctk.CTkFont(size=13), command=reveal,
        fg_color="transparent", border_width=1,
        border_color=UJET_BLUE_HEX, text_color=UJET_BLUE_HEX,
        hover_color=("gray85", "gray20"),
    )

    choose_btn.pack(fill="x")
    status.pack(pady=(16, 8))
    generate_btn.configure(command=run_generation, state="disabled")
    generate_btn.pack(fill="x", pady=(4, 0))

    ctk.CTkLabel(
        app, text="Output saves to your Downloads folder.",
        font=ctk.CTkFont(size=11), text_color=("gray50", "gray50"),
    ).pack(side="bottom", pady=8)

    app.mainloop()


if __name__ == "__main__":
    main()
