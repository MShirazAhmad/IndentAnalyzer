# File Loaders

File loaders are the boundary between vendor-specific raw files and the rest of IndentAnalyzer. The analyzer, curve fitting, calibration, GUI, and batch tools should not need to know whether a file came from an Agilent G200 workbook or a future instrument export. A loader translates the vendor format into one normalized structure.

The current loader is:

```text
src/fileloader/AgilentG200.py
```

It supports:

```text
.xls
.xlsx
```

## Purpose

Nanoindentation instruments export different column names, sheet names, units, metadata rows, and file layouts. The file-loader layer solves that problem by doing three jobs:

1. Identify whether a loader supports a file.
2. Read the vendor-specific file layout.
3. Return the normalized analyzer structure expected by `ExcelDataLoader`, `DataProcessor`, and `NanoindentationAnalyzer`.

After the loader succeeds, all downstream modules expect each indentation test as a `pandas.DataFrame` with these columns:

```text
Time (sec)
Load (mN)
Displacement (nm)
```

That normalized column contract is the most important rule when adding support for another file format.

## Current Agilent G200 Loader

The Agilent loader processes Excel sheets named like:

```text
Test 001
Test 002
Test 003
```

It detects vendor columns using text patterns:

| Normalized field | Typical vendor text |
| --- | --- |
| `Time (sec)` | `time on sample`, `time`, `sec`, `second` |
| `Load (mN)` | `load on sample`, `load`, `force`, `mN` |
| `Displacement (nm)` | `displacement into surface`, `displacement`, `depth`, `nm` |

If no time column is found, the loader creates a numeric sequence:

```python
0, 1, 2, ...
```

The loader removes invalid numeric rows, infinite values, and duplicate rows before returning the normalized DataFrame.

## Required Loader Contract

To support another file format, create a new Python file under:

```text
src/fileloader/
```

For example:

```text
src/fileloader/MyInstrument.py
```

The loader should define these module-level values and functions.

### `LOADER_NAME`

Human-readable loader name.

```python
LOADER_NAME = "MyInstrument"
```

### `ALLOWED_EXTENSIONS`

List of file suffixes accepted by the loader.

```python
ALLOWED_EXTENSIONS = [".csv", ".txt"]
```

### `OUTPUT_STRUCTURE`

Documentation dictionary describing the shape returned by `load_file`.

```python
OUTPUT_STRUCTURE = {
    "success": "bool",
    "data": {
        "<test name>": [
            "Time (sec)",
            "Load (mN)",
            "Displacement (nm)",
        ]
    },
    "metadata": {
        "file_path": "str",
        "file_size_bytes": "int",
        "file_extension": "str",
        "loader": LOADER_NAME,
    },
    "errors": "list[str]",
    "warnings": "list[str]",
}
```

### `supports_file(file_path)`

Returns `True` when the loader accepts the file.

```python
def supports_file(file_path):
    return Path(file_path).suffix.lower() in ALLOWED_EXTENSIONS
```

### `get_sheet_names(file_path)`

Returns available data sources inside the file.

For Excel files, these are sheet names. For CSV or text files, return a synthetic list such as:

```python
["Test 001"]
```

### `load_sheet(file_path, sheet_name=0)`

Returns raw vendor data and a unit dictionary:

```python
raw_dataframe, units_by_column = load_sheet(file_path, sheet_name)
```

This function is useful for GUI preview, expert inspection, and debugging. It does not have to normalize columns, but it should preserve enough raw information to see what was loaded.

### `load_file(file_path)`

Returns the final normalized analyzer structure. This is the function used by the main loader wrapper.

```python
{
    "success": bool,
    "data": {
        "Test 001": pandas.DataFrame,
        "Test 002": pandas.DataFrame,
    },
    "metadata": {...},
    "errors": [...],
    "warnings": [...],
}
```

Every DataFrame in `data` must contain:

```text
Time (sec)
Load (mN)
Displacement (nm)
```

## Output Structure

The normalized return object should always use the same top-level keys.

### `success`

Boolean status for the whole file.

Use `True` only when at least one valid test was loaded:

```python
"success": True
```

Use `False` when no valid tests were loaded:

```python
"success": False
```

### `data`

Dictionary mapping test names to normalized DataFrames:

```python
"data": {
    "Test 001": df_test_001,
    "Test 002": df_test_002,
}
```

Each DataFrame should use these exact column names and units:

| Column | Unit | Required |
| --- | --- | --- |
| `Time (sec)` | seconds | Yes, can be generated if absent |
| `Load (mN)` | millinewtons | Yes |
| `Displacement (nm)` | nanometres | Yes |

