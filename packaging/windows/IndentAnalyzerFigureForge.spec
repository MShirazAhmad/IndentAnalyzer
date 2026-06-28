# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules


project_root = Path(SPECPATH).resolve().parents[1]
datas = collect_data_files(
    "FigureForge",
    includes=["resources/**/*", "plugins/*.png", "plugins/plugin_requirements.txt", "structure.json"],
)
datas += collect_data_files("qdarktheme")

a = Analysis(
    [str(project_root / "src" / "figureforge_bridge.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=collect_submodules("FigureForge") + collect_submodules("qdarktheme"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PyQt5"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="IndentAnalyzerFigureForge",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=str(project_root / "src" / "logo" / "NanoInd.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="IndentAnalyzerFigureForge",
)
