# UJET Animated Profile GIF Generator

Generate an animated GIF profile picture for your **Google account** that loops between your photo and the `ujet.cx` logo on UJET blue. Drop in any photo, get back a polished 480x480 GIF ready to upload.

> Note: this is intended for **Google profile pictures** (Gmail, Google Chat, Calendar, Workspace). Slack does not animate profile pictures — it will display the first frame as a static image.

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

## Uploading to Google

The output is a 480x480 **square** GIF. When you set it as your Google profile photo, the upload UI will let you crop a circle from the square.

The circle isn't baked into the GIF on purpose — building it in caused dark halo artifacts at the circle edges. Letting Google's upload UI handle the crop avoids that.

Where it animates:

- Gmail (sender avatar in some views)
- Google Chat
- Google Calendar event participants
- Other Google Workspace surfaces that render avatars as GIFs

Where it shows as static (first frame):

- Slack (does not animate profile pictures)
- Most Account Chooser dropdowns and small thumbnail contexts
- Anywhere that renders avatars as static images

## Branding

This generator is locked to UJET branding:

- UJET Blue background (`#109FFF`)
- `ujet.cx` brand wordmark, embedded directly in the script as base64
- Brand-approved timing and easing

The script is fully self-contained — a single `make_profile.py` with no asset folder to clone. The exact brand wordmark ships inside the file, so it works the moment you download it.

To override with a different logo, pass `--logo path/to/logo.png`. The logo should be white on a black or transparent background — the script extracts the bright pixels as the alpha mask. If the embedded image ever fails to decode, the script falls back to rendering the wordmark from a bold system font.

## Troubleshooting

**`ERROR: Missing dependencies`** — Run `pip install Pillow numpy`.

**`ERROR: Logo not found`** — Only happens if you pass `--logo` with a path that doesn't exist. Without `--logo`, the embedded brand wordmark is used and no file is needed.

**Output is huge / slow** — The 96-color quantization should keep files under 1 MB for typical photos. If you have an unusually high-detail photo and want a smaller file, you can edit `num_colors=96` down to `64` in `make_profile.py`.

## License

Internal UJET use.
