# IndentAnalyzer

**IndentAnalyzer** is a PyQt5-based nanoindentation analysis application written for Excel data exported from an **Agilent Nano Indenter G200 system (MTS Nano Instruments, Oak Ridge, TN, USA)**. It provides a guided workflow for Oliver–Pharr analysis, including tip-area calibration, sample-file loading, analysis settings, result review, individual test inspection, test exclusion, and export of final results.

This README is intended for GitHub users who want to install the project, open the interface, understand the workflow, and reproduce the analysis shown in the screenshots.

---

## 1. What This Project Does

IndentAnalyzer processes instrumented nanoindentation load–displacement data and calculates:

- indentation hardness,
- reduced modulus,
- Oliver–Pharr sample modulus,
- loading and unloading fit quality,
- per-test result tables,
- reliability statistics,
- publication-ready summary values.

The application is designed around data files exported from the **Agilent Nano Indenter G200**. Other nanoindenter export formats may require edits to the data-loading or column-mapping logic.

---

## 2. Main Features

- Graphical PyQt5 interface
- Agilent G200 Excel file loading (`.xls`, `.xlsx`)
- Fused-silica calibration workflow
- Manual tip-area coefficient entry
- Oliver–Pharr unloading fit
- Per-test hardness and modulus calculation
- Test-by-test curve visualization
- Inclusion/exclusion control for individual indents
- Reliability plots and summary statistics
- CSV/Excel result export
- Analysis log for reproducibility

---

## 3. Repository Layout

```text
IndentAnalyzer/
├── README.md
├── scripts/
│   └── launch_application.sh
├── src/
│   ├── gui/
│   │   └── main_interface.py
│   ├── analysis/
│   │   ├── main_analyzer.py
│   │   ├── enhanced_analyzer.py
│   │   ├── legacy_analyzer.py
│   │   ├── mechanical_calculator.py
│   │   └── curve_fitting.py
│   ├── core/
│   │   ├── standards.py
│   │   ├── data_processor.py
│   │   └── validators.py
│   └── calibration/
│       └── nist_methods.py
└── docs/
    └── screenshots/
```

`src/gui/main_interface.py` is the main interface file. The command-line launcher is located at `scripts/launch_application.sh`.

---

## 4. Add the Screenshots for GitHub Display

The screenshots should be placed in:

```text
docs/screenshots/
```

The README uses the exact filenames listed below:

```text
Screenshot 2026-05-01 at 10.03.35 AM.png
Screenshot 2026-05-01 at 10.03.48 AM.png
Screenshot 2026-05-01 at 10.03.56 AM.png
Screenshot 2026-05-01 at 10.04.10 AM.png
Screenshot 2026-05-01 at 10.04.19 AM.png
Screenshot 2026-05-01 at 10.04.24 AM.png
Screenshot 2026-05-01 at 10.04.31 AM.png
Screenshot 2026-05-01 at 10.04.48 AM.png
Screenshot 2026-05-01 at 10.04.55 AM.png
Screenshot 2026-05-01 at 10.05.09 AM.png
Screenshot 2026-05-01 at 10.05.19 AM.png
Screenshot 2026-05-01 at 10.05.25 AM.png
```

If the screenshots are still inside `NewImages.zip`, extract them from the repository root:

```bash
mkdir -p docs/screenshots
unzip NewImages.zip -d docs/screenshots
rm -rf docs/screenshots/__MACOSX
```

Then commit the README and screenshots:

```bash
git add README.md docs/screenshots/*.png
git commit -m "Add GUI workflow screenshots"
```

---

## 5. Installation

Install the Python dependencies:

```bash
python3 -m pip install PyQt5 matplotlib pandas numpy scipy xlrd openpyxl
```

Then launch the application from the repository root:

```bash
bash scripts/launch_application.sh
```

The launcher opens the graphical interface:

```text
Nanoindentation Analysis Suite
ISO 14577-4:2016 Compliant · Advanced Tip Calibration · Oliver-Pharr Method
```

---

## 6. Getting Started: GUI Workflow

The interface is organized into five main workflow tabs:

1. **Calibration**
2. **Load File**
3. **Settings**
4. **Results**
5. **Export**

The right-side panel contains result and diagnostic tabs:

1. **Calibration**
2. **Results Table**
3. **Reliability**
4. **Test Plot**
5. **Log**

---

## 7. Step-by-Step Workflow with Screenshots

### Step 1 — Open the Calibration Tab

Start by selecting or generating the tip-area calibration. The calibration converts contact depth into projected contact area, which is required for both hardness and modulus calculations.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%2010.03.35%E2%80%AFAM.png" alt="Calibration tab in IndentAnalyzer" width="900">

The calibration tab provides three options:

- load an existing calibration profile,
- generate calibration from fused silica,
- manually enter tip-area coefficients.

The projected contact area is represented as:

$$
A(h_c)=C_0h_c^2+C_1h_c+C_2h_c^{1/2}+C_3h_c^{1/4}+C_4h_c^{1/8}+\cdots
$$

For an ideal Berkovich tip:

$$
C_0=24.56
$$

---

