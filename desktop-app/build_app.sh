#!/usr/bin/env bash
#
# build_app.sh - Build the UJET Profile GIF desktop app into an Iru-ready .pkg
#
# Pipeline: PyInstaller builds a self-contained .app, then macOS-native
# pkgbuild/productbuild wrap it into a .pkg that installs to /Applications.
# No third-party packaging tools required.
#
# Produces:
#   dist/UJET Profile GIF.app   the standalone macOS app bundle
#   UJET-Profile-GIF.pkg        the installer to upload to Iru as a Custom App
#
# Run on a Mac:
#   chmod +x build_app.sh && ./build_app.sh
#
# Optional code signing (recommended): export your identities first, e.g.
#   export DEVELOPER_ID_APP="Developer ID Application: UJET, Inc. (TEAMID)"
#   export DEVELOPER_ID_INSTALLER="Developer ID Installer: UJET, Inc. (TEAMID)"
#
set -euo pipefail

APP_NAME="UJET Profile GIF"
BUNDLE_ID="cx.ujet.profile-gif"
VERSION="${VERSION:-1.0.0}"
PKG_NAME="UJET-Profile-GIF.pkg"
ENTRY="ujet_profile_app.py"
VENV=".buildvenv"

# ---- colored logging -------------------------------------------------------
BLUE="\033[0;34m"; GREEN="\033[0;32m"; YELLOW="\033[1;33m"; RED="\033[0;31m"; NC="\033[0m"
log()  { printf "${BLUE}[%s]${NC} %s\n" "$(date +%H:%M:%S)" "$1"; }
ok()   { printf "${GREEN}[%s] %s${NC}\n" "$(date +%H:%M:%S)" "$1"; }
warn() { printf "${YELLOW}[%s] %s${NC}\n" "$(date +%H:%M:%S)" "$1"; }
die()  { printf "${RED}[%s] ERROR: %s${NC}\n" "$(date +%H:%M:%S)" "$1"; exit 1; }

case "${1:-}" in
  -h|--help)
    echo "Usage: ./build_app.sh"
    echo "Builds '${APP_NAME}.app' and ${PKG_NAME} (version ${VERSION}) from ${ENTRY}."
    echo "Override version with: VERSION=1.2.3 ./build_app.sh"
    echo "Sign by exporting DEVELOPER_ID_APP and DEVELOPER_ID_INSTALLER first."
    exit 0
    ;;
esac

[ "$(uname)" = "Darwin" ] || die "This must run on macOS (it produces a .app/.pkg)."
[ -f "$ENTRY" ] || die "Cannot find $ENTRY in the current directory."
[ -f "make_icon.py" ] || die "Cannot find make_icon.py in the current directory."

# ---- tkinter preflight -----------------------------------------------------
# customtkinter needs the tkinter stdlib module. Homebrew Python ships without
# it by default; install the matching python-tk formula if it is missing.
log "Checking that Python has tkinter..."
if ! python3 -c "import tkinter" >/dev/null 2>&1; then
  warn "tkinter not found for this python3."
  PYVER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  if command -v brew >/dev/null 2>&1; then
    warn "Attempting: brew install python-tk@${PYVER}"
    brew install "python-tk@${PYVER}" || die "Could not install python-tk@${PYVER}. Install Tk for your Python and re-run."
  else
    die "Install Tk for your Python (e.g. 'brew install python-tk@${PYVER}') and re-run."
  fi
  python3 -c "import tkinter" >/dev/null 2>&1 || die "tkinter still unavailable after install."
fi
ok "tkinter present."

# ---- virtualenv + deps -----------------------------------------------------
log "Creating build virtualenv ($VENV)..."
rm -rf "$VENV"
python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
log "Installing build dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
ok "Dependencies installed."

# ---- icon: generate png, then png -> icns ----------------------------------
log "Generating icon.png from the embedded wordmark..."
python make_icon.py
log "Building icon.icns from icon.png..."
rm -rf icon.iconset icon.icns
mkdir icon.iconset
for size in 16 32 64 128 256 512; do
  sips -z "$size" "$size"         icon.png --out "icon.iconset/icon_${size}x${size}.png"    >/dev/null
  sips -z $((size*2)) $((size*2)) icon.png --out "icon.iconset/icon_${size}x${size}@2x.png" >/dev/null
done
iconutil -c icns icon.iconset
rm -rf icon.iconset
ok "icon.icns built."

# ---- PyInstaller .app ------------------------------------------------------
log "Building the .app bundle with PyInstaller..."
rm -rf build dist "${APP_NAME}.spec"
pyinstaller --noconfirm --clean --windowed \
  --name "$APP_NAME" \
  --osx-bundle-identifier "$BUNDLE_ID" \
  --icon icon.icns \
  --collect-all customtkinter \
  "$ENTRY"
APP_PATH="dist/${APP_NAME}.app"
[ -d "$APP_PATH" ] || die "PyInstaller did not produce $APP_PATH"
ok "Built $APP_PATH"

# ---- optional: sign the .app -----------------------------------------------
if [ -n "${DEVELOPER_ID_APP:-}" ]; then
  log "Signing the .app with: $DEVELOPER_ID_APP"
  codesign --force --deep --options runtime --timestamp \
    --sign "$DEVELOPER_ID_APP" "$APP_PATH"
  codesign --verify --deep --strict "$APP_PATH" && ok "App signature verified."
else
  warn "DEVELOPER_ID_APP not set - leaving the .app unsigned."
fi

# ---- pkgbuild + productbuild -> .pkg ---------------------------------------
log "Building ${PKG_NAME} (installs to /Applications)..."
rm -rf pkgroot component.pkg "$PKG_NAME"
mkdir -p "pkgroot/Applications"
cp -R "$APP_PATH" "pkgroot/Applications/"

pkgbuild --root pkgroot \
  --identifier "$BUNDLE_ID" \
  --version "$VERSION" \
  --install-location / \
  component.pkg >/dev/null

if [ -n "${DEVELOPER_ID_INSTALLER:-}" ]; then
  log "Signing the installer with: $DEVELOPER_ID_INSTALLER"
  productbuild --package component.pkg --sign "$DEVELOPER_ID_INSTALLER" "$PKG_NAME" >/dev/null
else
  warn "DEVELOPER_ID_INSTALLER not set - building an unsigned .pkg."
  productbuild --package component.pkg "$PKG_NAME" >/dev/null
fi
rm -rf pkgroot component.pkg
ok "Created ${PKG_NAME} (version ${VERSION})"

deactivate
echo
ok "Done."
echo "  App: dist/${APP_NAME}.app"
echo "  Pkg: ${PKG_NAME}"
echo
log "Upload ${PKG_NAME} to Iru as a Custom App and scope it to Self Service so"
log "people can install it on demand."
echo
if [ -z "${DEVELOPER_ID_INSTALLER:-}" ]; then
  warn "The .pkg is unsigned. Deploying via Iru/Kandji still works (MDM-installed"
  warn "apps are not quarantined, so no Gatekeeper prompt). To sign it, export"
  warn "DEVELOPER_ID_APP and DEVELOPER_ID_INSTALLER and re-run."
fi
