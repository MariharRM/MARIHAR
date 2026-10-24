# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for MARIHAR
"""
import os
import sys

block_cipher = None

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(SPEC))

# Collect all files from Backend
backend_files = []
for root, dirs, files in os.walk(os.path.join(BASE_DIR, 'Backend')):
    for file in files:
        if file.endswith('.py'):
            backend_files.append((os.path.join(root, file), 'Backend'))

# Collect all files from Frontend
frontend_files = []
for root, dirs, files in os.walk(os.path.join(BASE_DIR, 'Frontend')):
    for file in files:
        frontend_files.append((os.path.join(root, file), os.path.join('Frontend', os.path.relpath(root, os.path.join(BASE_DIR, 'Frontend')))))

# Collect Assets
assets_files = []
for root, dirs, files in os.walk(os.path.join(BASE_DIR, 'Assets')):
    for file in files:
        assets_files.append((os.path.join(root, file), 'Assets'))

# Collect Binaries
binaries_files = []
for root, dirs, files in os.walk(os.path.join(BASE_DIR, 'Binaries')):
    for file in files:
        binaries_files.append((os.path.join(root, file), 'Binaries'))

# Collect Docs
docs_files = []
for root, dirs, files in os.walk(os.path.join(BASE_DIR, 'Docs')):
    for file in files:
        docs_files.append((os.path.join(root, file), os.path.join('Docs', os.path.relpath(root, os.path.join(BASE_DIR, 'Docs')))))

# Collect Dependencies
deps_files = []
for root, dirs, files in os.walk(os.path.join(BASE_DIR, 'Dependencies')):
    for file in files:
        deps_files.append((os.path.join(root, file), 'Dependencies'))

a = Analysis(
    ['Backend/desktop_app.py'],
    pathex=[BASE_DIR],
    binaries=binaries_files,
    datas=frontend_files + assets_files + docs_files + deps_files,
    hiddenimports=[
        'flask',
        'flask_cors',
        'pywebview',
        'tkinter',
        'tkinter.filedialog',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MARIHAR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(BASE_DIR, 'Assets', 'Logo_marino.ico')
)
