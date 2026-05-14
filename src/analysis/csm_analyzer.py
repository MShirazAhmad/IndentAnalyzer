#!/usr/bin/env python3
"""
Continuous stiffness measurement (CSM) helpers.

The first implementation mirrors the notebook workflow:
- collect loading-curve depth offsets from Test ### sheets,
- combine depth-profile columns across tests,
- average exported hardness/modulus versus depth,
- optionally recalculate hardness/modulus from load + CSM stiffness + area function.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import importlib.util

import numpy as np
import pandas as pd


DEFAULT_CSM_COLUMNS = [
    "Segment",
    "Depth (nm)",
    "Load On Sample (mN)",
    "Time On Sample (s)",
    "Harmonic Contact Stiffness (N/m)",
    "Hardness (GPa)",
    "Modulus (GPa)",
]


class CSMAnalyzer:
    """Notebook-derived CSM data processing and averaging."""

    def __init__(
        self,
        area_function_coefficients: Optional[Dict[str, float]] = None,
        file_loader_name: str = "AgilentG200",
    ):
        self.area_function_coefficients = area_function_coefficients or {"C0": 24.56}
        self.file_loader_name = file_loader_name or "AgilentG200"

    @staticmethod
    def sheet_name(test_number: int) -> str:
        return f"Test {test_number:03d}"

    @staticmethod
    def parse_test_range(text: str) -> List[int]:
        tests: List[int] = []
        for part in str(text).replace(" ", "").split(","):
            if not part:
                continue
            if "-" in part:
                start, end = part.split("-", 1)
                tests.extend(range(int(start), int(end) + 1))
            else:
                tests.append(int(part))
        return sorted(set(t for t in tests if t > 0))

    def _load_file_loader(self):
        loader_path = Path(__file__).resolve().parent.parent / "fileloader" / f"{self.file_loader_name}.py"
        if not loader_path.exists():
            return None
        spec = importlib.util.spec_from_file_location(f"csm_fileloader_{self.file_loader_name}", loader_path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _read_sheet(self, file_path: str, test_number: int) -> pd.DataFrame:
        sheet = CSMAnalyzer.sheet_name(test_number)
        loader = self._load_file_loader()
        if loader is not None and hasattr(loader, "get_sheet_names") and hasattr(loader, "load_sheet"):
            sheet_names = loader.get_sheet_names(file_path)
            if sheet not in sheet_names:
                matches = [name for name in sheet_names if str(name).startswith(sheet)]
                if not matches:
                    raise ValueError(f"Sheet '{sheet}' was not found.")
                sheet = matches[0]
            df, _units = loader.load_sheet(file_path, sheet)
        else:
            xls = pd.ExcelFile(file_path)
            if sheet not in xls.sheet_names:
                matches = [name for name in xls.sheet_names if str(name).startswith(sheet)]
                if not matches:
                    raise ValueError(f"Sheet '{sheet}' was not found.")
                sheet = matches[0]
            df = pd.read_excel(xls, sheet_name=sheet, dtype=str)
        if len(df.columns) >= len(DEFAULT_CSM_COLUMNS):
            df = df.iloc[:, : len(DEFAULT_CSM_COLUMNS)].copy()
            df.columns = DEFAULT_CSM_COLUMNS
        return df

    @staticmethod
    def _first_matching_column(df: pd.DataFrame, patterns: Iterable[str]) -> Optional[str]:
        lowered = [(col, str(col).lower()) for col in df.columns]
        for pattern in patterns:
            pattern_l = str(pattern).lower()
            for original, lower in lowered:
                if pattern_l in lower:
                    return original
        return None

    def contact_area_nm2(self, contact_depth_nm: np.ndarray) -> np.ndarray:
        depth = np.asarray(contact_depth_nm, dtype=float)
        area = np.full_like(depth, np.nan, dtype=float)
        valid = np.isfinite(depth) & (depth > 0)
        if not np.any(valid):
            return area
        depth_valid = depth[valid]
        area_valid = np.zeros_like(depth_valid, dtype=float)
        for idx in range(9):
            coeff = float(self.area_function_coefficients.get(f"C{idx}", 0.0))
            if idx == 0:
                term = depth_valid**2
            elif idx == 1:
                term = depth_valid
            else:
                term = depth_valid ** (1.0 / (2 ** (idx - 1)))
            area_valid += coeff * term
        area[valid] = area_valid
        return area

    def read_tests(
        self,
        file_path: str,
        test_numbers: Sequence[int],
        offsets_nm: Optional[Dict[int, float]] = None,
        recalculate: bool = False,
    ) -> pd.DataFrame:
        frames: List[pd.DataFrame] = []
        offsets_nm = offsets_nm or {}
        for test_number in test_numbers:
            raw = self._read_sheet(file_path, test_number)
            depth_col = self._first_matching_column(raw, ["Displacement Into Surface", "Depth (nm)", "Depth"])
            load_col = self._first_matching_column(raw, ["Load On Sample", "Load"])
            stiffness_col = self._first_matching_column(raw, ["Harmonic Contact Stiffness", "Stiffness"])
            hardness_col = self._first_matching_column(raw, ["Hardness (GPa)", "Hardness"])
            modulus_col = self._first_matching_column(raw, ["Modulus (GPa)", "Modulus"])
            if not depth_col:
                continue

            depth = pd.to_numeric(raw[depth_col], errors="coerce") - float(offsets_nm.get(test_number, 0.0))
            out = pd.DataFrame({"Depth (nm)": depth, "Test": test_number})

            if recalculate:
                if not load_col or not stiffness_col:
                    continue
                load_mn = pd.to_numeric(raw[load_col], errors="coerce")
                stiffness_n_m = pd.to_numeric(raw[stiffness_col], errors="coerce")
                area_nm2 = self.contact_area_nm2(depth.to_numpy())
                area_m2 = area_nm2 * 1e-18
                load_n = load_mn.to_numpy(dtype=float) * 1e-3
                stiffness = stiffness_n_m.to_numpy(dtype=float)
                valid_recalc = (
                    np.isfinite(depth.to_numpy(dtype=float))
                    & np.isfinite(load_n)
                    & np.isfinite(stiffness)
                    & np.isfinite(area_m2)
                    & (area_m2 > 0)
                    & (stiffness > 0)
                )
                with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
                    hardness = np.full_like(load_n, np.nan, dtype=float)
                    modulus = np.full_like(load_n, np.nan, dtype=float)
                    hardness[valid_recalc] = (load_n[valid_recalc] / area_m2[valid_recalc]) * 1e-9
                    beta = 1.034
                    modulus[valid_recalc] = (
                        (np.sqrt(np.pi) / (2 * beta))
                        * stiffness[valid_recalc]
                        / np.sqrt(area_m2[valid_recalc])
                    ) * 1e-9
                    out["Hardness (GPa)"] = hardness
                    out["Modulus (GPa)"] = modulus
            else:
                if hardness_col:
                    out["Hardness (GPa)"] = pd.to_numeric(raw[hardness_col], errors="coerce")
                if modulus_col:
                    out["Modulus (GPa)"] = pd.to_numeric(raw[modulus_col], errors="coerce")
                if load_col:
                    out["Load On Sample (mN)"] = pd.to_numeric(raw[load_col], errors="coerce")
                if stiffness_col:
                    out["Harmonic Contact Stiffness (N/m)"] = pd.to_numeric(raw[stiffness_col], errors="coerce")

            out = out.replace([np.inf, -np.inf], np.nan).dropna(subset=["Depth (nm)"])
            for property_col in ("Hardness (GPa)", "Modulus (GPa)"):
                if property_col in out:
                    out.loc[out[property_col].abs() > 1e6, property_col] = np.nan
            frames.append(out)
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    @staticmethod
    def average_by_index(data: pd.DataFrame) -> pd.DataFrame:
        """Average tests row-wise, matching the notebook's depth-profile approach."""
        if data.empty:
            return pd.DataFrame()
        working = data.copy()
        working["Point"] = working.groupby("Test").cumcount()
        grouped = working.groupby("Point", sort=True)
        result = pd.DataFrame({
            "Depth (nm)": grouped["Depth (nm)"].mean(),
            "Hardness Mean (GPa)": grouped["Hardness (GPa)"].mean() if "Hardness (GPa)" in working else np.nan,
            "Hardness SD (GPa)": grouped["Hardness (GPa)"].std(ddof=1) if "Hardness (GPa)" in working else np.nan,
            "Hardness Count": grouped["Hardness (GPa)"].count() if "Hardness (GPa)" in working else 0,
            "Modulus Mean (GPa)": grouped["Modulus (GPa)"].mean() if "Modulus (GPa)" in working else np.nan,
            "Modulus SD (GPa)": grouped["Modulus (GPa)"].std(ddof=1) if "Modulus (GPa)" in working else np.nan,
            "Modulus Count": grouped["Modulus (GPa)"].count() if "Modulus (GPa)" in working else 0,
        })
        return result.reset_index(drop=True).replace([np.inf, -np.inf], np.nan)

    @staticmethod
    def average_by_target_x_range(
        data: pd.DataFrame,
        target_x_range: Tuple[float, float, float],
    ) -> pd.DataFrame:
        """Average properties on a shared depth grid (start, end, step in nm)."""
        if data.empty:
            return pd.DataFrame()

        start_nm, end_nm, step_nm = [float(v) for v in target_x_range]
        if step_nm <= 0:
            raise ValueError("target_x_range step must be > 0.")
        if end_nm < start_nm:
            raise ValueError("target_x_range end must be >= start.")

        depth_grid = np.arange(start_nm, end_nm + 0.5 * step_nm, step_nm, dtype=float)
        if depth_grid.size == 0:
            return pd.DataFrame()

        hardness_rows: List[np.ndarray] = []
        modulus_rows: List[np.ndarray] = []

        for test_number, group in data.groupby("Test"):
            depth = pd.to_numeric(group["Depth (nm)"], errors="coerce").to_numpy(dtype=float)
            finite_depth = np.isfinite(depth)
            if not np.any(finite_depth):
                continue
            depth = depth[finite_depth]
            order = np.argsort(depth)
            depth = depth[order]
            if depth.size < 2:
                continue
            unique_depth, unique_indices = np.unique(depth, return_index=True)
            if unique_depth.size < 2:
                continue

            if "Hardness (GPa)" in group:
                hardness = pd.to_numeric(group["Hardness (GPa)"], errors="coerce").to_numpy(dtype=float)[finite_depth][order]
                hardness = hardness[unique_indices]
                valid = np.isfinite(hardness)
                if np.count_nonzero(valid) >= 2:
                    hardness_interp = np.interp(depth_grid, unique_depth[valid], hardness[valid], left=np.nan, right=np.nan)
                    outside = (depth_grid < np.nanmin(unique_depth[valid])) | (depth_grid > np.nanmax(unique_depth[valid]))
                    hardness_interp[outside] = np.nan
                    hardness_rows.append(hardness_interp)

            if "Modulus (GPa)" in group:
                modulus = pd.to_numeric(group["Modulus (GPa)"], errors="coerce").to_numpy(dtype=float)[finite_depth][order]
                modulus = modulus[unique_indices]
                valid = np.isfinite(modulus)
                if np.count_nonzero(valid) >= 2:
                    modulus_interp = np.interp(depth_grid, unique_depth[valid], modulus[valid], left=np.nan, right=np.nan)
                    outside = (depth_grid < np.nanmin(unique_depth[valid])) | (depth_grid > np.nanmax(unique_depth[valid]))
                    modulus_interp[outside] = np.nan
                    modulus_rows.append(modulus_interp)

        result = pd.DataFrame({"Depth (nm)": depth_grid})
        if hardness_rows:
            hardness_mat = np.vstack(hardness_rows)
            result["Hardness Mean (GPa)"] = np.nanmean(hardness_mat, axis=0)
            result["Hardness SD (GPa)"] = np.nanstd(hardness_mat, axis=0, ddof=1)
            result["Hardness Count"] = np.sum(np.isfinite(hardness_mat), axis=0)
        else:
            result["Hardness Mean (GPa)"] = np.nan
            result["Hardness SD (GPa)"] = np.nan
            result["Hardness Count"] = 0

        if modulus_rows:
            modulus_mat = np.vstack(modulus_rows)
            result["Modulus Mean (GPa)"] = np.nanmean(modulus_mat, axis=0)
            result["Modulus SD (GPa)"] = np.nanstd(modulus_mat, axis=0, ddof=1)
            result["Modulus Count"] = np.sum(np.isfinite(modulus_mat), axis=0)
        else:
            result["Modulus Mean (GPa)"] = np.nan
            result["Modulus SD (GPa)"] = np.nan
            result["Modulus Count"] = 0

        return result.replace([np.inf, -np.inf], np.nan)

    @staticmethod
    def _weighted_combine(
        mean_columns: List[np.ndarray],
        sd_columns: List[np.ndarray],
        count_columns: List[np.ndarray],
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        if not mean_columns:
            empty = np.asarray([], dtype=float)
            return empty, empty, empty

        means = np.vstack(mean_columns).astype(float)
        sds = np.vstack(sd_columns).astype(float) if sd_columns else np.full_like(means, np.nan)
        counts = np.vstack(count_columns).astype(float) if count_columns else np.ones_like(means)
        n_points = means.shape[1]

        combined_mean = np.full(n_points, np.nan, dtype=float)
        combined_unc = np.full(n_points, np.nan, dtype=float)
        combined_count = np.zeros(n_points, dtype=float)

        for idx in range(n_points):
            point_means = means[:, idx]
            point_sds = sds[:, idx]
            point_counts = counts[:, idx]
            finite_mean = np.isfinite(point_means)
            if not np.any(finite_mean):
                continue

            used_means = point_means[finite_mean]
            used_sds = point_sds[finite_mean]
            used_counts = np.where(np.isfinite(point_counts[finite_mean]), point_counts[finite_mean], 1.0)

            with np.errstate(divide="ignore", invalid="ignore"):
                se = np.where(
                    np.isfinite(used_sds) & (used_sds > 0) & (used_counts > 1),
                    used_sds / np.sqrt(used_counts),
                    np.where(np.isfinite(used_sds) & (used_sds > 0), used_sds, np.nan),
                )

            valid_unc = np.isfinite(se) & (se > 0)
            if np.any(valid_unc):
                weights = 1.0 / np.square(se[valid_unc])
                mean_values = used_means[valid_unc]
                weighted_mean = float(np.sum(weights * mean_values) / np.sum(weights))
                weighted_unc = float(np.sqrt(1.0 / np.sum(weights)))
            else:
                weighted_mean = float(np.mean(used_means))
                weighted_unc = float(np.std(used_means, ddof=1) / np.sqrt(len(used_means))) if len(used_means) > 1 else np.nan

            combined_mean[idx] = weighted_mean
            combined_unc[idx] = weighted_unc
            combined_count[idx] = float(len(used_means))

        return combined_mean, combined_unc, combined_count

    def compare_files_with_weighted_uncertainty(
        self,
        file_configs: Sequence[Dict[str, Any]],
        x_pattern: str = "Depth (nm)",
        hardness_pattern: str = "Hardness (GPa)",
        modulus_pattern: str = "Modulus (GPa)",
        target_x_range: Tuple[float, float, float] = (100, 200, 50),
        hardness_ylim: Tuple[float, float] = (0, 30),
        modulus_ylim: Tuple[float, float] = (0, 200),
    ) -> Dict[str, Any]:
        """Compare one or more CSM files on a shared depth grid using weighted uncertainty."""
        if not file_configs:
            raise ValueError("file_configs must contain at least one configuration.")

        start_nm, end_nm, _step_nm = [float(v) for v in target_x_range]
        depth_range = (start_nm, end_nm)

        per_file_results: List[Dict[str, Any]] = []
        hardness_means: List[np.ndarray] = []
        hardness_sds: List[np.ndarray] = []
        hardness_counts: List[np.ndarray] = []
        modulus_means: List[np.ndarray] = []
        modulus_sds: List[np.ndarray] = []
        modulus_counts: List[np.ndarray] = []
        depth_reference: Optional[np.ndarray] = None

        for idx, config in enumerate(file_configs):
            file_path = str(config.get("file_path", config.get("path", ""))).strip()
            if not file_path:
                raise ValueError(f"file_configs[{idx}] missing file_path/path.")

            if "test_numbers" in config and config["test_numbers"] is not None:
                test_numbers = [int(t) for t in config["test_numbers"]]
            elif "test_range" in config and config["test_range"]:
                test_numbers = self.parse_test_range(str(config["test_range"]))
            else:
                raise ValueError(f"file_configs[{idx}] missing test_numbers/test_range.")

            label = str(config.get("label") or Path(file_path).stem)
            offsets_nm = config.get("offsets_nm")
            recalculate = bool(config.get("recalculate", False))

            analyzed = self.analyze_file(
                file_path=file_path,
                test_numbers=test_numbers,
                depth_range=depth_range,
                offsets_nm=offsets_nm,
                recalculate=recalculate,
                target_x_range=target_x_range,
            )

            averaged = analyzed["averaged"].copy()
            if averaged.empty:
                continue

            x_col = self._first_matching_column(averaged, [x_pattern, "Depth (nm)"])
            h_mean_col = self._first_matching_column(averaged, [f"{hardness_pattern.split('(')[0].strip()} Mean", "Hardness Mean (GPa)"])
            h_sd_col = self._first_matching_column(averaged, [f"{hardness_pattern.split('(')[0].strip()} SD", "Hardness SD (GPa)"])
            h_count_col = self._first_matching_column(averaged, [f"{hardness_pattern.split('(')[0].strip()} Count", "Hardness Count"])
            m_mean_col = self._first_matching_column(averaged, [f"{modulus_pattern.split('(')[0].strip()} Mean", "Modulus Mean (GPa)"])
            m_sd_col = self._first_matching_column(averaged, [f"{modulus_pattern.split('(')[0].strip()} SD", "Modulus SD (GPa)"])
            m_count_col = self._first_matching_column(averaged, [f"{modulus_pattern.split('(')[0].strip()} Count", "Modulus Count"])

            if not x_col:
                raise ValueError(f"Could not resolve x column using pattern '{x_pattern}' for file: {file_path}")

            x_values = pd.to_numeric(averaged[x_col], errors="coerce").to_numpy(dtype=float)
            if depth_reference is None:
                depth_reference = x_values
            elif depth_reference.shape != x_values.shape:
                raise ValueError("target_x_range alignment mismatch between compared files.")

            def _get_column(column_name: Optional[str]) -> np.ndarray:
                if not column_name:
                    return np.full_like(x_values, np.nan, dtype=float)
                return pd.to_numeric(averaged[column_name], errors="coerce").to_numpy(dtype=float)

            hard_mean = _get_column(h_mean_col)
            hard_sd = _get_column(h_sd_col)
            hard_count = _get_column(h_count_col)
            mod_mean = _get_column(m_mean_col)
            mod_sd = _get_column(m_sd_col)
            mod_count = _get_column(m_count_col)

            hardness_means.append(hard_mean)
            hardness_sds.append(hard_sd)
            hardness_counts.append(hard_count)
            modulus_means.append(mod_mean)
            modulus_sds.append(mod_sd)
            modulus_counts.append(mod_count)

            per_file_results.append({
                "label": label,
                "file_path": file_path,
                "test_numbers": test_numbers,
                "recalculate": recalculate,
                "averaged": averaged,
            })

        if depth_reference is None:
            raise ValueError("No valid CSM rows produced for comparison.")

        hard_mean, hard_unc, hard_n = self._weighted_combine(hardness_means, hardness_sds, hardness_counts)
        mod_mean, mod_unc, mod_n = self._weighted_combine(modulus_means, modulus_sds, modulus_counts)

        comparison = pd.DataFrame({
            "Depth (nm)": depth_reference,
            "Hardness Weighted Mean (GPa)": hard_mean,
            "Hardness Weighted Uncertainty (GPa)": hard_unc,
            "Hardness Files Contributing": hard_n,
            "Modulus Weighted Mean (GPa)": mod_mean,
            "Modulus Weighted Uncertainty (GPa)": mod_unc,
            "Modulus Files Contributing": mod_n,
        })

        return {
            "file_results": per_file_results,
            "comparison": comparison,
            "x_pattern": x_pattern,
            "hardness_pattern": hardness_pattern,
            "modulus_pattern": modulus_pattern,
            "target_x_range": tuple(float(v) for v in target_x_range),
            "hardness_ylim": tuple(float(v) for v in hardness_ylim),
            "modulus_ylim": tuple(float(v) for v in modulus_ylim),
        }

    def analyze_file(
        self,
        file_path: str,
        test_numbers: Sequence[int],
        depth_range: Tuple[float, float],
        offsets_nm: Optional[Dict[int, float]] = None,
        recalculate: bool = False,
        target_x_range: Optional[Tuple[float, float, float]] = None,
    ) -> Dict[str, object]:
        raw = self.read_tests(file_path, test_numbers, offsets_nm=offsets_nm, recalculate=recalculate)
        if target_x_range is not None:
            averaged = self.average_by_target_x_range(raw, target_x_range)
        else:
            averaged = self.average_by_index(raw)
        if not averaged.empty:
            d_min, d_max = depth_range
            averaged = averaged[(averaged["Depth (nm)"] >= d_min) & (averaged["Depth (nm)"] <= d_max)]
        return {
            "file_path": str(Path(file_path)),
            "test_numbers": list(test_numbers),
            "raw": raw,
            "averaged": averaged.reset_index(drop=True),
            "source": "recalculated" if recalculate else "instrument_exported",
            "target_x_range": target_x_range,
        }


def compare_files_with_weighted_uncertainty(
    file_configs: Sequence[Dict[str, Any]],
    x_pattern: str = "Depth (nm)",
    hardness_pattern: str = "Hardness (GPa)",
    modulus_pattern: str = "Modulus (GPa)",
    target_x_range: Tuple[float, float, float] = (100, 200, 50),
    hardness_ylim: Tuple[float, float] = (0, 30),
    modulus_ylim: Tuple[float, float] = (0, 200),
    area_function_coefficients: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Function-style wrapper for multi-file CSM comparison with weighted uncertainty."""
    analyzer = CSMAnalyzer(area_function_coefficients=area_function_coefficients)
    return analyzer.compare_files_with_weighted_uncertainty(
        file_configs=file_configs,
        x_pattern=x_pattern,
        hardness_pattern=hardness_pattern,
        modulus_pattern=modulus_pattern,
        target_x_range=target_x_range,
        hardness_ylim=hardness_ylim,
        modulus_ylim=modulus_ylim,
    )
