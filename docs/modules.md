# Module Guide

The API Reference is generated from every Python file under `src/`. This guide explains what each module does before you jump into the generated source pages.

## `src/__init__.py`

Package-level metadata for the source tree.

## `src/core/__init__.py`

Exports the core building blocks used by analysis modules: constants, loader/processor classes, validators, and summary helpers.

## `src/core/standards.py`

Stores standards and configuration data:

- ISO/NIST-style constants,
- minimum data and fit-quality thresholds,
- geometry-specific \(\epsilon\) and unloading exponents,
- fused-silica and diamond reference values,
- material property lookup table,
- default Berkovich area-function coefficients,
- validation limits.

Use this file when you need to understand a threshold or default value used elsewhere.

## `src/core/data_processor.py`

Contains the general data import and preprocessing layer:

- `ExcelDataLoader` dispatches to the selected vendor loader.
- `DataProcessor` validates columns, filters low loads, splits loading/unloading phases, and handles horizontal segments.
- `BatchProcessor` processes folders of Excel workbooks.
- `create_summary_statistics` summarizes batch-processing results.

This module prepares clean curve data but does not calculate final mechanical properties by itself.

## `src/core/validators.py`

Contains quality and validation utilities:

- data completeness checks,
- noise estimates,
- monotonicity checks,
- physical hardness/modulus limits,
- curve quality grades,
- horizontal segment detection,
- comprehensive validation report creation.

The analyzer uses this after fitting and property calculation to label risky results.

## `src/fileloader/__init__.py`

Package marker for file-loader modules.

## `src/fileloader/AgilentG200.py`

Vendor-specific loader for Agilent G200 Excel exports. It defines the loader contract for future instruments:

- accepted file extensions,
- sheet-name discovery,
- raw sheet reading,
- normalized output structure,
- Agilent column detection,
- `Test ###` sheet filtering.

The normalized output lets the rest of the code avoid vendor-specific column names.

## `src/analysis/__init__.py`

Package marker for analysis modules.

## `src/analysis/curve_fitting.py`

Implements curve models and stiffness/contact-depth extraction:

- `CurveFitter` fits Oliver-Pharr and normalized power-law unloading curves.
- `LinearFitter` estimates stiffness from a linear upper-unloading fit.
- `AreaFunction` evaluates the area function from \(C_0\) through \(C_8\).
- `fit_multiple_methods` compares available fitting methods and chooses the best successful one.

This is the main source for unloading-fit equations and \(R^2\) behavior.

## `src/analysis/mechanical_calculator.py`

Calculates final properties:

- hardness,
- reduced modulus,
- sample elastic modulus,
- derived ratios and estimates,
- reference-material tip calibration helper,
- property trend statistics across repeated tests.

Most unit conversions are performed here.

## `src/analysis/main_analyzer.py`

The primary orchestration layer. `NanoindentationAnalyzer` coordinates:

- loading,
- preprocessing,
- curve fitting,
- mechanical calculations,
- validation,
- file summaries,
- directory/batch summaries,
- result export helpers.

Use this class for programmatic analysis.

## `src/analysis/csm_analyzer.py`

Continuous stiffness measurement helper module. It reads depth-profile data, applies optional depth offsets, recalculates hardness/modulus when requested, averages profiles by index, interpolates onto target depth grids, and combines profile statistics.

Use this for CSM datasets where properties vary continuously with depth.

## `src/analysis/enhanced_analyzer.py`

Enhanced analyzer derived from the original script workflow. It includes advanced horizontal segment detection, ISO-style quality checks, tip-area function calculations, and plotting/reporting behavior that supports the GUI and legacy workflows.

## `src/analysis/legacy_analyzer.py`

Legacy analyzer implementation retained for compatibility with earlier workflows. It is useful for understanding the original Excel-analysis logic and for comparing behavior after refactors.

## `src/calibration/__init__.py`

Package marker for calibration modules.

## `src/calibration/nist_methods.py`

NIST-style calibration utilities:

- load-frame compliance regression,
- tip-area function calibration,
- calibration extraction from a fused-silica workbook,
- reference-material validation,
- Type A uncertainty and precision assessment.

This module is the best entry point for calibration mathematics.

## `src/gui/__init__.py`

GUI package marker.

## `src/gui/main_interface.py`

PyQt5 graphical interface for the full workflow. It provides tabs and panels for calibration, file loading, settings, analysis, reliability review, per-test plots, exclusion, logs, and export-oriented summaries.

The GUI is a front end over the same analysis modules described above.

## Generated API Reference

The generated source reference is built by `docs/gen_ref_pages.py`. During `mkdocs build`, it creates pages under `reference/` for each module listed here and uses `mkdocstrings` to render docstrings, signatures, members, and source code.

Open **API Reference** in the published documentation to browse the exact code for each `.py` file.
