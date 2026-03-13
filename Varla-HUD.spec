# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app_v2_enhanced.py'],
    pathex=[],
    binaries=[],
    datas=[('icons', 'icons')],
    hiddenimports=['PySide6.QtWidgets', 'PySide6.QtGui', 'PySide6.QtCore'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PySide6.QtNetwork',
        'PySide6.QtQml',
        'PySide6.QtQmlMeta',
        'PySide6.QtQmlModels',
        'PySide6.QtQmlWorkerScript',
        'PySide6.QtQuick',
        'PySide6.QtOpenGL',
        'PySide6.QtPdf',
        'PySide6.QtSvg',
    ],
    noarchive=False,
    optimize=0,
)
# Strip unnecessary Qt DLLs that bloat the exe (~20MB+ savings)
_exclude_dlls = {
    'opengl32sw.dll',
    'Qt6Quick.dll', 'Qt6Qml.dll', 'Qt6QmlMeta.dll',
    'Qt6QmlModels.dll', 'Qt6QmlWorkerScript.dll',
    'Qt6Pdf.dll', 'Qt6Network.dll', 'Qt6OpenGL.dll', 'Qt6Svg.dll',
    'qdirect2d.dll',
}
a.binaries = [b for b in a.binaries if b[0].split('\\')[-1] not in _exclude_dlls]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Varla-HUD',
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
)
