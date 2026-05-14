# Function Reference

This page documents the main Python classes and functions in the same practical style as framework reference documentation: grouped by purpose, with signatures, behavior, examples, and links to the generated source pages.

The project does not expose network endpoints or a web service. These are Python entry points used by the GUI, scripts, tests, and future developer workflows.

## Main Analysis

The main analysis entry points live in `src.analysis.main_analyzer`.

### `NanoindentationAnalyzer` [source](reference/analysis/main_analyzer.md)

High-level orchestrator for a complete nanoindentation analysis workflow.

```python
NanoindentationAnalyzer(
    area_function_coefficients: Optional[Dict] = None,
    sample_poisson: float = 0.3,
    indenter_material: str = "diamond",
)
```

Creates the loader, processor, validator, curve fitter, calibration helper, area function, and mechanical-property calculator used by file and directory analysis.

Usage:

```python
from src.analysis.main_analyzer import NanoindentationAnalyzer

analyzer = NanoindentationAnalyzer(sample_poisson=0.30)
results = analyzer.analyze_file("samples/HEC12_2_03132025.xls")
```

Parameters:

- `area_function_coefficients`: optional calibrated area-function coefficients. If omitted, the ideal Berkovich coefficients are used.
- `sample_poisson`: sample Poisson ratio used when converting reduced modulus into sample elastic modulus.
- `indenter_material`: material lookup key. The default is `diamond`.

### `analyze_file(file_path, fitting_method="oliver_pharr")` [source](reference/analysis/main_analyzer.md)

Analyzes every valid indentation sheet in one Excel workbook.

```python
analyzer.analyze_file(
    file_path: Union[str, Path],
    fitting_method: str = "oliver_pharr",
) -> Dict[str, Any]
```

Accepted fitting methods:

- `oliver_pharr`: use the Oliver-Pharr unloading model.
- `power_law`: use the normalized power-law unloading model.
- `auto`: fit multiple methods and keep the best successful one.

Returns a dictionary containing:

- file path and timestamp,
- analysis parameters,
- per-test results,
- file summary,
- warnings and errors.

Example:

```python
results = analyzer.analyze_file(
    "samples/Silica Before.xls",
    fitting_method="auto",
)

print(results["file_summary"]["successful_tests"])
```

### `analyze_single_test(data, test_name, fitting_method="oliver_pharr")` [source](reference/analysis/main_analyzer.md)

Analyzes one normalized test DataFrame.

```python
analyzer.analyze_single_test(
    data: pandas.DataFrame,
    test_name: str,
    fitting_method: str = "oliver_pharr",
) -> Dict[str, Any]
```

The input DataFrame should contain:

```text
Time (sec)
Load (mN)
Displacement (nm)
```

This method performs processing, unloading fitting, mechanical-property calculation, validation, and quality assessment.

### `analyze_directory(directory_path, file_pattern="*.xls*", fitting_method="oliver_pharr")` [source](reference/analysis/main_analyzer.md)

Analyzes every matching Excel file in a directory.

```python
analyzer.analyze_directory(
    directory_path: Union[str, Path],
    file_pattern: str = "*.xls*",
    fitting_method: str = "oliver_pharr",
) -> Dict[str, Any]
```

Use this for sample batches where each workbook contains multiple indentation tests.

Example:

```python
batch = analyzer.analyze_directory("samples", file_pattern="*.xls")
print(batch["batch_summary"])
```

### `get_summary_report(analysis_type="latest")` [source](reference/analysis/main_analyzer.md)

Returns a summary of stored analysis results.

```python
analyzer.get_summary_report(analysis_type: str = "latest") -> Dict[str, Any]
```

`analysis_type` can target the latest stored analysis or available batch summaries, depending on what has been run in the analyzer instance.

### `export_results(output_path, format_type="excel")` [source](reference/analysis/main_analyzer.md)

Exports stored analysis results.

```python
analyzer.export_results(
    output_path: Union[str, Path],
    format_type: str = "excel",
) -> bool
```

Supported output paths are handled by the internal Excel, CSV, and JSON export helpers.

