# -*- mode: python ; coding: utf-8 -*-
import os
import flet

block_cipher = None

# Dynamically locate flet resources regardless of virtualenv setup
flet_dir = os.path.dirname(flet.__file__)
flet_icons_json = os.path.join(flet_dir, "controls", "material", "icons.json")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('bot/config', 'bot/config'),
        (flet_icons_json, 'flet/controls/material'),
    ],
    hiddenimports=[
        # --- YOUR APP MODULES ---
        'gui.pages.login',
        'gui.pages.dashboard',
        'gui.pages.settings',
        'gui.pages.shop',
        'gui.pages.presets',
        'gui.components.subscription',
        
        # --- THIRD PARTY LIBRARIES ---
        'scapy.layers.all',
        'sqlalchemy.dialects.postgresql',
        'psycopg2',
        'flet',
        'cv2',
        'PIL',
        'win32timezone'
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
    [],
    exclude_binaries=True,
    name='MarketTrader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to True if you want to see the terminal window for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='bot/config/app_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MarketTrader',
)