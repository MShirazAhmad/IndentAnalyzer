# IndentAnalyzer

**IndentAnalyzer** is a graphical nanoindentation analysis tool written for Excel data exported from an **Agilent Nano Indenter G200 system (MTS Nano Instruments, Oak Ridge, TN, USA)**. It guides the user through tip-area calibration, sample-file loading, Oliver–Pharr analysis, result review, individual test inspection, test exclusion, and final reporting.

---

## 1. What This Tool Does

IndentAnalyzer analyzes instrumented nanoindentation load–displacement data and reports:

- hardness,
- reduced modulus,
- sample elastic modulus,
- loading and unloading fit quality,
- per-indent result tables,
- reliability statistics,
- final mean ± standard deviation values.

The tool is designed for files exported from the **Agilent Nano Indenter G200**. Data from other nanoindenters may not load correctly unless the file format is adapted.

---

## 2. What You Need Before Starting

Before using the software, prepare:

1. A fused-silica calibration file exported from the Agilent G200.
2. One or more unknown sample indentation files exported from the Agilent G200.
3. The sample Poisson ratio used for modulus calculation.
4. A decision rule for excluding questionable indents, such as pores, poor contact, surface defects, or abnormal curve shape.

Supported file types:

```text
.xls
.xlsx
```

The files should contain full load–displacement curves, not only summary values.

---

## 3. Setup and Launch

### Step 1 — Clone the Repository

Open a terminal and clone the project:

```bash
git clone https://github.com/MShirazAhmad/IndentAnalyzer.git
cd IndentAnalyzer
```

### Step 2 — Create a Python Environment

Create a local environment for the project:

```bash
python3 -m venv .venv
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### Step 3 — Install Required Packages

Install the packages needed to run the software:

```bash
python -m pip install --upgrade pip
python -m pip install PyQt5 matplotlib pandas numpy scipy xlrd openpyxl
```

### Step 4 — Launch the App

Run the launcher from the project folder:

```bash
bash scripts/launch_application.sh
```

The app opens as:

```text
Nanoindentation Analysis Suite
ISO 14577-4:2016 Compliant · Advanced Tip Calibration · Oliver-Pharr Method
```

After the app opens, start with the **Calibration** tab and follow the workflow shown below.

---

## 4. Main Workflow

The interface is organized into five steps:

1. **Calibration** — load or generate the tip-area calibration.
2. **Load File** — select the unknown sample file.
3. **Settings** — choose fitting and material parameters.
4. **Results** — run analysis and inspect values.
5. **Export** — save final results.

The right-side panel shows:

1. **Calibration** — calibration summary.
2. **Results Table** — calculated values for each indent.
3. **Reliability** — statistics and distribution plots.
4. **Test Plot** — individual load–displacement curves.
5. **Log** — analysis record and recalculated averages.

---

## 5. Step-by-Step Use

### Step 1 — Open the Calibration Tab

Start by selecting or generating the tip-area calibration. This step converts contact depth into projected contact area, which is required for both hardness and modulus.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%2010.03.35%E2%80%AFAM.png" alt="Calibration tab in IndentAnalyzer" width="900">

The calibration tab provides three options:

- load an existing calibration profile,
- generate calibration from fused silica,
- manually enter tip-area coefficients.

The projected contact area is calculated using:

$$
A(h_c)=C_0h_c^2+C_1h_c+C_2h_c^{1/2}+C_3h_c^{1/4}+C_4h_c^{1/8}+\cdots
$$

For an ideal Berkovich tip:

$$
C_0=24.56
$$

---

### Step 2 — Select the Fused-Silica Calibration File

For calibration from a reference material, select the fused-silica file. In the example shown, the selected file is `Silica Before.xls`.

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

This view summarizes fit quality, hardness distribution, reduced modulus distribution, and accepted calibration tests. The calibration should be checked before analyzing unknown samples because all final hardness and modulus values depend on the calibrated area function.

Fit quality is evaluated using:

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

The software identifies the maximum load and corresponding displacement:

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

The file is treated as a set of individual indentation tests. Each test is analyzed independently. Final averages are calculated only from included tests.

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

The contact depth is calculated as:

$$
h_c=h_{max}-\varepsilon\frac{P_{max}}{S}
$$

For a Berkovich indenter, the common Oliver–Pharr value is:

$$
\varepsilon\approx0.75
$$

The calculated $h_c$ is passed into the tip-area function $A(h_c)$.

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

If a test passes the numerical $R^2$ threshold but appears physically questionable, exclude it from final statistics.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%2010.05.19%E2%80%AFAM.png" alt="Exclude individual test from final statistics" width="900">

Possible reasons for exclusion include:

- surface defects,
- pores,
- poor contact,
- abnormal loading behavior,
- large offset,
- indentation on a nonrepresentative microstructural region.

After exclusion, final averages are recalculated using only the included tests:

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

The log is useful for reproducibility because it records the analysis sequence and inclusion/exclusion decisions.

---

## 6. Core Equations

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

---

## 7. What to Report

For publication, dissertation, or supplementary-methods reporting, include:

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

## 8. Common Issues

### File does not load

Check that the file is an Agilent G200 `.xls` or `.xlsx` export and contains full load–displacement curves.

### Fit passes but the curve looks wrong

Do not rely on $R^2$ alone. Inspect the curve in the **Test Plot** tab. Exclude tests affected by pores, surface roughness, poor contact, pile-up/sink-in artifacts, or abnormal loading behavior.

### Final average changes after excluding a test

This is expected. The software recalculates the mean, standard deviation, and coefficient of variation using only the included tests.