### `analyze_nanoindentation_file(file_path, sample_poisson=0.3, fitting_method="oliver_pharr")` [source](reference/analysis/main_analyzer.md)

Convenience function for one-file analysis without manually constructing an analyzer.

```python
analyze_nanoindentation_file(
    file_path: Union[str, Path],
    sample_poisson: float = 0.3,
    fitting_method: str = "oliver_pharr",
) -> Dict[str, Any]
```

Example:

```python
from src.analysis.main_analyzer import analyze_nanoindentation_file

results = analyze_nanoindentation_file("samples/HEC14 SP1_03132025.xls")
```

## File Loading

The Agilent G200 loader lives in `src.fileloader.AgilentG200`.

### `supports_file(file_path)` [source](reference/fileloader/AgilentG200.md)

Returns whether the loader accepts a file extension.

```python
supports_file(file_path: Union[str, Path]) -> bool
```

Accepted extensions:

```text
.xls
.xlsx
```

### `get_sheet_names(file_path)` [source](reference/fileloader/AgilentG200.md)

Returns all sheet names from an Excel workbook.

```python
get_sheet_names(file_path: Union[str, Path]) -> list[str]
```

### `load_sheet(file_path, sheet_name=0)` [source](reference/fileloader/AgilentG200.md)

Reads one raw sheet and returns vendor columns plus detected unit labels.

```python
load_sheet(
    file_path: Union[str, Path],
    sheet_name=0,
) -> Tuple[pandas.DataFrame, Dict[str, str]]
```

This is useful for GUI expert mode or debugging vendor export layout.

### `load_file(file_path)` [source](reference/fileloader/AgilentG200.md)

Loads a complete Agilent G200 workbook into the normalized analyzer structure.

```python
load_file(file_path: Union[str, Path]) -> Dict[str, object]
```

Return shape:

```python
{
    "success": bool,
    "data": {
        "Test 001": dataframe,
        "Test 002": dataframe,
    },
    "metadata": {...},
    "errors": [...],
    "warnings": [...],
}
```

Only sheets matching the `Test ###` pattern are processed.

### `normalize_sheet(df)` [source](reference/fileloader/AgilentG200.md)

Extracts and renames Agilent columns into the analyzer format.

```python
normalize_sheet(df: pandas.DataFrame) -> pandas.DataFrame
```

Output columns:

```text
Time (sec)
Load (mN)
Displacement (nm)
```

Rows with invalid numeric values are removed.

## Data Processing

The processing classes live in `src.core.data_processor`.

### `ExcelDataLoader` [source](reference/core/data_processor.md)

General loader wrapper that dispatches to a selected vendor loader module.

```python
ExcelDataLoader()
```

By default it uses:

```text
AgilentG200
```

### `set_loader(loader_module_name)` [source](reference/core/data_processor.md)

Changes the vendor loader module name.

```python
loader.set_loader(loader_module_name: str)
```

Use this when a future loader is added under `src/fileloader/`.

### `load_excel_file(file_path)` [source](reference/core/data_processor.md)

Loads and normalizes a workbook through the configured loader.

```python
loader.load_excel_file(file_path: Union[str, Path]) -> Dict[str, Any]
```

The returned structure follows the same `success`, `data`, `metadata`, `errors`, and `warnings` pattern used by the vendor loader.

### `DataProcessor` [source](reference/core/data_processor.md)

Processes one normalized indentation curve.

```python
DataProcessor()
```

### `process_test_data(df, test_name="Unknown")` [source](reference/core/data_processor.md)

Filters, splits, and annotates one indentation test.

```python
processor.process_test_data(
    df: pandas.DataFrame,
    test_name: str = "Unknown",
) -> Dict[str, Any]
```

This method:

- verifies required columns,
- filters low-load points,
- separates loading and unloading,
- detects horizontal segments,
- returns phase data and metadata.

### `BatchProcessor` [source](reference/core/data_processor.md)

Processes multiple files without running the full mechanical-property stack.

```python
BatchProcessor()
```

### `process_directory(directory_path, file_pattern="*.xls*")` [source](reference/core/data_processor.md)

Processes every matching workbook in a directory.

