# Installation

This page gives the minimal setup needed to run IndentAnalyzer locally from the same Git repository used by Read the Docs.

## Clone

```bash
git clone https://github.com/MShirazAhmad/IndentAnalyzer.git
cd IndentAnalyzer
```

For the current development branch:

```bash
git checkout indevelopment
```

## Create Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Launch the GUI

```bash
bash scripts/launch_application.sh
```

The application opens the Nanoindentation Analysis Suite GUI. Start with calibration, then load the experiment file, review/exclude tests, configure settings, run analysis, and export results.

## Build Documentation Locally

Read the Docs installs documentation dependencies from `docs/requirements.txt`. To test the same build locally:

```bash
python -m pip install -r docs/requirements.txt
mkdocs build --clean --strict
```

For live preview:

```bash
mkdocs serve
```

