# IndentAnalyzer

IndentAnalyzer is a graphical nanoindentation analysis tool for Excel data exported from an **Agilent Nano Indenter G200 system (MTS Nano Instruments, Oak Ridge, TN, USA)**. It supports tip-area calibration, sample-file loading, Oliver–Pharr analysis, result review, test exclusion, and export.

## Documentation

The full documentation set now lives in `/home/runner/work/IndentAnalyzer/IndentAnalyzer/docs` and is structured for Read the Docs.

Start here:

- [Documentation index](docs/index.md)
- [Overview](docs/overview.md)
- [Installation and launch](docs/installation.md)
- [Quickstart](docs/quickstart.md)
- [Full workflow](docs/workflow.md)
- [Developer architecture](docs/developer/architecture.md)
- [API reference](docs/developer/api.md)

## Quick start

```bash
git clone https://github.com/MShirazAhmad/IndentAnalyzer.git
cd IndentAnalyzer
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
bash scripts/launch_application.sh
```

On Windows, launch the GUI with:

```powershell
python src\gui\main_interface.py
```

## Active code and archived material

- Active application code lives under `/home/runner/work/IndentAnalyzer/IndentAnalyzer/src`.
- Archived material under `/home/runner/work/IndentAnalyzer/IndentAnalyzer/dump` is not part of the active documentation baseline.
