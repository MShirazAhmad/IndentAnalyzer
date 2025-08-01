#!/usr/bin/env python3
"""
Unified Utilities Module
Consolidates common utility functions used across multiple files to eliminate duplication
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import warnings
import json
import pickle
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy import stats


class NanoindentationUtils:
    """
    Unified utilities for nanoindentation analysis
    Consolidates common functions from multiple modules
    """
    
    @staticmethod
    def calculate_theoretical_areas(contact_depths: Union[List[float], np.ndarray], 
                                  coefficients: Dict[str, float]) -> np.ndarray:
        """
        Calculate theoretical contact areas using tip area function
        
        Standard area function: A(h_c) = C₀·h_c² + C₁·h_c + C₂·h_c^0.5 + C₃·h_c^0.25 + ...
        
        Args:
            contact_depths: Contact depth values in nm
            coefficients: Area function coefficients dictionary
        
        Returns:
            Theoretical contact areas in nm²
        """
        # Extract coefficients with defaults
        C0 = coefficients.get('C0_nm2_per_nm2', coefficients.get('C0', 24.5))
        C1 = coefficients.get('C1_nm2_per_nm', coefficients.get('C1', 0.0))
        C2 = coefficients.get('C2_nm2_per_nm05', coefficients.get('C2', 0.0))
        C3 = coefficients.get('C3_nm2_per_nm025', coefficients.get('C3', 0.0))
        C4 = coefficients.get('C4_nm2_per_nm0125', coefficients.get('C4', 0.0))
        
        contact_depths = np.array(contact_depths)
        
        # Calculate area function
        areas = (C0 * contact_depths**2 + 
                C1 * contact_depths + 
                C2 * contact_depths**0.5)
        
        # Add higher-order terms if present
        if C3 != 0:
            areas += C3 * contact_depths**0.25
        if C4 != 0:
            areas += C4 * contact_depths**0.125
        
        return areas
    
    @staticmethod
    def calculate_r_squared(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        Calculate coefficient of determination (R²)
        
        Args:
            y_true: True values
            y_pred: Predicted values
        
        Returns:
            R² value
        """
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        
        if ss_tot == 0:
            return 0.0
        
        return 1 - (ss_res / ss_tot)
    
    @staticmethod
    def calculate_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        Calculate Mean Absolute Error
        
        Args:
            y_true: True values
            y_pred: Predicted values
        
        Returns:
            MAE value
        """
        return np.mean(np.abs(y_true - y_pred))
    
    @staticmethod
    def calculate_mse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        Calculate Mean Squared Error
        
        Args:
            y_true: True values
            y_pred: Predicted values
        
        Returns:
            MSE value
        """
        return np.mean((y_true - y_pred) ** 2)
    
    @staticmethod
    def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        Calculate Root Mean Squared Error
        
        Args:
            y_true: True values
            y_pred: Predicted values
        
        Returns:
            RMSE value
        """
        return np.sqrt(np.mean((y_true - y_pred) ** 2))
    
    @staticmethod
    def calculate_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        Calculate Mean Absolute Percentage Error
        
        Args:
            y_true: True values
            y_pred: Predicted values
        
        Returns:
            MAPE value as percentage
        """
        # Avoid division by zero
        mask = y_true != 0
        if np.sum(mask) == 0:
            return float('inf')
        
        return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    
    @staticmethod
    def oliver_pharr_model(h: np.ndarray, A: float, m: float, hf: float) -> np.ndarray:
        """
        Oliver-Pharr power law model: P = A(h - hf)^m
        
        Args:
            h: Displacement values
            A: Fitting parameter
            m: Power law exponent
            hf: Final displacement
        
        Returns:
            Load values
        """
        return A * np.power(np.maximum(h - hf, 1e-10), m)
    
    @staticmethod
    def fit_oliver_pharr(displacement: np.ndarray, load: np.ndarray,
                        max_iterations: int = 5000) -> Dict[str, any]:
        """
        Fit Oliver-Pharr power law to unloading data
        
        Args:
            displacement: Displacement values in nm
            load: Load values in mN
            max_iterations: Maximum fitting iterations
        
        Returns:
            Fitting results dictionary
        """
        result = {
            'success': False,
            'A': 0.0,
            'm': 0.0,
            'hf': 0.0,
            'r_squared': 0.0,
            'stiffness': 0.0,
            'contact_depth': 0.0,
            'errors': []
        }
        
        try:
            # Remove invalid data
            valid_mask = (load > 0) & (displacement > 0) & np.isfinite(load) & np.isfinite(displacement)
            if np.sum(valid_mask) < 5:
                result['errors'].append("Insufficient valid data points")
                return result
            
            load_clean = load[valid_mask]
            disp_clean = displacement[valid_mask]
            
            # Initial guess
            P_max = np.max(load_clean)
            h_max = disp_clean[np.argmax(load_clean)]
            initial_guess = [P_max, 2.0, h_max * 0.9]
            
            # Fit curve
            popt, pcov = curve_fit(
                NanoindentationUtils.oliver_pharr_model,
                disp_clean,
                load_clean,
                p0=initial_guess,
                maxfev=max_iterations
            )
            
            A, m, hf = popt
            
            # Calculate R²
            y_pred = NanoindentationUtils.oliver_pharr_model(disp_clean, A, m, hf)
            r_squared = NanoindentationUtils.calculate_r_squared(load_clean, y_pred)
            
            # Calculate stiffness at maximum load
            stiffness = m * A * np.power(h_max - hf, m - 1)
            
            # Calculate contact depth (Oliver-Pharr method)
            epsilon = 0.75  # Geometric constant for Berkovich indenter
            contact_depth = h_max - epsilon * P_max / stiffness
            
            result.update({
                'success': True,
                'A': A,
                'm': m,
                'hf': hf,
                'r_squared': r_squared,
                'stiffness': stiffness,
                'contact_depth': contact_depth,
                'max_load': P_max,
                'max_displacement': h_max
            })
            
        except Exception as e:
            result['errors'].append(f"Curve fitting failed: {str(e)}")
        
        return result
    
    @staticmethod
    def detect_outliers_iqr(data: Union[List[float], np.ndarray],
                           factor: float = 1.5) -> List[int]:
        """
        Detect outliers using Interquartile Range (IQR) method
        
        Args:
            data: Data values
            factor: IQR multiplier for outlier threshold
        
        Returns:
            List of outlier indices
        """
        data_array = np.array(data)
        Q1 = np.percentile(data_array, 25)
        Q3 = np.percentile(data_array, 75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - factor * IQR
        upper_bound = Q3 + factor * IQR
        
        outliers = []
        for i, value in enumerate(data_array):
            if value < lower_bound or value > upper_bound:
                outliers.append(i)
        
        return outliers
    
    @staticmethod
    def detect_outliers_zscore(data: Union[List[float], np.ndarray],
                              threshold: float = 3.0) -> List[int]:
        """
        Detect outliers using Z-score method
        
        Args:
            data: Data values
            threshold: Z-score threshold for outliers
        
        Returns:
            List of outlier indices
        """
        data_array = np.array(data)
        z_scores = np.abs(stats.zscore(data_array))
        
        outliers = []
        for i, z_score in enumerate(z_scores):
            if z_score > threshold:
                outliers.append(i)
        
        return outliers
    
    @staticmethod
    def smooth_data(data: np.ndarray, method: str = 'moving_average',
                   window_size: int = 5) -> np.ndarray:
        """
        Smooth data using various methods
        
        Args:
            data: Input data
            method: Smoothing method ('moving_average', 'savgol')
            window_size: Window size for smoothing
        
        Returns:
            Smoothed data
        """
        if method == 'moving_average':
            return pd.Series(data).rolling(window=window_size, center=True).mean().fillna(data)
        elif method == 'savgol':
            from scipy.signal import savgol_filter
            return savgol_filter(data, window_size, 3)  # 3rd order polynomial
        else:
            return data
    
    @staticmethod
    def analyze_property_trends(property_values: List[float],
                               depth_values: List[float]) -> Dict[str, any]:
        """
        Analyze trends in mechanical properties vs depth
        
        Args:
            property_values: Property values (e.g., hardness, modulus)
            depth_values: Corresponding depth values
        
        Returns:
            Trend analysis results
        """
        if len(property_values) != len(depth_values) or len(property_values) < 3:
            return {'error': 'Insufficient data for trend analysis'}
        
        prop_array = np.array(property_values)
        depth_array = np.array(depth_values)
        
        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(depth_array, prop_array)
        
        # Trend classification
        if abs(r_value) < 0.3:
            trend_type = 'no_trend'
        elif slope > 0:
            trend_type = 'increasing'
        else:
            trend_type = 'decreasing'
        
        # Statistical significance
        is_significant = p_value < 0.05
        
        return {
            'trend_type': trend_type,
            'slope': slope,
            'intercept': intercept,
            'correlation': r_value,
            'r_squared': r_value**2,
            'p_value': p_value,
            'std_error': std_err,
            'is_significant': is_significant,
            'trend_strength': abs(r_value)
        }
    
    @staticmethod
    def calculate_statistics(data: Union[List[float], np.ndarray]) -> Dict[str, float]:
        """
        Calculate comprehensive statistics for a dataset
        
        Args:
            data: Input data
        
        Returns:
            Statistics dictionary
        """
        data_array = np.array(data)
        
        if len(data_array) == 0:
            return {'error': 'Empty dataset'}
        
        return {
            'count': len(data_array),
            'mean': np.mean(data_array),
            'median': np.median(data_array),
            'std': np.std(data_array),
            'var': np.var(data_array),
            'min': np.min(data_array),
            'max': np.max(data_array),
            'range': np.max(data_array) - np.min(data_array),
            'cv_percent': (np.std(data_array) / np.mean(data_array)) * 100 if np.mean(data_array) != 0 else 0,
            'q25': np.percentile(data_array, 25),
            'q75': np.percentile(data_array, 75),
            'iqr': np.percentile(data_array, 75) - np.percentile(data_array, 25),
            'skewness': stats.skew(data_array),
            'kurtosis': stats.kurtosis(data_array)
        }
    
    @staticmethod
    def save_results(results: Dict, file_path: Union[str, Path],
                    format: str = 'json') -> bool:
        """
        Save results to file in various formats
        
        Args:
            results: Results dictionary
            file_path: Output file path
            format: Output format ('json', 'pickle', 'excel')
        
        Returns:
            Success status
        """
        try:
            file_path = Path(file_path)
            
            if format.lower() == 'json':
                with open(file_path, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
            
            elif format.lower() == 'pickle':
                with open(file_path, 'wb') as f:
                    pickle.dump(results, f)
            
            elif format.lower() == 'excel':
                # Convert nested dictionaries to flat structure for Excel
                flat_results = NanoindentationUtils._flatten_dict(results)
                df = pd.DataFrame([flat_results])
                df.to_excel(file_path, index=False)
            
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            return True
            
        except Exception as e:
            print(f"Failed to save results: {e}")
            return False
    
    @staticmethod
    def load_results(file_path: Union[str, Path], format: str = 'auto') -> Optional[Dict]:
        """
        Load results from file
        
        Args:
            file_path: Input file path
            format: Input format ('json', 'pickle', 'auto')
        
        Returns:
            Loaded results or None if failed
        """
        try:
            file_path = Path(file_path)
            
            if format == 'auto':
                # Determine format from extension
                if file_path.suffix.lower() == '.json':
                    format = 'json'
                elif file_path.suffix.lower() in ['.pkl', '.pickle']:
                    format = 'pickle'
                else:
                    format = 'json'  # Default
            
            if format.lower() == 'json':
                with open(file_path, 'r') as f:
                    return json.load(f)
            
            elif format.lower() == 'pickle':
                with open(file_path, 'rb') as f:
                    return pickle.load(f)
            
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            print(f"Failed to load results: {e}")
            return None
    
    @staticmethod
    def _flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """
        Flatten nested dictionary for Excel export
        
        Args:
            d: Input dictionary
            parent_key: Parent key prefix
            sep: Key separator
        
        Returns:
            Flattened dictionary
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(NanoindentationUtils._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    @staticmethod
    def generate_quality_report(analysis_results: Dict) -> Dict[str, any]:
        """
        Generate a comprehensive quality report from analysis results
        
        Args:
            analysis_results: Analysis results dictionary
        
        Returns:
            Quality report
        """
        report = {
            'overall_grade': 'unknown',
            'data_quality': 'unknown',
            'fitting_quality': 'unknown',
            'property_reliability': 'unknown',
            'iso_compliance': False,
            'recommendations': [],
            'scores': {}
        }
        
        try:
            # Data quality assessment
            if 'validation_report' in analysis_results:
                validation = analysis_results['validation_report']
                report['data_quality'] = validation.get('curve_quality', {}).get('overall_grade', 'unknown')
            
            # Fitting quality assessment
            if 'curve_fitting' in analysis_results:
                r_squared = analysis_results['curve_fitting'].get('r_squared', 0)
                if r_squared >= 0.99:
                    report['fitting_quality'] = 'excellent'
                elif r_squared >= 0.98:
                    report['fitting_quality'] = 'good'
                elif r_squared >= 0.95:
                    report['fitting_quality'] = 'acceptable'
                else:
                    report['fitting_quality'] = 'poor'
                    report['recommendations'].append("Improve curve fitting quality")
                
                # ISO compliance
                report['iso_compliance'] = r_squared >= 0.98
                report['scores']['r_squared'] = r_squared
            
            # Property reliability assessment
            if 'mechanical_properties' in analysis_results:
                props = analysis_results['mechanical_properties']
                if props.get('overall_valid', False):
                    report['property_reliability'] = 'good'
                else:
                    report['property_reliability'] = 'poor'
                    report['recommendations'].append("Review mechanical property calculations")
            
            # Overall grade determination
            grades = ['excellent', 'good', 'acceptable', 'poor', 'unknown']
            individual_grades = [
                report['data_quality'],
                report['fitting_quality'],
                report['property_reliability']
            ]
            
            # Find worst grade
            worst_grade_idx = len(grades) - 1
            for grade in individual_grades:
                if grade in grades:
                    worst_grade_idx = min(worst_grade_idx, grades.index(grade))
            
            report['overall_grade'] = grades[worst_grade_idx]
            
            # Generate additional recommendations
            if not report['iso_compliance']:
                report['recommendations'].append("Analysis does not meet ISO 14577-4:2016 standards")
            
            if report['overall_grade'] == 'poor':
                report['recommendations'].append("Consider repeating measurements with improved conditions")
            
        except Exception as e:
            report['error'] = f"Quality report generation failed: {str(e)}"
        
        return report
    
    @staticmethod
    def create_summary_plot(data: Dict, output_path: Optional[str] = None) -> str:
        """
        Create a summary plot of analysis results
        
        Args:
            data: Analysis data
            output_path: Optional output path for saving
        
        Returns:
            Path to generated plot
        """
        try:
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            
            # Plot 1: Load-Displacement curve
            if 'raw_data' in data:
                ax = axes[0, 0]
                raw_data = data['raw_data']
                ax.plot(raw_data['displacement'], raw_data['load'], 'b-', alpha=0.7)
                ax.set_xlabel('Displacement (nm)')
                ax.set_ylabel('Load (mN)')
                ax.set_title('Load-Displacement Curve')
                ax.grid(True, alpha=0.3)
            
            # Plot 2: Property values
            if 'mechanical_properties' in data:
                ax = axes[0, 1]
                props = data['mechanical_properties']
                hardness = props.get('hardness', {}).get('hardness_gpa', 0)
                modulus = props.get('sample_modulus', {}).get('sample_modulus_gpa', 0)
                
                ax.bar(['Hardness', 'Modulus'], [hardness, modulus])
                ax.set_ylabel('Value (GPa)')
                ax.set_title('Mechanical Properties')
                ax.grid(True, alpha=0.3)
            
            # Plot 3: Quality metrics
            if 'curve_fitting' in data:
                ax = axes[1, 0]
                r_squared = data['curve_fitting'].get('r_squared', 0)
                ax.bar(['R²'], [r_squared])
                ax.set_ylim(0, 1)
                ax.set_ylabel('R²')
                ax.set_title('Fitting Quality')
                ax.grid(True, alpha=0.3)
            
            # Plot 4: Summary text
            ax = axes[1, 1]
            ax.axis('off')
            
            # Generate summary text
            summary_lines = []
            if 'mechanical_properties' in data:
                props = data['mechanical_properties']
                hardness = props.get('hardness', {}).get('hardness_gpa', 0)
                modulus = props.get('sample_modulus', {}).get('sample_modulus_gpa', 0)
                summary_lines.extend([
                    f"Hardness: {hardness:.2f} GPa",
                    f"Modulus: {modulus:.1f} GPa"
                ])
            
            if 'curve_fitting' in data:
                r_squared = data['curve_fitting'].get('r_squared', 0)
                summary_lines.append(f"R²: {r_squared:.4f}")
            
            # Add quality assessment
            quality_report = NanoindentationUtils.generate_quality_report(data)
            summary_lines.extend([
                "",
                f"Overall Grade: {quality_report['overall_grade'].title()}",
                f"ISO Compliant: {'Yes' if quality_report['iso_compliance'] else 'No'}"
            ])
            
            summary_text = '\n'.join(summary_lines)
            ax.text(0.1, 0.9, summary_text, transform=ax.transAxes, 
                   fontsize=12, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
            
            plt.tight_layout()
            
            # Save or return
            if output_path:
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                plt.close()
                return output_path
            else:
                temp_path = 'temp_summary_plot.png'
                plt.savefig(temp_path, dpi=300, bbox_inches='tight')
                plt.close()
                return temp_path
                
        except Exception as e:
            print(f"Failed to create summary plot: {e}")
            return ""


# Convenience functions for backward compatibility
def calculate_theoretical_areas(contact_depths: Union[List[float], np.ndarray], 
                               coefficients: Dict[str, float]) -> np.ndarray:
    """Backward compatible wrapper"""
    return NanoindentationUtils.calculate_theoretical_areas(contact_depths, coefficients)

def calculate_R_2(x_true: np.ndarray, y_true: np.ndarray, 
                 poly_coeffs: Optional[np.ndarray] = None) -> float:
    """Backward compatible R² calculation"""
    if poly_coeffs is not None:
        # If polynomial coefficients provided, evaluate polynomial
        y_pred = np.polyval(poly_coeffs, x_true)
    else:
        # Assume y_true is predicted values
        y_pred = y_true
        y_true = x_true
    
    return NanoindentationUtils.calculate_r_squared(y_true, y_pred)

def analyze_residuals_meaning(residuals: np.ndarray, areas: np.ndarray) -> Dict[str, any]:
    """Backward compatible residual analysis"""
    return {
        'mean_residual': np.mean(residuals),
        'std_residual': np.std(residuals),
        'outliers_iqr': NanoindentationUtils.detect_outliers_iqr(residuals),
        'outliers_zscore': NanoindentationUtils.detect_outliers_zscore(residuals),
        'statistics': NanoindentationUtils.calculate_statistics(residuals)
    }
