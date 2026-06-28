# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path(SPECPATH).resolve().parents[1]

a = Analysis(
    [str(project_root / "src" / "gui" / "main_interface.py")],
    pathex=[str(project_root / "src")],
    binaries=[],
    datas=[
        (str(project_root / "config"), "config"),
        (str(project_root / "src" / "logo"), "src/logo"),
        (str(project_root / "src" / "fileloader"), "src/fileloader"),
        (
            str(
                project_root
                / "build"
                / "macos-helper-dist"
                / "IndentAnalyzerFigureForge"
            ),
            "figureforge",
        ),
    ],
    hiddenimports=[
        "openpyxl",
        "openpyxl.cell._writer",
        "xlrd",
        "analysis.curve_fitting",
        "analysis.main_analyzer",
        "analysis.enhanced_analyzer",
        "analysis.legacy_analyzer",
        "analysis.csm_analyzer",
        "analysis.mechanical_calculator",
        "calibration.nist_methods",
        "core.standards",
        "core.validators",
        "core.data_processor",
        "fileloader.AgilentG200",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PyQt5.QtWebEngineWidgets",
        "PyQt5.QtWebEngineCore",
        "PyQt5.QtWebChannel",
        "plotly",
        "PySide6",
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="IndentAnalyzer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch="arm64",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="IndentAnalyzer",
)

app = BUNDLE(
    coll,
    name="IndentAnalyzer.app",
    icon=str(project_root / "src" / "logo" / "NanoInd.png"),
    bundle_identifier="com.mshirazahmad.indentanalyzer",
    version="2.0.0",
    info_plist={
        "CFBundleDisplayName": "IndentAnalyzer",
        "CFBundleShortVersionString": "2.0.0",
        "CFBundleVersion": "2.0.0",
        "NSHighResolutionCapable": True,
    },
)
