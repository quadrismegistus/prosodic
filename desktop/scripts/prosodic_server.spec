# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for prosodic server sidecar.

Build with:
    cd desktop/scripts
    pyinstaller prosodic_server.spec

Output: dist/prosodic-server (single directory bundle)
"""
import os
import sys
import subprocess

block_cipher = None

# Paths
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(SPECPATH), '..', '..'))
PROSODIC_PKG = os.path.join(REPO_ROOT, 'prosodic')

# Find espeak data
espeak_data = None
for candidate in [
    '/opt/homebrew/share/espeak-data',
    '/usr/share/espeak-data',
    '/usr/lib/x86_64-linux-gnu/espeak-data',
    '/usr/local/share/espeak-data',
]:
    if os.path.isdir(candidate):
        espeak_data = candidate
        break

# Find espeak binary
espeak_bin = None
for candidate in ['/opt/homebrew/bin/espeak', '/usr/bin/espeak', '/usr/local/bin/espeak']:
    if os.path.isfile(candidate):
        espeak_bin = candidate
        break

# Build data list
datas = [
    # prosodic package data (corpora, lang data, web static build)
    (os.path.join(PROSODIC_PKG, 'langs'), 'prosodic/langs'),
    (os.path.join(PROSODIC_PKG, 'web', 'static_build'), 'prosodic/web/static_build'),
]

# Add corpora if present
corpora_dir = os.path.join(REPO_ROOT, 'corpora')
if os.path.isdir(corpora_dir):
    datas.append((corpora_dir, 'corpora'))

# Add espeak data
if espeak_data:
    datas.append((espeak_data, 'espeak-data'))

# Add espeak binary
binaries = []
if espeak_bin:
    binaries.append((espeak_bin, '.'))

# Find espeak dylib
for candidate in [
    '/opt/homebrew/lib/libespeak.1.dylib',
    '/opt/homebrew/lib/libespeak.dylib',
    '/usr/lib/libespeak.so.1',
    '/usr/lib/x86_64-linux-gnu/libespeak.so.1',
]:
    if os.path.isfile(candidate):
        binaries.append((candidate, '.'))
        break

a = Analysis(
    [os.path.join(SPECPATH, 'prosodic_server.py')],
    pathex=[REPO_ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        'prosodic',
        'prosodic.web',
        'prosodic.web.api',
        'prosodic.web.models',
        'prosodic.parsing',
        'prosodic.parsing.meter',
        'prosodic.parsing.vectorized',
        'prosodic.parsing.constraints',
        'prosodic.parsing.parses',
        'prosodic.parsing.parselists',
        'prosodic.parsing.maxent',
        'prosodic.texts',
        'prosodic.words',
        'prosodic.langs',
        'prosodic.langs.english',
        'prosodic.langs.finnish',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi',
        'starlette',
        'starlette.routing',
        'starlette.responses',
        'starlette.middleware',
        'httptools',
        'httptools.parser',
        'numpy',
        'pandas',
        'scipy',
        'scipy.optimize',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch',       # GPU support optional, saves ~2GB
        'spacy',       # syntax optional, download on demand
        'tkinter',
        'matplotlib',
        'PIL',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='prosodic-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Needed for stdout port communication
    target_arch=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='prosodic-server',
)
