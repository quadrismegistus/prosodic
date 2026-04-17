# Prosodic Desktop App

Standalone desktop application built with Tauri v2. Bundles the prosodic Python
backend (via PyInstaller) and espeak TTS as a self-contained app — no Python
installation required for end users.

## Architecture

```
Prosodic.app
├── Tauri (native webview shell, ~5MB)
├── SvelteKit frontend (static HTML/JS/CSS, ~200KB)
├── prosodic-server (PyInstaller bundle, ~300MB)
│   ├── Python 3.10 runtime
│   ├── prosodic + numpy + pandas + scipy + uvicorn
│   └── espeak binary + data files
└── corpora/ (bundled text files)
```

At launch, Tauri starts the `prosodic-server` sidecar on a random port,
then loads the frontend in a native webview. API calls go to `localhost:{port}`.

## Prerequisites (build machine only)

- Rust (rustup.rs)
- Node.js 18+
- Python 3.10+ with prosodic installed (`pip install -e .`)
- PyInstaller (`pip install pyinstaller`)
- espeak (`brew install espeak` on macOS)

## Build

```bash
# Full release build (frontend + PyInstaller + Tauri .app bundle)
./desktop/build.sh

# Dev mode (uses system Python, hot reload frontend)
./desktop/build.sh --dev
```

Output: `desktop/src-tauri/target/release/bundle/`
- macOS: `.dmg` and `.app`
- Windows: `.msi` and `.exe`
- Linux: `.deb` and `.AppImage`

## Dev mode

In dev mode, no PyInstaller bundle is built. Tauri tries to launch
`python -m prosodic.desktop_server` using your system Python. Run the
frontend dev server separately on port 5173 for hot reload.

## Replacing placeholder icons

Generate proper icons from a source image:

```bash
cargo tauri icon path/to/icon.png
```

## Notes

- GPU (torch) and spaCy are excluded from the bundle to keep size manageable.
  They can be added by editing `prosodic_server.spec`.
- macOS builds require code signing for distribution (Apple Developer account).
- The sidecar communicates its port via a temp file; the frontend reads it
  from `window.__PROSODIC_PORT__`.
