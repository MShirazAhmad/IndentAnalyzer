"""
Agilent G200 nanoindentation file loader.

Loader contract for future instruments:
- ALLOWED_EXTENSIONS declares file suffixes accepted by the loader.
- get_sheet_names(file_path) returns available sources/sheets.
- load_sheet(file_path, sheet_name) returns (raw_dataframe, units_by_column).
- load_file(file_path) returns the normalized analyzer structure:
    {
        "success": bool,
        "data": {
            "Test 001": DataFrame[
                "Time (sec)", "Load (mN)", "Displacement (nm)"
            ],
            ...
        },
        "metadata": {...},
        "errors": [str, ...],
        "warnings": [str, ...],
    }

New loader modules should reformulate vendor-specific files into the same
normalized load_file output so the rest of the software can process them.
"""

from pathlib import Path
from typing import Dict, Tuple, Union

import numpy as np
import pandas as pd


LOADER_NAME = "AgilentG200"
ALLOWED_EXTENSIONS = [".xls", ".xlsx"]
OUTPUT_STRUCTURE = {
    "success": "bool",
    "data": {
        "<sheet/test name>": [
            "Time (sec)",
            "Load (mN)",
            "Displacement (nm)",
        ]
    },
    "metadata": {
        "file_path": "str",
        "file_size_bytes": "int",
        "file_extension": "str",
        "sheet_names": "list[str]",
        "total_sheets": "int",
        "processed_sheets": "int",
        "loader": LOADER_NAME,
    },
    "errors": "list[str]",
    "warnings": "list[str]",
}


def supports_file(file_path: Union[str, Path]) -> bool:
    return Path(file_path).suffix.lower() in ALLOWED_EXTENSIONS


def get_sheet_names(file_path: Union[str, Path]) -> list[str]:
    excel_file = pd.ExcelFile(file_path)
    return list(excel_file.sheet_names)


def load_sheet(file_path: Union[str, Path], sheet_name=0) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """Return raw vendor columns and detected unit row for GUI/Expert Mode."""
    raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
    if raw.empty:
        return pd.DataFrame(), {}

    headers = [
        str(value).strip() if pd.notna(value) else f"Column {idx + 1}"
        for idx, value in enumerate(raw.iloc[0])
    ]
    units: Dict[str, str] = {}
    data_start = 1

    if len(raw) > 1:
        unit_row = raw.iloc[1]
        non_empty_units = 0
        for header, unit_value in zip(headers, unit_row):
            if pd.isna(unit_value):
                continue
            unit_text = str(unit_value).strip()
            if unit_text and not _looks_numeric(unit_text):
                units[header] = unit_text
                non_empty_units += 1
        if non_empty_units:
            data_start = 2

    df = raw.iloc[data_start:].copy()
    df.columns = headers
    df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")
    return df.reset_index(drop=True), units


def load_file(file_path: Union[str, Path]) -> Dict[str, object]:
    """Load Agilent G200 XLS/XLSX data into the analyzer-normalized structure."""
    result = {
        "success": False,
        "data": {},
        "metadata": {},
        "errors": [],
        "warnings": [],
    }
    file_path = Path(file_path)
    result["metadata"].update({
        "file_path": str(file_path),
        "file_size_bytes": file_path.stat().st_size if file_path.exists() else 0,
        "file_extension": file_path.suffix,
        "loader": LOADER_NAME,
        "allowed_extensions": ALLOWED_EXTENSIONS,
        "output_structure": OUTPUT_STRUCTURE,
    })

    if not file_path.exists():
        result["errors"].append(f"File not found: {file_path}")
        return result
    if not supports_file(file_path):
        result["errors"].append(f"Unsupported file format for {LOADER_NAME}: {file_path.suffix}")
        return result

    try:
        sheet_names = get_sheet_names(file_path)
        result["metadata"]["sheet_names"] = sheet_names
        result["metadata"]["total_sheets"] = len(sheet_names)

        processed = {}
        for sheet_name in sheet_names:
            if not _is_test_sheet_name(sheet_name):
                continue
            try:
                raw_df, _units = load_sheet(file_path, sheet_name)
                normalized = normalize_sheet(raw_df)
                if normalized is None or normalized.empty:
                    result["warnings"].append(f"Sheet '{sheet_name}': no load/displacement data found")
                    continue
                processed[sheet_name] = normalized
            except Exception as exc:
                result["warnings"].append(f"Sheet '{sheet_name}': {exc}")

        if processed:
            result["data"] = processed
            result["success"] = True
            result["metadata"]["processed_sheets"] = len(processed)
        else:
            result["errors"].append("No valid data found in any sheet")
    except Exception as exc:
        result["errors"].append(f"Failed to read Agilent G200 file: {exc}")

    return result


def normalize_sheet(df: pd.DataFrame) -> pd.DataFrame:
    """Extract Time/Load/Displacement columns from an Agilent sheet."""
    if df.empty:
        return pd.DataFrame()

    mapping = _detect_columns(df)
    if not mapping or "load" not in mapping or "displacement" not in mapping:
        return pd.DataFrame()

    out = pd.DataFrame()
    if "time" in mapping:
        out["Time (sec)"] = pd.to_numeric(df[mapping["time"]], errors="coerce")
    else:
        out["Time (sec)"] = np.arange(len(df), dtype=float)
    out["Load (mN)"] = pd.to_numeric(df[mapping["load"]], errors="coerce")
    out["Displacement (nm)"] = pd.to_numeric(df[mapping["displacement"]], errors="coerce")
    out = out.replace([np.inf, -np.inf], np.nan).dropna()
    out = out.drop_duplicates().reset_index(drop=True)
    return out


def _detect_columns(df: pd.DataFrame) -> Dict[str, str]:
    patterns = {
        "time": ["time on sample", "time", "sec", "second"],
        "load": ["load on sample", "load", "force", "mn"],
        "displacement": ["displacement into surface", "displacement", "depth", "nm"],
    }
    mapping: Dict[str, str] = {}
    columns = list(df.columns)
    lowered = [(column, str(column).lower()) for column in columns]
    for key, candidates in patterns.items():
        best_column = None
        best_score = 0
        for column, lower in lowered:
            score = sum(len(candidate) for candidate in candidates if candidate in lower)
            if score > best_score:
                best_column = column
                best_score = score
        if best_column is not None:
            mapping[key] = best_column
    return mapping


def _is_test_sheet_name(sheet_name: str) -> bool:
    parts = str(sheet_name).split()
    return len(parts) >= 2 and parts[0].lower() == "test" and parts[1].isdigit()


def _looks_numeric(text: str) -> bool:
    try:
        float(text)
    except (TypeError, ValueError):
        return False
    return True
