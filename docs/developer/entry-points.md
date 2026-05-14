# Entry points

## Shell launcher

**Path:** `/home/runner/work/IndentAnalyzer/IndentAnalyzer/scripts/launch_application.sh`

Purpose:

- validate runtime dependencies,
- print launch diagnostics,
- start the PyQt5 GUI from the active `src` package.

Expected outcome:

- a running `NanoindentationGUI` window for interactive analysis.

## GUI main entry point

**Path:** `/home/runner/work/IndentAnalyzer/IndentAnalyzer/src/gui/main_interface.py`

Relevant callables:

- `main()` — creates the `QApplication`, configures basic metadata, shows the main window, and starts the event loop.
- `NanoindentationGUI` — the main application window coordinating calibration, file selection, settings, results, plots, and export.
- `AnalysisWorker` — background worker thread used to run the analysis logic without blocking the GUI.

Expected inputs:

- selected calibration source,
- experiment Excel file,
- sample Poisson ratio,
- fit-quality and fitting-method choices.

Expected outputs:

- populated results table,
- reliability summary,
- per-test plots and summaries,
- exportable included results.

## Programmatic analysis entry point

**Path:** `/home/runner/work/IndentAnalyzer/IndentAnalyzer/src/analysis/main_analyzer.py`

Relevant callable:

- `analyze_nanoindentation_file(file_path, area_function_coefficients=None, sample_poisson=0.3, fitting_method='oliver_pharr')`

Expected input:

- path to an Agilent-style nanoindentation Excel file,
- optional calibrated area-function coefficients,
- optional sample Poisson ratio,
- fitting-method name.

Expected output:

- a dictionary containing file metadata, per-test results, summary data, warnings, and errors.
