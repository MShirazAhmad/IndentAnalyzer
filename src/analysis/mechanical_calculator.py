#!/usr/bin/env python3
"""
Mechanical Properties Calculation Module
ISO 14577-4:2016 compliant hardness and modulus calculations
"""

import numpy as np
from typing import Dict, Optional, Tuple

# Import from local modules
try:
    from ..core.standards import ISO14577Constants, MaterialProperties
    from .curve_fitting import AreaFunction
except ImportError:
    from ..core.standards import ISO14577Constants, MaterialProperties
    from .curve_fitting import AreaFunction


class MechanicalPropertiesCalculator:
    """Calculate mechanical properties from nanoindentation data"""
    
    def __init__(self, area_function: Optional[AreaFunction] = None):
        self.iso = ISO14577Constants()
        self.materials = MaterialProperties()
        self.area_function = area_function or AreaFunction()
    
    def calculate_hardness(self, max_load: float, contact_area: float) -> Dict[str, float]:
        """
        Calculate hardness according to ISO 14577-4:2016
        
        H = P_max / A_c
        
        Args:
            max_load: maximum applied load (mN)
            contact_area: projected contact area (nm²)
        
        Returns:
            Dict with hardness in GPa and related metrics
        """
        results = {
            'hardness_gpa': 0.0,
            'hardness_mpa': 0.0,
            'max_load_mn': max_load,
            'contact_area_nm2': contact_area,
            'valid': False
        }
        
        if contact_area <= 0 or max_load <= 0:
            results['error'] = "Invalid input: load and area must be positive"
            return results
        
        # Convert units: mN to N, nm² to m²
        load_n = max_load * 1e-3  # mN to N
        area_m2 = contact_area * 1e-18  # nm² to m²
        
        # Hardness in Pa
        hardness_pa = load_n / area_m2
        
        # Convert to GPa and MPa
        results.update({
            'hardness_gpa': hardness_pa * 1e-9,
            'hardness_mpa': hardness_pa * 1e-6,
            'hardness_pa': hardness_pa,
            'valid': True
        })
        
        return results
    
    def calculate_reduced_modulus(self, stiffness: float, contact_area: float) -> Dict[str, float]:
        """
        Calculate reduced modulus according to ISO 14577-4:2016
        
        E_r = (√π / 2) * (S / √A_c)
        
        Args:
            stiffness: contact stiffness (mN/nm)
            contact_area: projected contact area (nm²)
        
        Returns:
            Dict with reduced modulus and related metrics
        """
        results = {
            'reduced_modulus_gpa': 0.0,
            'reduced_modulus_pa': 0.0,
            'stiffness_mn_nm': stiffness,
            'contact_area_nm2': contact_area,
            'valid': False
        }
        
        if stiffness <= 0 or contact_area <= 0:
            results['error'] = "Invalid input: stiffness and area must be positive"
            return results
        
        # Convert units: mN/nm to N/m
        stiffness_n_m = stiffness * 1e6  # mN/nm to N/m
        area_m2 = contact_area * 1e-18  # nm² to m²
        
        # Reduced modulus calculation
        sqrt_area = np.sqrt(area_m2)
        reduced_modulus_pa = (np.sqrt(np.pi) / 2) * (stiffness_n_m / sqrt_area)
        
        results.update({
            'reduced_modulus_pa': reduced_modulus_pa,
            'reduced_modulus_gpa': reduced_modulus_pa * 1e-9,
            'valid': True
        })
        
        return results
    
    def calculate_sample_modulus(self, reduced_modulus: float,
                               indenter_material: str = 'diamond',
                               sample_poisson: float = 0.3) -> Dict[str, float]:
        """
        Calculate sample modulus from reduced modulus
        
        1/E_r = (1-ν_s²)/E_s + (1-ν_i²)/E_i
        
        Therefore: E_s = (1-ν_s²) / (1/E_r - (1-ν_i²)/E_i)
        
        Args:
            reduced_modulus: reduced modulus (Pa)
            indenter_material: indenter material ('diamond')
            sample_poisson: sample Poisson's ratio
        
        Returns:
            Dict with sample modulus and related metrics
        """
        results = {
            'sample_modulus_gpa': 0.0,
            'sample_modulus_pa': 0.0,
            'sample_poisson': sample_poisson,
            'indenter_material': indenter_material,
            'valid': False
        }
        
        if reduced_modulus <= 0:
            results['error'] = "Invalid reduced modulus"
            return results
        
        # Get indenter properties
        indenter_props = self.materials.get_material(indenter_material)
        if not indenter_props:
            results['error'] = f"Unknown indenter material: {indenter_material}"
            return results
        
        E_i = indenter_props['modulus']  # Pa
        nu_i = indenter_props['poisson']
        
        # Calculate sample modulus
        try:
            indenter_compliance = (1 - nu_i**2) / E_i
            total_compliance = 1 / reduced_modulus
            sample_compliance = total_compliance - indenter_compliance
            
            if sample_compliance <= 0:
                results['error'] = "Invalid sample compliance (negative or zero)"
                return results
            
            sample_modulus_pa = (1 - sample_poisson**2) / sample_compliance
            
            results.update({
                'sample_modulus_pa': sample_modulus_pa,
                'sample_modulus_gpa': sample_modulus_pa * 1e-9,
                'indenter_modulus_gpa': E_i * 1e-9,
                'indenter_poisson': nu_i,
                'valid': True
            })
            
        except Exception as e:
            results['error'] = f"Sample modulus calculation failed: {str(e)}"
        
        return results
    
    def calculate_all_properties(self, max_load: float, contact_depth: float,
                               stiffness: float, sample_poisson: float = 0.3,
                               indenter_material: str = 'diamond') -> Dict[str, any]:
        """
        Calculate all mechanical properties from basic measurements
        
        Args:
            max_load: maximum load (mN)
            contact_depth: contact depth (nm)
            stiffness: contact stiffness (mN/nm)
            sample_poisson: sample Poisson's ratio
            indenter_material: indenter material name
        
        Returns:
            Comprehensive dictionary of mechanical properties
        """
        results = {
            'input_parameters': {
                'max_load_mn': max_load,
                'contact_depth_nm': contact_depth,
                'stiffness_mn_nm': stiffness,
                'sample_poisson': sample_poisson,
                'indenter_material': indenter_material
            },
            'contact_area': {},
            'hardness': {},
            'reduced_modulus': {},
            'sample_modulus': {},
            'derived_properties': {},
            'overall_valid': False
        }
        
        # Calculate contact area
        contact_area = self.area_function.calculate_contact_area(contact_depth)
        results['contact_area'] = {
            'area_nm2': contact_area,
            'area_um2': contact_area * 1e-6,
            'depth_nm': contact_depth
        }
        
        if contact_area <= 0:
            results['contact_area']['error'] = "Invalid contact area"
            return results
        
        # Calculate hardness
        results['hardness'] = self.calculate_hardness(max_load, contact_area)
        
        # Calculate reduced modulus
        results['reduced_modulus'] = self.calculate_reduced_modulus(stiffness, contact_area)
        
        # Calculate sample modulus
        if results['reduced_modulus']['valid']:
            results['sample_modulus'] = self.calculate_sample_modulus(
                results['reduced_modulus']['reduced_modulus_pa'],
                indenter_material,
                sample_poisson
            )
        
        # Calculate derived properties
        if results['hardness']['valid'] and results['sample_modulus']['valid']:
            results['derived_properties'] = self._calculate_derived_properties(
                results['hardness']['hardness_pa'],
                results['sample_modulus']['sample_modulus_pa'],
                max_load,
                contact_area
            )
        
        # Overall validity
        results['overall_valid'] = (
            results['hardness']['valid'] and
            results['reduced_modulus']['valid'] and
            results['sample_modulus']['valid']
        )
        
        return results
    
    def _calculate_derived_properties(self, hardness: float, modulus: float,
                                    max_load: float, contact_area: float) -> Dict[str, float]:
        """Calculate derived mechanical properties"""
        results = {}
        
        # H/E ratio (important for wear resistance)
        results['h_over_e_ratio'] = hardness / modulus
        
        # Elastic work ratio (We/Wt)
        # This requires load-displacement data integration, approximated here
        
        # Yield strength estimation (Tabor relation: H ≈ 3σy for many materials)
        results['estimated_yield_strength_gpa'] = (hardness * 1e-9) / 3
        
        # Contact pressure (same as hardness for sharp indenters)
        results['contact_pressure_gpa'] = hardness * 1e-9
        
        # Indent volume (approximate)
        contact_depth_estimate = np.sqrt(contact_area / 24.56)  # For Berkovich
        results['indent_volume_nm3'] = contact_area * contact_depth_estimate / 3
        
        # Specific energy (energy per unit volume)
        work_done = max_load * 1e-3 * contact_depth_estimate * 1e-9  # J (approximate)
        if results['indent_volume_nm3'] > 0:
            results['specific_energy_j_m3'] = work_done / (results['indent_volume_nm3'] * 1e-27)
        
        return results


