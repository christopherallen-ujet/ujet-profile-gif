# UJET Profile GIF - Desktop App

A double-click GUI version of the profile GIF generator for non-technical
folks. No Python, no terminal, no GitHub required by the end user: they open
the app, choose a photo, click **Generate GIF**, and the result lands in their
Downloads folder.

The `ujet.cx` brand wordmark is embedded in `ujet_profile_app.py`, so the app
is self-contained.

## Files

- `ujet_profile_app.py` - the app (CustomTkinter GUI + the generator engine)
- `make_icon.py` - generates the app icon from the embedded wordmark at build time
- `requirements.txt` - Python dependencies
- `build_app.sh` - builds the `.app` and `.pkg`

## Building the app (run on a Mac)

```bash
chmod +x build_app.sh && ./build_app.sh
```

That produces:

- `dist/UJET Profile GIF.app` - the standalone app bundle
- `UJET-Profile-GIF.pkg` - the installer to upload to Iru

The script creates a throwaway virtualenv, installs the dependencies, converts
the icon, runs PyInstaller, and wraps the `.app` into a `.pkg` (installing to
/Applications) using the built-in `pkgbuild`/`productbuild` tools. No
third-party packaging app is needed.

Override the version with `VERSION=1.2.3 ./build_app.sh`.

### Prerequisites

- macOS
- Python 3 with `tkinter`. Homebrew Python ships without it; the build script
  will attempt `brew install python-tk@<version>` if it is missing.

## Testing the app before packaging

You can run the GUI directly without building:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python ujet_profile_app.py
```

## Deploying via Iru

Upload `UJET-Profile-GIF.pkg` to Iru as a Custom App and scope it to **Self
Service**, so people install the generator on demand rather than having it
forced onto every Mac. This mirrors the existing `.pkg`-via-Iru deployment
pattern.

### Code signing

The build is **unsigned** unless you provide signing identities. Deploying an
unsigned `.pkg` through Iru/Kandji still works: MDM-installed apps are not
quarantined, so Gatekeeper does not prompt. (A download-distributed unsigned
app would be blocked - which is why Iru is the right channel.)

To produce a signed build, export your identities before running the script:

```bash
export DEVELOPER_ID_APP="Developer ID Application: UJET, Inc. (TEAMID)"
export DEVELOPER_ID_INSTALLER="Developer ID Installer: UJET, Inc. (TEAMID)"
./build_app.sh
```

## How it works

The generator engine (`generate_profile_gif`) is identical in behavior to the
command-line `make_profile.py`: it center-crops the photo to a square, builds a
~10 second loop (photo -> UJET blue -> `ujet.cx` wordmark -> back), and saves a
480x480 animated GIF. The GUI runs generation on a background thread so the
window stays responsive, then reveals the output in Finder.
