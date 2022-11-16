# This Python file uses the following encoding: utf-8
#
# SPDX-FileCopyrightText: 2021-2022 Raphaël Doursenaud <rdoursenaud@free.fr>
#
# SPDX-License-Identifier: GPL-3.0-or-later
import os
from datetime import datetime

from PyInstaller.building.api import PYZ, EXE
from PyInstaller.building.build_main import Analysis
from PyInstaller.building.datastruct import Tree
from kivy.tools.packaging.pyinstaller_hooks import get_deps_minimal, hookspath, runtime_hooks
from kivy_deps import sdl2, glew

from denonremote.__about__ import __version__

block_cipher = None

added_files = [
    ('src/denonremote/fonts', 'fonts'),
    ('src/denonremote/images', 'images'),
    ('src/denonremote/settings', 'settings'),
    ('src/denonremote/denonremote.kv', 'denonremote'),
]

# Minimize dependencies bundling
dependencies = get_deps_minimal(exclude_ignored=False, window=True, text=True, image=True)
# Fixes ModuleNotFoundError: No module named 'twisted'
dependencies['hiddenimports'].append('twisted.internet._threadedselect')
dependencies['excludes'].remove('twisted')

# Set build date
BUILD_FILE = 'src/denonremote/__build__.py'
__build_date__ = datetime.now().isoformat()
with open(BUILD_FILE, 'w') as f:
    f.write(f'__build_date__ = "{__build_date__}"\r')

a = Analysis(
    cipher=block_cipher,
    datas=added_files,
    hookspath=hookspath(),
    noarchive=False,
    runtime_hooks=runtime_hooks(),
    scripts=['src/denonremote/__main__.py'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    **dependencies,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    Tree('src/denonremote'),
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    bootloader_ignore_signals=False,
    console=False,
    debug=False,
    icon='icon.ico',
    name=f'denonremote-v{__version__}',
    runtime_tmpdir=None,
    strip=False,
    upx=True,
    upx_exclude=[],
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
)

# Cleanup the build date file
try:
    os.remove(BUILD_FILE)
except FileNotFoundError:
    pass
