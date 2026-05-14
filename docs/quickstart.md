# Quickstart

Use this page for the fastest path from installation to a complete analysis session.

## Before you start

Prepare:

1. A fused-silica calibration file exported from the Agilent G200.
2. One or more unknown sample files exported from the Agilent G200.
3. The sample Poisson ratio for modulus calculation.
4. A rule for excluding questionable indents.

## Five-step workflow

The GUI is organized into five workflow steps:

1. **Calibration**
2. **Load File**
3. **Settings**
4. **Results**
5. **Export**

The right-side results area exposes the current calibration summary, results table, reliability view, individual test plots, and log output.

## Step 1: open the application

```bash
bash scripts/launch_application.sh
```

## Step 2: calibrate the tip area function

Load an existing profile, generate a calibration from fused silica, or enter coefficients manually.

![Calibration tab](screenshots/Screenshot%202026-05-01%20at%2010.03.35%E2%80%AFAM.png)

## Step 3: load an experiment file

Choose the unknown sample Excel export.

![Load experiment file](screenshots/Screenshot%202026-05-01%20at%2010.04.10%E2%80%AFAM.png)

## Step 4: confirm settings and run analysis

Set the fit threshold, unloading fit fraction, sample Poisson ratio, indenter, and fitting method, then start the analysis.

![Run analysis](screenshots/Screenshot%202026-05-01%20at%2010.04.31%E2%80%AFAM.png)

## Step 5: review and export

Inspect the results table, reliability summaries, and individual curves before exporting the included results.

![Results table](screenshots/Screenshot%202026-05-01%20at%2010.04.48%E2%80%AFAM.png)

For the full annotated workflow, continue to {doc}`workflow`.
