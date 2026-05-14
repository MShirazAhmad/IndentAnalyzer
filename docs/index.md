# IndentAnalyzer Documentation

IndentAnalyzer is a Python application for nanoindentation analysis of Agilent Nano Indenter G200 Excel exports. It combines a PyQt GUI, a normalized file-loader interface, preprocessing and validation tools, Oliver-Pharr unloading fits, NIST-style calibration helpers, and ISO 14577-aligned hardness and modulus calculations.

The documentation is built for Read the Docs with MkDocs Material. It contains both extended user-facing explanations and an auto-generated code reference for every Python module under `src/`.

## What the Software Does

IndentAnalyzer turns raw load-displacement spreadsheets into per-indent and summary mechanical properties:

- reads Agilent G200 `.xls` and `.xlsx` exports,
- normalizes each `Test ###` sheet to time, load, and displacement columns,
- separates loading and unloading portions of each indentation curve,
- removes or reports horizontal/plateau-like curve segments,
- fits unloading curves with Oliver-Pharr or normalized power-law models,
- calculates stiffness, contact depth, projected contact area, hardness, reduced modulus, and sample modulus,
- calibrates tip-area coefficients from fused-silica reference data,
- processes CSM depth profiles and averages hardness/modulus versus depth,
- exposes results through the GUI, batch workflows, and Python classes.

## Documentation Map

- **Installation** explains the local environment, GUI launch command, and documentation build command.
- **Features** gives the full feature set from a user and developer point of view.
- **Code Workflow** follows data through the working code from file load to final result.
- **Calculations** documents the mathematical equations, unit conversions, thresholds, and quality calculations used in the implementation.
- **Module Guide** explains each `src/**/*.py` file and points to the generated source reference.
- **Function Reference** documents the important classes and functions in a Django-style reference format.
- **Code Reference** is generated during the MkDocs build from the source tree, with source code visible on each module page.
- **Read the Docs Setup** explains how publishing works from GitHub to Read the Docs.

## Repository Links

- Repository: <https://github.com/MShirazAhmad/IndentAnalyzer>
- README usage guide: <https://github.com/MShirazAhmad/IndentAnalyzer/blob/main/README.md>
