# GUI Walkthrough

This is the canonical screenshot-based guide for the IndentAnalyzer GUI workflow used in Read the Docs.

## Scope

This walkthrough covers the standard guided workflow:

1. `1. Calibration`
2. `2. Load File`
3. `3. Settings`
4. `4. Results`
5. `5. Export`

It also references right-panel review tabs used during analysis:

- `Calibration`
- `Calibration Metrics`
- `Results Table`
- `Reliability`
- `Summary Statistics`
- `Curve Viewer`
- `Log`

The labels above match the current GUI implementation in `src/gui/main_interface.py`.

## Screenshot-to-UI Mapping

| Screenshot | GUI state | Documentation step |
|---|---|---|
| `10.03.35` | Step 1 calibration options | Step 1 |
| `10.03.48` | Generate calibration from fused silica | Step 2 |
| `10.03.56` | Calibration completed + reliability view | Step 3 |
| `10.04.10` | Step 2 file picker (`Research context + data file`) | Step 4 |
| `10.04.19` | Loaded file confirmation and reliability summary | Step 5 |
| `10.04.24` | Step 3 analysis parameters | Step 6 |
| `10.04.31` | Step 4 readiness checklist before analysis | Step 7 |
| `10.04.48` | Right-panel `Results Table` populated | Step 8 |
| `10.04.55` | Right-panel `Reliability` summary | Step 9 |
| `10.05.09` | Right-panel `Curve Viewer` with selected test | Step 10 |
| `10.05.19` | Step 4 exclusion from final calculations | Step 11 |
| `10.05.25` | Right-panel `Log` showing run summary | Step 12 |

## OCR Verification Notes

The step text below was revised using OCR extraction from the screenshots and then normalized for readability and consistency.
OCR-visible labels include:

- `Step 2 of 5: Research context + data file`
- `Step 3 of 5: Analysis parameters`
- `Step 4 of 5: Results`
- `Use in final calculations`
- `Curve Viewer` (right panel tab name in current GUI)

## Step-by-Step Workflow

### Step 1 — Open **1. Calibration**

Start in **1. Calibration** and choose how to define area-function coefficients (`C0...C8`).

<img src="screenshots/Screenshot%202026-05-01%20at%2010.03.35%E2%80%AFAM.png" alt="Calibration step with options to load, generate, or enter coefficients" width="900">

The three options are:

- load a saved calibration profile,
- generate calibration from fused-silica indentation data,
- manually enter coefficients.

Projected area is computed from the area function:

$$
A(h_c)=C_0h_c^2+C_1h_c+C_2h_c^{1/2}+C_3h_c^{1/4}+\cdots
$$

### Step 2 — Generate from fused silica (if needed)

If generating calibration, click **Generate from Fused-Silica XLS/XLSX** and select the reference file.

<img src="screenshots/Screenshot%202026-05-01%20at%2010.03.48%E2%80%AFAM.png" alt="Selecting fused silica calibration workflow in Step 1" width="900">

Reference constants used in this workflow:

$$
E_s=72\,\text{GPa},\quad \nu_s=0.17
$$

### Step 3 — Review calibration quality

After generation/apply, inspect calibration quality before proceeding.

<img src="screenshots/Screenshot%202026-05-01%20at%2010.03.56%E2%80%AFAM.png" alt="Calibration completed with reliability summary" width="900">

Fit quality uses:

$$
R^2=1-\frac{\sum_i(P_i-\hat{P}_i)^2}{\sum_i(P_i-\bar{P})^2}
$$

### Step 4 — Open **2. Load File** and select sample data

Move to **2. Load File** (`Research context + data file`) and choose the unknown-sample file.

<img src="screenshots/Screenshot%202026-05-01%20at%2010.04.10%E2%80%AFAM.png" alt="Load File step with sample goal and file chooser" width="900">

### Step 5 — Confirm loaded dataset

After loading, verify the selected file and test set are recognized.

<img src="screenshots/Screenshot%202026-05-01%20at%2010.04.19%E2%80%AFAM.png" alt="Loaded file confirmation with reliability panel visible" width="900">

### Step 6 — Configure **3. Settings**

Open **3. Settings** (`Analysis parameters`) and set fit/model/material parameters.

<img src="screenshots/Screenshot%202026-05-01%20at%2010.04.24%E2%80%AFAM.png" alt="Analysis settings step with fit and material parameters" width="900">

Typical values shown in the example:

- Generate Plots: enabled
- Export Plot Images: enabled
- Minimum fit R²: `0.980`
- Fit curve percentage: `25.0%`
- Sample Poisson ratio: `0.170`
- Indenter: `diamond`
- Method: `oliver_pharr`

### Step 7 — Run analysis in **4. Results**

In **4. Results**, confirm readiness checks, then run analysis.

<img src="screenshots/Screenshot%202026-05-01%20at%2010.04.31%E2%80%AFAM.png" alt="Results step readiness checklist before running analysis" width="900">

Contact depth relation:

$$
h_c=h_{max}-\varepsilon\frac{P_{max}}{S},\quad \varepsilon\approx0.75
$$

### Step 8 — Inspect **Results Table**

Review per-test outputs in right-panel **Results Table**.

<img src="screenshots/Screenshot%202026-05-01%20at%2010.04.48%E2%80%AFAM.png" alt="Results Table with hardness, modulus, and fit columns" width="900">

Core relations:

$$
H=\frac{P_{max}}{A_c},\qquad E_r=\frac{\sqrt{\pi}}{2}\frac{S}{\sqrt{A_c}}
$$

### Step 9 — Inspect **Reliability**

Use right-panel **Reliability** to evaluate spread and acceptance quality.

<img src="screenshots/Screenshot%202026-05-01%20at%2010.04.55%E2%80%AFAM.png" alt="Reliability summary with accepted tests and distribution views" width="900">

### Step 10 — Review a test in **Curve Viewer**

Open an individual test in right-panel **Curve Viewer** and inspect fit behavior.

<img src="screenshots/Screenshot%202026-05-01%20at%2010.05.09%E2%80%AFAM.png" alt="Curve Viewer for an individual test with load-displacement fit" width="900">

### Step 11 — Exclude questionable tests

Use **Use in final calculations** for tests that should be excluded from summary metrics.

<img src="screenshots/Screenshot%202026-05-01%20at%2010.05.19%E2%80%AFAM.png" alt="Excluding a questionable test from final calculations" width="900">

After exclusions, included-test statistics are recalculated:

$$
\bar{x}_{included}=\frac{1}{n_{included}}\sum_{i=1}^{n_{included}}x_i
$$

### Step 12 — Review right-panel **Log**

Use the right-panel **Log** for analysis traceability (run state, accepted/excluded tests, and final means).

<img src="screenshots/Screenshot%202026-05-01%20at%2010.05.25%E2%80%AFAM.png" alt="Analysis log with run summary and recalculated averages" width="900">

## Notes on Other Tabs

- **Expert Mode** is available for custom X/Y plotting and h0-offset control.
- **CSM** workflows are available through settings and right-panel CSM tabs when used.
- These advanced flows are intentionally separate from the standard 5-step guided path documented above.
