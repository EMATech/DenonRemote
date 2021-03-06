# -*- mode: python ; coding: utf-8 -*-

# Minimize dependencies bundling
from kivy.tools.packaging.pyinstaller_hooks import get_deps_all, hookspath, runtime_hooks
from kivy_deps import sdl2, glew

block_cipher = None

added_files = [
    ('denonremote\\fonts', 'fonts'),
    ('denonremote\\images', 'images'),
    ('denonremote\\settings', 'settings')
]

dependencies = get_deps_all()  # FIXME: minimize dependencies
dependencies['hiddenimports'].append(
    'pystray._win32')  # FIXME: use the hook at https://github.com/moses-palmer/pystray/issues/55

a = Analysis(['denonremote\\main.py'],
             pathex=['denonremote', '.\\venv\\Lib\\site-packages\\pystray'],
             datas=added_files,
             hookspath=hookspath(),
             runtime_hooks=runtime_hooks(),
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False,
             **dependencies)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz, Tree('denonremote'),
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='denonremote',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          icon='icon.ico')
