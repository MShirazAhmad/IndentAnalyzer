# IndentAnalyzer

**IndentAnalyzer** is an ISO 14577-4:2016-oriented nanoindentation analysis project with:
- a PyQt5 GUI workflow for experimental users,
- modular analysis code for programmatic use,
- NIST-style calibration utilities for tip and compliance studies.

This README is written as an extended, wiki-style reference for PhD researchers who need both **theory** and **implementation detail**.

---

## 1. Research Context and Scope

The project targets instrumented indentation analysis based on the Oliver-Pharr framework:
- load-displacement curve preprocessing,
- unloading-curve fitting,
- contact depth/area estimation,
- hardness and modulus extraction,
- quality checks against ISO-style thresholds.

It supports both:
1. **Operational analysis** (GUI + modular analyzer),
2. **Calibration workflows** (NIST-inspired routines for area function and compliance).

---

## 2. Theoretical Foundation (Short Reference)

### 2.1 Core Mechanical Quantities

Given maximum load \(P_{max}\), contact stiffness \(S\), and contact depth \(h_c\):

1. **Hardness**
   \[
   H = \frac{P_{max}}{A_c}
   \]
   where \(A_c\) is projected contact area.

2. **Reduced modulus**
   \[
   E_r = \frac{\sqrt{\pi}}{2} \cdot \frac{S}{\sqrt{A_c}}
   \]

3. **Sample modulus**
   \[
   \frac{1}{E_r} = \frac{1-\nu_s^2}{E_s} + \frac{1-\nu_i^2}{E_i}
   \]
   solved for \(E_s\), using indenter properties \((E_i,\nu_i)\) and sample Poisson ratio \(\nu_s\).

### 2.2 Unloading Curve Models

Implemented models include:
- **Oliver-Pharr form**: \(P = A(h-h_f)^m\)
- **Power-law form**: equivalent normalized representation

The fitting quality is evaluated via \(R^2\), with ISO-oriented thresholds in the standards module.

### 2.3 Area Function

Tip area function uses a polynomial-style expansion:
\[
A(h_c) = C_0 h_c^2 + C_1 h_c + C_2 h_c^{1/2} + C_3 h_c^{1/4} + ...
\]

For Berkovich, \(C_0 = 24.56\) is used as theoretical baseline; higher-order terms capture tip imperfections.

---

## 3. Project Structure (Active Path)

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
└── dump/  # archived/legacy utilities, docs, tests, data
    └── unused_src/
        └── calibration/
            └── tip_calibrator.py
```

> `dump/` contains historical scripts and artifacts; the active GUI workflow is rooted in `scripts/` + `src/`.

---

## 4. Installation and Launch

## 4.1 GUI-first launch (recommended)

From repository root:

```bash
bash scripts/launch_application.sh
```

The launcher checks/installs required Python packages (`PyQt5`, `matplotlib`, `pandas`, `numpy`, `scipy`, `xlrd`) and starts the GUI.

### 4.2 Manual Python setup (optional)

```bash
python3 -m pip install PyQt5 matplotlib pandas numpy scipy xlrd openpyxl
```

---

## 5. Data Expectations

The loader (`src/core/data_processor.py`) expects Excel (`.xls` or `.xlsx`) sheets containing load/displacement data.  
Column mapping is pattern-based (supports variants), then normalized to:
- `Load (mN)`
- `Displacement (nm)`
- optional `Time (sec)`

The system cleans numeric data, removes invalid rows, and identifies loading/unloading phases around peak load.

---

## 6. Script and Module Wiki (How each part works and how to use it)

## 6.1 `scripts/launch_application.sh`

**Purpose:** Operational entry point for end users.  
**How it works:** dependency checks -> inserts `src/` into Python path -> starts `gui.main_interface.NanoindentationGUI`.  
**Use it when:** you want interactive analysis, plotting, and exports without writing code.

```bash
bash scripts/launch_application.sh
```

## 6.2 `src/gui/main_interface.py`

**Purpose:** Full PyQt5 application layer.  
**Main responsibilities:**
- file selection and analysis controls,
- async analysis worker thread,
- result tables and per-test plotting,
- export buttons and runtime logs.

**Use it when:** you need visual QA, quick experiment turnaround, and operator-friendly workflow.

## 6.3 `src/analysis/main_analyzer.py`

**Purpose:** Main modular analysis engine (`NanoindentationAnalyzer`).  
**Pipeline:**
1. load Excel sheets,
2. preprocess and phase-separate,
3. fit unloading curve (Oliver-Pharr / power law / auto),
4. compute hardness/modulus set,
5. generate validation + quality assessment.

**Use it when:** scripting batch studies or building reproducible computational workflows.

Programmatic example:

```python
from src.analysis.main_analyzer import analyze_nanoindentation_file

