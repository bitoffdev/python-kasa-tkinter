# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

def kasa_dist_info_datas():
    """find the kasa-python dist-info directory

    pyinstaller doesn't seem to include the dist-info directory, which causes a runtime issue. This is a workaround.
    """
    import os, sys
    for import_path in sys.path:
        if not os.path.isdir(import_path):
            continue
        for name in os.listdir(import_path):
            if "kasa" in name and name[-9:] == "dist-info":
                full_path = os.path.join(import_path, name)
                return (full_path, name)
    raise Exception("Could not find python-kasa dist info directory")

a = Analysis(['kasatk/__main__.py'],
             pathex=['.\\env\\Lib\\site-packages\\', '.'],
             binaries=[],
             datas=[kasa_dist_info_datas()],
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
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='kasatk',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
