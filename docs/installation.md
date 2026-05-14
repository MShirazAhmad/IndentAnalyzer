# Installation and launch

## Clone the repository

```bash
git clone https://github.com/MShirazAhmad/IndentAnalyzer.git
cd IndentAnalyzer
```

## Create a Python environment

### macOS and Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

Command Prompt:

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Install runtime dependencies

Use the repository requirement file:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The runtime dependency list currently includes:

- PyQt5
- matplotlib
- pandas
- numpy
- scipy
- xlrd
- openpyxl

## Launch the GUI

### macOS and Linux

```bash
bash scripts/launch_application.sh
```

The launcher script checks for required packages and attempts to install missing runtime dependencies before starting the GUI.

### Windows

```powershell
python src\gui\main_interface.py
```

## Alternate Python entry point

If you prefer to start the GUI without the shell launcher:

```bash
python src/gui/main_interface.py
```

## First-run expectation

After startup, begin in the **Calibration** step before loading unknown samples.