!!! note
    Convert units inside the loader. If a vendor export stores load in newtons or displacement in micrometres, convert them before returning the normalized DataFrame.

### `metadata`

Dictionary with file and loader details:

```python
"metadata": {
    "file_path": str(file_path),
    "file_size_bytes": file_path.stat().st_size,
    "file_extension": file_path.suffix,
    "loader": LOADER_NAME,
    "allowed_extensions": ALLOWED_EXTENSIONS,
    "sheet_names": sheet_names,
    "total_sheets": len(sheet_names),
    "processed_sheets": len(processed),
}
```

You can add vendor-specific metadata, but keep the common fields because the GUI and docs use them for traceability.

### `errors`

List of fatal problems that prevent useful loading:

```python
"errors": [
    "File not found: example.csv",
    "No valid data found in any sheet",
]
```

If `success` is `False`, this list should explain why.

### `warnings`

List of non-fatal problems:

```python
"warnings": [
    "Sheet 'Summary': skipped because it is not a test sheet",
    "Sheet 'Test 004': no load/displacement data found",
]
```

Use warnings when the file can still be analyzed.

## Loader Skeleton

Use this as a starting point for a new file format.

```python
from pathlib import Path
from typing import Dict, Tuple, Union

import numpy as np
import pandas as pd


LOADER_NAME = "MyInstrument"
ALLOWED_EXTENSIONS = [".csv"]


def supports_file(file_path: Union[str, Path]) -> bool:
    return Path(file_path).suffix.lower() in ALLOWED_EXTENSIONS


def get_sheet_names(file_path: Union[str, Path]) -> list[str]:
    return ["Test 001"]


def load_sheet(file_path: Union[str, Path], sheet_name=0) -> Tuple[pd.DataFrame, Dict[str, str]]:
    raw = pd.read_csv(file_path)
    units = {
        "time": "s",
        "load": "mN",
        "depth": "nm",
    }
    return raw, units


def normalize_sheet(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["Time (sec)"] = pd.to_numeric(df["time"], errors="coerce")
    out["Load (mN)"] = pd.to_numeric(df["load"], errors="coerce")
    out["Displacement (nm)"] = pd.to_numeric(df["depth"], errors="coerce")
    out = out.replace([np.inf, -np.inf], np.nan).dropna()
    return out.reset_index(drop=True)


def load_file(file_path: Union[str, Path]) -> Dict[str, object]:
    file_path = Path(file_path)
    result = {
        "success": False,
        "data": {},
        "metadata": {
            "file_path": str(file_path),
            "file_size_bytes": file_path.stat().st_size if file_path.exists() else 0,
            "file_extension": file_path.suffix,
            "loader": LOADER_NAME,
            "allowed_extensions": ALLOWED_EXTENSIONS,
        },
        "errors": [],
        "warnings": [],
    }

    if not file_path.exists():
        result["errors"].append(f"File not found: {file_path}")
        return result
    if not supports_file(file_path):
        result["errors"].append(f"Unsupported file format: {file_path.suffix}")
        return result

    try:
        raw, units = load_sheet(file_path)
        normalized = normalize_sheet(raw)
        if normalized.empty:
            result["errors"].append("No valid load/displacement rows found")
            return result
        result["data"] = {"Test 001": normalized}
        result["metadata"]["processed_sheets"] = 1
        result["success"] = True
    except Exception as exc:
        result["errors"].append(f"Failed to load file: {exc}")

    return result
```

## Selecting a New Loader

`ExcelDataLoader` loads a module by name from `src/fileloader/`.

```python
from src.core.data_processor import ExcelDataLoader

loader = ExcelDataLoader()
loader.set_loader("MyInstrument")
loaded = loader.load_excel_file("example.csv")
```

The GUI default loader is configured in:

```text
config/analysis_settings.ini
```

```ini
[loader]
default_file_loader = AgilentG200
```

To use a new loader by default, change `default_file_loader` to the module name without `.py`:

```ini
[loader]
default_file_loader = MyInstrument
```

## Checklist for New File Formats

- Create `src/fileloader/<LoaderName>.py`.
- Define `LOADER_NAME` and `ALLOWED_EXTENSIONS`.
- Implement `supports_file`, `get_sheet_names`, `load_sheet`, and `load_file`.
- Normalize all test data to `Time (sec)`, `Load (mN)`, and `Displacement (nm)`.
- Convert units inside the loader.
- Return warnings for skipped sheets or partial data.
- Return errors when no analyzable test remains.
- Test the loader with `ExcelDataLoader.set_loader("<LoaderName>")`.
- Add the loader name to project documentation if it becomes officially supported.