### Step 2 — Select the Fused-Silica Calibration File

For calibration from a reference material, select the fused-silica file. In the example workflow, the selected file is `Silica Before.xls`.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%2010.03.48%E2%80%AFAM.png" alt="Selecting fused silica calibration file" width="900">

The fused-silica reference values used by the workflow are:

$$
E_s=72\,\text{GPa}
$$

$$
\nu_s=0.17
$$

The reduced modulus relation is:

$$
\frac{1}{E_r}=\frac{1-\nu_s^2}{E_s}+\frac{1-\nu_i^2}{E_i}
$$

where $E_i$ and $\nu_i$ are the indenter elastic constants.

---

### Step 3 — Review Calibration Reliability

After calibration, inspect the calibration reliability plots and summary values.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%2010.03.56%E2%80%AFAM.png" alt="Calibration reliability summary" width="900">

The reliability view summarizes fit quality, hardness distribution, reduced modulus distribution, and accepted calibration tests. This step confirms whether the calibration profile is suitable before analyzing unknown samples.

The coefficient of determination is used to evaluate fit quality:

$$
R^2=1-\frac{\sum_i(P_i-\hat{P}_i)^2}{\sum_i(P_i-\bar{P})^2}
$$

---

### Step 4 — Load the Unknown Sample File

Move to the **Load File** tab and select the Agilent G200 Excel file for the unknown sample.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%2010.04.10%E2%80%AFAM.png" alt="Selecting unknown sample file" width="900">

The example workflow uses:

```text
HEC12_2_03132025.xls
```

The raw data are treated as load–displacement arrays:

$$
P_i=P(t_i),\qquad h_i=h(t_i)
$$

The software identifies:

$$
P_{max}=\max(P_i)
$$

$$
h_{max}=h(P_{max})
$$

---

### Step 5 — Confirm the Loaded Sample

After selecting the unknown sample file, the interface confirms that the experiment file has been loaded.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%2010.04.19%E2%80%AFAM.png" alt="Loaded sample file confirmation" width="900">

The file is treated as a set of individual indentation tests. Each test is analyzed independently, and the final average is calculated only from included tests.

---

### Step 6 — Choose Analysis Settings

Open the **Settings** tab and select the fitting and analysis parameters.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%2010.04.24%E2%80%AFAM.png" alt="Analysis settings tab" width="900">

The example settings shown are:

```text
Generate Plots: enabled
Export Plot Images: enabled
Minimum R²: 0.980
Curve percentage used: 25.0%
Sample Poisson ratio: 0.170
Indenter material: diamond
Fitting method: oliver_pharr
```

The unloading curve is fitted using the Oliver–Pharr power law:

$$
P=\alpha(h-h_f)^m
$$

The stiffness is calculated at maximum depth:

$$
S=\left.\frac{dP}{dh}\right|_{h=h_{max}}
$$

For the power-law fit:

$$
S=\alpha m(h_{max}-h_f)^{m-1}
$$

---

### Step 7 — Run the Analysis

Open the **Results** tab and check that calibration, file selection, Poisson ratio, and fitting method are set. Then click **Start Analysis**.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%2010.04.31%E2%80%AFAM.png" alt="Run analysis tab" width="900">

The software calculates contact depth:

$$
h_c=h_{max}-\varepsilon\frac{P_{max}}{S}
$$

For a Berkovich indenter, the common Oliver–Pharr value is:

$$
\varepsilon\approx0.75
$$

The calculated $h_c$ is then passed into the tip-area function $A(h_c)$.

---

### Step 8 — Inspect the Results Table

The **Results Table** tab lists the calculated mechanical properties for each accepted test.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%2010.04.48%E2%80%AFAM.png" alt="Results table" width="900">

Typical columns include:

```text
Source File
Test
Hardness (GPa)
Oliver-Pharr Modulus (GPa)
Loading R²
Loading Power C
Loading Power n
Loading Offset h0 (nm)
Unloading R²
```

Hardness is calculated as:

$$
H=\frac{P_{max}}{A_c}
$$

Reduced modulus is calculated as:

$$
E_r=\frac{\sqrt{\pi}}{2}\frac{S}{\sqrt{A_c}}
$$

---

### Step 9 — Review Reliability Statistics

The **Reliability** tab summarizes the spread of accepted tests.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%2010.04.55%E2%80%AFAM.png" alt="Reliability statistics for unknown sample" width="900">

The example reliability panel reports 14 included tests for `HEC12_2_03132025.xls`, with approximately:

```text
Hardness: 22.119 ± 2.887 GPa
Reduced modulus: 288.21 ± 12.20 GPa
Hardness CV: 13.1%
Reduced modulus CV: 4.2%
```

The mean and sample standard deviation are:

$$
\bar{x}=\frac{1}{n}\sum_{i=1}^{n}x_i
$$

$$
s=\sqrt{\frac{1}{n-1}\sum_{i=1}^{n}(x_i-\bar{x})^2}
$$

The coefficient of variation is:

$$
CV(\%)=\frac{s}{\bar{x}}\times100
$$

---

### Step 10 — Inspect an Individual Test Curve

