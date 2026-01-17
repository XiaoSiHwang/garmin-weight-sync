# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('src', 'src')]
binaries = []
hiddenimports = ['PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'garmin', 'xiaomi', 'core', 'core.models', 'core.config_manager', 'core.sync_service', 'jaraco.collections', 'jaraco.functools', 'importlib_metadata', 'pkg_resources', 'packaging']
tmp_ret = collect_all('fit_tool')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('garth')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['src/gui/main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_rth_pyqt6.py'],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'scipy', 'PIL', 'logfire'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GarminWeightSync',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GarminWeightSync',
)
app = BUNDLE(
    coll,
    name='GarminWeightSync.app',
    icon=None,
    bundle_identifier=None,
)
