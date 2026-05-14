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

## Common setup issues

- **GUI fails to launch**: confirm `PyQt5` is installed from `requirements.txt` and run from an active virtual environment.
- **File not loading**: confirm the file is an Agilent G200 `.xls`/`.xlsx` export with test sheets.
- **Docs build failure**: run the strict build command above and resolve missing links/assets before publishing.

