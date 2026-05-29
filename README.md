# IndentAnalyzer

![IndentAnalyzer documentation icon](https://github.com/user-attachments/assets/636c922f-8742-4f5e-82f5-0a4a1da1ee37)

**IndentAnalyzer** is a graphical nanoindentation analysis tool for Excel data exported from an **Agilent Nano Indenter G200 system (MTS Nano Instruments, Oak Ridge, TN, USA)**.

It guides users through:

- tip-area calibration,
- sample-file loading,
- Oliver–Pharr analysis,
- per-test review and exclusion,
- final reporting/export.

## Quick Start

```bash
git clone https://github.com/MShirazAhmad/IndentAnalyzer.git
cd IndentAnalyzer
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install PyQt5 matplotlib pandas numpy scipy xlrd openpyxl
bash scripts/launch_application.sh
```

Windows activation alternatives:

```powershell
.venv\Scripts\activate.bat
# or
.venv\Scripts\Activate.ps1
```

## Full Documentation

- Read the Docs home: <https://indentanalyzer.readthedocs.io/>
- GUI walkthrough (canonical screenshot guide): <https://indentanalyzer.readthedocs.io/en/latest/gui-walkthrough/>
- Source docs page in this repo: `/home/runner/work/IndentAnalyzer/IndentAnalyzer/docs/gui-walkthrough.md`

## Workflow Summary

Left workflow tabs:

1. `1. Calibration`
2. `2. Load File`
3. `3. Settings`
4. `4. Results`
5. `5. Export`

Additional workflow tabs:

- `Expert Mode`
- `Log`

Right-panel review tabs include:

- `Calibration`
- `Calibration Metrics`
- `Results Table`
- `Reliability`
- `Summary Statistics`
- `Curve Viewer`
- `Log`

## Common Issues

### File does not load

Confirm the file is an Agilent G200 `.xls` or `.xlsx` export with full load–displacement curves.

### Fit passes but the curve looks wrong

Do not rely on $R^2$ alone. Review the curve in **Curve Viewer** and exclude physically questionable tests.

### Final averages change after exclusion

This is expected. Final statistics are recalculated from only included tests.

## License

Copyright (c) 2026 M Shiraz Ahmad.

This repository is licensed under the Creative Commons Attribution-NoDerivatives 4.0 International License (CC BY-ND 4.0). You may share the material with attribution, but you may not distribute modified versions.

## Build Windows EXE

You can create a single-file Windows executable (`.exe`) using PyInstaller. Building for Windows must be done on Windows (PyInstaller does not reliably cross-compile from macOS).

Locally on Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install pyinstaller
pip install -r requirements.txt
powershell -File scripts\build_windows_exe.ps1
```

Or use the included GitHub Actions workflow which runs on `windows-latest` and uploads the resulting EXE as an artifact. Trigger it from the Actions tab or push to `main`/`master`.

## Build macOS Installer

On macOS, build a clickable installer package with:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
bash scripts/build_macos_installer.sh
```

The installer is written to `dist/IndentAnalyzer-1.0.1-macOS.pkg` by default. Set `VERSION=1.2.3` to change the package filename and package metadata.

Because public macOS builds should be signed and notarized, unsigned local builds may show Apple's "developer cannot be verified" message on first launch. The installer includes a readme and opens System Settings after installation to guide users to **Privacy & Security > Open Anyway**.

For a signed release build:

```bash
CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)" \
INSTALLER_SIGN_IDENTITY="Developer ID Installer: Your Name (TEAMID)" \
VERSION=1.0.0 \
bash scripts/build_macos_installer.sh
```
