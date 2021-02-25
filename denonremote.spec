# -*- mode: python ; coding: utf-8 -*-

from kivy_deps import sdl2, glew

block_cipher = None


a = Analysis(['main.py'],
             pathex=['G:\\raph\\Documents\\GitHub\\denonremote'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz, Tree('G:\\raph\\Documents\\GitHub\\denonremote\\'),
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
          console=False)
