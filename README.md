# UJET Animated Profile GIF Generator

Generate an animated GIF profile picture that loops between your photo and the `ujet.cx` logo on UJET blue. Drop in any photo, get back a polished 480x480 GIF ready to upload to Google, Slack, or anywhere else.

## What it does

The animation runs a clean sequential loop (no muddy crossfading):

1. Your photo holds (~4.8s)
2. Photo fades to solid UJET blue
3. White `ujet.cx` logo fades in
4. Logo holds (~1.2s)
5. Logo fades out
6. Blue fades back to your photo

Total loop: ~10 seconds. File size: ~800 KB to 1 MB.

## Requirements

- Python 3.8+
- Pillow and numpy

Install dependencies:

```bash
pip install Pillow numpy
```

## Usage

```bash
python make_profile.py your_photo.jpg
```

Output: `ujet_profile.gif` in the current directory.

### Options

```bash
# Custom output filename
python make_profile.py your_photo.jpg --output my_avatar.gif

# Show help
python make_profile.py --help
```

## Photo tips

- Any photo format Pillow supports works (JPG, PNG, WEBP, HEIC, etc).
- The script center-crops your photo to a square automatically. For best results, use a photo where your face is roughly centered.
- High-resolution sources look best (1000x1000 or larger).
- Background doesn't need to be removed — a clean studio photo or a casual snapshot both work.

## Uploading

The output is a 480x480 **square** GIF. When you set it as your profile photo:

- **Google / Gmail**: the upload UI lets you crop a circle from the square.
- **Slack**: same — Slack's avatar uploader handles the crop.
- Most other platforms work the same way.

This is intentional. Building the circle into the GIF caused dark halo artifacts on some platforms, so the upload UI handles the circle crop for clean results everywhere.

## Branding

This generator is locked to UJET branding:

- UJET Blue background (`#109FFF`)
- `ujet.cx` logo (bundled in `assets/ujet_logo.png`)
- Brand-approved timing and easing

If you want to point it at a different logo file for testing, use `--logo path/to/logo.png` (the logo should be white on black background for the alpha extraction to work).

## Troubleshooting

**`ERROR: Missing dependencies`** — Run `pip install Pillow numpy`.

**`ERROR: Logo not found`** — Make sure you cloned the full repo, not just the script. The logo lives at `assets/ujet_logo.png`.

**Output is huge / slow** — The 96-color quantization should keep files under 1 MB for typical photos. If you have an unusually high-detail photo and want a smaller file, you can edit `num_colors=96` down to `64` in `make_profile.py`.

## License

Internal UJET use.
