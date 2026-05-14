# API reference

This page documents stable analysis and standards surfaces that are safe to reference from automation or downstream tooling.

## Analysis API

```{eval-rst}
.. automodule:: src.analysis.main_analyzer
   :members: NanoindentationAnalyzer, analyze_nanoindentation_file
   :undoc-members:
   :member-order: bysource
```

## Standards and configuration API

```{eval-rst}
.. automodule:: src.core.standards
   :members: ISO14577Constants, AnalysisConfig, MaterialProperties, AreaFunctionCoefficients, ValidationLimits
   :undoc-members:
   :member-order: bysource
```

## Calibration API

```{eval-rst}
.. automodule:: src.calibration.nist_methods
   :members: NISTCalibrationMethods
   :undoc-members:
   :member-order: bysource
```

## GUI surface

The GUI entry points are documented descriptively rather than through autodoc because the GUI module imports heavyweight UI dependencies and runtime display integrations.

Stable GUI-facing surfaces to know about:

- `src.gui.main_interface.NanoindentationGUI`
- `src.gui.main_interface.AnalysisWorker`
- `src.gui.main_interface.main`

## Known incomplete backend hooks

`src.analysis.main_analyzer.NanoindentationAnalyzer` currently contains placeholder backend export helpers for Excel and CSV export. The active user-facing export path is implemented in the GUI layer, where included results are exported with pandas from the current session.
