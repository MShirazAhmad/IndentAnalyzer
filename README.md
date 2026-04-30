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
│       ├── nist_methods.py
│       └── tip_calibrator.py
└── dump/  # archived/legacy utilities, docs, tests, data
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

## 6.12 `src/calibration/tip_calibrator.py`

**Purpose:** end-to-end calibration helper with plotting and interpretive output.  
**Typical use:** calibration studies with fused silica references and visual reporting.

Module-style execution example:

```bash
python3 -m src.calibration.tip_calibrator
```

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

