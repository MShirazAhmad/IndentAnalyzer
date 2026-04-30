#!/usr/bin/env python3
"""
NIST Standard Calibration Methods
Based on "Review of Instrumented Indentation" NIST Guide
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy.stats import linregress
import warnings

# Import from local modules
try:
    from ..core.standards import ISO14577Constants, AnalysisConfig
    from ..analysis.mechanical_calculator import MechanicalPropertiesCalculator
except ImportError:
    from core.standards import ISO14577Constants, AnalysisConfig
    from analysis.mechanical_calculator import MechanicalPropertiesCalculator


class NISTCalibrationMethods:
    """
    Implementation of NIST standard calibration methods
    Based on Section 2.4 of the NIST Guide
    """
    
    def __init__(self):
        self.iso = ISO14577Constants()
        self.config = AnalysisConfig()
        self.properties_calc = MechanicalPropertiesCalculator()
    
    def calibrate_load_frame_compliance(self, reference_data: List[Dict]) -> Dict[str, any]:
        """
        Calibrate load-frame compliance using reference material
        
        NIST Guide Section 2.4: C_total = C_lf + C_sp
        C_sp = (√π / 2E_r) * (1 / √A)
        
        Args:
            reference_data: List of indentation results on reference material
                           Each dict should contain: max_load, contact_area, stiffness, modulus
        
        Returns:
            Dict with compliance calibration results
        """
        results = {
            'load_frame_compliance': 0.0,
            'compliance_uncertainty': 0.0,
            'r_squared': 0.0,
            'n_points': 0,
            'reference_material': 'fused_silica',
            'method': 'total_compliance_vs_inverse_sqrt_area',
            'valid': False,
            'warnings': [],
            'errors': []
        }
        
        if len(reference_data) < self.config.MIN_INDENTS_FOR_CALIBRATION:
            results['errors'].append(f"Need at least {self.config.MIN_INDENTS_FOR_CALIBRATION} reference indents")
            return results
        
        try:
            # Extract data arrays
            total_compliance = []
            inv_sqrt_area = []
            
            for data in reference_data:
                if data.get('stiffness', 0) > 0 and data.get('contact_area', 0) > 0:
                    C_total = 1.0 / data['stiffness']  # Total compliance
                    inv_sqrt_A = 1.0 / np.sqrt(data['contact_area'])
                    
                    total_compliance.append(C_total)
                    inv_sqrt_area.append(inv_sqrt_A)
            
            if len(total_compliance) < 3:
                results['errors'].append("Insufficient valid data points for calibration")
                return results
            
            # Linear regression: C_total = C_lf + (√π / 2E_r) * (1 / √A)
            slope, intercept, r_value, p_value, std_err = linregress(inv_sqrt_area, total_compliance)
            
            # Load-frame compliance is the y-intercept
            load_frame_compliance = intercept
            
            # Validate results
            if load_frame_compliance < 0:
                results['warnings'].append("Negative load-frame compliance indicates calibration issues")
            
            if r_value**2 < 0.9:
                results['warnings'].append(f"Low correlation (R² = {r_value**2:.3f}) indicates poor calibration")
            
            results.update({
                'load_frame_compliance': load_frame_compliance,
                'compliance_uncertainty': std_err,
                'r_squared': r_value**2,
                'n_points': len(total_compliance),
                'slope': slope,
                'p_value': p_value,
                'valid': True
            })
            
        except Exception as e:
            results['errors'].append(f"Calibration failed: {str(e)}")
        
        return results
    
    def calibrate_tip_area_function(self, reference_data: List[Dict], 
                                   known_modulus: float = None) -> Dict[str, any]:
        """
        Calibrate tip area function using reference material
        
        NIST Guide Section 2.4: Area function calibration
        A(h_c) = C₀h_c² + C₁h_c + C₂h_c^(1/2) + C₃h_c^(1/4) + ...
        
        Args:
            reference_data: List of indentation results with keys:
                          - contact_depth (m), stiffness (N/m), reduced_modulus (Pa)
            known_modulus: Known modulus of reference material (Pa)
        
        Returns:
            Dict with area function calibration results
        """
        results = {
            'area_coefficients': {},
            'theoretical_area': 24.56e-18,  # Perfect Berkovich in m²/m²
            'r_squared': 0.0,
            'modulus_consistency': 0.0,
            'valid': False,
            'warnings': [],
            'errors': [],
            'n_points': 0
        }
        
        if known_modulus is None:
            known_modulus = self.iso.FUSED_SILICA_MODULUS
            
        try:
            # Extract contact depths and calculate areas
            contact_depths = []
            calculated_areas = []
            
            for data in reference_data:
                if all(k in data for k in ['contact_depth', 'stiffness', 'reduced_modulus']):
                    h_c = data['contact_depth']
                    S = data['stiffness']
                    E_r = data['reduced_modulus']
                    
                    # Calculate area from stiffness using β = 1.034 for Berkovich
                    # A = (π/4) * (S/(β*E_r))²
                    if E_r > 0 and S > 0:
                        beta = 1.034  # Shape factor for Berkovich indenter
                        area = (np.pi / 4) * (S / (beta * E_r))**2
                        contact_depths.append(h_c)
                        calculated_areas.append(area)
            
            if len(contact_depths) < 5:
                results['errors'].append("Insufficient data for area function calibration (need ≥5 points)")
                return results
            
            # Convert to numpy arrays
            h_c_array = np.array(contact_depths)
            A_array = np.array(calculated_areas)
            results['n_points'] = len(h_c_array)
            
            # Method 1: Simple C₀ fit (perfect Berkovich)
            C0_simple = np.mean(A_array / h_c_array**2)
            
            # Method 2: Constrained area function fit with C₀ fixed to theoretical
            # A(h_c) = C₀h_c² + C₁h_c + C₂h_c^(1/2)
            # Fix C₀ to theoretical Berkovich and fit C₁, C₂ for tip imperfections
            try:
                from scipy.optimize import curve_fit
                
                def area_function_constrained(h, C1, C2):
                    """Area function with C₀ fixed to theoretical Berkovich"""
                    C0_fixed = 24.56e-18  # Fixed theoretical value in m²/m²
                    return C0_fixed * h**2 + C1 * h + C2 * h**0.5
                
                # Fit only C₁ and C₂, keeping C₀ theoretical
                popt, pcov = curve_fit(
                    area_function_constrained, 
                    h_c_array, A_array, 
                    p0=[0, 0],  # Initial guess for C₁, C₂
                    maxfev=5000
                )
                
                # Calculate fitted areas
                A_fitted = area_function_constrained(h_c_array, *popt)
                
                # Calculate R²
                ss_res = np.sum((A_array - A_fitted)**2)
                ss_tot = np.sum((A_array - np.mean(A_array))**2)
                r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                
                # Parameter uncertainties
                param_errors = np.sqrt(np.diag(pcov))
                
                # Use theoretical C₀ with fitted C₁, C₂
                C0_theoretical = 24.56e-18  # m²/m²
                C1_fitted = popt[0]
                C2_fitted = popt[1]
                
                results.update({
                    'area_coefficients': {
                        'C0': C0_theoretical,  # m²/m² (theoretical)
                        'C1': C1_fitted,       # m²/m (fitted)
                        'C2': C2_fitted,       # m²/m^0.5 (fitted)
                        'C0_nm2_per_nm2': 24.56,  # Exactly theoretical
                        'C1_nm2_per_nm': C1_fitted * 1e9,         # nm²/nm (fitted)
                        'C2_nm2_per_nm05': C2_fitted * 1e9 / np.sqrt(1e-9)  # nm²/nm^0.5 (fitted)
                    },
                    'uncertainties': {
                        'C0_error': 0,  # Fixed value
                        'C1_error': param_errors[0],
                        'C2_error': param_errors[1]
                    },
                    'r_squared': r_squared,
                    'simple_C0': C0_simple,
                    'simple_C0_nm2_per_nm2': C0_simple * 1e18,
                    'theoretical_C0_used': True,
                    'valid': r_squared > 0.90
                })
                
                # Quality assessment
                if r_squared > 0.98:
                    results['warnings'].append("Excellent fit quality (R² > 0.98)")
                elif r_squared > 0.95:
                    results['warnings'].append("Good fit quality (R² > 0.95)")
                elif r_squared > 0.90:
                    results['warnings'].append("Acceptable fit quality (R² > 0.90)")
                else:
                    results['warnings'].append("Poor fit quality (R² < 0.90) - check data")
                
                # Interpret fitted coefficients
                if abs(C1_fitted * 1e9) > 10:  # nm²/nm
                    results['warnings'].append(f"Significant C₁ = {C1_fitted * 1e9:.1f} nm²/nm indicates tip wear/blunting")
                else:
                    results['warnings'].append(f"Small C₁ = {C1_fitted * 1e9:.1f} nm²/nm indicates good tip condition")
                
                if abs(C2_fitted * 1e9 / np.sqrt(1e-9)) > 50:  # nm²/nm^0.5
                    results['warnings'].append(f"Significant C₂ = {C2_fitted * 1e9 / np.sqrt(1e-9):.1f} nm²/nm^0.5 indicates tip geometry deviation")
                else:
                    results['warnings'].append(f"Small C₂ = {C2_fitted * 1e9 / np.sqrt(1e-9):.1f} nm²/nm^0.5 indicates good tip geometry")
                
            except ImportError:
                # Fallback to linear algebra method
                X = np.column_stack([
                    h_c_array**2,      # C₀ term
                    h_c_array,         # C₁ term  
                    h_c_array**0.5     # C₂ term
                ])
                
                coefficients, residuals, rank, s = np.linalg.lstsq(X, A_array, rcond=None)
                
                results.update({
                    'area_coefficients': {
                        'C0': coefficients[0],
                        'C1': coefficients[1] if len(coefficients) > 1 else 0,
                        'C2': coefficients[2] if len(coefficients) > 2 else 0,
                        'C0_nm2_per_nm2': coefficients[0] * 1e18
                    },
                    'residuals_sum': residuals[0] if len(residuals) > 0 else 0,
                    'valid': True
                })
                
            except Exception as fit_error:
                results['errors'].append(f"Curve fitting failed: {str(fit_error)}")
                # Use simple C₀ as fallback
                results.update({
                    'area_coefficients': {
                        'C0': C0_simple,
                        'C1': 0,
                        'C2': 0,
                        'C0_nm2_per_nm2': C0_simple * 1e18
                    },
                    'valid': True
                })
            
        except Exception as e:
            results['errors'].append(f"Area function calibration failed: {str(e)}")
        
        return results
    
    def extract_tip_coefficients_from_file(self, xls_file_path: str, 
                                         reference_material: str = 'fused_silica') -> Dict[str, any]:
        """
        Convenience method to extract tip area function coefficients from XLS file
        
        Args:
            xls_file_path: Path to the XLS file containing reference measurements
            reference_material: Type of reference material ('fused_silica', 'aluminum', etc.)
        
        Returns:
            Dict with calibration results and extracted coefficients
        """
        # Import here to avoid circular imports
        try:
            from ..analysis.main_analyzer import NanoindentationAnalyzer
        except ImportError:
            from analysis.main_analyzer import NanoindentationAnalyzer
        
        results = {
            'file_analyzed': xls_file_path,
            'reference_material': reference_material,
            'coefficients': {},
            'quality_metrics': {},
            'valid': False,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Initialize analyzer
            analyzer = NanoindentationAnalyzer()
            
            # Analyze the XLS file
            analysis_results = analyzer.analyze_file(xls_file_path)
            
            if not analysis_results or 'tests' not in analysis_results:
                results['errors'].append("No valid test results found in XLS file")
                return results
            
            # Get reference material properties for calibration
            ref_material = self.iso.get_reference_material(reference_material)
            known_modulus = ref_material['modulus']
            known_poisson = ref_material.get('poisson', self.iso.FUSED_SILICA_POISSON)
            indenter_modulus = self.iso.DIAMOND_MODULUS
            indenter_poisson = self.iso.DIAMOND_POISSON

            # Reduced modulus for the chosen reference material (constant for this run)
            ref_compliance = ((1 - known_poisson**2) / known_modulus) + ((1 - indenter_poisson**2) / indenter_modulus)
            reference_reduced_modulus = (1.0 / ref_compliance) if ref_compliance > 0 else known_modulus

            # Extract calibration data using unloading-fit criteria
            calibration_data = []
            
            for test_name, test_data in analysis_results['tests'].items():
                curve_fit = test_data.get('curve_fitting', {})
                if not curve_fit.get('success', False):
                    continue

                contact_depth_nm = curve_fit.get('contact_depth')
                stiffness_mn_nm = curve_fit.get('stiffness')

                if contact_depth_nm is None or stiffness_mn_nm is None:
                    continue
                if contact_depth_nm <= 0 or stiffness_mn_nm <= 0:
                    continue

                # Convert units for NIST calibration
                test_calibration_data = {
                    'contact_depth': contact_depth_nm * 1e-9,  # nm to m
                    'stiffness': stiffness_mn_nm * 1e6,        # mN/nm → N/m (1 mN/nm = 10⁶ N/m)
                    'reduced_modulus': reference_reduced_modulus,  # Pa (reference material)
                    'test_name': test_name
                }
                calibration_data.append(test_calibration_data)
            
            if len(calibration_data) < 5:
                results['errors'].append(f"Insufficient valid unloading fits found: {len(calibration_data)} (need ≥5)")
                return results
            
            # Perform tip area function calibration
            calibration_results = self.calibrate_tip_area_function(
                reference_data=calibration_data,
                known_modulus=known_modulus
            )
            
            # Extract key results
            coeffs = calibration_results.get('area_coefficients', {})
            has_coefficients = all(k in coeffs for k in ['C0', 'C1', 'C2'])
            calibration_is_high_quality = calibration_results.get('valid', False)

            if has_coefficients:
                results.update({
                    'coefficients': {
                        'C0_nm2_per_nm2': coeffs.get('C0_nm2_per_nm2', coeffs.get('C0', 0) * 1e18),
                        'C1_nm2_per_nm': coeffs.get('C1_nm2_per_nm', coeffs.get('C1', 0) * 1e9),
                        'C2_nm2_per_nm05': coeffs.get('C2_nm2_per_nm05', coeffs.get('C2', 0) * 1e9 / np.sqrt(1e-9)),
                        'C0_SI': coeffs.get('C0', 0),  # m²/m²
                        'C1_SI': coeffs.get('C1', 0),  # m²/m
                        'C2_SI': coeffs.get('C2', 0)   # m²/m^0.5
                    },
                    'quality_metrics': {
                        'r_squared': calibration_results.get('r_squared', 0),
                        'n_data_points': calibration_results.get('n_points', 0),
                        'simple_C0_nm2_per_nm2': calibration_results.get('simple_C0_nm2_per_nm2', 0)
                    },
                    'valid': True,
                    'warnings': calibration_results.get('warnings', []),
                    'errors': calibration_results.get('errors', [])
                })
                if not calibration_is_high_quality:
                    results['warnings'].append(
                        "Calibration coefficients were generated, but fit quality is below the preferred threshold."
                    )
            else:
                results['errors'].extend(calibration_results.get('errors', []))
                results['warnings'].extend(calibration_results.get('warnings', []))
                if not results['errors']:
                    results['errors'].append("Calibration failed: no area-function coefficients were produced.")
        
        except Exception as e:
            results['errors'].append(f"Tip coefficient extraction failed: {str(e)}")
        
        return results
    
    def validate_reference_material(self, measurement_data: List[Dict],
                                   expected_modulus: float,
                                   expected_hardness: float) -> Dict[str, any]:
        """
        Validate measurements against known reference material properties
        
        Args:
            measurement_data: List of measurement results
            expected_modulus: Expected modulus (GPa)
            expected_hardness: Expected hardness (GPa)
        
        Returns:
            Dict with validation results
        """
        results = {
            'measured_modulus_mean': 0.0,
            'measured_modulus_std': 0.0,
            'measured_hardness_mean': 0.0,
            'measured_hardness_std': 0.0,
            'modulus_deviation_percent': 0.0,
            'hardness_deviation_percent': 0.0,
            'modulus_within_tolerance': False,
            'hardness_within_tolerance': False,
            'n_measurements': 0,
            'valid': False
        }
        
        if not measurement_data:
            return results
        
        # Extract modulus and hardness values
        moduli = [d.get('reduced_modulus_gpa', 0) for d in measurement_data if d.get('reduced_modulus_gpa', 0) > 0]
        hardnesses = [d.get('hardness_gpa', 0) for d in measurement_data if d.get('hardness_gpa', 0) > 0]
        
        if not moduli or not hardnesses:
            return results
        
        # Calculate statistics
        modulus_mean = np.mean(moduli)
        modulus_std = np.std(moduli)
        hardness_mean = np.mean(hardnesses)
        hardness_std = np.std(hardnesses)
        
        # Calculate deviations
        modulus_deviation = abs(modulus_mean - expected_modulus) / expected_modulus * 100
        hardness_deviation = abs(hardness_mean - expected_hardness) / expected_hardness * 100
        
        # Check tolerances
        tolerance = self.config.REFERENCE_MATERIAL_MODULUS_TOLERANCE * 100  # Convert to percentage
        
        results.update({
            'measured_modulus_mean': modulus_mean,
            'measured_modulus_std': modulus_std,
            'measured_hardness_mean': hardness_mean,
            'measured_hardness_std': hardness_std,
            'modulus_deviation_percent': modulus_deviation,
            'hardness_deviation_percent': hardness_deviation,
            'modulus_within_tolerance': modulus_deviation <= tolerance,
            'hardness_within_tolerance': hardness_deviation <= tolerance,
            'n_measurements': len(measurement_data),
            'valid': True
        })
        
        return results
    
    def assess_measurement_uncertainty(self, measurement_data: List[Dict]) -> Dict[str, any]:
        """
        Assess measurement uncertainty according to NIST guidelines
        
        Args:
            measurement_data: List of measurement results
        
        Returns:
            Dict with uncertainty assessment
        """
        results = {
            'modulus_uncertainty_type_a': 0.0,
            'hardness_uncertainty_type_a': 0.0,
            'modulus_cv_percent': 0.0,
            'hardness_cv_percent': 0.0,
            'measurement_precision': 'unknown',
            'valid': False
        }
        
        if len(measurement_data) < 3:
            return results
        
        # Extract valid measurements
        moduli = [d.get('reduced_modulus_gpa', 0) for d in measurement_data if d.get('reduced_modulus_gpa', 0) > 0]
        hardnesses = [d.get('hardness_gpa', 0) for d in measurement_data if d.get('hardness_gpa', 0) > 0]
        
        if len(moduli) < 3 or len(hardnesses) < 3:
            return results
        
        # Type A uncertainty (statistical)
        modulus_mean = np.mean(moduli)
        modulus_std = np.std(moduli, ddof=1)  # Sample standard deviation
        modulus_uncertainty_a = modulus_std / np.sqrt(len(moduli))
        
        hardness_mean = np.mean(hardnesses)
        hardness_std = np.std(hardnesses, ddof=1)
        hardness_uncertainty_a = hardness_std / np.sqrt(len(hardnesses))
        
        # Coefficient of variation (CV)
        modulus_cv = (modulus_std / modulus_mean) * 100 if modulus_mean > 0 else 0
        hardness_cv = (hardness_std / hardness_mean) * 100 if hardness_mean > 0 else 0
        
        # Assess precision
        if modulus_cv <= 5 and hardness_cv <= 5:
            precision = 'excellent'
        elif modulus_cv <= 10 and hardness_cv <= 10:
            precision = 'good'
        elif modulus_cv <= 20 and hardness_cv <= 20:
            precision = 'acceptable'
        else:
            precision = 'poor'
        
        results.update({
            'modulus_uncertainty_type_a': modulus_uncertainty_a,
            'hardness_uncertainty_type_a': hardness_uncertainty_a,
            'modulus_cv_percent': modulus_cv,
            'hardness_cv_percent': hardness_cv,
            'measurement_precision': precision,
            'n_measurements': len(measurement_data),
            'valid': True
        })
        
        return results
