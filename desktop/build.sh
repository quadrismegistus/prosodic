#!/bin/bash
set -euo pipefail

# Build script for Prosodic desktop app
# Usage: ./desktop/build.sh [--dev]

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DESKTOP_DIR="$REPO_ROOT/desktop"
FRONTEND_DIR="$REPO_ROOT/prosodic/web/frontend"
SCRIPTS_DIR="$DESKTOP_DIR/scripts"
TAURI_DIR="$DESKTOP_DIR/src-tauri"

echo "=== Prosodic Desktop Build ==="
echo "Repo: $REPO_ROOT"

# --- Step 1: Build frontend ---
echo ""
echo "--- Building frontend ---"
cd "$FRONTEND_DIR"
npm run build
echo "Frontend built to static_build/"

# --- Step 2: Build PyInstaller sidecar ---
echo ""
echo "--- Building PyInstaller sidecar ---"
cd "$SCRIPTS_DIR"

# Install pyinstaller if needed
pip show pyinstaller >/dev/null 2>&1 || pip install pyinstaller

pyinstaller prosodic_server.spec --noconfirm
echo "Sidecar built to dist/prosodic-server/"

# --- Step 3: Copy sidecar into Tauri resources ---
echo ""
echo "--- Copying sidecar to Tauri resources ---"
SIDECAR_DEST="$TAURI_DIR/sidecar"
rm -rf "$SIDECAR_DEST"
cp -r "$SCRIPTS_DIR/dist/prosodic-server" "$SIDECAR_DEST"
echo "Sidecar copied to $SIDECAR_DEST"

# --- Step 4: Build Tauri app ---
if [[ "${1:-}" == "--dev" ]]; then
    echo ""
    echo "--- Starting Tauri dev mode ---"
    cd "$DESKTOP_DIR"
    cargo tauri dev
else
    echo ""
    echo "--- Building Tauri release ---"
    cd "$DESKTOP_DIR"
    cargo tauri build
    echo ""
    echo "=== Build complete ==="
    echo "App bundle at: $TAURI_DIR/target/release/bundle/"
fi
