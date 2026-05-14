# Code Workflow

This page follows the working code path from a spreadsheet on disk to final hardness and modulus values.

## 1. File Selection

The GUI or a Python caller passes a file path to `NanoindentationAnalyzer.analyze_file`.

```python
from src.analysis.main_analyzer import NanoindentationAnalyzer

analyzer = NanoindentationAnalyzer(sample_poisson=0.30)
results = analyzer.analyze_file("samples/HEC12_2_03132025.xls")
```

`NanoindentationAnalyzer` creates the core collaborators:

- `ExcelDataLoader` for file loading,
- `DataProcessor` for preprocessing and phase splitting,
- `DataValidator` for quality checks,
- `CurveFitter` for unloading fits,
- `NISTCalibrationMethods` for calibration helper workflows,
- `MechanicalPropertiesCalculator` for hardness and modulus.

## 2. Loader Dispatch

`ExcelDataLoader.load_excel_file` dispatches to the selected file-loader module. By default this is:

```text
src/fileloader/AgilentG200.py
```

The loader checks file existence and extension, reads workbook sheet names, and processes only sheets that look like Agilent test sheets:

```text
Test 001
Test 002
Test 003
```

Each sheet is normalized to the standard analyzer columns:

```text
Time (sec)
Load (mN)
Displacement (nm)
```

The return structure is:

```python
{
    "success": bool,
    "data": {"Test 001": dataframe, "...": dataframe},
    "metadata": {...},
    "errors": [...],
    "warnings": [...],
}
```

## 3. Per-Test Processing

For every loaded sheet, `NanoindentationAnalyzer.analyze_single_test` calls:

```python
DataProcessor.process_test_data(dataframe, test_name)
```

This step:

- verifies required load and displacement columns,
- filters low-load points,
- finds the maximum load index,
- splits the curve into loading and unloading phases,
- checks whether those phases have enough points and the expected trend,
- detects horizontal segments,
- prepares filtered unloading data for fitting.

The main output used by the next step is:

```python
processing_result["phases"]["unloading"]["filtered_data"]
```

## 4. Unloading Fit

The default fitting method is `oliver_pharr`:

```python
CurveFitter.fit_unloading_curve(displacement, load, method="oliver_pharr")
```

The fitted unloading curve is:

\[
P(h)=A(h-h_f)^m
\]

The fit returns:

- fitted parameters,
- \(R^2\) for the fit segment,
- full-curve \(R^2\),
- fitted display curve,
- residuals,
- tangent line coordinates,
- contact stiffness,
- contact depth.

If the caller selects `auto`, the analyzer runs Oliver-Pharr, normalized power law, and linear stiffness options, then chooses the successful method with the highest \(R^2\).

## 5. Contact Area

The curve fit supplies contact depth:

\[
h_c = h_{\max} - \epsilon\frac{P_{\max}}{S}
\]

`AreaFunction.calculate_contact_area` converts contact depth into projected contact area:

\[
A(h_c)=C_0h_c^2+C_1h_c+C_2h_c^{1/2}+\cdots+C_8h_c^{1/128}
\]

Without user calibration, the default coefficients represent an ideal Berkovich tip:

```python
{"C0": 24.56, "C1": 0.0, "C2": 0.0, "...": 0.0}
```

## 6. Mechanical Property Calculation

`MechanicalPropertiesCalculator.calculate_all_properties` runs the full property stack:

```python
properties = calculator.calculate_all_properties(
    max_load=max_load,
    contact_depth=contact_depth,
    stiffness=stiffness,
    sample_poisson=0.30,
    indenter_material="diamond",
)
```

It calculates:

- contact area,
- hardness,
- reduced modulus,
- sample elastic modulus,
- derived property estimates.

The main equations are:

\[
H=\frac{P_{\max}}{A_c}
\]

\[
E_r=\frac{\sqrt{\pi}}{2\beta}\frac{S}{\sqrt{A_c}}
\]

\[
E_s=\frac{1-\nu_s^2}{\frac{1}{E_r}-\frac{1-\nu_i^2}{E_i}}
\]

## 7. Validation and Quality Assessment

The analyzer builds a validation summary with:

```python
create_comprehensive_validation_report(data, analysis_summary)
```

The validator checks:

- required columns and data completeness,
- load and displacement ranges,
- noise level,
- fit \(R^2\),
- physical limits for hardness and modulus,
- \(H/E\) reasonableness.

`NanoindentationAnalyzer._assess_overall_quality` then summarizes the result for the caller and GUI.

## 8. File and Batch Summaries

After every sheet is analyzed, `analyze_file` reports:

```python
{
    "total_tests": int,
    "successful_tests": int,
    "success_rate": float,
    "file_metadata": {...},
}
```

`analyze_directory` applies the same process to every matching Excel file in a directory and then calculates cross-test statistics for hardness, modulus, stiffness, contact depth, and fit quality.

## 9. Calibration Workflow

Tip calibration is handled by `NISTCalibrationMethods.extract_tip_coefficients_from_file`. The calibration path is:

1. Analyze the fused-silica workbook with `NanoindentationAnalyzer`.
2. Keep tests with successful unloading fits.
3. Convert contact depth from nm to m.
4. Convert stiffness from mN/nm to N/m.
5. Calculate the reference reduced modulus from fused silica and diamond constants.
6. Convert stiffness and reduced modulus into projected area.
7. Fit area-function coefficients.
8. Return coefficients in both SI and nm-friendly display units.

These coefficients can then be passed into:

```python
NanoindentationAnalyzer(area_function_coefficients=coefficients)
```

## 10. GUI Integration

`src/gui/main_interface.py` wraps these workflows in the Nanoindentation Analysis Suite. The GUI keeps state for calibration coefficients, loaded sample files, analysis settings, selected/excluded tests, plots, and exported summaries. The numerical work still flows through the same loader, analyzer, calibration, fitting, and calculator modules described above.
