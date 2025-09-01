# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.building.build_main import Analysis, BUNDLE
block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/*.py', 'src'),
        ('data/*.db', 'data'),
        ('resources/*.ico', 'resources'),
        (os.path.join(os.path.dirname(sys.executable), '../lib/python3.13/site-packages/streamlit'), 'streamlit'),
        (os.path.join(os.path.dirname(sys.executable), '../lib/python3.13/site-packages/flask'), 'flask'),
    ],
    hiddenimports=[
        'streamlit', 'flask', 'stripe', 'Crypto', 'psutil', 'pandas', 'numpy',
        'sqlite3', 'datetime', 'json', 'hashlib', 'base64', 'tempfile'
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
    name='SamShakkurAntivirus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Mettre à True pour le débogage
    icon='resources/icon.ico',
)
