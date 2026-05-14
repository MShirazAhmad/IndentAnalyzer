# Analysis Configuration

IndentAnalyzer has two configuration surfaces:

1. Researcher-editable defaults in `config/analysis_settings.ini`.
2. Code-level constants in `src/core/standards.py`.

Use the INI file for workflow defaults and GUI-facing settings. Edit `standards.py` only when changing the behavior of the analysis engine itself.

## Researcher Defaults

The editable settings file is:

```text
config/analysis_settings.ini
```

It is organized into sections:

```ini
[analysis]
[calibration]
[loader]
[validation]
```

Keep section names and key names unchanged because GUI workflows read them directly.

## `[analysis]`

Controls curve-processing and fit defaults.

### `min_data_points_loading`

Minimum number of numeric points required in the loading segment.

```ini
min_data_points_loading = 50
```

Increase this if you want stricter data completeness. Decrease it only for sparse files where the curve is still scientifically acceptable.

### `min_data_points_unloading`

Minimum number of numeric points required in the unloading segment.

```ini
min_data_points_unloading = 30
```

Unloading fits are sensitive to point count, so lowering this can make stiffness and modulus less stable.

### `min_r_squared`

Minimum accepted coefficient of determination for curve fits.

```ini
min_r_squared = 0.98
```

This is dimensionless. A stricter value rejects more tests. A lower value accepts more tests but may include poor unloading fits.

### `fit_curve_percent`

Fit window as a percentage of the curve segment.

```ini
fit_curve_percent = 25.0
```

Use this for workflows that fit only a portion of loading or unloading data. Confirm the implementation path using the Code Reference before relying on this setting for a publication workflow.

### `noise_threshold`

Relative noise threshold.

```ini
noise_threshold = 0.15
```

This is a fraction, not a percent. `0.15` means 15% relative noise.

### `default_fitting_method`

Default unloading fit model.

```ini
default_fitting_method = oliver_pharr
```

Common values:

```text
oliver_pharr
power_law
auto
```

Use `auto` when you want the analyzer to compare available methods and choose the best successful fit by fit quality.

## `[calibration]`

Controls reference material and indenter defaults.

### `reference_material`

Name of the calibration reference material.

```ini
reference_material = fused_silica
```

The current code includes fused silica as the primary reference material.

### `reference_modulus`

Reference modulus in pascals.

```ini
reference_modulus = 72e9
```

This uses scientific notation. `72e9` means \(72\ \text{GPa}\).

### `reference_poisson`

Reference material Poisson ratio.

```ini
reference_poisson = 0.17
```

This is dimensionless.

### `reference_hardness`

Reference hardness in gigapascals.

```ini
reference_hardness = 9.0
```

### `default_indenter`

Default indenter material.

```ini
default_indenter = diamond
```

The material properties are defined in `MaterialProperties` and `ISO14577Constants` in `src/core/standards.py`.

## `[loader]`

Controls the default file-loader module.

### `default_file_loader`

Python module name from `src/fileloader/`, without `.py`.

```ini
default_file_loader = AgilentG200
```

If you add:

```text
src/fileloader/MyInstrument.py
```

then set:

```ini
default_file_loader = MyInstrument
```

See the File Loaders guide for the required loader output structure.

## `[validation]`

Controls plausible physical-property limits used in quality checks.

### `max_hardness` and `min_hardness`

Hardness limits in GPa.

```ini
max_hardness = 100.0
min_hardness = 0.1
```

Values outside this range are treated as physically suspicious.

### `max_modulus` and `min_modulus`

Modulus limits in Pa.

```ini
max_modulus = 1000e9
min_modulus = 1e9
```

`1000e9` means \(1000\ \text{GPa}\).

## Code-Level Constants

The code-level constants file is:

```text
src/core/standards.py
```

It contains:

- `ISO14577Constants`,
- `AnalysisConfig`,
- `MaterialProperties`,
- `AreaFunctionCoefficients`,
- `ValidationLimits`.

