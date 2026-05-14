# Configuration and environment

## Runtime dependencies

The repository runtime dependencies are listed in `/home/runner/work/IndentAnalyzer/IndentAnalyzer/requirements.txt`:

```text
PyQt5
matplotlib
pandas
numpy
scipy
xlrd
openpyxl
```

## Launcher behavior

The shell launcher at `/home/runner/work/IndentAnalyzer/IndentAnalyzer/scripts/launch_application.sh`:

1. prints basic environment information,
2. checks for required runtime packages,
3. installs any missing packages with `pip3`,
4. starts the PyQt5 GUI by importing `src.gui.main_interface.NanoindentationGUI`.

Use the shell launcher on macOS and Linux. On Windows, use the Python entry point directly.

## Analysis settings file

The active configuration file is `/home/runner/work/IndentAnalyzer/IndentAnalyzer/config/analysis_settings.ini`.

Current sections:

```ini
[analysis]
min_data_points_loading = 50
min_data_points_unloading = 30
min_r_squared = 0.98
noise_threshold = 0.15
default_fitting_method = oliver_pharr

[calibration]
reference_material = fused_silica
reference_modulus = 72e9
reference_poisson = 0.17
reference_hardness = 9.0
default_indenter = diamond

[validation]
max_hardness = 100.0
min_hardness = 0.1
max_modulus = 1000e9
min_modulus = 1e9
```

## Settings currently consumed by the GUI

The GUI loads defaults from `config/analysis_settings.ini` through `NanoindentationGUI.load_analysis_config()`.

Currently wired values are:

- `analysis.min_r_squared`
- `analysis.fit_curve_percent` if present
- `calibration.reference_poisson`

Other values in the INI file remain useful as documented defaults and reference settings, but they are not all currently applied as direct GUI startup defaults.

## Platform-specific notes

- **macOS/Linux:** prefer `bash scripts/launch_application.sh`.
- **Windows:** prefer `python src\gui\main_interface.py`.
- **Headless documentation builds:** the docs build does not execute the GUI workflow.