```python
batch.process_directory(
    directory_path: Union[str, Path],
    file_pattern: str = "*.xls*",
) -> Dict[str, Any]
```

### `process_single_file(file_path)` [source](reference/core/data_processor.md)

Loads and processes each test sheet in one workbook.

```python
batch.process_single_file(file_path: Union[str, Path]) -> Dict[str, Any]
```

### `create_summary_statistics(batch_results)` [source](reference/core/data_processor.md)

Builds summary statistics from `BatchProcessor` output.

```python
create_summary_statistics(batch_results: Dict[str, Any]) -> Dict[str, Any]
```

## Curve Fitting

Curve-fitting tools live in `src.analysis.curve_fitting`.

### `CurveFitter` [source](reference/analysis/curve_fitting.md)

Fits unloading curves and calculates stiffness/contact depth.

```python
CurveFitter()
```

### `power_law_unloading(h, P_max, h_f, m)` [source](reference/analysis/curve_fitting.md)

Static model function for normalized power-law unloading.

```python
CurveFitter.power_law_unloading(
    h: numpy.ndarray,
    P_max: float,
    h_f: float,
    m: float,
) -> numpy.ndarray
```

Formula:

\[
P(h)=P_{\max}\left(\frac{h-h_f}{h_{\max}-h_f}\right)^m
\]

### `oliver_pharr_unloading(h, A, h_f, m)` [source](reference/analysis/curve_fitting.md)

Static model function for Oliver-Pharr unloading.

```python
CurveFitter.oliver_pharr_unloading(
    h: numpy.ndarray,
    A: float,
    h_f: float,
    m: float,
) -> numpy.ndarray
```

Formula:

\[
P(h)=A(h-h_f)^m
\]

### `fit_unloading_curve(displacement, load, method="oliver_pharr", tip_geometry="berkovich")` [source](reference/analysis/curve_fitting.md)

Fits an unloading curve and returns fit parameters, fit quality, stiffness, and contact depth.

```python
fitter.fit_unloading_curve(
    displacement: numpy.ndarray,
    load: numpy.ndarray,
    method: str = "oliver_pharr",
    tip_geometry: str = "berkovich",
) -> Dict[str, Any]
```

Returns:

- `success`,
- `parameters`,
- `r_squared`,
- `r_squared_full`,
- `stiffness`,
- `contact_depth`,
- fitted curve arrays,
- tangent-line arrays,
- errors.

### `LinearFitter.fit_linear_stiffness(displacement, load, fit_range=0.25)` [source](reference/analysis/curve_fitting.md)

Fits a linear stiffness estimate on the highest-load unloading segment.

```python
LinearFitter.fit_linear_stiffness(
    displacement: numpy.ndarray,
    load: numpy.ndarray,
    fit_range: float = 0.25,
) -> Dict[str, Any]
```

The slope of \(P=Sh+b\) is returned as `stiffness`.

### `AreaFunction` [source](reference/analysis/curve_fitting.md)

Evaluates the projected contact area from area-function coefficients.

```python
AreaFunction(coefficients: Optional[Dict] = None)
```

### `calculate_contact_area(contact_depth)` [source](reference/analysis/curve_fitting.md)

Calculates contact area for a contact depth in nanometres.

```python
area_function.calculate_contact_area(contact_depth: float) -> float
```

Formula:

\[
A(h_c)=C_0h_c^2+C_1h_c+C_2h_c^{1/2}+\cdots+C_8h_c^{1/128}
\]

### `update_coefficients(new_coefficients)` [source](reference/analysis/curve_fitting.md)

Updates area-function coefficients in place.

```python
area_function.update_coefficients(new_coefficients: Dict)
```

### `fit_multiple_methods(displacement, load)` [source](reference/analysis/curve_fitting.md)

Runs Oliver-Pharr, normalized power-law, and linear stiffness approaches and ranks successful methods by \(R^2\).

```python
fit_multiple_methods(
    displacement: numpy.ndarray,
    load: numpy.ndarray,
) -> Dict[str, Dict]
```

## Mechanical Properties

Mechanical calculations live in `src.analysis.mechanical_calculator`.

