#!/usr/bin/env python3
"""
Curve Fitting Module for Nanoindentation Analysis
ISO 14577-4:2016 compliant curve fitting and contact mechanics
"""

import numpy as np
from scipy.optimize import curve_fit, minimize_scalar
from scipy.stats import linregress
from typing import Tuple, Dict, Optional, Callable
import warnings

# Import from local modules
try:
    from ..core.standards import ISO14577Constants, AnalysisConfig
except ImportError:
    from ..core.standards import ISO14577Constants, AnalysisConfig


class CurveFitter:
    """Advanced curve fitting for nanoindentation unloading curves"""
    
    def __init__(self):
        self.iso = ISO14577Constants()
        self.config = AnalysisConfig()
    
    @staticmethod
    def power_law_unloading(h: np.ndarray, P_max: float, h_f: float, m: float) -> np.ndarray:
        """
        Power law unloading curve: P = P_max * ((h - h_f) / (h_max - h_f))^m
        
        Args:
            h: displacement array
            P_max: maximum load
            h_f: final displacement (residual indent)
            m: power law exponent
        """
        h_max = np.max(h)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ratio = np.maximum((h - h_f) / (h_max - h_f), 0)
            return P_max * np.power(ratio, m)
    
    @staticmethod
    def oliver_pharr_unloading(h: np.ndarray, A: float, h_f: float, m: float) -> np.ndarray:
        """
        Oliver-Pharr unloading curve: P = A * (h - h_f)^m
        
        Args:
            h: displacement array
            A: fitting parameter
            h_f: final displacement
            m: power law exponent
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return A * np.power(np.maximum(h - h_f, 0), m)
    
    def fit_unloading_curve(self, displacement: np.ndarray, load: np.ndarray,
                           method: str = 'oliver_pharr', tip_geometry: str = 'berkovich') -> Dict[str, any]:
        """
        Fit unloading curve using specified method according to NIST Guide
        
        Args:
            displacement: displacement data (nm)
            load: load data (mN)
            method: 'oliver_pharr' or 'power_law'
            tip_geometry: 'berkovich', 'vickers', 'spherical', 'cone', 'flat_punch'
        """
        results = {
            'method': method,
            'tip_geometry': tip_geometry,
            'success': False,
            'parameters': {},
            'r_squared': 0.0,
            'fitted_curve': None,
            'residuals': None,
            'stiffness': 0.0,
            'contact_depth': 0.0,
            'power_law_exponent': self._get_theoretical_exponent(tip_geometry),
            'epsilon_factor': self._get_epsilon_factor(tip_geometry),
            'errors': []
        }
        
        if len(displacement) < 3 or len(load) < 3:
            results['errors'].append("Insufficient data points for curve fitting")
            return results
        
        # Use upper portion of unloading curve (ISO standard)
        n_points = len(displacement)
        start_idx = int(n_points * (1 - self.iso.STIFFNESS_RANGE_PERCENT))
        
        h_fit = displacement[start_idx:]
        P_fit = load[start_idx:]
        
        if len(h_fit) < 3:
            results['errors'].append("Insufficient points in fitting range")
            return results
        
        try:
            if method == 'oliver_pharr':
                results.update(self._fit_oliver_pharr(h_fit, P_fit, displacement, load))
            elif method == 'power_law':
                results.update(self._fit_power_law(h_fit, P_fit, displacement, load))
            else:
                results['errors'].append(f"Unknown fitting method: {method}")
                return results
            
            # Calculate stiffness and contact depth
            if results['success']:
                results.update(self._calculate_contact_properties(
                    displacement, load, results['parameters'], method
                ))
            
        except Exception as e:
            results['errors'].append(f"Curve fitting failed: {str(e)}")
        
        return results
    
    def _get_theoretical_exponent(self, tip_geometry: str) -> float:
        """Get theoretical power law exponent m from NIST Guide Table 1"""
        geometry_map = {
            'flat_punch': self.iso.POWER_LAW_EXPONENT_FLAT_PUNCH,
            'paraboloid': self.iso.POWER_LAW_EXPONENT_PARABOLOID,
            'spherical': self.iso.POWER_LAW_EXPONENT_PARABOLOID,  # Same as paraboloid
            'cone': self.iso.POWER_LAW_EXPONENT_CONE,
            'berkovich': self.iso.POWER_LAW_EXPONENT_CONE,  # Pyramidal ~ cone
            'vickers': self.iso.POWER_LAW_EXPONENT_CONE     # Pyramidal ~ cone
        }
        return geometry_map.get(tip_geometry.lower(), 1.5)  # Default to paraboloid
    
    def _get_epsilon_factor(self, tip_geometry: str) -> float:
        """Get epsilon factor ε from NIST Guide Table 1"""
        geometry_map = {
            'flat_punch': self.iso.EPSILON_FLAT_PUNCH,
            'paraboloid': self.iso.EPSILON_PARABOLOID,
            'spherical': self.iso.EPSILON_SPHERICAL,
            'cone': self.iso.EPSILON_CONE,
            'berkovich': self.iso.EPSILON_BERKOVICH,
            'vickers': self.iso.EPSILON_VICKERS
        }
        return geometry_map.get(tip_geometry.lower(), 0.75)  # Default value
    
    def _fit_oliver_pharr(self, h_fit: np.ndarray, P_fit: np.ndarray,
                         h_full: np.ndarray, P_full: np.ndarray) -> Dict[str, any]:
        """Fit Oliver-Pharr unloading curve"""
        results = {'success': False, 'parameters': {}}
        
        # Initial parameter estimates
        h_max = np.max(h_full)
        P_max = np.max(P_full)
        h_f_init = np.min(h_fit) * 0.8  # Estimate residual depth
        A_init = P_max / ((h_max - h_f_init) ** 1.5)
        m_init = 1.5  # Typical value for many materials
        
        # Parameter bounds
        h_f_bounds = (0, np.min(h_fit))
        A_bounds = (0, P_max * 10)
        m_bounds = (1.1, 3.0)  # Physical reasonable range
        
        try:
            # Fit using scipy.optimize.curve_fit
            popt, pcov = curve_fit(
                self.oliver_pharr_unloading,
                h_fit, P_fit,
                p0=[A_init, h_f_init, m_init],
                bounds=([A_bounds[0], h_f_bounds[0], m_bounds[0]],
                       [A_bounds[1], h_f_bounds[1], m_bounds[1]]),
                maxfev=self.config.MAX_FITTING_ITERATIONS
            )
            
            A_fit, h_f_fit, m_fit = popt
            
            # Calculate fitted curve for full displacement range
            P_fitted = self.oliver_pharr_unloading(h_full, A_fit, h_f_fit, m_fit)
            
            # Calculate R-squared
            ss_res = np.sum((P_full - P_fitted) ** 2)
            ss_tot = np.sum((P_full - np.mean(P_full)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            # Check fitting quality
            if r_squared >= self.iso.MIN_R_SQUARED:
                results.update({
                    'success': True,
                    'parameters': {'A': A_fit, 'h_f': h_f_fit, 'm': m_fit},
                    'r_squared': r_squared,
                    'fitted_curve': P_fitted,
                    'residuals': P_full - P_fitted,
                    'parameter_errors': np.sqrt(np.diag(pcov))
                })
            else:
                results['errors'] = [f"Poor fit quality: R² = {r_squared:.4f} < {self.iso.MIN_R_SQUARED}"]
        
        except Exception as e:
            results['errors'] = [f"Oliver-Pharr fitting failed: {str(e)}"]
        
        return results
    
    def _fit_power_law(self, h_fit: np.ndarray, P_fit: np.ndarray,
                      h_full: np.ndarray, P_full: np.ndarray) -> Dict[str, any]:
        """Fit power law unloading curve"""
        results = {'success': False, 'parameters': {}}
        
        P_max = np.max(P_full)
        h_max = np.max(h_full)
        h_f_init = np.min(h_fit) * 0.8
        m_init = 1.5
        
        # Parameter bounds
        h_f_bounds = (0, np.min(h_fit))
        m_bounds = (1.1, 3.0)
        
        try:
            # Fit using scipy.optimize.curve_fit with fixed P_max
            def power_law_fixed_pmax(h, h_f, m):
                return self.power_law_unloading(h, P_max, h_f, m)
            
            popt, pcov = curve_fit(
                power_law_fixed_pmax,
                h_fit, P_fit,
                p0=[h_f_init, m_init],
                bounds=([h_f_bounds[0], m_bounds[0]],
                       [h_f_bounds[1], m_bounds[1]]),
                maxfev=self.config.MAX_FITTING_ITERATIONS
            )
            
            h_f_fit, m_fit = popt
            
            # Calculate fitted curve
            P_fitted = self.power_law_unloading(h_full, P_max, h_f_fit, m_fit)
            
            # Calculate R-squared
            ss_res = np.sum((P_full - P_fitted) ** 2)
            ss_tot = np.sum((P_full - np.mean(P_full)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            if r_squared >= self.iso.MIN_R_SQUARED:
                results.update({
                    'success': True,
                    'parameters': {'P_max': P_max, 'h_f': h_f_fit, 'm': m_fit},
                    'r_squared': r_squared,
                    'fitted_curve': P_fitted,
                    'residuals': P_full - P_fitted,
                    'parameter_errors': np.sqrt(np.diag(pcov))
                })
            else:
                results['errors'] = [f"Poor fit quality: R² = {r_squared:.4f} < {self.iso.MIN_R_SQUARED}"]
        
        except Exception as e:
            results['errors'] = [f"Power law fitting failed: {str(e)}"]
        
        return results
    
    def _calculate_contact_properties(self, displacement: np.ndarray, load: np.ndarray,
                                    parameters: Dict, method: str) -> Dict[str, any]:
        """Calculate contact stiffness and depth from fitted parameters"""
        results = {}
        
        try:
            h_max = np.max(displacement)
            P_max = np.max(load)
            
            if method == 'oliver_pharr':
                A, h_f, m = parameters['A'], parameters['h_f'], parameters['m']
                
                # Stiffness at maximum load: dP/dh at h_max
                stiffness = A * m * ((h_max - h_f) ** (m - 1))
                
                # Contact depth (Oliver-Pharr method)
                contact_depth = h_max - (P_max / stiffness) * self.iso.EPSILON_BERKOVICH
                
            elif method == 'power_law':
                P_max_fit, h_f, m = parameters['P_max'], parameters['h_f'], parameters['m']
                h_range = h_max - h_f
                
                # Stiffness at maximum load
                stiffness = (P_max_fit * m / h_range) if h_range > 0 else 0
                
                # Contact depth
                contact_depth = h_max - (P_max / stiffness) * self.iso.EPSILON_BERKOVICH
            
            else:
                raise ValueError(f"Unknown method: {method}")
            
            # Ensure physical reasonableness
            contact_depth = max(0, min(contact_depth, h_max))
            stiffness = max(0, stiffness)
            
            results.update({
                'stiffness': stiffness,
                'contact_depth': contact_depth
            })
            
        except Exception as e:
            results['errors'] = results.get('errors', []) + [f"Contact property calculation failed: {str(e)}"]
        
        return results


class LinearFitter:
    """Linear regression tools for stiffness calculation"""
    
    @staticmethod
    def fit_linear_stiffness(displacement: np.ndarray, load: np.ndarray,
                           fit_range: float = 0.25) -> Dict[str, any]:
        """
        Calculate stiffness using linear regression on upper portion of unloading curve
        
        Args:
            displacement: displacement data
            load: load data  
            fit_range: fraction of unloading curve to use (default 0.25 = upper 25%)
        """
        results = {
            'stiffness': 0.0,
            'r_squared': 0.0,
            'intercept': 0.0,
            'std_error': 0.0,
            'success': False
        }
        
        if len(displacement) < 3 or len(load) < 3:
            return results
        
        # Use upper portion of curve
        n_points = len(displacement)
        start_idx = int(n_points * (1 - fit_range))
        
        h_fit = displacement[start_idx:]
        P_fit = load[start_idx:]
        
        if len(h_fit) < 2:
            return results
        
        try:
            # Linear regression: P = S*h + intercept
            slope, intercept, r_value, p_value, std_err = linregress(h_fit, P_fit)
            
            results.update({
                'stiffness': slope,
                'r_squared': r_value ** 2,
                'intercept': intercept,
                'std_error': std_err,
                'success': True,
                'p_value': p_value
            })
            
        except Exception as e:
            results['error'] = str(e)
        
        return results


class AreaFunction:
    """Area function calculations for different indenter geometries"""
    
    def __init__(self, coefficients: Optional[Dict] = None):
        try:
            from ..core.standards import AreaFunctionCoefficients
        except ImportError:
            from ..core.standards import AreaFunctionCoefficients
        self.coefficients = coefficients or AreaFunctionCoefficients.PERFECT_BERKOVICH
    
    def calculate_contact_area(self, contact_depth: float) -> float:
        """
        Calculate contact area using area function
        
        Area function: A = C0*h_c^2 + C1*h_c + C2*h_c^{1/2} + ... + C8*h_c^{1/128}
        """
        if contact_depth <= 0:
            return 0.0
        
        h_c = contact_depth
        area = 0.0
        
        # Standard terms
        area += self.coefficients.get('C0', 0) * (h_c ** 2)
        area += self.coefficients.get('C1', 0) * h_c
        area += self.coefficients.get('C2', 0) * (h_c ** 0.5)
        area += self.coefficients.get('C3', 0) * (h_c ** 0.25)
        area += self.coefficients.get('C4', 0) * (h_c ** 0.125)
        area += self.coefficients.get('C5', 0) * (h_c ** (1/16))
        area += self.coefficients.get('C6', 0) * (h_c ** (1/32))
        area += self.coefficients.get('C7', 0) * (h_c ** (1/64))
        area += self.coefficients.get('C8', 0) * (h_c ** (1/128))
        
        return max(0, area)  # Area cannot be negative
    
    def update_coefficients(self, new_coefficients: Dict):
        """Update area function coefficients"""
        self.coefficients.update(new_coefficients)


def fit_multiple_methods(displacement: np.ndarray, load: np.ndarray) -> Dict[str, Dict]:
    """Fit unloading curve using multiple methods and compare results"""
    fitter = CurveFitter()
    linear_fitter = LinearFitter()
    
    results = {
        'oliver_pharr': fitter.fit_unloading_curve(displacement, load, 'oliver_pharr'),
        'power_law': fitter.fit_unloading_curve(displacement, load, 'power_law'),
        'linear': linear_fitter.fit_linear_stiffness(displacement, load),
        'best_method': 'none',
        'comparison': {}
    }
    
    # Determine best method based on R-squared
    best_r2 = 0
    best_method = 'none'
    
    for method, result in results.items():
        if method in ['comparison', 'best_method']:
            continue
        
        if result.get('success', False) and result.get('r_squared', 0) > best_r2:
            best_r2 = result['r_squared']
            best_method = method
    
    results['best_method'] = best_method
    
    # Add comparison metrics
    if best_method != 'none':
        results['comparison'] = {
            'best_r_squared': best_r2,
            'method_ranking': sorted(
                [(method, result.get('r_squared', 0)) 
                 for method, result in results.items() 
                 if method not in ['comparison', 'best_method'] and result.get('success', False)],
                key=lambda x: x[1], reverse=True
            )
        }
    
    return results
