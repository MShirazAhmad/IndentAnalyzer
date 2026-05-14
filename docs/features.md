# Features

IndentAnalyzer is designed for end-to-end nanoindentation analysis with emphasis on calibration traceability and fit-quality review.

## 1) Data ingestion

- Reads Agilent Nano Indenter G200 `.xls` and `.xlsx` exports.
- Parses multi-sheet workbooks where tests are typically named `Test ###`.
- Normalizes to a consistent internal schema:

```text
Time (sec)
Load (mN)
Displacement (nm)
```

- Captures metadata, warnings, and load errors for traceability.

## 2) Processing and quality preparation

- Numeric coercion and invalid-row removal.
- Duplicate cleanup and low-load filtering.
- Loading/unloading segmentation at maximum load.
- Horizontal/plateau segment detection to reduce fit artifacts.

## 3) Fitting and mechanics

- Oliver-Pharr unloading model.
- Alternative normalized power-law model.
- Multi-method comparison (`auto`) with fit-quality selection.
- Contact stiffness and contact-depth extraction.
- Hardness, reduced modulus, and sample modulus calculations.

See [Mathematical Calculations](calculations.md) for equations and unit conversions.

## 4) Calibration and reliability

- Fused-silica reference workflows.
- Tip-area function calibration and quality checks.
- Load-frame compliance calibration support.
- Reliability summaries, outlier awareness, and per-test review.

## 5) GUI workflow

- Guided tabs: `1. Calibration` → `2. Load File` → `3. Settings` → `4. Results` → `5. Export`.
- Right-panel review: `Results Table`, `Reliability`, `Summary Statistics`, `Curve Viewer`, `Log`.
- Optional `Expert Mode` for advanced diagnostics.

See [GUI Walkthrough](gui-walkthrough.md) for screenshot-level usage.

## 6) CSM support

- CSM sheet handling through the loader path.
- Depth-profile averaging and interpolation workflows.
- Optional recalculation from harmonic stiffness and area function.

## 7) Developer extensibility

- Modular structure under `src/` (loader, core, analysis, calibration, GUI).
- New instrument support via loader modules in `src/fileloader/`.
- Auto-generated API/source documentation under [Code Reference](reference/index.md).

For new loader design rules, see [File Loaders](file-loaders.md).