class TipCalibration:
    """Tip area function calibration using reference materials"""
    
    def __init__(self, reference_material: str = 'fused_silica'):
        self.reference_material = reference_material
        self.materials = MaterialProperties()
        self.ref_props = self.materials.get_material(reference_material)
        
        if not self.ref_props:
            raise ValueError(f"Unknown reference material: {reference_material}")
    
    def calibrate_area_function(self, measurements: list) -> Dict[str, any]:
        """
        Calibrate area function using reference material measurements
        
        Args:
            measurements: List of dicts with keys 'contact_depth', 'stiffness', 'max_load'
        
        Returns:
            Calibrated area function coefficients
        """
        results = {
            'coefficients': {},
            'r_squared': 0.0,
            'valid_measurements': 0,
            'total_measurements': len(measurements),
            'reference_material': self.reference_material,
            'success': False
        }
        
        if len(measurements) < 3:
            results['error'] = "Insufficient measurements for calibration (need at least 3)"
            return results
        
        # Extract valid measurements
        valid_data = []
        for meas in measurements:
            try:
                h_c = meas['contact_depth']
                S = meas['stiffness']
                P_max = meas['max_load']
                
                if h_c > 0 and S > 0 and P_max > 0:
                    # Calculate contact area from reference material modulus
                    E_r_ref = self._calculate_reference_reduced_modulus()
                    A_c = (np.pi / 4) * (S / E_r_ref)**2
                    valid_data.append({'h_c': h_c, 'A_c': A_c})
                    
            except (KeyError, TypeError, ValueError):
                continue
        
        results['valid_measurements'] = len(valid_data)
        
        if len(valid_data) < 3:
            results['error'] = "Insufficient valid measurements after filtering"
            return results
        
        # Fit area function: A = C0 * h_c^2 + C1 * h_c + C2 * h_c^0.5 + ...
        h_c_data = np.array([d['h_c'] for d in valid_data])
        A_c_data = np.array([d['A_c'] for d in valid_data])
        
        try:
            # Simple calibration: fit C0 (perfect Berkovich) and C1 (bluntness correction)
            from scipy.optimize import curve_fit
            
            def area_function_simple(h_c, C0, C1):
                return C0 * h_c**2 + C1 * h_c
            
            popt, pcov = curve_fit(area_function_simple, h_c_data, A_c_data)
            C0_fit, C1_fit = popt
            
            # Calculate R-squared
            A_fitted = area_function_simple(h_c_data, C0_fit, C1_fit)
            ss_res = np.sum((A_c_data - A_fitted)**2)
            ss_tot = np.sum((A_c_data - np.mean(A_c_data))**2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            results.update({
                'coefficients': {
                    'C0': C0_fit,
                    'C1': C1_fit,
                    'C2': 0.0,  # Can be extended for more sophisticated calibration
                    'C3': 0.0,
                    'C4': 0.0,
                    'C5': 0.0,
                    'C6': 0.0,
                    'C7': 0.0,
                    'C8': 0.0
                },
                'r_squared': r_squared,
                'parameter_errors': np.sqrt(np.diag(pcov)),
                'success': True
            })
            
        except Exception as e:
            results['error'] = f"Calibration fitting failed: {str(e)}"
        
        return results
    
    def _calculate_reference_reduced_modulus(self) -> float:
        """Calculate reduced modulus for reference material"""
        # For fused silica with diamond indenter
        E_s = self.ref_props['modulus']
        nu_s = self.ref_props['poisson']
        
        # Diamond properties
        diamond_props = self.materials.get_material('diamond')
        E_i = diamond_props['modulus']
        nu_i = diamond_props['poisson']
        
        # Calculate reduced modulus
        sample_compliance = (1 - nu_s**2) / E_s
        indenter_compliance = (1 - nu_i**2) / E_i
        total_compliance = sample_compliance + indenter_compliance
        
        return 1 / total_compliance


def analyze_property_trends(property_data: list, depth_range: Tuple[float, float] = None) -> Dict[str, any]:
    """
    Analyze trends in mechanical properties across multiple measurements
    
    Args:
        property_data: List of property dictionaries from multiple tests
        depth_range: Optional depth range to filter data (min_depth, max_depth) in nm
    
    Returns:
        Statistical analysis of property trends
    """
    results = {
        'statistics': {},
        'trends': {},
        'outliers': {},
        'recommendations': []
    }
    
    if not property_data:
        results['error'] = "No property data provided"
        return results
    
    # Extract properties of interest
    properties = ['hardness_gpa', 'sample_modulus_gpa', 'contact_depth_nm', 'h_over_e_ratio']
    
    for prop in properties:
        values = []
        depths = []
        
        for data in property_data:
            try:
                if prop == 'hardness_gpa':
                    val = data['hardness']['hardness_gpa']
                elif prop == 'sample_modulus_gpa':
                    val = data['sample_modulus']['sample_modulus_gpa']
                elif prop == 'contact_depth_nm':
                    val = data['input_parameters']['contact_depth_nm']
                elif prop == 'h_over_e_ratio':
                    val = data['derived_properties']['h_over_e_ratio']
                else:
                    continue
                
                depth = data['input_parameters']['contact_depth_nm']
                
                # Apply depth filter if specified
                if depth_range:
                    if depth < depth_range[0] or depth > depth_range[1]:
                        continue
                
                values.append(val)
                depths.append(depth)
                
            except (KeyError, TypeError):
                continue
        
        if len(values) >= 3:
            values = np.array(values)
            depths = np.array(depths)
            
            # Calculate statistics
            results['statistics'][prop] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'count': len(values),
                'cv_percent': (np.std(values) / np.mean(values)) * 100 if np.mean(values) != 0 else 0
            }
            
            # Detect outliers (values beyond 2 standard deviations)
            mean_val = np.mean(values)
            std_val = np.std(values)
            outlier_mask = np.abs(values - mean_val) > 2 * std_val
            
            if np.any(outlier_mask):
                results['outliers'][prop] = {
                    'indices': np.where(outlier_mask)[0].tolist(),
                    'values': values[outlier_mask].tolist(),
                    'depths': depths[outlier_mask].tolist()
                }
            
            # Analyze depth dependence
            if len(set(depths)) > 1:  # Need variation in depth
                correlation = np.corrcoef(depths, values)[0, 1]
                results['trends'][prop] = {
                    'depth_correlation': correlation,
                    'trend_description': _interpret_correlation(correlation)
                }


def _interpret_correlation(correlation: float) -> str:
    """Interpret correlation coefficient"""
    abs_corr = abs(correlation)
    direction = "increases" if correlation > 0 else "decreases"
    
    if abs_corr > 0.8:
        strength = "strongly"
    elif abs_corr > 0.5:
        strength = "moderately"
    elif abs_corr > 0.3:
        strength = "weakly"
    else:
        return "no clear trend"
    
    return f"{strength} {direction} with depth"

    return results
