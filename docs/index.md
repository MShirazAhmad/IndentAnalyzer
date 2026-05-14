# IndentAnalyzer Documentation

IndentAnalyzer is a nanoindentation analysis toolkit for **Agilent Nano Indenter G200** Excel exports. This documentation is written for material scientists who need to move from raw load-displacement curves to defensible hardness/modulus results.

## Start Here (Recommended Reading Order)

1. [Installation](installation.md) — set up environment and launch GUI.
2. [GUI Walkthrough](gui-walkthrough.md) — run the standard 5-step workflow with screenshots.
3. [Mathematical Calculations](calculations.md) — verify equations, units, and assumptions.
4. [Analysis Configuration](analysis-configuration.md) — tune thresholds and defaults.
5. [Features](features.md) — full capability map including CSM and expert review.

## What Input Data Is Expected

- Agilent G200 `.xls` or `.xlsx` files.
- Test sheets named like `Test 001`, `Test 002`, etc.
- Curves with load and displacement series that can be split into loading/unloading segments.

For loader details and extension strategy, see [File Loaders](file-loaders.md).

## What You Get as Output

- Per-test fit quality and quality flags.
- Contact stiffness, contact depth, contact area.
- Hardness (
\(H\)) and reduced modulus (\(E_r\)).
- Sample elastic modulus (\(E_s\)) from the indenter/sample compliance relation.
- Summary statistics with optional exclusion of questionable tests.

## Scientific Caution

Good-looking summary numbers can still hide poor individual fits. Always pair numerical filters (for example minimum \(R^2\)) with visual inspection in **Curve Viewer** and clear exclusion rationale.

## Documentation Map

- [Installation](installation.md)
- [GUI Walkthrough](gui-walkthrough.md)
- [Features](features.md)
- [File Loaders](file-loaders.md)
- [Analysis Configuration](analysis-configuration.md)
- [Code Workflow](code-workflow.md)
- [Mathematical Calculations](calculations.md)
- [Module Guide](modules.md)
- [Function Reference](function-reference.md)
- [Publishing](readthedocs.md)
- [Code Reference](reference/index.md)
- [License](license.md)