### `MechanicalPropertiesCalculator` [source](reference/analysis/mechanical_calculator.md)

Calculates hardness, reduced modulus, sample modulus, and derived values.

```python
MechanicalPropertiesCalculator(area_function: Optional[AreaFunction] = None)
```

### `calculate_hardness(max_load, contact_area)` [source](reference/analysis/mechanical_calculator.md)

Calculates hardness from maximum load and projected contact area.

```python
calculator.calculate_hardness(
    max_load: float,
    contact_area: float,
) -> Dict[str, float]
```

Input units:

- `max_load`: mN,
- `contact_area`: nm².

Formula:

\[
H=\frac{P_{\max}}{A_c}
\]

### `calculate_reduced_modulus(stiffness, contact_area)` [source](reference/analysis/mechanical_calculator.md)

Calculates reduced modulus.

```python
calculator.calculate_reduced_modulus(
    stiffness: float,
    contact_area: float,
) -> Dict[str, float]
```

Input units:

- `stiffness`: mN/nm,
- `contact_area`: nm².

Formula:

\[
E_r=\frac{\sqrt{\pi}}{2\beta}\frac{S}{\sqrt{A_c}}
\]

with \(\beta=1.034\).

### `calculate_sample_modulus(reduced_modulus, indenter_material="diamond", sample_poisson=0.3)` [source](reference/analysis/mechanical_calculator.md)

Calculates sample modulus from reduced modulus and elastic constants.

```python
calculator.calculate_sample_modulus(
    reduced_modulus: float,
    indenter_material: str = "diamond",
    sample_poisson: float = 0.3,
) -> Dict[str, float]
```

`reduced_modulus` is expected in Pa.

### `calculate_all_properties(max_load, contact_depth, stiffness, sample_poisson=0.3, indenter_material="diamond")` [source](reference/analysis/mechanical_calculator.md)

Runs contact area, hardness, reduced modulus, sample modulus, and derived-property calculations together.

```python
calculator.calculate_all_properties(
    max_load: float,
    contact_depth: float,
    stiffness: float,
    sample_poisson: float = 0.3,
    indenter_material: str = "diamond",
) -> Dict[str, Any]
```

Input units:

- `max_load`: mN,
- `contact_depth`: nm,
- `stiffness`: mN/nm.

### `TipCalibration` [source](reference/analysis/mechanical_calculator.md)

Calibrates area-function coefficients from reference-material measurements.

```python
TipCalibration(reference_material: str = "fused_silica")
```

### `calibrate_area_function(measurements)` [source](reference/analysis/mechanical_calculator.md)

Fits a simple area function from measurement dictionaries.

```python
tip_calibration.calibrate_area_function(measurements: list) -> Dict[str, Any]
```

Expected measurement keys:

```text
contact_depth
stiffness
max_load
```

### `analyze_property_trends(property_data, depth_range=None)` [source](reference/analysis/mechanical_calculator.md)

Computes statistics, depth trends, and outlier information across repeated property results.

```python
analyze_property_trends(
    property_data: list,
    depth_range: Tuple[float, float] | None = None,
) -> Dict[str, Any]
```

## Calibration

Calibration helpers live in `src.calibration.nist_methods`.

### `NISTCalibrationMethods` [source](reference/calibration/nist_methods.md)

Implements NIST-style calibration workflows.

```python
NISTCalibrationMethods()
```

### `calibrate_load_frame_compliance(reference_data)` [source](reference/calibration/nist_methods.md)

Fits load-frame compliance from reference indentation results.

```python
nist.calibrate_load_frame_compliance(
    reference_data: List[Dict],
) -> Dict[str, Any]
```

Expected keys in each reference-data row:

```text
max_load
contact_area
stiffness
modulus
```

Model:

\[
C_{\text{total}}=C_{\text{lf}}+k\frac{1}{\sqrt{A}}
\]

The intercept is returned as `load_frame_compliance`.

### `calibrate_tip_area_function(reference_data, known_modulus=None)` [source](reference/calibration/nist_methods.md)

Calibrates tip-area coefficients from reference-material contact depths and stiffness values.

