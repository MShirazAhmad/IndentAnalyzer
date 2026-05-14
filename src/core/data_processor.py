#!/usr/bin/env python3
"""
Data Processing Module for Nanoindentation Analysis
Excel file parsing, data cleaning, and preprocessing
"""

import pandas as pd
import numpy as np
import xlrd
from typing import Dict, List, Tuple, Optional, Union
import warnings
from pathlib import Path
import importlib.util

# Import from local modules
try:
    from .standards import AnalysisConfig
except ImportError:
    from .standards import AnalysisConfig


class ExcelDataLoader:
    """Load and parse nanoindentation data from Excel files"""
    
    def __init__(self):
        self.config = AnalysisConfig()
        self.loader_module_name = "AgilentG200"
        # Import here to avoid circular imports
        try:
            from .validators import DataValidator
        except ImportError:
            from .validators import DataValidator
        self.validator = DataValidator()

    def set_loader(self, loader_module_name: str):
        self.loader_module_name = loader_module_name or "AgilentG200"

    def _load_selected_loader(self):
        loader_dir = Path(__file__).resolve().parent.parent / "fileloader"
        loader_path = loader_dir / f"{self.loader_module_name}.py"
        if not loader_path.exists():
            raise FileNotFoundError(f"File loader not found: {loader_path}")
        spec = importlib.util.spec_from_file_location(f"fileloader.{self.loader_module_name}", loader_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not import file loader: {loader_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
        
    def load_excel_file(self, file_path: Union[str, Path]) -> Dict[str, any]:
        """
        Load nanoindentation data from Excel file
        
        Args:
            file_path: Path to Excel file
        
        Returns:
            Dictionary containing loaded data and metadata
        """
        results = {
            'success': False,
            'data': {},
            'metadata': {},
            'errors': [],
            'warnings': []
        }
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            results['errors'].append(f"File not found: {file_path}")
            return results
        
        try:
            loader = self._load_selected_loader()
            if hasattr(loader, "load_file"):
                loaded = loader.load_file(file_path)
                if isinstance(loaded, dict):
                    return loaded

            if file_path.suffix.lower() not in ['.xls', '.xlsx']:
                results['errors'].append(f"Unsupported file format: {file_path.suffix}")
                return results

            # Try to read with pandas first
            try:
                # Read all sheets
                all_sheets = pd.read_excel(file_path, sheet_name=None, engine='xlrd' if file_path.suffix == '.xls' else 'openpyxl')
                results['metadata']['sheet_names'] = list(all_sheets.keys())
                results['metadata']['total_sheets'] = len(all_sheets)
                
                # Process each sheet
                processed_data = {}
                for sheet_name, df in all_sheets.items():
                    sheet_result = self._process_sheet_data(df, sheet_name)
                    if sheet_result['success']:
                        processed_data[sheet_name] = sheet_result['data']
                    else:
                        results['warnings'].extend([f"Sheet '{sheet_name}': {w}" for w in sheet_result['warnings']])
                        results['errors'].extend([f"Sheet '{sheet_name}': {e}" for e in sheet_result['errors']])
                
                if processed_data:
                    results['data'] = processed_data
                    results['success'] = True
                    results['metadata']['processed_sheets'] = len(processed_data)
                else:
                    results['errors'].append("No valid data found in any sheet")
                
            except Exception as e:
                results['errors'].append(f"Failed to read Excel file: {str(e)}")
        
        except Exception as e:
            results['errors'].append(f"Unexpected error loading file: {str(e)}")
        
        # Add file metadata
        results['metadata'].update({
            'file_path': str(file_path),
            'file_size_bytes': file_path.stat().st_size if file_path.exists() else 0,
            'file_extension': file_path.suffix
        })
        
        return results
    
    def _process_sheet_data(self, df: pd.DataFrame, sheet_name: str) -> Dict[str, any]:
        """Process individual sheet data"""
        results = {
            'success': False,
            'data': None,
            'errors': [],
            'warnings': []
        }
        
        if df.empty:
            results['errors'].append("Empty sheet")
            return results
        
        # Detect column structure
        column_mapping = self._detect_columns(df)
        
        if not column_mapping:
            results['errors'].append("Could not identify required columns")
            return results
        
        # Extract and clean data
        try:
            cleaned_data = self._extract_clean_data(df, column_mapping)
            
            if cleaned_data is not None and len(cleaned_data) > 0:
                results['data'] = cleaned_data
                results['success'] = True
            else:
                results['errors'].append("No valid data after cleaning")
        
        except Exception as e:
            results['errors'].append(f"Data extraction failed: {str(e)}")
        
        return results
    
    def _detect_columns(self, df: pd.DataFrame) -> Optional[Dict[str, str]]:
        """Detect which columns contain time, load, and displacement data"""
        column_patterns = {
            'time': ['time', 'zeit', 'temps', 'sec', 'second'],
            'load': ['load', 'force', 'last', 'kraft', 'charge', 'mn', 'newton', 'n'],
            'displacement': ['displacement', 'depth', 'tiefe', 'profondeur', 'nm', 'nanometer']
        }
        
        mapping = {}
        
        # Convert column names to lowercase for matching
        columns_lower = [str(col).lower() for col in df.columns]
        
        for data_type, patterns in column_patterns.items():
            best_match = None
            best_score = 0
            
            for i, col_name in enumerate(columns_lower):
                score = 0
                for pattern in patterns:
                    if pattern in col_name:
                        score += len(pattern)
                
                if score > best_score:
                    best_score = score
                    best_match = df.columns[i]
            
            if best_match is not None:
                mapping[data_type] = best_match
        
        # Check if we have the minimum required columns
        required = ['load', 'displacement']
        if all(req in mapping for req in required):
            return mapping
        
        return None
    
    def _extract_clean_data(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> Optional[pd.DataFrame]:
        """Extract and clean the data based on column mapping"""
        # Create standardized column names
        data_columns = {}
        
        if 'time' in column_mapping:
            data_columns['Time (sec)'] = column_mapping['time']
        
        data_columns['Load (mN)'] = column_mapping['load']
        data_columns['Displacement (nm)'] = column_mapping['displacement']
        
        # Extract relevant columns
        try:
            extracted_df = df[list(data_columns.values())].copy()
            extracted_df.columns = list(data_columns.keys())
            
            # Clean data
            cleaned_df = self._clean_numeric_data(extracted_df)
            
            return cleaned_df
        
        except Exception as e:
            raise ValueError(f"Data extraction failed: {str(e)}")
    
    def _clean_numeric_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate numeric data"""
        cleaned_df = df.copy()
        
        # Convert to numeric, coercing errors to NaN
        for col in cleaned_df.columns:
            cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
        
        # Remove rows with any NaN values
        initial_length = len(cleaned_df)
        cleaned_df = cleaned_df.dropna()
        final_length = len(cleaned_df)
        
        if final_length < initial_length * 0.8:  # Lost more than 20% of data
            warnings.warn(f"Significant data loss during cleaning: {initial_length} → {final_length} rows")
        
        # Remove duplicate rows
        cleaned_df = cleaned_df.drop_duplicates()
        
        # Sort by time if available, otherwise by displacement
        if 'Time (sec)' in cleaned_df.columns:
            cleaned_df = cleaned_df.sort_values('Time (sec)')
        else:
            cleaned_df = cleaned_df.sort_values('Displacement (nm)')
        
        # Reset index
        cleaned_df = cleaned_df.reset_index(drop=True)
        
        return cleaned_df


class DataProcessor:
    """Process and prepare nanoindentation data for analysis"""
    
    def __init__(self):
        self.config = AnalysisConfig()
        # Import here to avoid circular imports
        try:
            from .validators import HorizontalSegmentDetector
        except ImportError:
            from .validators import HorizontalSegmentDetector
        self.segment_detector = HorizontalSegmentDetector()
        
    def process_test_data(self, df: pd.DataFrame, test_name: str = "Unknown") -> Dict[str, any]:
        """
        Process complete nanoindentation test data
        
        Args:
            df: DataFrame with columns ['Time (sec)', 'Load (mN)', 'Displacement (nm)']
            test_name: Name identifier for the test
        
        Returns:
            Processed data with loading/unloading phases separated
        """
        results = {
            'test_name': test_name,
            'success': False,
            'original_data': df.copy(),
            'processed_data': {},
            'phases': {},
            'metadata': {},
            'warnings': [],
            'errors': []
        }
        
        # Basic validation
        required_columns = ['Load (mN)', 'Displacement (nm)']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            results['errors'].append(f"Missing required columns: {missing_columns}")
            return results
        
        if len(df) < self.config.MIN_LOAD_THRESHOLD:
            results['errors'].append(f"Insufficient data points: {len(df)}")
            return results
        
        try:
            # Filter and clean data
            filtered_data = self._filter_low_loads(df)
            
            if len(filtered_data) < 10:
                results['errors'].append("Insufficient data after filtering")
                return results
            
            # Detect loading and unloading phases
            phases = self._detect_loading_unloading_phases(filtered_data)
            
            if not phases['loading']['valid'] or not phases['unloading']['valid']:
                results['errors'].append("Could not identify valid loading/unloading phases")
                return results
            
            # Process horizontal segments
            processed_phases = self._process_horizontal_segments(phases)
            
            # Calculate metadata
            metadata = self._calculate_data_metadata(df, processed_phases)
            
            results.update({
                'success': True,
                'processed_data': filtered_data,
                'phases': processed_phases,
                'metadata': metadata
            })
            
        except Exception as e:
            results['errors'].append(f"Processing failed: {str(e)}")
        
        return results
    
    def _filter_low_loads(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter out low load data points"""
        max_load = df['Load (mN)'].max()
        min_load_threshold = max(
            max_load * self.config.LOAD_THRESHOLD_FACTOR,
            self.config.MIN_LOAD_THRESHOLD
        )
        
        # Keep data above threshold
        filtered_df = df[df['Load (mN)'] >= min_load_threshold].copy()
        
        return filtered_df.reset_index(drop=True)
    
    def _detect_loading_unloading_phases(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Detect loading and unloading phases in the data"""
        load = df['Load (mN)'].values
        displacement = df['Displacement (nm)'].values
        
        # Find maximum load point
        max_load_idx = np.argmax(load)
        max_load = load[max_load_idx]
        
        # Split into loading and unloading
        loading_indices = np.arange(0, max_load_idx + 1)
        unloading_indices = np.arange(max_load_idx, len(load))
        
        phases = {
            'loading': {
                'valid': len(loading_indices) >= self.config.MIN_SEGMENT_LENGTH,
                'indices': loading_indices,
                'data': df.iloc[loading_indices].copy() if len(loading_indices) > 0 else None,
                'max_load': max_load,
                'max_displacement': displacement[max_load_idx]
            },
            'unloading': {
                'valid': len(unloading_indices) >= self.config.MIN_SEGMENT_LENGTH,
                'indices': unloading_indices,
                'data': df.iloc[unloading_indices].copy() if len(unloading_indices) > 0 else None,
                'max_load': max_load,
                'max_displacement': displacement[max_load_idx]
            }
        }
        
        # Additional validation
        if phases['loading']['valid']:
            loading_data = phases['loading']['data']
            # Check if loading shows generally increasing trend
            load_trend = np.corrcoef(loading_data.index, loading_data['Load (mN)'])[0, 1]
            if load_trend < 0.5:  # Weak positive correlation
                phases['loading']['valid'] = False
        
        if phases['unloading']['valid']:
            unloading_data = phases['unloading']['data']
            # Check if unloading shows generally decreasing trend
            load_trend = np.corrcoef(unloading_data.index, unloading_data['Load (mN)'])[0, 1]
            if load_trend > -0.5:  # Weak negative correlation
                phases['unloading']['valid'] = False
        
        return phases
    
    def _process_horizontal_segments(self, phases: Dict[str, Dict]) -> Dict[str, Dict]:
        """Process and optionally remove horizontal segments"""
        processed_phases = phases.copy()
        
        for phase_name, phase_data in phases.items():
            # Always initialize filtered_data, even for invalid phases
            processed_phases[phase_name]['horizontal_segments'] = []
            processed_phases[phase_name]['segment_count'] = 0
            processed_phases[phase_name]['filtered_data'] = None
            
            if not phase_data['valid'] or phase_data['data'] is None:
                continue
            
            df_phase = phase_data['data']
            displacement = df_phase['Displacement (nm)'].values
            load = df_phase['Load (mN)'].values
            
            # Detect horizontal segments
            segments = self.segment_detector.detect_horizontal_segments(displacement, load)
            
            if segments:
                processed_phases[phase_name]['horizontal_segments'] = segments
                processed_phases[phase_name]['segment_count'] = len(segments)
                
                # Optionally filter out horizontal segments
                filtered_disp, filtered_load = self.segment_detector.filter_horizontal_segments(
                    displacement, load
                )
                
                if len(filtered_disp) >= self.config.MIN_SEGMENT_LENGTH:
                    # Create filtered DataFrame
                    filtered_df = pd.DataFrame({
                        'Load (mN)': filtered_load,
                        'Displacement (nm)': filtered_disp
                    })
                    
                    if 'Time (sec)' in df_phase.columns:
                        # Interpolate time values for remaining points
                        original_time = df_phase['Time (sec)'].values
                        # This is a simplified approach - in practice, you might want more sophisticated interpolation
                        filtered_df['Time (sec)'] = np.linspace(
                            original_time[0], original_time[-1], len(filtered_load)
                        )
                    
                    processed_phases[phase_name]['filtered_data'] = filtered_df
                else:
                    processed_phases[phase_name]['valid'] = False
                    # Still provide the original data as filtered_data
                    processed_phases[phase_name]['filtered_data'] = df_phase.copy()
            else:
                processed_phases[phase_name]['horizontal_segments'] = []
                processed_phases[phase_name]['segment_count'] = 0
                processed_phases[phase_name]['filtered_data'] = df_phase.copy()
        
        return processed_phases
    
    def _calculate_data_metadata(self, original_df: pd.DataFrame, 
                               processed_phases: Dict[str, Dict]) -> Dict[str, any]:
        """Calculate metadata about the processed data"""
        metadata = {
            'original_points': len(original_df),
            'load_range': {
                'min': original_df['Load (mN)'].min(),
                'max': original_df['Load (mN)'].max(),
                'range': original_df['Load (mN)'].max() - original_df['Load (mN)'].min()
            },
            'displacement_range': {
                'min': original_df['Displacement (nm)'].min(),
                'max': original_df['Displacement (nm)'].max(),
                'range': original_df['Displacement (nm)'].max() - original_df['Displacement (nm)'].min()
            },
            'phases': {}
        }
        
        for phase_name, phase_data in processed_phases.items():
            if phase_data['valid'] and phase_data['data'] is not None:
                df_phase = phase_data['data']
                metadata['phases'][phase_name] = {
                    'points': len(df_phase),
                    'horizontal_segments': phase_data.get('segment_count', 0),
                    'load_range': df_phase['Load (mN)'].max() - df_phase['Load (mN)'].min(),
                    'displacement_range': df_phase['Displacement (nm)'].max() - df_phase['Displacement (nm)'].min()
                }
                
                if 'filtered_data' in phase_data:
                    filtered_df = phase_data['filtered_data']
                    metadata['phases'][phase_name]['filtered_points'] = len(filtered_df)
        
        return metadata


class BatchProcessor:
    """Process multiple nanoindentation files in batch"""
    
    def __init__(self):
        self.loader = ExcelDataLoader()
        self.processor = DataProcessor()
        
    def process_directory(self, directory_path: Union[str, Path],
                         file_pattern: str = "*.xls*") -> Dict[str, any]:
        """
        Process all Excel files in a directory
        
        Args:
            directory_path: Path to directory containing Excel files
            file_pattern: Glob pattern for file matching
        
        Returns:
            Dictionary with results for all processed files
        """
        directory_path = Path(directory_path)
        
        results = {
            'directory': str(directory_path),
            'file_pattern': file_pattern,
            'processed_files': {},
            'summary': {},
            'errors': []
        }
        
        if not directory_path.exists():
            results['errors'].append(f"Directory not found: {directory_path}")
            return results
        
        if not directory_path.is_dir():
            results['errors'].append(f"Path is not a directory: {directory_path}")
            return results
        
        # Find matching files
        excel_files = list(directory_path.glob(file_pattern))
        
        if not excel_files:
            results['errors'].append(f"No files found matching pattern: {file_pattern}")
            return results
        
        # Process each file
        successful_files = 0
        total_tests = 0
        
        for file_path in excel_files:
            try:
                file_result = self.process_single_file(file_path)
                results['processed_files'][file_path.name] = file_result
                
                if file_result['success']:
                    successful_files += 1
                    total_tests += len(file_result['tests'])
                
            except Exception as e:
                results['processed_files'][file_path.name] = {
                    'success': False,
                    'error': f"Unexpected error: {str(e)}"
                }
        
        # Generate summary
        results['summary'] = {
            'total_files': len(excel_files),
            'successful_files': successful_files,
            'failed_files': len(excel_files) - successful_files,
            'total_tests': total_tests
        }
        
        return results
    
    def process_single_file(self, file_path: Union[str, Path]) -> Dict[str, any]:
        """Process a single Excel file"""
        file_path = Path(file_path)
        
        results = {
            'file_path': str(file_path),
            'success': False,
            'tests': {},
            'metadata': {},
            'errors': [],
            'warnings': []
        }
        
        # Load Excel file
        load_result = self.loader.load_excel_file(file_path)
        
        if not load_result['success']:
            results['errors'].extend(load_result['errors'])
            results['warnings'].extend(load_result['warnings'])
            return results
        
        # Process each sheet as a separate test
        successful_tests = 0
        
        for sheet_name, sheet_data in load_result['data'].items():
            try:
                test_result = self.processor.process_test_data(sheet_data, f"{file_path.stem}_{sheet_name}")
                results['tests'][sheet_name] = test_result
                
                if test_result['success']:
                    successful_tests += 1
                
            except Exception as e:
                results['tests'][sheet_name] = {
                    'success': False,
                    'error': f"Test processing failed: {str(e)}"
                }
        
        # Update results
        if successful_tests > 0:
            results['success'] = True
        
        results['metadata'] = load_result['metadata']
        results['metadata']['successful_tests'] = successful_tests
        results['metadata']['total_tests'] = len(load_result['data'])
        
        return results


def create_summary_statistics(batch_results: Dict[str, any]) -> Dict[str, any]:
    """Create summary statistics from batch processing results"""
    summary = {
        'file_statistics': {},
        'test_statistics': {},
        'data_quality': {},
        'recommendations': []
    }
    
    if 'processed_files' not in batch_results:
        return summary
    
    # Collect data from all successful tests
    all_tests = []
    file_success_rate = 0
    
    for file_name, file_result in batch_results['processed_files'].items():
        if file_result.get('success', False):
            file_success_rate += 1
            
            for test_name, test_result in file_result.get('tests', {}).items():
                if test_result.get('success', False):
                    test_info = {
                        'file_name': file_name,
                        'test_name': test_name,
                        'metadata': test_result.get('metadata', {})
                    }
                    all_tests.append(test_info)
    
    # File statistics
    total_files = len(batch_results['processed_files'])
    summary['file_statistics'] = {
        'total_files': total_files,
        'successful_files': file_success_rate,
        'success_rate_percent': (file_success_rate / total_files * 100) if total_files > 0 else 0
    }
    
    # Test statistics
    if all_tests:
        load_ranges = [test['metadata'].get('load_range', {}).get('range', 0) for test in all_tests]
        disp_ranges = [test['metadata'].get('displacement_range', {}).get('range', 0) for test in all_tests]
        
        summary['test_statistics'] = {
            'total_tests': len(all_tests),
            'load_range_stats': {
                'mean': np.mean(load_ranges),
                'std': np.std(load_ranges),
                'min': np.min(load_ranges),
                'max': np.max(load_ranges)
            },
            'displacement_range_stats': {
                'mean': np.mean(disp_ranges),
                'std': np.std(disp_ranges),
                'min': np.min(disp_ranges),
                'max': np.max(disp_ranges)
            }
        }
    
    return summary
