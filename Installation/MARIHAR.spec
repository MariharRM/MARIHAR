# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

spec_dir = os.path.dirname(os.path.abspath(SPEC))
project_root = os.path.dirname(spec_dir)


def PR(path):
    return os.path.join(project_root, path)


a = Analysis(
    [PR('Backend/desktop_app.py')],
    pathex=[project_root, PR('Backend')],
    binaries=[
        (PR('Binaries/yt-dlp.exe'), 'Binaries'),
        (PR('Binaries/ffmpeg.exe'), 'Binaries'),
        (PR('Binaries/ffprobe.exe'), 'Binaries'),
        (PR('Binaries/ffplay.exe'), 'Binaries'),
        (PR('Binaries/deno.exe'), 'Binaries'),
    ],
    datas=[
        (PR('Frontend/templates'), 'Frontend/templates'),
        (PR('Frontend/static'), 'Frontend/static'),
        (PR('Assets/Logo_marino.ico'), 'Assets'),
        (PR('Assets/Logo_marino.png'), 'Assets'),
        (PR('Docs/README_UTILISATEUR.txt'), 'Docs'),
        (PR('Docs/Plateformes_supportées.txt'), 'Docs'),
        (PR('Docs/licenses'), 'Docs/licenses'),
    ],
    excludes=[
        'dev-docs',
        '*.cache',
        '*cache*',
        'dep_analysis_*',
        'node_analysis_*',
        'build_last.log',
        '*.backup',
    ],
    hiddenimports=[
        'flask',
        'flask_cors',
        'webview',
        'yt_dlp',
        'ytdlp_service',
        'ytdlp_wrapper',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
    name='MARIHAR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=PR('Assets/Logo_marino.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MARIHAR',
)