```python
nist.calibrate_tip_area_function(
    reference_data: List[Dict],
    known_modulus: float | None = None,
) -> Dict[str, Any]
```

Expected keys:

```text
contact_depth
stiffness
reduced_modulus
```

### `extract_tip_coefficients_from_file(xls_file_path, reference_material="fused_silica")` [source](reference/calibration/nist_methods.md)

Analyzes a calibration workbook and extracts fitted area-function coefficients.

```python
nist.extract_tip_coefficients_from_file(
    xls_file_path: str,
    reference_material: str = "fused_silica",
) -> Dict[str, Any]
```

Use this when the user has a fused-silica calibration export and needs coefficients for later sample analysis.

### `validate_reference_material(measurement_data, expected_modulus, expected_hardness)` [source](reference/calibration/nist_methods.md)

Compares measured reference-material results to expected values.

```python
nist.validate_reference_material(
    measurement_data: List[Dict],
    expected_modulus: float,
    expected_hardness: float,
) -> Dict[str, Any]
```

Reports mean, standard deviation, percentage deviation, and tolerance pass/fail fields.

### `assess_measurement_uncertainty(measurement_data)` [source](reference/calibration/nist_methods.md)

Calculates Type A uncertainty, coefficient of variation, and a precision label.

```python
nist.assess_measurement_uncertainty(
    measurement_data: List[Dict],
) -> Dict[str, Any]
```

Precision labels are based on modulus and hardness CV values.

## Continuous Stiffness Measurement

CSM helpers live in `src.analysis.csm_analyzer`.

### `CSMAnalyzer` [source](reference/analysis/csm_analyzer.md)

Processes CSM depth-profile data.

```python
CSMAnalyzer(
    area_function_coefficients: Optional[Dict[str, float]] = None,
    file_loader_name: str = "AgilentG200",
)
```

### `sheet_name(test_number)` [source](reference/analysis/csm_analyzer.md)

Formats a test number as an Agilent-style sheet name.

```python
CSMAnalyzer.sheet_name(test_number: int) -> str
```

Example:

```python
CSMAnalyzer.sheet_name(7)
# "Test 007"
```

### `parse_test_range(text)` [source](reference/analysis/csm_analyzer.md)

Parses a test selection string into unique positive test numbers.

```python
CSMAnalyzer.parse_test_range(text: str) -> List[int]
```

Example:

```python
CSMAnalyzer.parse_test_range("1-3, 7, 9")
# [1, 2, 3, 7, 9]
```

### `contact_area_nm2(contact_depth_nm)` [source](reference/analysis/csm_analyzer.md)

Calculates CSM contact area values from depth values.

```python
csm.contact_area_nm2(contact_depth_nm: numpy.ndarray) -> numpy.ndarray
```

### `read_tests(file_path, test_numbers, offsets_nm=None, recalculate=False)` [source](reference/analysis/csm_analyzer.md)

Reads selected CSM tests from a workbook.

```python
csm.read_tests(
    file_path: str,
    test_numbers: Sequence[int],
    offsets_nm: Optional[Dict[int, float]] = None,
    recalculate: bool = False,
) -> pandas.DataFrame
```

When `recalculate=True`, hardness and modulus are recalculated from load, harmonic contact stiffness, and the area function.

### `average_by_index(data)` [source](reference/analysis/csm_analyzer.md)

Averages repeated CSM profiles row by row.

```python
CSMAnalyzer.average_by_index(data: pandas.DataFrame) -> pandas.DataFrame
```

### `average_by_target_x_range(data, target_x_range)` [source](reference/analysis/csm_analyzer.md)

Interpolates each test to a shared depth grid before averaging.

```python
CSMAnalyzer.average_by_target_x_range(
    data: pandas.DataFrame,
    target_x_range: Tuple[float, float, float],
) -> pandas.DataFrame
```

`target_x_range` is:

```text
(start_nm, end_nm, step_nm)
```

### `compare_files_with_weighted_uncertainty(...)` [source](reference/analysis/csm_analyzer.md)

Compares multiple CSM files and combines means, standard deviations, and counts with weighted uncertainty handling.

Use this for side-by-side depth-profile comparison across multiple workbooks.

## Validation

