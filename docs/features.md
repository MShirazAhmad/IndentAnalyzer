# Features

IndentAnalyzer is organized around the complete nanoindentation workflow: import, calibration, analysis, review, exclusion, statistics, and export.

## File Input

- Agilent Nano Indenter G200 `.xls` and `.xlsx` exports.
- Multi-sheet workbooks where indentation tests are stored as `Test ###` sheets.
- Vendor-sheet normalization to a common analyzer structure:

```text
Time (sec)
Load (mN)
Displacement (nm)
```

- Loader metadata including file path, extension, sheet names, total sheet count, processed sheet count, warnings, and errors.
- A loader contract in `src/fileloader/AgilentG200.py` that future vendor loaders can follow.

## Data Processing

- Numeric coercion and removal of empty/non-numeric rows.
- Duplicate row removal.
- Low-load filtering based on maximum load and a fixed minimum threshold.
- Automatic maximum-load detection.
- Loading and unloading phase separation.
- Horizontal segment detection and filtering.
- Per-test metadata for original point count, filtered point count, load range, displacement range, and phase statistics.

## Curve Fitting

- Oliver-Pharr unloading model.
- Normalized power-law unloading model.
- Linear stiffness fallback for upper unloading data.
- Automatic method comparison through `fit_multiple_methods`.
- Fit quality reporting with fit-segment and full-curve \(R^2\).
- Tangent-line construction at maximum load for visualization.
- Contact stiffness and contact depth calculation from fitted parameters.

## Mechanical Properties

- Contact area from ideal or calibrated area-function coefficients.
- Hardness in Pa, MPa, and GPa.
- Reduced modulus in Pa and GPa.
- Sample elastic modulus using the sample and indenter compliance relation.
- Derived \(H/E\), contact pressure, approximate yield strength, approximate indent volume, and specific energy.
- Configurable sample Poisson ratio.
- Default diamond indenter constants.

## Calibration

- Fused-silica reference material constants.
- Load-frame compliance calibration by regression of total compliance against \(1/\sqrt{A}\).
- Tip-area function calibration from reference-material stiffness and contact depth.
- Constrained Berkovich calibration with fixed \(C_0=24.56\) and fitted \(C_1\), \(C_2\).
- Calibration quality warnings for low correlation, large correction terms, or insufficient data.
- Reference material validation against expected modulus and hardness.
- Type A uncertainty and coefficient-of-variation precision summaries.

## Continuous Stiffness Measurement

- Test-range parsing such as `1-5,8,10`.
- CSM sheet reading through the same loader path when available.
- Optional depth offsets per test.
- Direct averaging of exported hardness and modulus columns.
- Optional recalculation from load, harmonic contact stiffness, and area function.
- Row-wise profile averaging.
- Interpolated averaging on a shared target depth grid.
- Weighted combination of profile means, standard deviations, and counts.

## GUI Workflow

- Calibration tab for loading, generating, or entering tip-area coefficients.
- Sample-file loading tab.
- Settings for fitting and material parameters.
- Results table for per-indent calculations.
- Reliability plots and summary statistics.
- Individual test curve inspection.
- Test exclusion and recalculated averages.
- Export-oriented result review.

## Developer Features

- Modular package layout under `src/`.
- Separate loader, core preprocessing, validation, fitting, calibration, analysis, CSM, and GUI layers.
- Auto-generated code reference for every `.py` file.
- Read the Docs configuration through `.readthedocs.yaml`.
- Local documentation build with `mkdocs build --clean --strict`.
