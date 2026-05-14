# Analysis Configuration

Use this page to tune IndentAnalyzer defaults without changing scientific meaning accidentally.

## Where to configure

### Researcher-editable settings

```text
config/analysis_settings.ini
```

Primary sections:

- `[analysis]`
- `[calibration]`
- `[loader]`
- `[validation]`

### Engine-level constants

```text
src/core/standards.py
```

Edit this only when intentionally changing core algorithm behavior for all users.

## Key settings and scientific impact

### `[analysis] min_r_squared`

Minimum accepted fit quality threshold.

- Higher value: stricter acceptance, fewer tests kept.
- Lower value: more tests kept, higher risk of physically poor fits.

### `[analysis] fit_curve_percent`

Controls fraction of curve used by fitting pathways.

- Can improve robustness for noisy tails.
- Must be reported in methods if changed from defaults.

### `[analysis] default_fitting_method`

Typical values:

- `oliver_pharr`
- `power_law`
- `auto`

Use `auto` when method comparison is desired, but still inspect physical plausibility in `Curve Viewer`.

### `[calibration]` reference constants

Includes fused silica reference values and default indenter assumptions used in calibration paths. Ensure these match your laboratory method documentation.

### `[validation]` physical limits

Hardness/modulus bounds provide plausibility guards. Treat out-of-range values as prompts for review, not blind rejection.

## Units you must keep consistent

- Load: mN
- Displacement/contact depth: nm
- Contact area (internal path): nm² (converted to SI for mechanics)
- Modulus internal calculations: Pa (reported commonly in GPa)

Cross-check with [Mathematical Calculations](calculations.md).

## Safe change workflow

1. Change one parameter group at a time.
2. Run the same known dataset before/after.
3. Compare accepted-test counts and mean property shifts.
4. Confirm curve-level plausibility, not only summary metrics.
5. Document changed values in your experimental methods/report.

## Related pages

- [GUI Walkthrough](gui-walkthrough.md)
- [Mathematical Calculations](calculations.md)
- [File Loaders](file-loaders.md)

