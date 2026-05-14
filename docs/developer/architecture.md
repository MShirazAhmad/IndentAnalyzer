# Architecture

## Active repository layout

```text
/home/runner/work/IndentAnalyzer/IndentAnalyzer/
├── README.md
├── config/
├── docs/
├── requirements.txt
├── scripts/
└── src/
    ├── analysis/
    ├── calibration/
    ├── core/
    └── gui/
```

The `dump/` directory is archival and is not part of the active architecture baseline for this documentation set.

## Module responsibilities

### `src/gui`

The PyQt5 GUI lives here. `main_interface.py` owns the user workflow, results-table presentation, reliability plots, individual test review, test exclusion, export actions, and session logging.

### `src/analysis`

This layer orchestrates the analysis workflow. `main_analyzer.py` coordinates data loading, validation, curve fitting, and mechanical-property calculations. Supporting modules implement curve fitting, mechanical calculations, and legacy behavior.

### `src/core`

Core functionality includes standards, configuration-like constants, validation logic, and Excel data processing.

### `src/calibration`

Calibration helpers implement NIST-oriented compliance and tip-area-function calculations.

## High-level flow

1. The launcher starts `NanoindentationGUI`.
2. The GUI loads calibration defaults and user-selected files.
3. `AnalysisWorker` invokes the modular analyzer for file processing.
4. Analysis results feed the table, reliability views, individual test views, and export actions.
5. Inclusion and exclusion decisions recalculate final summaries in the GUI layer.

## Current UI organization reflected in the docs

- Five main workflow steps are exposed in the GUI.
- The results area separates results table, reliability views, individual test review, and log output.
- Individual test review uses a tabbed plot-and-summary presentation rather than a single mixed panel.
