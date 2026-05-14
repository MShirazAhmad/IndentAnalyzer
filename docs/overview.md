# Overview

IndentAnalyzer guides a researcher through tip calibration, sample-file loading, Oliver–Pharr analysis, result review, test exclusion, and final reporting for nanoindentation experiments exported from the Agilent Nano Indenter G200 platform.

## Source of truth

This documentation revision treats the following as authoritative:

- `/home/runner/work/IndentAnalyzer/IndentAnalyzer/README.md` for the maintained user-facing narrative.
- Active application code under `/home/runner/work/IndentAnalyzer/IndentAnalyzer/src`.

Archived content under `/home/runner/work/IndentAnalyzer/IndentAnalyzer/dump` is intentionally excluded from the active documentation baseline.

## Documentation scope

The Read the Docs set covers both:

- a user guide for running the GUI workflow, and
- a lightweight developer guide for architecture and stable API entry points.

## What the application reports

IndentAnalyzer analyzes load–displacement curves and reports:

- hardness,
- reduced modulus,
- sample elastic modulus,
- loading and unloading fit quality,
- per-indent result tables,
- reliability statistics, and
- final mean ± standard deviation values.

## Supported inputs

The current workflow is designed for Excel exports from the Agilent Nano Indenter G200 and expects full load–displacement curve data rather than summary-only exports.

Supported file types:

```text
.xls
.xlsx
```

## Active application areas

- `src/gui`: PyQt5 workflow, results panels, exports, and user interaction.
- `src/analysis`: analysis orchestration, fitting, and mechanics calculations.
- `src/core`: ISO constants, validation, and data processing.
- `src/calibration`: NIST-oriented calibration helpers.
