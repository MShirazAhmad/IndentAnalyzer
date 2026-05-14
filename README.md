# IndentAnalyzer

**IndentAnalyzer** is a Python/PyQt nanoindentation analysis system for Excel data exported from an **Agilent Nano Indenter G200 system (MTS Nano Instruments, Oak Ridge, TN, USA)**. It supports a complete research workflow: fused-silica tip-area calibration, sample-file loading, loading/unloading curve inspection, Oliver-Pharr-style analysis, CSM profile review, test exclusion, and final statistical reporting.

The project is written for researchers who need traceable hardness and modulus calculations rather than a black-box spreadsheet. The documentation explains the physical equations, units, assumptions, validation checks, and code modules used to transform load-displacement data into mechanical properties.

## What the software calculates

For each usable indentation test, IndentAnalyzer can report:

- maximum load and maximum displacement,
- unloading fit parameters and fit quality,
- contact stiffness,
- contact depth,
- projected contact area,
- hardness,
- reduced modulus,
- sample elastic modulus,
- test-level validation warnings,
- included/excluded-test statistics.

The default analysis pathway follows the Oliver-Pharr family of instrumented-indentation calculations. The documentation also explains the limits of those calculations, including the importance of tip-area calibration, pile-up/sink-in behavior, surface roughness, porosity, and microstructural heterogeneity.

## Repository structure

```text
src/
  analysis/      curve fitting, CSM analysis, mechanical-property orchestration
  calibration/   NIST-style compliance and tip-area calibration helpers
  core/          constants, standards, validation, preprocessing, batch processing
  fileloader/    Agilent G200 file normalization layer
  gui/           PyQt desktop interface
docs/            ReadTheDocs / MkDocs scientific documentation
scripts/         launch and utility scripts
samples/         example research data files, when present
```

## Installation

```bash
git clone https://github.com/MShirazAhmad/IndentAnalyzer.git
cd IndentAnalyzer
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## Launch the GUI

```bash
bash scripts/launch_application.sh
```

If the shell launcher is unavailable on Windows, run:

```powershell
python src\gui\main_interface.py
```

## Basic programmatic use

```python
from src.analysis.main_analyzer import NanoindentationAnalyzer

analyzer = NanoindentationAnalyzer(sample_poisson=0.17)
results = analyzer.analyze_file(
    "samples/HEC12_2_03132025.xls",
    fitting_method="oliver_pharr",
)
```

## Core equations

The projected contact area is evaluated from the contact depth \(h_c\):

$$
A_c = A(h_c)=C_0h_c^2+C_1h_c+C_2h_c^{1/2}+C_3h_c^{1/4}+\cdots
$$

For an ideal Berkovich tip, \(C_0\approx24.56\). Real tips should be calibrated because tip rounding, wear, and truncation directly affect hardness and modulus.

The unloading curve is represented with a power law:

$$
P(h)=\alpha(h-h_f)^m
$$

The contact stiffness is the unloading slope at maximum depth:

$$
S=\left.\frac{dP}{dh}\right|_{h=h_{max}}
$$

The contact depth is calculated as:

$$
h_c=h_{max}-\varepsilon\frac{P_{max}}{S}
$$

Hardness is:

$$
H=\frac{P_{max}}{A_c}
$$

Reduced modulus is:

$$
E_r=\frac{\sqrt{\pi}}{2\beta}\frac{S}{\sqrt{A_c}}
$$

Sample modulus is obtained from the reduced-modulus compliance relation:

$$
\frac{1}{E_r}=\frac{1-\nu_s^2}{E_s}+\frac{1-\nu_i^2}{E_i}
$$

## Documentation

The detailed scientific documentation is in `docs/` and is built with MkDocs for ReadTheDocs.

```bash
python -m pip install -r docs/requirements.txt
mkdocs serve
```

Build the documentation locally with strict checking:

```bash
mkdocs build --clean --strict
```

Start with:

- `docs/scientific-methods.md` for the scientific basis and equations,
- `docs/implementation-map.md` for module/function structure,
- `docs/calculations.md` for unit conversions and property calculations,
- `docs/validation-and-trust.md` for reproducibility, uncertainty, and result-quality checks.

## Scientific reporting checklist

For dissertation, manuscript, or supplementary-methods reporting, record:

- instrument model and software version/commit,
- indenter geometry and material,
- calibration material and calibration file,
- area-function coefficients,
- load/depth protocol,
- fitting model and fit-window rule,
- sample Poisson ratio,
- number of total, accepted, and excluded indents,
- exclusion rationale,
- hardness and modulus as mean ± standard deviation,
- coefficient of variation,
- microstructural context such as porosity, grain size, phase purity, and indentation placement.

## License

See `LICENSE` for the repository license. If you reuse the software or documentation in a manuscript, thesis, presentation, or derivative research workflow, cite the repository and the exact version/commit used.