results = analyze_nanoindentation_file(
    file_path="your_data.xls",
    sample_poisson=0.30,
    fitting_method="oliver_pharr"  # or "power_law", "auto"
)
print(results["overall_success"])
```

## 6.4 `src/analysis/curve_fitting.py`

**Purpose:** Unloading-fit implementations and contact-property extraction.  
**Includes:** model equations, fit bounds, parameter estimation, \(R^2\) acceptance, geometry-specific epsilon/exponent logic.  
**Use it when:** testing alternative fit strategies or extending tip geometry handling.

## 6.5 `src/analysis/mechanical_calculator.py`

**Purpose:** Core property calculations from \(P_{max}, S, h_c\).  
**Includes:** hardness, reduced modulus, sample modulus, derived indicators (e.g., H/E ratio).  
**Use it when:** validating formulas independently of GUI/loader.

## 6.6 `src/analysis/enhanced_analyzer.py`

**Purpose:** Backward-compatible analyzer path used as a fallback in GUI contexts.  
**Use it when:** reproducing historical behavior or comparing legacy vs modular outputs.

## 6.7 `src/analysis/legacy_analyzer.py`

**Purpose:** historical IndentXLSAnalyzer class retained for compatibility.  
**Use it when:** rerunning old notebooks/scripts that depended on the original class design.

## 6.8 `src/core/standards.py`

**Purpose:** central constants/configuration (ISO thresholds, tip geometry constants, reference properties).  
**Use it when:** adjusting global analysis policy (fit acceptance, calibration minima, material assumptions).

## 6.9 `src/core/data_processor.py`

**Purpose:** Excel IO, cleaning, normalization, and phase detection utilities.  
**Use it when:** diagnosing ingestion issues or adapting to new instrument export formats.

## 6.10 `src/core/validators.py`

**Purpose:** quality and consistency checks (completeness, noise, monotonicity, physical-range sanity).  
**Use it when:** enforcing data quality filters or generating QA reports for publication supplements.

## 6.11 `src/calibration/nist_methods.py`

**Purpose:** NIST-style calibration routines:
- load-frame compliance from compliance-vs-\(1/\sqrt{A}\),
- tip area function coefficient extraction,
- coefficient extraction from a reference XLS workflow.

**Use it when:** establishing metrological traceability before analyzing unknown samples.

## 6.12 `dump/unused_src/calibration/tip_calibrator.py`

**Purpose:** end-to-end calibration helper with plotting and interpretive output.  
**Typical use:** archived calibration studies with fused silica references and visual reporting.

---

## 7. Recommended Research Workflow

1. **Instrument + reference check** using fused silica and calibration utilities.  
2. **Run GUI or programmatic analyzer** on sample datasets.  
3. **Review fit quality and ISO-oriented thresholds** (`R²`, noise, monotonicity, physical plausibility).  
4. **Aggregate statistics** across indents/files (mean, SD, CV, outlier checks).  
5. **Document calibration coefficients and analysis parameters** alongside reported material properties.

---

## 8. Interpreting Outputs

Key output sections from modular analysis:
- `data_processing`: cleaning and phase extraction status,
- `curve_fitting`: model, parameters, \(R^2\), stiffness, contact depth,
- `mechanical_properties`: hardness, \(E_r\), sample modulus,
- `validation_report`: data and fit quality,
- `quality_assessment`: overall grade and compliance hints.

For publication-quality reporting, always include:
- fitting method,
- Poisson assumptions,
- area-function coefficients,
- quality thresholds used.

---

## 9. Troubleshooting

- **GUI does not open:** ensure PyQt5 install is successful and run from repo root.  
- **Excel read failures:** verify `.xls/.xlsx` format and expected load/displacement columns.  
- **Poor \(R^2\):** inspect unloading segment quality and acquisition noise; retry with `fitting_method="auto"`.  
- **Unphysical modulus/hardness:** verify calibration coefficients, indenter material constants, and sample Poisson ratio.

---

## 10. Notes on Archived Material

`dump/` contains historical scripts, tests, and documents from prior cleanup/restructuring cycles.  
Treat it as archive/reference unless you are explicitly reproducing legacy behavior.

# IndentAnalyzer

**IndentAnalyzer** is an ISO 14577-4:2016-oriented nanoindentation analysis project for extracting hardness, reduced modulus, sample modulus, and fit-quality metrics from instrumented indentation load-displacement data.

The project provides:

- a PyQt5 graphical workflow for experimental nanoindentation analysis,
- modular Python analysis code for reproducible batch processing,
- NIST-style calibration utilities for tip-area and compliance studies,
- GitHub-visible step-by-step screenshots for user documentation.

This README is written as a practical research guide for PhD-level nanoindentation work. It explains both **how to use the interface** and **what mathematics is applied at each step**.

---

## 1. Repository Preparation for GitHub Screenshots

The screenshots are supplied in `Archive.zip`. GitHub cannot display images directly from inside a `.zip` file, so the images must be extracted and committed into the repository.

Recommended folder structure:

```text
IndentAnalyzer/
├── README.md
├── docs/
│   └── screenshots/
│       ├── Screenshot 2026-05-01 at 9.49.06 AM.png
│       ├── Screenshot 2026-05-01 at 9.49.25 AM.png
│       ├── Screenshot 2026-05-01 at 9.50.04 AM.png
│       ├── Screenshot 2026-05-01 at 9.50.25 AM.png
│       ├── Screenshot 2026-05-01 at 9.50.33 AM.png
│       ├── Screenshot 2026-05-01 at 9.50.42 AM.png
│       ├── Screenshot 2026-05-01 at 9.50.53 AM.png
│       ├── Screenshot 2026-05-01 at 9.51.01 AM.png
│       ├── Screenshot 2026-05-01 at 9.51.10 AM.png
│       ├── Screenshot 2026-05-01 at 9.51.16 AM.png
│       ├── Screenshot 2026-05-01 at 9.51.54 AM.png
│       ├── Screenshot 2026-05-01 at 9.52.03 AM.png
│       └── Screenshot 2026-05-01 at 9.52.11 AM.png
├── scripts/
│   └── launch_application.sh
└── src/
    ├── gui/
    │   └── main_interface.py
    ├── analysis/
    ├── core/
    └── calibration/
