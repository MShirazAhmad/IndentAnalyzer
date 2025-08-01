#!/usr/bin/env python3
"""
Data Validation Module for Nanoindentation Analysis
ISO 14577-4:2016 compliant validation and quality assessment
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, List, Optional

# Import from local modules
try:
    from .standards import ISO14577Constants, ValidationLimits
except ImportError:
    from .standards import ISO14577Constants, ValidationLimits


class DataValidator:
    """Data validation and quality assessment for nanoindentation data"""
    
    def __init__(self):
        self.iso = ISO14577Constants()
        self.limits = ValidationLimits()
        
    def validate_data_completeness(self, df: pd.DataFrame) -> Dict[str, any]:
        """Validate data completeness according to ISO standards"""
        results = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'metrics': {}
        }
        
        # Check required columns
        required_columns = ['Time (sec)', 'Load (mN)', 'Displacement (nm)']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            results['valid'] = False
            results['errors'].append(f"Missing required columns: {missing_columns}")
            return results
        
        # Check data points count
        total_points = len(df)
        results['metrics']['total_points'] = total_points
        
        if total_points < self.iso.MIN_DATA_POINTS_LOADING:
            results['valid'] = False
            results['errors'].append(f"Insufficient data points: {total_points} < {self.iso.MIN_DATA_POINTS_LOADING}")
        
        # Check for NaN values
        nan_counts = df[required_columns].isnull().sum()
        if nan_counts.any():
            results['warnings'].append(f"Found NaN values: {dict(nan_counts)}")
        
        # Data range validation
        load_range = df['Load (mN)'].max() - df['Load (mN)'].min()
        disp_range = df['Displacement (nm)'].max() - df['Displacement (nm)'].min()
        
        results['metrics']['load_range'] = load_range
        results['metrics']['displacement_range'] = disp_range
        
        if load_range <= 0:
            results['valid'] = False
            results['errors'].append("Invalid load range: no load variation detected")
        
        if disp_range <= 0:
            results['valid'] = False
            results['errors'].append("Invalid displacement range: no displacement variation detected")
        
        return results
    
    def detect_noise_level(self, data: np.ndarray) -> Dict[str, float]:
        """Detect noise level in data using statistical methods"""
        if len(data) < 10:
            return {'noise_level': float('inf'), 'quality': 'insufficient_data'}
        
        # Remove trend by differencing
        diff_data = np.diff(data)
        
        # Calculate noise metrics
        noise_std = np.std(diff_data) / np.sqrt(2)  # Account for differencing
        signal_range = np.max(data) - np.min(data)
        
        if signal_range == 0:
            relative_noise = float('inf')
        else:
            relative_noise = noise_std / signal_range
        
        # Classify noise level
        if relative_noise < self.limits.LOW_NOISE:
            quality = 'excellent'
        elif relative_noise < self.limits.MODERATE_NOISE:
            quality = 'good'
        elif relative_noise < self.limits.HIGH_NOISE:
            quality = 'acceptable'
        else:
            quality = 'poor'
        
        return {
            'noise_level': relative_noise,
            'noise_std': noise_std,
            'signal_range': signal_range,
            'quality': quality
        }
    
    def check_monotonicity(self, x: np.ndarray, y: np.ndarray, 
                          phase: str = 'loading') -> Dict[str, any]:
        """Check monotonicity requirements for loading/unloading curves"""
        results = {
            'valid': True,
            'violations': 0,
            'violation_rate': 0.0,
            'details': []
        }
        
        if len(x) < 2 or len(y) < 2:
            results['valid'] = False
            results['details'].append("Insufficient data for monotonicity check")
            return results
        
        if phase == 'loading':
            # Loading: both load and displacement should increase
            x_violations = np.sum(np.diff(x) <= 0)
            y_violations = np.sum(np.diff(y) <= 0)
        else:  # unloading
            # Unloading: load should decrease, displacement may vary
            x_violations = np.sum(np.diff(x) >= 0)
            y_violations = 0  # Don't check displacement for unloading
        
        total_violations = x_violations + y_violations
        total_points = len(x) - 1  # Number of intervals
        violation_rate = total_violations / total_points
        
        results['violations'] = total_violations
        results['violation_rate'] = violation_rate
        
        if violation_rate > self.iso.MONOTONIC_VIOLATION_LIMIT:
            results['valid'] = False
            results['details'].append(
                f"Excessive monotonicity violations: {violation_rate:.1%} > "
                f"{self.iso.MONOTONIC_VIOLATION_LIMIT:.1%}"
            )
        
        if x_violations > 0:
            results['details'].append(f"X-axis violations: {x_violations}")
        if y_violations > 0:
            results['details'].append(f"Y-axis violations: {y_violations}")
        
        return results
    
    def validate_physical_properties(self, hardness: float, modulus: float) -> Dict[str, any]:
        """Validate computed physical properties against reasonable limits"""
        results = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Hardness validation
        if hardness < self.limits.MIN_HARDNESS:
            results['errors'].append(f"Hardness too low: {hardness:.2f} < {self.limits.MIN_HARDNESS}")
            results['valid'] = False
        elif hardness > self.limits.MAX_HARDNESS:
            results['errors'].append(f"Hardness too high: {hardness:.2f} > {self.limits.MAX_HARDNESS}")
            results['valid'] = False
        
        # Modulus validation
        if modulus < self.limits.MIN_MODULUS:
            results['errors'].append(f"Modulus too low: {modulus:.1e} < {self.limits.MIN_MODULUS:.1e}")
            results['valid'] = False
        elif modulus > self.limits.MAX_MODULUS:
            results['errors'].append(f"Modulus too high: {modulus:.1e} > {self.limits.MAX_MODULUS:.1e}")
            results['valid'] = False
        
        # Cross-validation: hardness-modulus relationship
        # For most materials, H/E ratio is typically 0.01-0.2
        he_ratio = hardness * 1e9 / modulus  # Convert hardness to Pa
        
        if he_ratio < 0.001:
            results['warnings'].append(f"Unusually low H/E ratio: {he_ratio:.4f}")
        elif he_ratio > 0.5:
            results['warnings'].append(f"Unusually high H/E ratio: {he_ratio:.4f}")
        
        return results
    
    def assess_curve_quality(self, load: np.ndarray, displacement: np.ndarray,
                           r_squared: float, stiffness: float) -> Dict[str, any]:
        """Comprehensive curve quality assessment"""
        results = {
            'overall_grade': 'unknown',
            'r_squared_grade': 'unknown',
            'noise_grade': 'unknown',
            'monotonicity_grade': 'unknown',
            'data_completeness_grade': 'unknown',
            'recommendations': []
        }
        
        # R-squared grading
        if r_squared >= self.limits.EXCELLENT_R2:
            results['r_squared_grade'] = 'excellent'
        elif r_squared >= self.limits.GOOD_R2:
            results['r_squared_grade'] = 'good'
        elif r_squared >= self.limits.ACCEPTABLE_R2:
            results['r_squared_grade'] = 'acceptable'
        else:
            results['r_squared_grade'] = 'poor'
            results['recommendations'].append("Improve curve fitting or check data quality")
        
        # Noise assessment
        noise_info = self.detect_noise_level(load)
        results['noise_grade'] = noise_info['quality']
        
        if noise_info['quality'] == 'poor':
            results['recommendations'].append("Reduce environmental vibrations or increase averaging")
        
        # Data completeness
        data_points = len(load)
        if data_points >= self.limits.RECOMMENDED_LOADING_POINTS:
            results['data_completeness_grade'] = 'excellent'
        elif data_points >= self.iso.MIN_DATA_POINTS_LOADING:
            results['data_completeness_grade'] = 'acceptable'
        else:
            results['data_completeness_grade'] = 'poor'
            results['recommendations'].append("Increase data acquisition rate")
        
        # Overall grade (worst of all components)
        grades = ['excellent', 'good', 'acceptable', 'poor']
        all_grades = [
            results['r_squared_grade'],
            results['noise_grade'],
            results['data_completeness_grade']
        ]
        
        worst_grade_idx = max([grades.index(g) for g in all_grades if g in grades])
        results['overall_grade'] = grades[worst_grade_idx]
        
        return results


class HorizontalSegmentDetector:
    """Detect and handle horizontal segments in load-displacement curves"""
    
    def __init__(self, config=None):
        try:
            from .standards import AnalysisConfig
        except ImportError:
            from .standards import AnalysisConfig
        self.config = config or AnalysisConfig()
    
    def detect_horizontal_segments(self, displacement: np.ndarray, 
                                 load: np.ndarray) -> List[Tuple[int, int]]:
        """Detect horizontal segments where load plateaus"""
        segments = []
        
        if len(displacement) < self.config.MIN_SEGMENT_LENGTH:
            return segments
        
        # Calculate load changes
        load_changes = np.abs(np.diff(load))
        displacement_span = np.max(displacement) - np.min(displacement)
        
        if displacement_span < self.config.MIN_DISPLACEMENT_SPAN:
            return segments
        
        # Adaptive threshold based on total load range
        load_range = np.max(load) - np.min(load)
        threshold = max(
            load_range * self.config.RELATIVE_THRESHOLD,
            np.std(load_changes) * 2
        )
        
        # Find regions with small load changes
        horizontal_mask = load_changes < threshold
        
        # Group consecutive horizontal points
        start_idx = None
        for i, is_horizontal in enumerate(horizontal_mask):
            if is_horizontal and start_idx is None:
                start_idx = i
            elif not is_horizontal and start_idx is not None:
                segment_length = i - start_idx
                if segment_length >= self.config.MIN_SEGMENT_LENGTH:
                    segments.append((start_idx, i))
                start_idx = None
        
        # Handle segment at end
        if start_idx is not None:
            segment_length = len(horizontal_mask) - start_idx
            if segment_length >= self.config.MIN_SEGMENT_LENGTH:
                segments.append((start_idx, len(horizontal_mask)))
        
        return segments
    
    def filter_horizontal_segments(self, displacement: np.ndarray,
                                 load: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Remove horizontal segments from data"""
        segments = self.detect_horizontal_segments(displacement, load)
        
        if not segments:
            return displacement.copy(), load.copy()
        
        # Create mask for valid data points
        valid_mask = np.ones(len(displacement), dtype=bool)
        
        for start, end in segments:
            valid_mask[start:end] = False
        
        return displacement[valid_mask], load[valid_mask]


