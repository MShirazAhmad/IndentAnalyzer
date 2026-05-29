# Installation

This page gives the minimum setup to run IndentAnalyzer locally and verify the documentation build.

## 1) Clone and switch to development branch

```bash
git clone https://github.com/MShirazAhmad/IndentAnalyzer.git
cd IndentAnalyzer
git checkout indevelopment
```

## 2) Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 3) Launch the GUI

```bash
bash scripts/launch_application.sh
```

The standard user flow is:

1. `1. Calibration`
2. `2. Load File`
3. `3. Settings`
4. `4. Results`
5. `5. Export`

Then review details in right-panel tabs such as `Results Table`, `Reliability`, and `Curve Viewer`.

See [GUI Walkthrough](gui-walkthrough.md) for the full scientific workflow.

## 4) Build documentation locally (strict)

```bash
python -m pip install -r docs/requirements.txt
mkdocs build --clean --strict
```

Optional live preview:

```bash
mkdocs serve
```

## Build a macOS installer package

On macOS, create a clickable `.pkg` installer:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt pyinstaller
bash scripts/build_macos_installer.sh
```

The package is created at `dist/IndentAnalyzer-1.0.1-macOS.pkg`. Use `VERSION=1.2.3 bash scripts/build_macos_installer.sh` to set a release version.

Unsigned or unnotarized builds may be blocked by Gatekeeper on first launch. The installer opens System Settings after installation and includes the approval path: **System Settings > Privacy & Security > Open Anyway**.

## Common setup issues

- **GUI fails to launch**: confirm `PyQt5` is installed from `requirements.txt` and run from an active virtual environment.
- **File not loading**: confirm the file is an Agilent G200 `.xls`/`.xlsx` export with test sheets.
- **Docs build failure**: run the strict build command above and resolve missing links/assets before publishing.