Use the test buttons to open individual indentation curves in the **Test Plot** tab.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%2010.05.09%E2%80%AFAM.png" alt="Individual indentation test plot" width="900">

The plot shows the loading curve, unloading curve, fitted unloading curve, stiffness tangent, residual depth $h_f$, contact depth $h_c$, and maximum depth $h_{max}$.

The sample modulus is calculated from the reduced modulus relation:

$$
E_s=\frac{1-\nu_s^2}{\frac{1}{E_r}-\frac{1-\nu_i^2}{E_i}}
$$

---

### Step 11 — Exclude a Questionable Test

If a test passes the numerical $R^2$ threshold but appears physically questionable, it can be excluded from final statistics.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%2010.05.19%E2%80%AFAM.png" alt="Exclude individual test from final statistics" width="900">

A test may be excluded because of surface defects, pores, poor contact, abnormal loading behavior, large offset, or an indentation placed on a nonrepresentative microstructural region.

After exclusion, the final mean and standard deviation are recalculated using only the included tests:

$$
\bar{x}_{included}=\frac{1}{n_{included}}\sum_{i=1}^{n_{included}}x_i
$$

---

### Step 12 — Review the Analysis Log

The **Log** tab records file loading, calibration source, accepted tests, excluded tests, and recalculated averages.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%2010.05.25%E2%80%AFAM.png" alt="Analysis log and recalculated averages" width="900">

In the example workflow, excluding `Test 012` changes the final result approximately to:

```text
13/14 tests included
Average Hardness: 22.78 ± 1.69 GPa
Average Modulus: 291.16 ± 6.19 GPa
```

The log should be preserved because it records the analysis sequence and supports reproducibility.

---

## 8. Data Requirements

The current import workflow is written for Excel exports from the **Agilent Nano Indenter G200 system (MTS Nano Instruments, Oak Ridge, TN, USA)**.

Supported file types:

```text
.xls
.xlsx
```

The file should contain load and displacement data. Internally, the software normalizes recognized columns to names such as:

```text
Load (mN)
Displacement (nm)
Time (sec)
```

Before running analysis, confirm that:

- load is reported in mN or correctly converted,
- displacement is reported in nm or correctly converted,
- unloading data are present,
- the file contains full indentation curves, not only summary values.

---

## 9. Core Equations

### Tip-area function

$$
A_c=A(h_c)=C_0h_c^2+C_1h_c+C_2h_c^{1/2}+C_3h_c^{1/4}+\cdots
$$

### Oliver–Pharr unloading fit

$$
P=\alpha(h-h_f)^m
$$

### Contact stiffness

$$
S=\left.\frac{dP}{dh}\right|_{h=h_{max}}
$$

### Contact depth

$$
h_c=h_{max}-\varepsilon\frac{P_{max}}{S}
$$

### Hardness

$$
H=\frac{P_{max}}{A_c}
$$

### Reduced modulus

$$
E_r=\frac{\sqrt{\pi}}{2}\frac{S}{\sqrt{A_c}}
$$

### Sample modulus

$$
E_s=\frac{1-\nu_s^2}{\frac{1}{E_r}-\frac{1-\nu_i^2}{E_i}}
$$

### Fit quality

$$
R^2=1-\frac{\sum_i(P_i-\hat{P}_i)^2}{\sum_i(P_i-\bar{P})^2}
$$

---

## 10. Export and Reporting

For publication or dissertation reporting, include:

- instrument model: **Agilent Nano Indenter G200 system (MTS Nano Instruments, Oak Ridge, TN, USA)**,
- indenter geometry and material,
- calibration material and calibration file,
- area-function coefficients,
- sample Poisson ratio,
- maximum load or depth protocol,
- unloading fit method,
- percentage of curve used for fitting,
- minimum accepted $R^2$,
- number of total tests,
- number of included and excluded tests,
- exclusion rationale,
- hardness mean ± standard deviation,
- reduced modulus mean ± standard deviation,
- sample modulus mean ± standard deviation.

For high-entropy carbides and other heterogeneous ceramics, also report relevant microstructural context, including porosity, phase purity, grain size, and indentation placement relative to pores or visible defects.

---

## 11. Troubleshooting

### Screenshots do not appear on GitHub

Confirm that the images are located in:

```text
docs/screenshots/
```

and committed:

```bash
git add docs/screenshots/*.png
```

If the filenames with special spaces do not render, rename them to simple names such as `step-01-calibration.png` and update the README paths.

### GUI does not open

Install dependencies and launch again:

```bash
python3 -m pip install PyQt5 matplotlib pandas numpy scipy xlrd openpyxl
bash scripts/launch_application.sh
```

### Excel file does not load

Check that the file is an Agilent G200 `.xls` or `.xlsx` export and that it contains load–displacement columns. If another instrument format is used, update the data-processing logic in:

```text
src/core/data_processor.py
```

### Fit passes but the curve looks wrong

Do not rely on $R^2$ alone. Inspect the curve in the **Test Plot** tab. Exclude tests affected by pores, surface roughness, poor contact, pile-up/sink-in artifacts, or abnormal loading behavior.