```

From the repository root, extract the screenshots using:

```bash
mkdir -p docs/screenshots
unzip Archive.zip -d docs/screenshots
rm -rf docs/screenshots/__MACOSX
```

After extraction, commit the images:

```bash
git add README.md docs/screenshots/*.png
git commit -m "Add GUI workflow screenshots to README"
```

---

## 2. Research Context and Scope

IndentAnalyzer targets instrumented indentation analysis based on the Oliver-Pharr framework. The main workflow includes:

1. calibration of the indenter tip-area function,
2. experimental file selection,
3. analysis-parameter selection,
4. load-displacement curve fitting,
5. hardness and modulus extraction,
6. quality checking,
7. export of tabular and graphical results.

The active GUI workflow is implemented in:

```text
src/gui/main_interface.py
```

The GUI uses a five-step workflow:

1. **Calibration**
2. **File Selection**
3. **Analysis Settings**
4. **Run Analysis / Results**
5. **Export**

---

## 3. Installation and Launch

### 3.1 GUI-first launch

From the repository root:

```bash
bash scripts/launch_application.sh
```

The launcher checks and installs required Python packages, then starts the PyQt5 interface.

### 3.2 Manual Python setup

```bash
python3 -m pip install PyQt5 matplotlib pandas numpy scipy xlrd openpyxl
```

Then run the GUI through the project launcher or directly through the source workflow.

---

## 4. Step-by-Step GUI Workflow with Screenshots and Mathematics

### Step 1 — Start the Application

Launch the application from the repository root:

```bash
bash scripts/launch_application.sh
```

The interface opens with the ISO 14577-4:2016 nanoindentation workflow and the five analysis tabs.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%209.49.06%E2%80%AFAM.png" alt="IndentAnalyzer main interface at startup" width="900">

At startup, the GUI initializes the analysis worker, plotting widgets, calibration panel, and logging system. Runtime logs are written to the user log folder:

```text
~/IndentXLSAnalyzer_logs/
```

No mechanical properties are calculated at this stage. The purpose of this step is to confirm that the GUI, analysis modules, and plotting backend are loaded correctly.

---

### Step 2 — Tip Area Function Calibration

The first workflow tab is **Calibration**. Three calibration paths are supported:

1. load a previously saved `.json` or `.csv` calibration profile,
2. generate calibration from a fused-silica reference indentation file,
3. enter area-function coefficients manually from lab protocol or instrument software.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%209.49.25%E2%80%AFAM.png" alt="Calibration workflow tab" width="900">

The projected contact area is calculated using the area-function expansion:

\[
A(h_c)=C_0h_c^2+C_1h_c+C_2h_c^{1/2}+C_3h_c^{1/4}+C_4h_c^{1/8}+\cdots
\]

For an ideal Berkovich indenter, the theoretical leading coefficient is:

\[
C_0=24.56
\]

Higher-order coefficients account for real tip rounding, truncation, polishing defects, and deviations from the ideal Berkovich geometry.

For reference-material calibration, the compliance relation can be written as:

\[
C_{total}=C_f+\frac{\sqrt{\pi}}{2E_r\sqrt{A_c}}
\]

where \(C_{total}\) is measured total compliance, \(C_f\) is load-frame compliance, \(E_r\) is reduced modulus, and \(A_c\) is projected contact area.

The calibration step determines the coefficients needed to convert contact depth into projected contact area. This is essential because hardness and modulus both depend directly on \(A_c\).

---

### Step 3 — Calibration Profile Visualization

After loading, generating, or manually entering calibration coefficients, the GUI shows a calibration reliability profile on the right-side plotting panel.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%209.50.04%E2%80%AFAM.png" alt="Calibration profile visualization" width="900">

The calibration profile is used to inspect whether the loaded area function behaves reasonably over the contact-depth range of the experiment. A practical comparison is made against the ideal Berkovich area:

\[
A_{ideal}=24.56h_c^2
\]

The percentage deviation from the ideal tip area can be evaluated as:

\[
\Delta A(\%)=\frac{A_{calibrated}(h_c)-A_{ideal}(h_c)}{A_{ideal}(h_c)}\times100
\]

Large deviations at shallow depth usually indicate tip rounding or imperfect calibration. Large deviations over the entire depth range may indicate incorrect coefficients, wrong units, or use of a calibration profile outside its valid range.

---

### Step 4 — Select the Research Goal and Experimental File

The second workflow tab is **File Selection**. Select the experimental `.xls` or `.xlsx` nanoindentation file.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%209.50.25%E2%80%AFAM.png" alt="File selection workflow" width="900">

The data loader expects columns containing load and displacement information. Column names are pattern-matched and normalized to:

```text
Load (mN)
Displacement (nm)
Time (sec)    # optional
```

The imported raw arrays are treated as:

\[
P_i=P(t_i)
\]

\[
h_i=h(t_i)
\]

where \(P_i\) is load and \(h_i\) is displacement at acquisition point \(i\).

The maximum load and maximum depth are identified as:

\[
P_{max}=\max(P_i)
\]

\[
h_{max}=h(P_{max})
\]

The loading and unloading segments are separated around \(P_{max}\). This separation is necessary because Oliver-Pharr analysis uses the unloading stiffness to estimate elastic contact response.

---

### Step 5 — Choose Analysis Settings

The third workflow tab is **Analysis Settings**. The GUI exposes the main numerical assumptions and quality thresholds.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%209.50.33%E2%80%AFAM.png" alt="Analysis settings workflow" width="900">

The main settings include:

- plot generation,
- plot image export,
- minimum accepted \(R^2\),
- unloading fit percentage,
- sample Poisson ratio,
- indenter material,
- fitting method.

The sample Poisson ratio \(\nu_s\) is required to convert reduced modulus into sample modulus. For diamond, the indenter constants are commonly taken as:

\[
E_i\approx1141\,\text{GPa}
\]

\[
\nu_i\approx0.07
\]

The selected unloading percentage defines which upper portion of the unloading curve is fitted. This is important because the initial unloading segment most closely represents elastic recovery.

---

### Step 6 — Run the ISO-Oriented Analysis

The fourth workflow tab is **Results**. Press **Start Analysis** to process the selected indentation file.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%209.50.42%E2%80%AFAM.png" alt="Run analysis tab before analysis" width="900">

The primary unloading model is the Oliver-Pharr power-law form:

\[
P=\alpha(h-h_f)^m
\]

where \(\alpha\) is a fitting constant, \(h_f\) is final residual depth, and \(m\) is the unloading exponent.

The contact stiffness is obtained from the unloading slope at maximum depth:

\[
S=\left.\frac{dP}{dh}\right|_{h=h_{max}}
\]

For the power-law unloading model:

\[
S=\alpha m(h_{max}-h_f)^{m-1}
\]

The contact depth is then calculated as:

\[
h_c=h_{max}-\varepsilon\frac{P_{max}}{S}
\]

For Berkovich geometry, a common Oliver-Pharr value is:

\[
\varepsilon\approx0.75
\]

The calculated \(h_c\) is passed into the calibrated area function to calculate \(A_c\).

---

### Step 7 — Inspect Fit Quality and Test-Level Results

After analysis, the GUI populates result tables and test-plot buttons. Each test can be inspected individually.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%209.50.53%E2%80%AFAM.png" alt="Analysis results table" width="900">

The goodness of fit is quantified using:

\[
R^2=1-\frac{\sum_i(P_i-\hat{P}_i)^2}{\sum_i(P_i-\bar{P})^2}
\]

where \(P_i\) is measured load, \(\hat{P}_i\) is fitted load, and \(\bar{P}\) is mean measured load over the fitted region.

A fit is accepted only when it satisfies the selected threshold:

\[
R^2\ge R^2_{min}
\]

Poor \(R^2\), nonphysical stiffness, negative contact depth, or unstable fitted parameters should be treated as warning signs. Such tests should be reviewed before using them in publication-level statistics.

---

### Step 8 — Open Individual Nanoindentation Curves

The GUI provides per-test curve visualization. Open a test plot from the result buttons or the test-plot panel.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%209.51.01%E2%80%AFAM.png" alt="Individual nanoindentation curve view" width="900">

A typical plot contains:

- loading curve,
- unloading curve,
- fitted unloading segment,
- tangent stiffness line,
- selected test metadata.

The tangent line represents the stiffness used for mechanical-property extraction. The physical interpretation is that the initial unloading response approximates elastic recovery of the contact.

---

### Step 9 — Calculate Hardness

Hardness is calculated from the maximum applied load and projected contact area:

<img src="docs/screenshots/Screenshot%202026-05-01%20at%209.51.10%E2%80%AFAM.png" alt="Hardness and modulus result display" width="900">

\[
H=\frac{P_{max}}{A_c}
\]

where \(H\) is indentation hardness, \(P_{max}\) is maximum load, and \(A_c\) is projected contact area at contact depth.

In SI units:

\[
1\,\text{GPa}=10^9\,\text{Pa}=10^9\,\frac{\text{N}}{\text{m}^2}
\]

Therefore, consistent unit conversion is required when load is imported in mN and depth is imported in nm.

---

### Step 10 — Calculate Reduced Modulus

The reduced modulus is calculated from stiffness and contact area:

<img src="docs/screenshots/Screenshot%202026-05-01%20at%209.51.16%E2%80%AFAM.png" alt="Reduced modulus calculation and results" width="900">

\[
E_r=\frac{\sqrt{\pi}}{2}\frac{S}{\sqrt{A_c}}
\]

where \(E_r\) is reduced modulus, \(S\) is contact stiffness, and \(A_c\) is projected contact area.

This quantity includes elastic deformation from both sample and indenter. It is not yet the sample-only Young's modulus.

---

### Step 11 — Convert Reduced Modulus to Sample Modulus

The sample elastic modulus is calculated using the elastic contact relation:

<img src="docs/screenshots/Screenshot%202026-05-01%20at%209.51.54%E2%80%AFAM.png" alt="Sample modulus and quality assessment" width="900">

\[
\frac{1}{E_r}=\frac{1-\nu_s^2}{E_s}+\frac{1-\nu_i^2}{E_i}
\]

Solving for sample modulus gives:

\[
E_s=\frac{1-\nu_s^2}{\frac{1}{E_r}-\frac{1-\nu_i^2}{E_i}}
\]

where \(E_s\) is sample modulus, \(\nu_s\) is sample Poisson ratio, \(E_i\) is indenter modulus, and \(\nu_i\) is indenter Poisson ratio.

Because \(E_s\) depends on \(\nu_s\), the selected sample Poisson ratio must be reported with final modulus values.

---

### Step 12 — Review Reliability and Quality Assessment

The right-side result panel provides reliability information, calibration profile, and individual test plots.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%209.52.03%E2%80%AFAM.png" alt="Reliability and quality assessment panel" width="900">

Recommended quality checks include:

- accepted unloading fit \(R^2\),
- positive stiffness \(S>0\),
- physically meaningful contact depth \(0<h_c<h_{max}\),
- calibrated area \(A_c>0\),
- reasonable hardness and modulus ranges for the material system,
- coefficient of variation across repeated indents.

For repeated measurements, mean and standard deviation are calculated as:

\[
\bar{x}=\frac{1}{n}\sum_{i=1}^{n}x_i
\]

\[
s=\sqrt{\frac{1}{n-1}\sum_{i=1}^{n}(x_i-\bar{x})^2}
\]

Coefficient of variation is:

\[
CV(\%)=\frac{s}{\bar{x}}\times100
\]

These statistics should be reported for hardness, reduced modulus, and sample modulus when multiple valid indents are available.

---

### Step 13 — Export Final Results

The fifth workflow tab is **Export**. Export options include Excel and CSV outputs.

<img src="docs/screenshots/Screenshot%202026-05-01%20at%209.52.11%E2%80%AFAM.png" alt="Export final nanoindentation results" width="900">

For publication-quality reporting, exported data should preserve:

- file name,
- test identifier,
- \(P_{max}\),
- \(h_{max}\),
- \(h_c\),
- \(A_c\),
- stiffness \(S\),
- hardness \(H\),
- reduced modulus \(E_r\),
- sample modulus \(E_s\),
- fit method,
- fit percentage,
- \(R^2\),
- calibration coefficients,
- sample Poisson ratio,
- indenter material constants.

A complete experimental report should state the calibration source, the area-function coefficients, the selected Poisson ratio, and the acceptance threshold used for unloading fits.

---

## 5. Summary of Mathematical Pipeline

The complete analysis sequence is:

### 5.1 Input data

\[
P_i=P(t_i),\qquad h_i=h(t_i)
\]

### 5.2 Peak detection

\[
P_{max}=\max(P_i)
\]

\[
h_{max}=h(P_{max})
\]

### 5.3 Unloading fit

\[
P=\alpha(h-h_f)^m
\]

### 5.4 Contact stiffness

\[
S=\left.\frac{dP}{dh}\right|_{h=h_{max}}
\]

\[
S=\alpha m(h_{max}-h_f)^{m-1}
\]

### 5.5 Contact depth

\[
h_c=h_{max}-\varepsilon\frac{P_{max}}{S}
\]

### 5.6 Contact area

\[
A_c=A(h_c)=C_0h_c^2+C_1h_c+C_2h_c^{1/2}+C_3h_c^{1/4}+\cdots
\]

### 5.7 Hardness

\[
H=\frac{P_{max}}{A_c}
\]

### 5.8 Reduced modulus

\[
E_r=\frac{\sqrt{\pi}}{2}\frac{S}{\sqrt{A_c}}
\]

### 5.9 Sample modulus

\[
E_s=\frac{1-\nu_s^2}{\frac{1}{E_r}-\frac{1-\nu_i^2}{E_i}}
\]

### 5.10 Fit quality

\[
R^2=1-\frac{\sum_i(P_i-\hat{P}_i)^2}{\sum_i(P_i-\bar{P})^2}
\]

---

## 6. Project Structure

```text
IndentAnalyzer/
├── README.md
├── docs/
│   └── screenshots/
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
└── dump/
    └── unused_src/
```

`dump/` contains archived scripts, historical tests, and cleanup artifacts. Treat it as reference material unless reproducing older workflows.

---

## 7. Script and Module Guide

### 7.1 `scripts/launch_application.sh`

Operational entry point for GUI users. It checks dependencies, inserts `src/` into the Python path, and starts the PyQt5 GUI.

```bash
bash scripts/launch_application.sh
```

### 7.2 `src/gui/main_interface.py`

Main PyQt5 application layer. It provides:

- five-step workflow tabs,
- file selection,
- calibration controls,
- analysis settings,
- threaded analysis execution,
- result tables,
- Matplotlib plots,
- CSV and Excel export buttons,
- logging and runtime status updates.

### 7.3 `src/analysis/main_analyzer.py`

Main modular analysis engine. It loads indentation files, preprocesses data, fits unloading curves, computes mechanical properties, and returns structured results.

Programmatic example:

```python
from src.analysis.main_analyzer import analyze_nanoindentation_file

results = analyze_nanoindentation_file(
    file_path="your_data.xls",
    sample_poisson=0.30,
    fitting_method="oliver_pharr"
)

print(results["overall_success"])
```

### 7.4 `src/analysis/curve_fitting.py`

Contains unloading-fit models, fitting bounds, parameter estimation, contact-stiffness extraction, and fit-quality calculations.

### 7.5 `src/analysis/mechanical_calculator.py`

Calculates hardness, reduced modulus, sample modulus, and derived mechanical indicators from \(P_{max}\), \(S\), and \(h_c\).

### 7.6 `src/core/data_processor.py`

Handles Excel input, numeric cleaning, column normalization, invalid-row removal, and loading/unloading phase detection.

### 7.7 `src/core/standards.py`

Central location for ISO-oriented constants, thresholds, default material properties, geometry constants, and analysis policy settings.

### 7.8 `src/core/validators.py`

Provides data-quality and result-quality checks, including completeness, noise, monotonicity, and physical plausibility.

### 7.9 `src/calibration/nist_methods.py`

Provides NIST-style routines for reference-material calibration, load-frame compliance estimation, and tip-area function coefficient extraction.

---

## 8. Data Expectations

The loader expects Excel files with load and displacement columns. Supported file types:

```text
.xls
.xlsx
```

Expected physical quantities:

```text
Load
Displacement
Time    # optional
```

The software normalizes recognized column variants to:

```text
Load (mN)
Displacement (nm)
Time (sec)
```

Before analysis, verify that:

- load is in mN or is correctly converted,
- displacement is in nm or is correctly converted,
- unloading data are present,
- the peak load is physically meaningful,
- the file contains complete indentation curves rather than only summary values.

---

## 9. Recommended Research Workflow

1. Run fused-silica or reference-material calibration.
2. Confirm that the calibrated area function is reasonable over the experimental depth range.
3. Select the unknown sample indentation file.
4. Choose sample Poisson ratio and unloading-fit settings.
5. Run analysis.
6. Inspect each unloading fit and tangent stiffness line.
7. Reject curves with poor fit quality or nonphysical values.
8. Aggregate valid indents as mean ± standard deviation.
9. Export Excel or CSV results.
10. Report calibration coefficients, fit method, Poisson ratio, and quality threshold in manuscripts or supplements.

---

## 10. Troubleshooting

### GUI does not open

Run from the repository root and confirm PyQt5 is installed:

```bash
python3 -m pip install PyQt5
bash scripts/launch_application.sh
```

### Screenshots do not show on GitHub

Confirm that the images are extracted and committed under:

```text
docs/screenshots/
```

Confirm that the file names match the names used in this README exactly, including spaces and the `AM` timestamp text.

### Excel file does not load

Check that the file is `.xls` or `.xlsx` and contains load-displacement columns. If the instrument export uses unusual column names, update the pattern mapping in:

```text
src/core/data_processor.py
```

### Poor unloading fit

Inspect the raw curve. Common causes include:

- noisy unloading segment,
- thermal drift,
- surface roughness,
- pop-in events,
- incomplete unloading data,
- incorrect fit percentage,
- indentation into pores or heterogeneous microstructural regions.

### Unphysical hardness or modulus

Check:

- area-function coefficients,
- load and depth units,
- sample Poisson ratio,
- indenter material constants,
- contact-depth calculation,
- whether the selected indentation curve is valid.

---

## 11. Reporting Checklist for Publications

When reporting nanoindentation results, include:

- instrumented indentation method,
- indenter geometry,
- maximum load or depth protocol,
- number of indents,
- calibration material,
- area-function coefficients,
- load-frame compliance correction if used,
- unloading model,
- unloading fit percentage,
- \(R^2\) threshold,
- sample Poisson ratio,
- hardness mean ± standard deviation,
- reduced modulus mean ± standard deviation,
- sample modulus mean ± standard deviation,
- reason for excluding any invalid indents.

For high-entropy carbides and other heterogeneous ceramics, also report microstructural context when available, including porosity, grain-size scale, phase purity, and indentation placement relative to visible pores or second phases.