Edit this file when a default is part of the analysis engine rather than a GUI/workflow preference.

## `ISO14577Constants`

Defines standards-style constants:

```python
MIN_DATA_POINTS_LOADING = 50
MIN_DATA_POINTS_UNLOADING = 30
MIN_R_SQUARED = 0.98
STIFFNESS_RANGE_PERCENT = 0.25
FUSED_SILICA_MODULUS = 72e9
FUSED_SILICA_POISSON = 0.17
DIAMOND_MODULUS = 1140e9
DIAMOND_POISSON = 0.07
PERFECT_BERKOVICH_C0 = 24.56
```

It also stores geometry factors for Berkovich, Vickers, conical, spherical/paraboloid, cube-corner, and flat-punch assumptions.

## `AnalysisConfig`

Defines processing, fitting, calibration, and quality-control behavior:

```python
LOAD_THRESHOLD_FACTOR = 0.1
MIN_LOAD_THRESHOLD = 40
NOISE_THRESHOLD = 0.15
MIN_SEGMENT_LENGTH = 5
MIN_DISPLACEMENT_SPAN = 10.0
UNLOADING_FIT_RANGE = 0.75
MIN_UNLOADING_POINTS = 10
MIN_INDENTS_FOR_CALIBRATION = 5
MAX_FITTING_ITERATIONS = 10000
```

Change these carefully because they affect all users of the analysis engine.

## `MaterialProperties`

Defines material lookup values:

```python
MATERIALS = {
    "fused_silica": {...},
    "diamond": {...},
    "aluminum": {...},
    "steel": {...},
}
```

To add a material:

```python
"my_material": {
    "modulus": 123e9,
    "poisson": 0.25,
    "hardness": 4.2,
    "name": "My Material",
}
```

Use modulus in Pa and hardness in GPa unless you also update the calling code.

## `AreaFunctionCoefficients`

Defines default area-function coefficient presets:

```python
PERFECT_BERKOVICH = {
    "C0": 24.56,
    "C1": 0.0,
    "C2": 0.0,
    ...
}
```

The calculator expects contact depth in nm and area in nm² for the default area-function path. Keep units consistent when adding a preset.

## `ValidationLimits`

Defines quality labels and physical bounds:

```python
EXCELLENT_R2 = 0.99
GOOD_R2 = 0.98
ACCEPTABLE_R2 = 0.95
LOW_NOISE = 0.05
MODERATE_NOISE = 0.15
HIGH_NOISE = 0.30
MIN_HARDNESS = 0.1
MAX_HARDNESS = 100.0
MIN_MODULUS = 1e9
MAX_MODULUS = 1000e9
```

These are used by validation reports and quality assessment.

## Safe Editing Workflow

1. Change one setting at a time.
2. Keep units exactly as documented.
3. Run a known sample before and after the change.
4. Compare hardness, modulus, contact depth, fit \(R^2\), and accepted/rejected test counts.
5. Document the changed setting if it affects published results.
6. Run the docs build if documentation was updated:

```bash
.venv/bin/mkdocs build --clean --strict
```

## Common Edits

### Use another file loader

```ini
[loader]
default_file_loader = MyInstrument
```

### Use automatic fit selection

```ini
[analysis]
default_fitting_method = auto
```

### Relax fit acceptance

```ini
[analysis]
min_r_squared = 0.95
```

Only do this when you have inspected the curves and can justify the lower threshold.

### Add a new material in code

Edit `MaterialProperties.MATERIALS` in `src/core/standards.py`, then use the new key when constructing the analyzer:

```python
analyzer = NanoindentationAnalyzer(indenter_material="my_material")
```

## Configuration Checklist

- Use `config/analysis_settings.ini` for GUI/workflow defaults.
- Use `src/core/standards.py` for engine-level constants.
- Keep units consistent: load mN, depth nm, area nm² for area-function output, modulus Pa internally, displayed modulus GPa.
- Keep loader names aligned with filenames in `src/fileloader/`.
- Rebuild and rerun known examples after changing thresholds.