def create_comprehensive_validation_report(df: pd.DataFrame,
                                         analysis_results: Dict) -> Dict[str, any]:
    """Create a comprehensive validation report for a nanoindentation test"""
    validator = DataValidator()
    
    report = {
        'timestamp': pd.Timestamp.now().isoformat(),
        'data_completeness': validator.validate_data_completeness(df),
        'curve_quality': None,
        'physical_properties': None,
        'overall_status': 'unknown',
        'recommendations': []
    }
    
    # Add curve quality assessment if analysis results available
    if analysis_results and 'r_squared' in analysis_results:
        load = df['Load (mN)'].values
        displacement = df['Displacement (nm)'].values
        
        report['curve_quality'] = validator.assess_curve_quality(
            load, displacement,
            analysis_results['r_squared'],
            analysis_results.get('stiffness', 0)
        )
        
        # Add physical properties validation
        if 'hardness' in analysis_results and 'modulus' in analysis_results:
            report['physical_properties'] = validator.validate_physical_properties(
                analysis_results['hardness'],
                analysis_results['modulus']
            )
    
    # Determine overall status
    all_valid = True
    
    if not report['data_completeness']['valid']:
        all_valid = False
    
    if report['curve_quality'] and report['curve_quality']['overall_grade'] == 'poor':
        all_valid = False
    
    if report['physical_properties'] and not report['physical_properties']['valid']:
        all_valid = False
    
    report['overall_status'] = 'valid' if all_valid else 'invalid'
    
    # Compile recommendations
    all_recommendations = []
    
    if report['curve_quality']:
        all_recommendations.extend(report['curve_quality']['recommendations'])
    
    if report['physical_properties']:
        all_recommendations.extend(report['physical_properties']['warnings'])
        all_recommendations.extend(report['physical_properties']['errors'])
    
    report['recommendations'] = list(set(all_recommendations))  # Remove duplicates
    
    return report