Validation utilities live in `src.core.validators`.

### `DataValidator` [source](reference/core/validators.md)

Quality checks for raw and calculated nanoindentation data.

```python
DataValidator()
```

### `validate_data_completeness(df)` [source](reference/core/validators.md)

Checks required columns, data count, NaN values, load range, and displacement range.

```python
validator.validate_data_completeness(df: pandas.DataFrame) -> Dict[str, Any]
```

### `detect_noise_level(data)` [source](reference/core/validators.md)

Estimates relative noise from differenced data.

```python
validator.detect_noise_level(data: numpy.ndarray) -> Dict[str, float]
```

Returns a numeric noise level and a quality label.

### `check_monotonicity(x, y, phase="loading")` [source](reference/core/validators.md)

Checks whether loading or unloading data has too many monotonicity violations.

```python
validator.check_monotonicity(
    x: numpy.ndarray,
    y: numpy.ndarray,
    phase: str = "loading",
) -> Dict[str, Any]
```

### `validate_physical_properties(hardness, modulus)` [source](reference/core/validators.md)

Checks calculated hardness and modulus against configured physical limits.

```python
validator.validate_physical_properties(
    hardness: float,
    modulus: float,
) -> Dict[str, Any]
```

### `assess_curve_quality(load, displacement, r_squared, stiffness)` [source](reference/core/validators.md)

Combines fit quality, noise, and data completeness into a curve quality grade.

```python
validator.assess_curve_quality(
    load: numpy.ndarray,
    displacement: numpy.ndarray,
    r_squared: float,
    stiffness: float,
) -> Dict[str, Any]
```

### `HorizontalSegmentDetector` [source](reference/core/validators.md)

Detects and filters plateau-like regions in load-displacement curves.

```python
HorizontalSegmentDetector(config=None)
```

### `detect_horizontal_segments(displacement, load)` [source](reference/core/validators.md)

Returns index ranges for horizontal segments.

```python
detector.detect_horizontal_segments(
    displacement: numpy.ndarray,
    load: numpy.ndarray,
) -> List[Tuple[int, int]]
```

### `filter_horizontal_segments(displacement, load)` [source](reference/core/validators.md)

Removes detected horizontal segments and returns filtered arrays.

```python
detector.filter_horizontal_segments(
    displacement: numpy.ndarray,
    load: numpy.ndarray,
) -> Tuple[numpy.ndarray, numpy.ndarray]
```

### `create_comprehensive_validation_report(df, analysis_results)` [source](reference/core/validators.md)

Builds a full validation report for one test.

```python
create_comprehensive_validation_report(
    df: pandas.DataFrame,
    analysis_results: Dict,
) -> Dict[str, Any]
```

## Standards and Constants

Constants live in `src.core.standards`.

### `ISO14577Constants` [source](reference/core/standards.md)

Stores ISO/NIST-style constants used across the project, including data requirements, fit thresholds, tip geometry factors, fused-silica properties, diamond properties, and Berkovich area constants.

### `get_tip_geometry_config(tip_geometry)` [source](reference/core/standards.md)

Returns geometry-specific parameters.

```python
ISO14577Constants.get_tip_geometry_config(tip_geometry: str) -> dict
```

Known geometry keys include:

```text
berkovich
vickers
cube_corner
conical
spherical
```

### `get_reference_material(material_name)` [source](reference/core/standards.md)

Returns known reference material properties.

```python
ISO14577Constants.get_reference_material(material_name: str) -> dict
```

### `MaterialProperties` [source](reference/core/standards.md)

Common material-property lookup table.

```python
MaterialProperties.get_material("diamond")
MaterialProperties.list_materials()
```

### `AreaFunctionCoefficients` [source](reference/core/standards.md)

Default area-function coefficient dictionaries.

Available presets:

```text
PERFECT_BERKOVICH
BLUNT_BERKOVICH
```

### `AnalysisConfig` and `ValidationLimits` [source](reference/core/standards.md)

Configuration containers for thresholds used by processing, fitting, calibration, and validation.

Use these classes to trace constants such as minimum data points, \(R^2\) thresholds, segment lengths, and physical property bounds.
