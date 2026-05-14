# File Loaders

File loaders convert vendor-specific exports into the normalized data structure used by the full analysis pipeline.

Current production loader:

```text
src/fileloader/AgilentG200.py
```

Supported extensions:

```text
.xls
.xlsx
```

## Why this matters for researchers

If the loader misidentifies columns or units, every downstream quantity (stiffness, contact depth, hardness, modulus) can become unreliable. Always confirm that your source files match supported instrument/export expectations.

## Normalized column contract

All downstream analysis expects each test as a DataFrame with:

```text
Time (sec)
Load (mN)
Displacement (nm)
```

If time is absent in source data, the loader can synthesize a sequence index.

## Agilent G200 behavior

- Reads sheets named like `Test 001`, `Test 002`, etc.
- Detects vendor column variants for time/load/displacement.
- Removes non-numeric/invalid rows and duplicates.
- Returns metadata, warnings, and errors alongside normalized data.

## Output structure (conceptual)

```python
{
    "success": bool,
    "data": {"Test 001": pandas.DataFrame, ...},
    "metadata": {...},
    "errors": [...],
    "warnings": [...],
}
```

## Adding another instrument format

Create a loader module under `src/fileloader/` that:

1. Detects supported file extensions.
2. Reads source data layout.
3. Normalizes data to the required column contract and units.
4. Returns clear warnings/errors for skipped or failed sheets.

Then set default loader in:

```text
config/analysis_settings.ini
```

```ini
[loader]
default_file_loader = AgilentG200
```

Replace with your loader module name when needed.

## Validation checklist before analysis

- File is from a supported instrument/export path.
- Test sheets are detected correctly.
- Units map to mN and nm after normalization.
- No critical loader errors are present.

## Related pages

- [Installation](installation.md)
- [GUI Walkthrough](gui-walkthrough.md)
- [Analysis Configuration](analysis-configuration.md)

