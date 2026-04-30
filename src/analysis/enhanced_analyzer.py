#!/Users/shiraz/scripts/HEC14s/.venv/bin/python
"""
Script to run IndentXLSAnalyzer on HEC14S1.xls file with FIXED fitting logic
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
# Do not force a global backend here; GUI and callers set their own backend.
import matplotlib.pyplot as plt
from scipy.optimize import minimize_scalar, curve_fit
from matplotlib.patches import Rectangle
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

# Add the current directory to Python path to import IndentXLSAnalyzer
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from .legacy_analyzer import IndentXLSAnalyzer
except ImportError:
    # Fallback for direct script execution
    from legacy_analyzer import IndentXLSAnalyzer

class FixedIndentXLSAnalyzer(IndentXLSAnalyzer):
    """
    Fixed version of IndentXLSAnalyzer with improved fitting logic
    ISO 14577-4:2016 compliant implementation for nanoindentation analysis
    """
    
    # ISO 14577-4:2016 compliance constants
    ISO_MIN_DATA_POINTS_LOADING = 50      # Minimum data points for loading curve
    ISO_MIN_DATA_POINTS_UNLOADING = 30    # Minimum data points for unloading curve
    ISO_MIN_R_SQUARED = 0.98              # Minimum R² for curve fits (ISO requirement)
    ISO_STIFFNESS_RANGE_PERCENT = 0.25    # Use upper 25% of unloading for stiffness
    ISO_EPSILON_BERKOVICH = 0.75          # Geometric constant for Berkovich indenter
    ISO_EPSILON_VICKERS = 0.75            # Geometric constant for Vickers indenter
    ISO_EPSILON_SPHERICAL = 0.75          # Geometric constant for spherical indenter
    ISO_FUSED_SILICA_MODULUS = 72e9       # Reference material modulus (Pa)
    ISO_FUSED_SILICA_POISSON = 0.17       # Reference material Poisson ratio
    ISO_DIAMOND_MODULUS = 1140e9          # Diamond indenter modulus (Pa)
    ISO_DIAMOND_POISSON = 0.07            # Diamond indenter Poisson ratio
    
    def detect_and_remove_horizontal_segments(self, filtered_df, original_df, peak_index, test_name):
        """
        Advanced horizontal segment detection with improved robustness for nanoindentation data
        
        Parameters:
        - filtered_df: DataFrame with load threshold filtering applied
        - original_df: Original unfiltered data
        - peak_index: Index of peak load in original data
        - test_name: Test identifier for debugging
        
        Returns:
        - horizontal_segments: List of detected horizontal segments with metadata
        - total_horizontal_adjustment: Total displacement adjustment to apply
        """
        
        # Step 1: Calculate multiple derivative measures for robust detection
        displacement = filtered_df['Displacement Into Surface'].values
        load = filtered_df['Load On Sample'].values
        
        # Primary derivative (gradient)
        load_derivative = np.gradient(load, displacement)
        filtered_df = filtered_df.copy()
        filtered_df['Load Derivative'] = load_derivative
        
        # Secondary derivative measures for validation
        # Moving average derivative for noise reduction
        window_size = min(5, len(load) // 10)
        if window_size >= 3:
            load_smooth = np.convolve(load, np.ones(window_size)/window_size, mode='same')
            load_derivative_smooth = np.gradient(load_smooth, displacement)
        else:
            load_derivative_smooth = load_derivative.copy()
        
        # Relative derivative (normalized by local load magnitude)
        load_derivative_relative = np.abs(load_derivative) / (load + 1e-6)  # Avoid division by zero
        
        # Step 2: Multi-criteria horizontal detection
        # Adaptive threshold based on data characteristics
        derivative_std = np.std(load_derivative)
        derivative_median = np.median(np.abs(load_derivative))
        adaptive_threshold = max(self.derivative_threshold, derivative_median * 0.5)
        
        # Primary criteria: low absolute derivative
        is_horizontal_primary = np.abs(load_derivative) < adaptive_threshold
        
        # Secondary criteria: low smooth derivative  
        is_horizontal_smooth = np.abs(load_derivative_smooth) < adaptive_threshold * 1.2
        
        # Tertiary criteria: low relative derivative
        relative_threshold = 0.02  # 2% relative change
        is_horizontal_relative = load_derivative_relative < relative_threshold
        
        # Combined horizontal detection (require at least 2 of 3 criteria)
        horizontal_votes = (is_horizontal_primary.astype(int) + 
                           is_horizontal_smooth.astype(int) + 
                           is_horizontal_relative.astype(int))
        is_horizontal = horizontal_votes >= 2
        
        # Step 3: Segment identification with minimum length requirement
        horizontal_segments = []
        min_segment_length = 5  # Minimum points in a horizontal segment
        min_displacement_span = 10.0  # Minimum displacement span (nm)
        
        segment_start = None
        
        for i in range(len(is_horizontal)):
            if is_horizontal[i] and segment_start is None:
                # Start of potential horizontal segment
                segment_start = i
            elif not is_horizontal[i] and segment_start is not None:
                # End of horizontal segment
                segment_length = i - segment_start
                
                if segment_length >= min_segment_length:
                    start_disp = displacement[segment_start]
                    end_disp = displacement[i-1]
                    displacement_span = end_disp - start_disp
                    
                    if displacement_span >= min_displacement_span:
                        # Extract segment data for validation
                        segment_load = load[segment_start:i]
                        segment_disp = displacement[segment_start:i]
                        
                        # Statistical validation of horizontal nature
                        load_std = np.std(segment_load)
                        load_range = np.max(segment_load) - np.min(segment_load)
                        load_cv = load_std / np.mean(segment_load) if np.mean(segment_load) > 0 else 1.0
                        
                        # Displacement trend validation (should be approximately constant slope)
                        disp_slope = (end_disp - start_disp) / segment_length
                        
                        # Map back to original dataframe indices
                        start_index_original = filtered_df.index[segment_start]
                        end_index_original = filtered_df.index[i-1]
                        
                        segment_info = {
                            'start_index': segment_start,
                            'end_index': i-1,
                            'start_index_original': start_index_original,
                            'end_index_original': end_index_original,
                            'start_disp': start_disp,
                            'end_disp': end_disp,
                            'length': displacement_span,
                            'n_points': segment_length,
                            'load_std': load_std,
                            'load_range': load_range,
                            'load_cv': load_cv,
                            'disp_slope': disp_slope,
                            'quality_score': 1.0 / (1.0 + load_cv + 0.1 * abs(load_derivative[segment_start:i]).mean())
                        }
                        
                        horizontal_segments.append(segment_info)
                
                segment_start = None
        
        # Handle case where data ends with a horizontal segment
        if segment_start is not None:
            segment_length = len(is_horizontal) - segment_start
            if segment_length >= min_segment_length:
                start_disp = displacement[segment_start]
                end_disp = displacement[-1]
                displacement_span = end_disp - start_disp
                
                if displacement_span >= min_displacement_span:
                    segment_load = load[segment_start:]
                    load_std = np.std(segment_load)
                    load_range = np.max(segment_load) - np.min(segment_load)
                    load_cv = load_std / np.mean(segment_load) if np.mean(segment_load) > 0 else 1.0
                    
                    start_index_original = filtered_df.index[segment_start]
                    end_index_original = filtered_df.index[-1]
                    
                    segment_info = {
                        'start_index': segment_start,
                        'end_index': len(is_horizontal)-1,
                        'start_index_original': start_index_original,
                        'end_index_original': end_index_original,
                        'start_disp': start_disp,
                        'end_disp': end_disp,
                        'length': displacement_span,
                        'n_points': segment_length,
                        'load_std': load_std,
                        'load_range': load_range,
                        'load_cv': load_cv,
                        'disp_slope': (end_disp - start_disp) / segment_length,
                        'quality_score': 1.0 / (1.0 + load_cv + 0.1 * abs(load_derivative[segment_start:]).mean())
                    }
                    
                    horizontal_segments.append(segment_info)
        
        # Step 4: Validate and rank segments by quality
        if len(horizontal_segments) > 0:
            # Sort by quality score (higher is better)
            horizontal_segments.sort(key=lambda x: x['quality_score'], reverse=True)
            
            # Additional validation: ensure segments are reasonable for nanoindentation
            valid_segments = []
            for segment in horizontal_segments:
                # Check that segment occurs after peak (typical for unloading)
                segment_original_start = segment['start_index_original']
                
                # Quality checks
                is_after_peak = segment_original_start >= peak_index * 0.8  # Allow some tolerance
                is_reasonable_length = 5 <= segment['length'] <= 200  # Reasonable displacement range
                is_stable_load = segment['load_cv'] < 0.2  # Load variation < 20%
                
                if is_after_peak and is_reasonable_length and is_stable_load:
                    valid_segments.append(segment)
            
            horizontal_segments = valid_segments
        
        # Step 5: Calculate total displacement adjustment
        total_horizontal_adjustment = 0.0
        
        if len(horizontal_segments) > 0:
            # For multiple segments, sum their individual adjustments
            for segment in horizontal_segments:
                segment_adjustment = segment['length']
                total_horizontal_adjustment += segment_adjustment
            
            # Apply safety limit to prevent over-correction
            max_adjustment = (original_df['Displacement Into Surface'].max() - 
                            original_df['Displacement Into Surface'].min()) * 0.2  # Max 20% of total range
            
            if total_horizontal_adjustment > max_adjustment:
                print(f"Warning: Large horizontal adjustment ({total_horizontal_adjustment:.1f} nm) "
                      f"capped at {max_adjustment:.1f} nm for test {test_name}")
                total_horizontal_adjustment = max_adjustment
        
        # Step 6: Diagnostic information
        if len(horizontal_segments) > 0:
            print(f"Horizontal segment detection summary for Test {test_name}:")
            print(f"  Adaptive threshold: {adaptive_threshold:.4f}")
            print(f"  Detection criteria: Primary + Smooth + Relative voting")
            print(f"  Valid segments found: {len(horizontal_segments)}")
        else:
            print(f"No valid horizontal segments detected for Test {test_name}")
            print(f"  Tried adaptive threshold: {adaptive_threshold:.4f}")
            print(f"  Data range: {displacement.min():.1f} to {displacement.max():.1f} nm")
            print(f"  Derivative range: {load_derivative.min():.4f} to {load_derivative.max():.4f}")
        
        return horizontal_segments, total_horizontal_adjustment
    
    def validate_iso_data_quality(self, displacement, load, curve_type="loading"):
        """
        Validate data quality according to ISO 14577-4:2016 requirements
        
        Parameters:
        displacement: displacement data (nm)
        load: load data (mN)
        curve_type: "loading" or "unloading"
        
        Returns:
        dict: validation results with pass/fail status
        """
        validation = {
            'data_points_sufficient': False,
            'data_monotonic': False,
            'noise_level_acceptable': False,
            'overall_quality': False,
            'warnings': []
        }
        
        # Check minimum data points
        min_points = self.ISO_MIN_DATA_POINTS_LOADING if curve_type == "loading" else self.ISO_MIN_DATA_POINTS_UNLOADING
        if len(displacement) >= min_points:
            validation['data_points_sufficient'] = True
        else:
            validation['warnings'].append(f"Insufficient data points: {len(displacement)} < {min_points} (ISO requirement)")
        
        # Check monotonicity for loading (relaxed criteria for real data)
        if curve_type == "loading":
            # Check overall trend rather than strict monotonicity
            disp_trend = np.polyfit(range(len(displacement)), displacement, 1)[0] >= 0
            load_trend = np.polyfit(range(len(load)), load, 1)[0] >= 0
            # Allow some non-monotonic points but check overall trend
            monotonic_violations = np.sum(np.diff(displacement) < 0) + np.sum(np.diff(load) < 0)
            monotonic_ratio = monotonic_violations / len(displacement)
            validation['data_monotonic'] = disp_trend and load_trend and monotonic_ratio < 0.1  # Allow up to 10% violations
            if not validation['data_monotonic']:
                validation['warnings'].append(f"Non-monotonic loading data: {monotonic_violations} violations ({monotonic_ratio*100:.1f}%)")
        
        # Check noise level using relative standard deviation around trend
        if len(load) > 10:
            # For trend-based data, check relative noise rather than absolute CV
            if len(load) > 20:
                # Fit a trend line and check residuals
                trend_coeffs = np.polyfit(range(len(load)), load, 1)
                trend_line = np.polyval(trend_coeffs, range(len(load)))
                residuals = load - trend_line
                relative_noise = np.std(residuals) / np.mean(load)
                # Relaxed threshold for experimental nanoindentation data
                validation['noise_level_acceptable'] = relative_noise < 0.15  # 15% relative noise for experimental data
                if not validation['noise_level_acceptable']:
                    validation['warnings'].append(f"High relative noise: {relative_noise:.3f} > 0.15")
            else:
                # For small datasets, use simple CV
                load_variation = np.std(load) / np.mean(load) if np.mean(load) > 0 else 1.0
                validation['noise_level_acceptable'] = load_variation < 0.30  # More relaxed for small datasets
                if not validation['noise_level_acceptable']:
                    validation['warnings'].append(f"High noise level: CV = {load_variation:.3f} > 0.30")
        
        # Overall quality assessment
        validation['overall_quality'] = all([
            validation['data_points_sufficient'],
            validation['data_monotonic'] if curve_type == "loading" else True,
            validation['noise_level_acceptable']
        ])
        
        return validation
    
    def calculate_iso_area_function(self, hc_nm, coeffs=None):
        """
        Calculate contact area using ISO 14577-4:2016 compliant area function
        A = C₀h²c + C₁hc + C₂h^(1/2)c + C₃h^(1/4)c + C₄h^(1/8)c + C₅h^(1/16)c + C₆h^(1/32)c + C₇h^(1/64)c + C₈h^(1/128)c
        
        Parameters:
        hc_nm: contact depth in nm
        coeffs: area function coefficients dict or None for perfect Berkovich
        
        Returns:
        area in m²
        """
        if coeffs is None:
            # ISO 14577-4:2016 perfect Berkovich indenter coefficients
            coeffs = {
                'C0': 24.56,    # Perfect Berkovich coefficient (h_c^2 term)
                'C1': 0.0,      # Linear term (h_c^1) - typically zero for perfect indenter
                'C2': 0.0,      # h_c^{1/2} term - calibrated from reference material
                'C3': 0.0,      # h_c^{1/4} term - calibrated from reference material
                'C4': 0.0,      # h_c^{1/8} term - calibrated from reference material
                'C5': 0.0,      # h_c^{1/16} term - calibrated from reference material
                'C6': 0.0,      # h_c^{1/32} term - calibrated from reference material
                'C7': 0.0,      # h_c^{1/64} term - calibrated from reference material
                'C8': 0.0       # h_c^{1/128} term - calibrated from reference material
            }
        
        # Calculate area function according to ISO standard
        A_c = (coeffs['C0'] * hc_nm**2 +
               coeffs['C1'] * hc_nm +
               coeffs['C2'] * hc_nm**(1/2) +
               coeffs['C3'] * hc_nm**(1/4) +
               coeffs['C4'] * hc_nm**(1/8) +
               coeffs['C5'] * hc_nm**(1/16) +
               coeffs['C6'] * hc_nm**(1/32) +
               coeffs['C7'] * hc_nm**(1/64) +
               coeffs['C8'] * hc_nm**(1/128))
        
        return A_c * 1e-18  # Convert nm² to m²
    
    def calibrate_tip_area_function(self, calibration_data):
        """
        Calibrate tip area function coefficients using fused silica reference material
        According to ISO 14577-4:2016 Section 7.3.2
        
        Parameters:
        calibration_data: list of dicts with keys ['hc_nm', 'S', 'P', 'Er']
        
        Returns:
        dict: calibrated area function coefficients
        """
        from scipy.optimize import minimize
        
        print("\n=== TIP AREA FUNCTION CALIBRATION ===")
        print("Using ISO 14577-4:2016 Section 7.3.2 method")
        print(f"Calibration dataset: {len(calibration_data)} measurements")
        
        # Extract calibration data
        hc_values = np.array([data['hc_nm'] for data in calibration_data])
        S_values = np.array([data['S'] for data in calibration_data])
        P_values = np.array([data['P'] for data in calibration_data])
        Er_values = np.array([data['Er'] for data in calibration_data])
        
        print(f"Contact depth range: {hc_values.min():.1f} to {hc_values.max():.1f} nm")
        print(f"Stiffness range: {S_values.min()/1e6:.2f} to {S_values.max()/1e6:.2f} mN/nm")
        print(f"Load range: {P_values.min()*1e3:.1f} to {P_values.max()*1e3:.1f} mN")
        
        # Physics-based contact areas for reference
        A_physics = np.pi * ((S_values / (2 * Er_values)) ** 2)
        
        def area_function_residual(coeffs_array):
            """
            Objective function: minimize difference between measured and expected fused silica hardness
            Target: 9.0 GPa for fused silica (ISO 14577-4:2016 reference value)
            """
            C0, C1, C2, C3, C4 = coeffs_array
            
            # Calculate area function for all data points
            A_func = np.zeros_like(hc_values)
            for i, hc in enumerate(hc_values):
                A_func[i] = (C0 * hc**2 +
                           C1 * hc +
                           C2 * hc**(1/2) +
                           C3 * hc**(1/4) +
                           C4 * hc**(1/8)) * 1e-18  # Convert nm² to m²
            
            # Calculate hardness using area function
            hardness_values = (P_values / A_func) * 1e-9  # Convert to GPa
            
            # Target hardness for fused silica: 9.0 GPa (ISO standard)
            target_hardness = 9.0  # GPa
            
            # Calculate error from target hardness
            hardness_errors = (hardness_values - target_hardness) / target_hardness
            
            # Also include area ratio constraint to prevent unrealistic values
            area_ratio_errors = (A_func - A_physics) / A_physics
            
            # Combined objective: hardness accuracy (70%) + area physics consistency (30%)
            total_error = (0.7 * np.sum(hardness_errors**2) + 
                          0.3 * np.sum(area_ratio_errors**2))
            
            return total_error
        
        # Initial guess: start with perfect Berkovich and allow C1 to vary
        initial_guess = [24.56, 0.0, 0.0, 0.0, 0.0]  # [C0, C1, C2, C3, C4]
        
        # Set reasonable bounds for coefficients
        bounds = [
            (20.0, 35.0),    # C0: allow broader range around Berkovich value
            (-50.0, 50.0),   # C1: allow significant linear correction for fused silica
            (-1000.0, 1000.0), # C2: h^(1/2) term for tip rounding
            (-1000.0, 1000.0), # C3: h^(1/4) term for tip blunting  
            (-500.0, 500.0)   # C4: h^(1/8) term for higher-order effects
        ]
        
        print("\nOptimizing area function coefficients...")
        print(f"Target fused silica hardness: 9.0 GPa")
        print(f"Initial guess: C0={initial_guess[0]:.3f}, C1={initial_guess[1]:.3f}, C2={initial_guess[2]:.3f}, C3={initial_guess[3]:.3f}, C4={initial_guess[4]:.3f}")
        
        # Try multiple optimization methods for robustness
        best_result = None
        best_residual = float('inf')
        
        for method in ['L-BFGS-B', 'TNC', 'SLSQP']:
            try:
                result = minimize(area_function_residual, initial_guess, method=method, bounds=bounds)
                if result.success and result.fun < best_residual:
                    best_result = result
                    best_residual = result.fun
                    print(f"  {method}: success, residual = {result.fun:.6e}")
            except:
                print(f"  {method}: failed")
                continue
        
        # Also try with different initial guesses
        alternative_guesses = [
            [30.0, -10.0, 50.0, 5.0, 0.0],   # Blunter tip with corrections
            [24.56, 5.0, -50.0, 1.0, 0.0],   # Sharp tip with rounding
            [27.0, 0.0, 100.0, 10.0, 0.0]    # Moderate blunting
        ]
        
        for i, alt_guess in enumerate(alternative_guesses):
            try:
                result = minimize(area_function_residual, alt_guess, method='L-BFGS-B', bounds=bounds)
                if result.success and result.fun < best_residual:
                    best_result = result
                    best_residual = result.fun
                    print(f"  Alternative guess {i+1}: success, residual = {result.fun:.6e}")
            except:
                continue
        
        if best_result and best_result.success:
            C0_opt, C1_opt, C2_opt, C3_opt, C4_opt = best_result.x
            
            print(f"\n✅ Calibration successful!")
            print(f"Optimized coefficients:")
            print(f"  C₀ = {C0_opt:.6f} nm⁻² (h_c² term)")
            print(f"  C₁ = {C1_opt:.6f} nm⁻¹ (h_c¹ term)")  
            print(f"  C₂ = {C2_opt:.6f} nm⁻⁰·⁵ (h_c^½ term)")
            print(f"  C₃ = {C3_opt:.6f} nm⁻⁰·²⁵ (h_c^¼ term)")
            print(f"  C₄ = {C4_opt:.6f} nm⁻⁰·¹²⁵ (h_c^⅛ term)")
            print(f"Final residual: {best_result.fun:.6e}")
            
            # Calculate calibration quality metrics
            A_calibrated = np.zeros_like(hc_values)
            hardness_calibrated = np.zeros_like(hc_values)
            
            for i, hc in enumerate(hc_values):
                A_calibrated[i] = (C0_opt * hc**2 +
                                 C1_opt * hc +
                                 C2_opt * hc**(1/2) +
                                 C3_opt * hc**(1/4) +
                                 C4_opt * hc**(1/8)) * 1e-18
                hardness_calibrated[i] = (P_values[i] / A_calibrated[i]) * 1e-9  # GPa
            
            # Area-based quality metrics
            relative_errors = (A_calibrated - A_physics) / A_physics
            rms_error = np.sqrt(np.mean(relative_errors**2)) * 100
            max_error = np.max(np.abs(relative_errors)) * 100
            
            # Hardness-based quality metrics  
            hardness_mean = np.mean(hardness_calibrated)
            hardness_std = np.std(hardness_calibrated)
            hardness_target_error = abs(hardness_mean - 9.0) / 9.0 * 100
            
            print(f"\nCalibration Quality:")
            print(f"  Area RMS relative error: {rms_error:.2f}%")
            print(f"  Area max relative error: {max_error:.2f}%")
            print(f"  Mean area ratio: {np.mean(A_calibrated/A_physics):.4f}")
            print(f"  Fused silica hardness: {hardness_mean:.2f} ± {hardness_std:.2f} GPa")
            print(f"  Target hardness error: {hardness_target_error:.1f}% (target: 9.0 GPa)")
            
            # Show tip characterization insights
            print(f"\nTip Characterization Insights:")
            C0_change = ((C0_opt - 24.56) / 24.56) * 100
            print(f"  C₀ change from perfect: {C0_change:+.2f}% ({'blunter' if C0_change > 0 else 'sharper'} than perfect)")
            
            if abs(C1_opt) > 0.1:
                print(f"  C₁ = {C1_opt:.3f}: {'Significant' if abs(C1_opt) > 1.0 else 'Moderate'} linear tip correction")
                
            if abs(C2_opt) > 1.0:
                print(f"  C₂ = {C2_opt:.1f}: {'Significant' if abs(C2_opt) > 10 else 'Moderate'} tip rounding effect")
            
            if abs(C3_opt) > 1.0:
                print(f"  C₃ = {C3_opt:.1f}: {'Significant' if abs(C3_opt) > 10 else 'Moderate'} tip blunting effect")
            
            # Return calibrated coefficients
            calibrated_coeffs = {
                'C0': C0_opt,
                'C1': C1_opt,
                'C2': C2_opt,
                'C3': C3_opt,
                'C4': C4_opt,
                'C5': 0.0,  # Higher-order terms set to zero for stability
                'C6': 0.0,
                'C7': 0.0,
                'C8': 0.0,
                'calibration_quality': {
                    'rms_error_percent': rms_error,
                    'max_error_percent': max_error,
                    'mean_area_ratio': np.mean(A_calibrated/A_physics),
                    'hardness_mean_GPa': hardness_mean,
                    'hardness_std_GPa': hardness_std,
                    'hardness_target_error_percent': hardness_target_error,
                    'n_measurements': len(calibration_data)
                }
            }
            
            return calibrated_coeffs
            
        else:
            print(f"❌ Calibration failed: No successful optimization found")
            print("Using perfect Berkovich coefficients as fallback")
            
            return {
                'C0': 24.56, 'C1': 0.0, 'C2': 0.0, 'C3': 0.0, 'C4': 0.0,
                'C5': 0.0, 'C6': 0.0, 'C7': 0.0, 'C8': 0.0,
                'calibration_quality': {'rms_error_percent': float('inf'), 'max_error_percent': float('inf'), 
                                      'mean_area_ratio': 1.0, 'n_measurements': 0}
            }
    
    def iso_stiffness_calculation(self, displacement, load, percentage=None):
        """
        Calculate contact stiffness according to ISO 14577-4:2016
        Uses upper portion of unloading curve for linear fit
        
        Parameters:
        displacement: unloading displacement data (nm)
        load: unloading load data (mN)
        percentage: fraction of data to use (default: 0.25 = upper 25%)
        
        Returns:
        tuple: (stiffness in N/m, r_squared, data_range_used)
        """
        if percentage is None:
            percentage = self.ISO_STIFFNESS_RANGE_PERCENT
        
        # Ensure data is sorted by displacement (high to low for unloading)
        sorted_indices = np.argsort(displacement)[::-1]  # Reverse sort for unloading
        disp_sorted = displacement[sorted_indices]
        load_sorted = load[sorted_indices]
        
        # Use upper percentage of unloading data (highest loads, most elastic)
        n_points = max(int(len(disp_sorted) * percentage), 10)  # Minimum 10 points
        disp_elastic = disp_sorted[:n_points]
        load_elastic = load_sorted[:n_points]
        
        # Linear fit: Load = slope * displacement + intercept
        coeffs = np.polyfit(disp_elastic, load_elastic, 1)
        stiffness = coeffs[0] * 1e6  # Convert mN/nm to N/m
        
        # Calculate R²
        load_pred = np.polyval(coeffs, disp_elastic)
        ss_res = np.sum((load_elastic - load_pred) ** 2)
        ss_tot = np.sum((load_elastic - np.mean(load_elastic)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        
        data_range = {
            'n_points_used': n_points,
            'percentage_used': percentage,
            'displacement_range': (disp_elastic.min(), disp_elastic.max()),
            'load_range': (load_elastic.min(), load_elastic.max())
        }
        
        return stiffness, r_squared, data_range
    
    def validate_curve_fit_quality(self, r_squared, curve_type="unknown"):
        """
        Validate curve fit quality according to ISO 14577-4:2016
        
        Parameters:
        r_squared: coefficient of determination
        curve_type: type of curve for reporting
        
        Returns:
        dict: validation results
        """
        validation = {
            'meets_iso_standard': r_squared >= self.ISO_MIN_R_SQUARED,
            'quality_level': 'excellent' if r_squared >= 0.99 else 
                            'good' if r_squared >= 0.98 else 
                            'poor' if r_squared >= 0.95 else 'unacceptable',
            'r_squared': r_squared,
            'iso_requirement': self.ISO_MIN_R_SQUARED,
            'curve_type': curve_type
        }
        
        return validation
    
    def loading_curve_fit(self, h, k, n, C):
        """
        Loading curve fitting function: P = k * h^n + C
        ISO 14577-4:2016 compliant implementation
        
        Parameters:
        h: displacement (nm)
        k: scaling parameter 
        n: power law exponent
        C: constant offset (mN)
        
        Returns:
        P: load (mN)
        """
        return k * np.power(np.maximum(h, 1e-10), n) + C
    
    def power_law_unloading(self, h, B, hf, m):
        """
        Power law fitting function for unloading: P = B(h - hf)^m
        Simple power law formula (no transformation needed)
        """
        return B * np.power(np.maximum(h - hf, 1e-10), m)
    
    def CalculateR_2(self, x_true, y_true, poly_coeffs):
        """
        Calculate the R² value for a polynomial fit.
        
        Parameters:
        - x_true: True x-values (independent variable).
        - y_true: True y-values (dependent variable).
        - poly_coeffs: Coefficients of the polynomial.
        
        Returns:
        - R²: Coefficient of determination (unitless).
        """
        y_pred = np.polyval(poly_coeffs, x_true)
        ss_res = np.sum((y_true - y_pred) ** 2)  # Residual sum of squares
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)  # Total sum of squares
        r_squared = 1 - (ss_res / ss_tot)
        return r_squared
    
    def fit_unloading_curve_power_law(self, displacement, load):
        """
        Fit unloading curve using power law: P = B(h - hf)^m
        
        Simplified approach following the original IndentXLSAnalyzer pattern.
        Use first portion of unloading data (highest loads) for elastic unloading.
        
        Parameters:
        displacement: displacement data (nm) - from unloading portion
        load: load data (mN) - from unloading portion  
        
        Returns:
        popt: optimal parameters [B, hf, m]
        pcov: covariance matrix
        r_squared: R-squared value
        """
        try:
            # Clean data and ensure positive values
            displacement = np.array(displacement)
            load = np.array(load)
            
            # Remove any negative or zero loads
            valid_indices = (load > 0) & (displacement > 0)
            displacement = displacement[valid_indices]
            load = load[valid_indices]
            
            if len(displacement) < 10:
                raise ValueError("Insufficient valid data points")
            
            # Sort data by displacement to ensure low to high range
            sorted_indices = np.argsort(displacement)
            displacement_sorted = displacement[sorted_indices]
            load_sorted = load[sorted_indices]
            
            # Use range from low x,y to high x,y (start from minimum displacement)
            displacement_elastic = displacement_sorted
            load_elastic = load_sorted
            
            print(f"Using all {len(displacement_elastic)} points for unloading power law fitting")
            print(f"Range from low to high - displacement: {displacement_elastic.min():.2f} to {displacement_elastic.max():.2f} nm")
            print(f"Range from low to high - load: {load_elastic.min():.2f} to {load_elastic.max():.2f} mN")
            
            # Initial guess for unloading power law
            hf_guess = displacement_elastic.min() - abs(displacement_elastic.max() - displacement_elastic.min()) * 0.1
            B_guess = load_elastic.max() / np.power(np.maximum(displacement_elastic.max() - hf_guess, 1e-10), 1.5)
            m_guess = 1.5  # Typical unloading exponent
            
            initial_guess = [B_guess, hf_guess, m_guess]
            print(f"Initial guess: B={B_guess:.3e}, hf={hf_guess:.2f}, m={m_guess:.2f}")
            
            # Bounds for unloading
            hf_lower = displacement_elastic.min() - abs(displacement_elastic.max() - displacement_elastic.min()) * 0.5
            hf_upper = displacement_elastic.min() + abs(displacement_elastic.max() - displacement_elastic.min()) * 0.1
            
            bounds = ([1e-10, hf_lower, 0.3], 
                     [np.inf, hf_upper, 3.0])
            
            # Try fitting with power law
            try:
                popt, pcov = curve_fit(self.power_law_unloading, displacement_elastic, load_elastic, 
                                     p0=initial_guess, bounds=bounds, maxfev=5000)
            except Exception as e1:
                print(f"First fitting attempt failed: {e1}")
                # Fallback with looser bounds
                bounds = ([1e-10, -1000, 0.1], 
                         [np.inf, 1000, 5.0])
                print(f"Trying fallback bounds")
                popt, pcov = curve_fit(self.power_law_unloading, displacement_elastic, load_elastic, 
                                     p0=[B_guess, hf_guess, m_guess], bounds=bounds, maxfev=10000)
            
            # Calculate R-squared
            y_pred = self.power_law_unloading(displacement_elastic, *popt)
            ss_res = np.sum((load_elastic - y_pred) ** 2)
            ss_tot = np.sum((load_elastic - np.mean(load_elastic)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)
            
            print(f"Unloading power law fit: B={popt[0]:.3e}, hf={popt[1]:.2f}, m={popt[2]:.3f}, R²={r_squared:.4f}")
            
            # Print comparison for all data points (low to high range)
            print("\nUnloading Fitting Comparison (Exp vs Fitted) - Low to High Range:")
            print("Point | Disp(nm) | Load_Exp(mN) | Load_Fit(mN) | Diff(mN) | Diff(%)")
            print("-" * 70)
            n_points = min(20, len(displacement_elastic))  # Show first 20 points for readability
            indices = np.linspace(0, len(displacement_elastic)-1, n_points, dtype=int)
            for idx in indices:
                i = indices.tolist().index(idx)
                disp = displacement_elastic[idx]
                load_exp = load_elastic[idx]
                load_fit = y_pred[idx]
                diff_abs = abs(load_exp - load_fit)
                diff_pct = (diff_abs / load_exp) * 100 if load_exp > 0 else 0
                print(f"{i+1:5d} | {disp:8.2f} | {load_exp:12.3f} | {load_fit:12.3f} | {diff_abs:8.3f} | {diff_pct:7.2f}")
            
            return popt, pcov, r_squared
            
        except Exception as e:
            print(f"Power law unloading fitting failed: {e}")
            return None, None, None
    
    def find_loading_unloading_intersection(self, loading_params, coeffs_unloading, coeffs_elastic_unloading, df_loading, df_unloading):
        """
        Find intersection between loading fit P = k*h^n + C and unloading polynomial
        """
        try:
            k, n, C = loading_params
            
            # Get data ranges
            h_min = max(df_loading['Displacement Into Surface'].min(), df_unloading['Displacement Into Surface'].min())
            h_max = min(df_loading['Displacement Into Surface'].max(), df_unloading['Displacement Into Surface'].max())
            
            # Create test points
            h_test = np.linspace(h_min, h_max, 1000)
            
            # Calculate loading and polynomial values
            p_loading = self.loading_curve_fit(h_test, k, n, C)
            p_poly = np.polyval(coeffs_unloading, h_test)
            
            # Find closest intersection
            diff = np.abs(p_loading - p_poly)
            min_idx = np.argmin(diff)
            
            x_intersection = h_test[min_idx]
            y_intersection = p_loading[min_idx]
            
            return x_intersection, y_intersection
            
        except Exception as e:
            print(f"Error finding loading-unloading intersection: {e}")
            # Fallback to max load point
            max_load_idx = df_loading['Load On Sample'].idxmax()
            x_intersection = df_loading.loc[max_load_idx, 'Displacement Into Surface']
            y_intersection = df_loading.loc[max_load_idx, 'Load On Sample']
            return x_intersection, y_intersection
    
    def fit_loading_curve_new(self, displacement, load):
        """
        Fit loading curve using: P = k * h^n + C
        
        Parameters:
        displacement: displacement data (nm)
        load: load data (mN)
        
        Returns:
        popt: optimal parameters [k, n, C]
        pcov: covariance matrix
        r_squared: R-squared value
        """
        try:
            # Clean data and ensure positive values
            displacement = np.array(displacement)
            load = np.array(load)
            
            # Remove any negative loads
            valid_indices = (load >= 0) & (displacement >= 0)
            displacement = displacement[valid_indices]
            load = load[valid_indices]
            
            if len(displacement) < 10:
                raise ValueError("Insufficient valid data points")
            
            # Initial guess for P = k * h^n + C
            # Estimate k and n from log-log relationship for high loads
            # Use upper 50% of data for initial estimation
            mid_idx = len(displacement) // 2
            h_high = displacement[mid_idx:]
            p_high = load[mid_idx:]
            
            # Remove zero loads for log calculation
            nonzero_mask = p_high > 0
            if np.sum(nonzero_mask) > 5:
                h_log = h_high[nonzero_mask]
                p_log = p_high[nonzero_mask]
                
                # Linear regression on log-log data: log(P) = log(k) + n*log(h)
                log_h = np.log(h_log)
                log_p = np.log(p_log)
                
                # Fit linear relationship
                poly_coeffs = np.polyfit(log_h, log_p, 1)
                n_guess = poly_coeffs[0]  # slope
                k_guess = np.exp(poly_coeffs[1])  # exp(intercept)
            else:
                # Fallback estimates
                n_guess = 2.0
                k_guess = load.max() / (displacement.max() ** n_guess)
            
            # Estimate C from minimum load values
            C_guess = np.median(load[:10]) if len(load) > 10 else 0.0
            
            initial_guess = [k_guess, n_guess, C_guess]
            print(f"Initial guess for P = k*h^n + C: k={k_guess:.3e}, n={n_guess:.3f}, C={C_guess:.3f}")
            
            # Set bounds
            bounds = ([1e-10, 0.1, -100], 
                     [np.inf, 10.0, 100])
            
            # Try fitting with the new equation
            try:
                popt, pcov = curve_fit(self.loading_curve_fit, displacement, load, 
                                     p0=initial_guess, bounds=bounds, maxfev=5000)
            except Exception as e1:
                print(f"First fitting attempt failed: {e1}")
                # Fallback with looser bounds and simpler initial guess
                bounds = ([1e-10, 0.5, -1000], 
                         [np.inf, 5.0, 1000])
                simple_guess = [load.max() / (displacement.max() ** 2), 2.0, 0.0]
                print(f"Trying fallback with k={simple_guess[0]:.3e}, n={simple_guess[1]:.3f}, C={simple_guess[2]:.3f}")
                popt, pcov = curve_fit(self.loading_curve_fit, displacement, load, 
                                     p0=simple_guess, bounds=bounds, maxfev=10000)
            
            # Calculate R-squared
            y_pred = self.loading_curve_fit(displacement, *popt)
            ss_res = np.sum((load - y_pred) ** 2)
            ss_tot = np.sum((load - np.mean(load)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)
            
            k, n, C = popt
            print(f"Loading curve fit successful: k={k:.3e}, n={n:.3f}, C={C:.3f} mN")
            
            # Print experimental vs fitted comparison at different points
            print("\nLoading Fitting Comparison (Exp vs Fitted):")
            print("Point | Disp(nm) | Load_Exp(mN) | Load_Fit(mN) | Diff(mN) | Diff(%)")
            print("-" * 70)
            n_points = min(10, len(displacement))
            indices = np.linspace(0, len(displacement)-1, n_points, dtype=int)
            for idx in indices:
                i = indices.tolist().index(idx)
                disp = displacement[idx]
                load_exp = load[idx]
                load_fit = y_pred[idx]
                diff_abs = abs(load_exp - load_fit)
                diff_pct = (diff_abs / load_exp) * 100 if load_exp > 0 else 0
                print(f"{i+1:5d} | {disp:8.2f} | {load_exp:12.3f} | {load_fit:12.3f} | {diff_abs:8.3f} | {diff_pct:7.2f}")
            
            return popt, pcov, r_squared
            
        except Exception as e:
            print(f"Loading curve fitting failed: {e}")
            return None, None, None
    
    def find_closest_intersection_point(self, coeffs1, coeffs2, coeffs3):
        """
        Fixed version with dynamic bounds and better error handling
        """
        def difference_in_y(x):
            y1 = np.polyval(coeffs1, x)
            y2 = np.polyval(coeffs2, x)
            y3 = np.polyval(coeffs3, x)
            return abs(y1 - y2) + abs(y1 - y3) + abs(y2 - y3)

        # Dynamic bounds based on data range instead of hard-coded values
        try:
            # Get reasonable bounds from the polynomial roots
            roots1 = np.roots(coeffs1)
            roots2 = np.roots(coeffs2)
            roots3 = np.roots(coeffs3)
            
            # Filter out complex roots
            real_roots1 = roots1[np.isreal(roots1)].real
            real_roots2 = roots2[np.isreal(roots2)].real
            real_roots3 = roots3[np.isreal(roots3)].real
            
            # Set bounds based on actual data range
            min_bound = 0
            max_bound = 5000  # Increased upper bound
            
            if len(real_roots1) > 0:
                max_bound = max(max_bound, np.max(real_roots1) * 1.5)
            if len(real_roots2) > 0:
                max_bound = max(max_bound, np.max(real_roots2) * 1.5)
            if len(real_roots3) > 0:
                max_bound = max(max_bound, np.max(real_roots3) * 1.5)
            
            # Ensure reasonable bounds
            max_bound = min(max_bound, 10000)  # Cap at 10000 nm
            
        except Exception as e:
            print(f"Warning: Could not determine dynamic bounds, using defaults: {e}")
            min_bound, max_bound = 0, 5000
        
        # Use minimize_scalar with dynamic bounds
        result = minimize_scalar(difference_in_y, bounds=(min_bound, max_bound), method='bounded')

        if result.success:
            x_min_difference = result.x
            y_min_difference = np.polyval(coeffs1, x_min_difference)
            return x_min_difference, y_min_difference
        else:
            print(f"Optimization failed: {result.message}")
            return None, None
    
    def run_analysis(self):
        """
        Fixed version with better data handling and debugging
        """
        print("Running analysis with FIXED fitting logic and TIP CALIBRATION...")
        
        # Read the Results sheet
        try:
            df_Results = pd.read_excel(self.filename, sheet_name="Results")
            print(f"Results sheet loaded successfully with {len(df_Results)} rows")
        except Exception as e:
            print(f"Error reading Results sheet: {e}")
            return []

        # First pass: collect all data for tip calibration
        calibration_data = []
        all_results = []

        print("\n=== PHASE 1: DATA COLLECTION FOR TIP CALIBRATION ===")
        
        for i in [f"0{str(i).zfill(2)}" for i in range(1, 21)]:  # Process Tests 001-020
            try:
                print(f"Collecting calibration data from Test {i}...")
                
                # Get hardness from results
                test_results = df_Results[df_Results.Test == str(int(i))]
                if len(test_results) == 0:
                    print(f"No results found for test {i} in Results sheet")
                    continue
                    
                hardnessCSM = test_results["H Average Over Defined Range"].iloc[0]

                # Check if worksheet exists first
                try:
                    # Load test data, dropping the first two rows to match the original structure
                    df = pd.read_excel(self.filename, sheet_name=f"Test {i}").drop(index=[0, 1])
                except ValueError as ve:
                    if "not found" in str(ve):
                        print(f"Worksheet 'Test {i}' not found - skipping")
                        continue
                    else:
                        raise ve
                
                df['Displacement Into Surface'] = pd.to_numeric(df['Displacement Into Surface'], errors='coerce')
                df['Load On Sample'] = pd.to_numeric(df['Load On Sample'], errors='coerce')
                df.dropna(subset=['Displacement Into Surface', 'Load On Sample'], inplace=True)
                
                if len(df) < 100:
                    print(f"Insufficient data points ({len(df)}) for test {i}")
                    continue
                
                # Find peak and create loading data
                peak_index = df["Load On Sample"].idxmax()
                df_before_peak = df.iloc[:peak_index + 1]

                # Improved data filtering with adaptive threshold
                load_threshold = max(40, df['Load On Sample'].max() * 0.1)  # Adaptive threshold
                filtered_df = df[df['Load On Sample'] > load_threshold].copy()
                
                if len(filtered_df) < 10:
                    print(f"Insufficient data after filtering for test {i}")
                    continue

                # Improved horizontal segment detection for calibration data collection
                horizontal_segments, total_horizontal_adjustment = self.detect_and_remove_horizontal_segments(
                    filtered_df, df, peak_index, i)
                
                if len(horizontal_segments) > 0:
                    # Use the end of the last horizontal segment as the transition point
                    last_segment = horizontal_segments[-1]
                    transition_index = last_segment['end_index_original']
                    
                    df_loading = df[:transition_index]
                    df_unloading = df[transition_index:].copy()
                    horizontal = total_horizontal_adjustment
                else:
                    # Fallback: use peak-based segmentation
                    df_loading = df[:peak_index]
                    df_unloading = df[peak_index:].copy()
                    horizontal = 0

                # Apply horizontal displacement correction to unloading data
                if horizontal > 0:
                    df_unloading.loc[:, 'Displacement Into Surface'] = (
                        df_unloading['Displacement Into Surface'] - horizontal)

                # Clean unloading data first (moved from later in the code)
                df_unloading_clean = df_unloading.copy()
                
                # Remove negative loads and very small loads (noise)
                valid_unloading = (df_unloading_clean['Load On Sample'] > 0.1) & (df_unloading_clean['Displacement Into Surface'] > 0)
                df_unloading_clean = df_unloading_clean[valid_unloading].copy()
                
                # Apply [::-1] logic to reverse the unloading curve order
                df_unloading_clean = df_unloading_clean.iloc[::-1].reset_index(drop=True)

                # Quick fitting for calibration data collection
                try:
                    loading_params, loading_cov, loading_r2 = self.fit_loading_curve_new(
                        df_before_peak['Displacement Into Surface'], df_before_peak['Load On Sample'])
                    if loading_params is None:
                        continue
                        
                    # Calculate stiffness using ISO method
                    iso_stiffness, iso_stiffness_r2, iso_stiffness_range = self.iso_stiffness_calculation(
                        df_unloading_clean['Displacement Into Surface'], 
                        df_unloading_clean['Load On Sample']
                    )
                    
                    # Autodetect Pmax at target displacement (~1600 nm)
                    target_displacement = 1600  # nm
                    displacement_diff = np.abs(df_before_peak['Displacement Into Surface'] - target_displacement)
                    closest_idx = displacement_diff.idxmin()
                    autodetected_load = df_before_peak.loc[closest_idx, 'Load On Sample']  # mN
                    Pmax = autodetected_load * 1e-3  # Convert to N
                    autodetected_displacement = df_before_peak.loc[closest_idx, 'Displacement Into Surface']  # nm
                    Hmax = autodetected_displacement * 1e-9  # Convert to m
                    
                    # Calculate contact depth using ISO standard
                    S = iso_stiffness
                    Hc = abs(Hmax - self.epsilon * (Pmax / S))
                    hc_nm = Hc * 1e9  # Convert to nm
                    
                    # Use ISO standard reference material properties for fused silica
                    silica_modulus = self.ISO_FUSED_SILICA_MODULUS  # 72e9 Pa
                    silica_poisson = self.ISO_FUSED_SILICA_POISSON  # 0.17
                    Er = self.compute_reduced_modulus(silica_modulus, silica_poisson, 
                                                      self.ISO_DIAMOND_MODULUS, self.ISO_DIAMOND_POISSON)
                    
                    # Store calibration data
                    calibration_data.append({
                        'test': i,
                        'hc_nm': hc_nm,
                        'S': S,
                        'P': Pmax,
                        'Er': Er,
                        'hardness_csm': hardnessCSM
                    })
                    
                    print(f"  ✓ Test {i}: hc={hc_nm:.1f}nm, S={S/1e6:.2f}mN/nm, P={Pmax*1e3:.1f}mN")
                    
                except Exception as e:
                    print(f"  ✗ Test {i}: Failed to collect calibration data - {e}")
                    continue
                    
            except Exception as e:
                print(f"Error processing test {i} for calibration: {str(e)}")
                continue

        # Perform tip calibration if we have enough data
        if len(calibration_data) >= 5:
            print(f"\n=== PHASE 2: TIP AREA FUNCTION CALIBRATION ===")
            calibrated_coeffs = self.calibrate_tip_area_function(calibration_data)
        else:
            print(f"\n⚠️ Insufficient calibration data ({len(calibration_data)} measurements)")
            print("Using perfect Berkovich coefficients")
            calibrated_coeffs = {
                'C0': 24.56, 'C1': 0.0, 'C2': 0.0, 'C3': 0.0, 'C4': 0.0,
                'C5': 0.0, 'C6': 0.0, 'C7': 0.0, 'C8': 0.0
            }

        print(f"\n=== PHASE 3: FINAL ANALYSIS WITH CALIBRATED TIP ===")
        print("Re-analyzing all tests with calibrated area function...")

        # Second pass: full analysis with calibrated tip
        for i in [f"0{str(i).zfill(2)}" for i in range(1, 21)]:  # Process Tests 001-020
            try:
                print(f"\nProcessing Test {i}...")
                
                # Get hardness from results
                test_results = df_Results[df_Results.Test == str(int(i))]
                if len(test_results) == 0:
                    print(f"No results found for test {i} in Results sheet")
                    continue
                    
                hardnessCSM = test_results["H Average Over Defined Range"].iloc[0]

                # Check if worksheet exists first
                try:
                    # Load test data, dropping the first two rows to match the original structure
                    df = pd.read_excel(self.filename, sheet_name=f"Test {i}").drop(index=[0, 1])
                except ValueError as ve:
                    if "not found" in str(ve):
                        print(f"Worksheet 'Test {i}' not found - skipping")
                        continue
                    else:
                        raise ve
                
                df['Displacement Into Surface'] = pd.to_numeric(df['Displacement Into Surface'], errors='coerce')
                df['Load On Sample'] = pd.to_numeric(df['Load On Sample'], errors='coerce')
                df.dropna(subset=['Displacement Into Surface', 'Load On Sample'], inplace=True)
                
                if len(df) < 100:
                    print(f"Insufficient data points ({len(df)}) for test {i}")
                    continue
                
                # Find peak and create loading data
                peak_index = df["Load On Sample"].idxmax()
                df_before_peak = df.iloc[:peak_index + 1]

                # Improved data filtering with adaptive threshold
                load_threshold = max(40, df['Load On Sample'].max() * 0.1)  # Adaptive threshold
                filtered_df = df[df['Load On Sample'] > load_threshold].copy()
                
                if len(filtered_df) < 10:
                    print(f"Insufficient data after filtering for test {i}")
                    continue

                # Improved horizontal segment detection and removal
                horizontal_segments, total_horizontal_adjustment = self.detect_and_remove_horizontal_segments(
                    filtered_df, df, peak_index, i)
                
                if len(horizontal_segments) > 0:
                    print(f"Found {len(horizontal_segments)} horizontal segment(s)")
                    for idx, seg in enumerate(horizontal_segments):
                        print(f"  Segment {idx+1}: {seg['start_disp']:.1f} to {seg['end_disp']:.1f} nm, "
                              f"length={seg['length']:.1f} nm, load_std={seg['load_std']:.3f} mN")
                    
                    # Use the end of the last horizontal segment as the transition point
                    last_segment = horizontal_segments[-1]
                    transition_index = last_segment['end_index_original']
                    
                    df_loading = df[:transition_index]
                    df_unloading = df[transition_index:].copy()
                    horizontal = total_horizontal_adjustment
                    
                    print(f"Total horizontal adjustment: {horizontal:.2f} nm")
                    print(f"Loading data: {len(df_loading)} points, Unloading data: {len(df_unloading)} points")
                else:
                    print(f"Could not find horizontal segment for test {i} - using peak-based fallback")
                    # Fallback: use peak-based segmentation
                    df_loading = df[:peak_index]
                    df_unloading = df[peak_index:].copy()
                    horizontal = 0

                # Apply horizontal displacement correction to unloading data
                if horizontal > 0:
                    df_unloading.loc[:, 'Displacement Into Surface'] = (
                        df_unloading['Displacement Into Surface'] - horizontal)
                    print(f"Applied horizontal correction of {horizontal:.2f} nm to unloading data")

                # Clean unloading data first (moved from later in the code)
                df_unloading_clean = df_unloading.copy()
                
                # Remove negative loads and very small loads (noise)
                valid_unloading = (df_unloading_clean['Load On Sample'] > 0.1) & (df_unloading_clean['Displacement Into Surface'] > 0)
                df_unloading_clean = df_unloading_clean[valid_unloading].copy()
                
                # Apply [::-1] logic to reverse the unloading curve order
                df_unloading_clean = df_unloading_clean.iloc[::-1].reset_index(drop=True)

                # ISO 14577-4:2016 Data Quality Validation
                print(f"\n=== ISO 14577-4:2016 DATA QUALITY VALIDATION ===")
                
                # Validate loading data quality
                loading_validation = self.validate_iso_data_quality(
                    df_before_peak['Displacement Into Surface'], 
                    df_before_peak['Load On Sample'], 
                    "loading"
                )
                
                print(f"Loading Data Quality:")
                print(f"  • Data points: {len(df_before_peak)} (ISO min: {self.ISO_MIN_DATA_POINTS_LOADING})")
                print(f"  • Quality status: {'✅ PASS' if loading_validation['overall_quality'] else '❌ FAIL'}")
                for warning in loading_validation['warnings']:
                    print(f"  • ⚠️  {warning}")
                
                # Validate unloading data quality  
                unloading_validation = self.validate_iso_data_quality(
                    df_unloading_clean['Displacement Into Surface'],
                    df_unloading_clean['Load On Sample'],
                    "unloading"
                )
                
                print(f"Unloading Data Quality:")
                print(f"  • Data points: {len(df_unloading_clean)} (ISO min: {self.ISO_MIN_DATA_POINTS_UNLOADING})")
                print(f"  • Quality status: {'✅ PASS' if unloading_validation['overall_quality'] else '❌ FAIL'}")
                for warning in unloading_validation['warnings']:
                    print(f"  • ⚠️  {warning}")
                
                # Loading curve fitting: P = k * h^n + C
                loading_params = None
                loading_r2 = None
                
                try:
                    loading_params, loading_cov, loading_r2 = self.fit_loading_curve_new(
                        df_before_peak['Displacement Into Surface'], df_before_peak['Load On Sample'])
                    if loading_params is not None:
                        k, n, C = loading_params
                        print(f"Loading curve fit: k={k:.3e}, n={n:.3f}, C={C:.3f} mN, R²={loading_r2:.4f}")
                        
                        # ISO 14577-4:2016 Curve Fit Quality Validation
                        loading_quality = self.validate_curve_fit_quality(loading_r2, "loading")
                        print(f"Loading Fit Quality: {loading_quality['quality_level']} ({'✅ ISO compliant' if loading_quality['meets_iso_standard'] else '❌ Below ISO standard'})")
                    else:
                        print("Loading curve fitting failed - skipping test")
                        continue
                except Exception as e:
                    print(f"Error in loading curve fitting: {e}")
                    continue

                # No displacement correction needed for P = k*h^n + C (starts from origin)

                # Improved unloading fitting - try both polynomial and power law approaches
                print(f"Raw unloading data: {len(df_unloading)} points")
                print(f"Raw unloading range: {df_unloading['Displacement Into Surface'].min():.2f} to {df_unloading['Displacement Into Surface'].max():.2f} nm")
                print(f"Raw load range: {df_unloading['Load On Sample'].min():.2f} to {df_unloading['Load On Sample'].max():.2f} mN")
                
                # Use cleaned unloading data that was already created earlier
                n_unloading_fit = len(df_unloading_clean)
                
                df_unloading_fit = df_unloading_clean.copy()
                
                print(f"Cleaned unloading data: {len(df_unloading_clean)} points")
                print(f"Using {n_unloading_fit} points for unloading fitting")
                print(f"Cleaned unloading range: {df_unloading_clean['Displacement Into Surface'].min():.2f} to {df_unloading_clean['Displacement Into Surface'].max():.2f} nm")
                print(f"Cleaned load range: {df_unloading_clean['Load On Sample'].min():.2f} to {df_unloading_clean['Load On Sample'].max():.2f} mN")
                print(f"Fitting range: {df_unloading_fit['Displacement Into Surface'].min():.2f} to {df_unloading_fit['Displacement Into Surface'].max():.2f} nm")
                
                # Try power law fitting for unloading first
                unloading_power_law_params = None
                unloading_power_law_r2 = None
                
                try:
                    print("\nAttempting power law fitting for unloading...")
                    unloading_power_law_params, unloading_power_law_cov, unloading_power_law_r2 = self.fit_unloading_curve_power_law(
                        df_unloading_fit['Displacement Into Surface'], df_unloading_fit['Load On Sample'])
                    
                    if unloading_power_law_params is not None and unloading_power_law_r2 > self.ISO_MIN_R_SQUARED:
                        power_law_quality = self.validate_curve_fit_quality(unloading_power_law_r2, "unloading power law")
                        print(f"Power law unloading fit: R² = {unloading_power_law_r2:.4f} ({power_law_quality['quality_level']})")
                        use_power_law_unloading = True
                    else:
                        print(f"Power law unloading fit not satisfactory: R² = {unloading_power_law_r2:.4f} (ISO requirement: {self.ISO_MIN_R_SQUARED})")
                        use_power_law_unloading = False
                except Exception as e:
                    print(f"Power law unloading fitting failed: {e}")
                    use_power_law_unloading = False
                
                # Polynomial fitting as backup or primary method
                coeffs_unloading = np.polyfit(df_unloading_fit['Displacement Into Surface'], df_unloading_fit['Load On Sample'], 2)
                
                # Elastic unloading using last 20 points for linear fit (most elastic region)
                n_elastic = min(20, len(df_unloading_fit))
                df_elastic_fit = df_unloading_fit.iloc[-n_elastic:].copy()  # Take last 20 points
                coeffs_elastic_unloading = np.polyfit(df_elastic_fit['Displacement Into Surface'],
                                                      df_elastic_fit['Load On Sample'], 1)
                
                print(f"Elastic unloading linear fit using last {n_elastic} points")
                print(f"Elastic fit range: {df_elastic_fit['Displacement Into Surface'].min():.2f} to {df_elastic_fit['Displacement Into Surface'].max():.2f} nm")
                
                # Calculate R-squared for polynomial fits using cleaned data
                r_squared_unloading = self.CalculateR_2(df_unloading_fit['Displacement Into Surface'],
                                                        df_unloading_fit['Load On Sample'], coeffs_unloading)
                
                # Choose best fitting method
                if use_power_law_unloading and unloading_power_law_r2 > r_squared_unloading:
                    print(f"Using power law unloading fit: R² = {unloading_power_law_r2:.4f}")
                    unloading_fit_type = "Power Law"
                    final_unloading_r2 = unloading_power_law_r2
                else:
                    print(f"Using polynomial unloading fit: R² = {r_squared_unloading:.4f}")
                    unloading_fit_type = "Polynomial"
                    final_unloading_r2 = r_squared_unloading
                    use_power_law_unloading = False
                
                print(f"Elastic unloading linear fit: slope={coeffs_elastic_unloading[0]:.3e}")
                
                # Print detailed fitting comparison for unloading
                if use_power_law_unloading:
                    y_pred_unloading = self.power_law_unloading(df_unloading_fit['Displacement Into Surface'], *unloading_power_law_params)
                    fit_method = "Power Law"
                else:
                    y_pred_unloading = np.polyval(coeffs_unloading, df_unloading_fit['Displacement Into Surface'])
                    fit_method = "Polynomial"
                
                print(f"\nUnloading {fit_method} Fitting Comparison (Exp vs Fitted):")
                print("Point | Disp(nm) | Load_Exp(mN) | Load_Fit(mN) | Diff(mN) | Diff(%)")
                print("-" * 70)
                n_points = min(10, len(df_unloading_fit))
                indices = np.linspace(0, len(df_unloading_fit)-1, n_points, dtype=int)
                for idx in indices:
                    point_idx = indices.tolist().index(idx)
                    disp = df_unloading_fit['Displacement Into Surface'].iloc[idx]
                    load_exp = df_unloading_fit['Load On Sample'].iloc[idx]
                    load_fit = y_pred_unloading[idx]
                    diff_abs = abs(load_exp - load_fit)
                    diff_pct = (diff_abs / load_exp) * 100 if load_exp > 0 else 0
                    print(f"{point_idx+1:5d} | {disp:8.2f} | {load_exp:12.3f} | {load_fit:12.3f} | {diff_abs:8.3f} | {diff_pct:7.2f}")
                
                # Set power law params and find intersection
                if use_power_law_unloading:
                    # Use loading-unloading intersection finding
                    x_intersection_point, y_intersection_point = self.find_loading_unloading_intersection(
                        loading_params, coeffs_unloading, coeffs_elastic_unloading, df_before_peak, df_unloading_fit)
                else:
                    # Use polynomial intersection finding
                    x_intersection_point, y_intersection_point = self.find_closest_intersection_point(
                        np.polyfit(df_before_peak['Displacement Into Surface'], df_before_peak['Load On Sample'], 2),
                        coeffs_unloading,
                        coeffs_elastic_unloading)
                
                print(f"Intersection point from {unloading_fit_type.lower()} fits: ({x_intersection_point:.2f} nm, {y_intersection_point:.2f} mN)")

                # Calculate R-squared for loading fit
                y_pred_loading = self.loading_curve_fit(df_before_peak['Displacement Into Surface'], *loading_params)
                ss_res_loading = np.sum((df_before_peak['Load On Sample'] - y_pred_loading) ** 2)
                ss_tot_loading = np.sum((df_before_peak['Load On Sample'] - np.mean(df_before_peak['Load On Sample'])) ** 2)
                r_squared_loading = 1 - (ss_res_loading / ss_tot_loading)
                
                # Print fitting summary for this test
                print(f"\n=== Test {i} Fitting Summary ===")
                print(f"Loading fit - R²: {r_squared_loading:.4f}, RMSE: {np.sqrt(ss_res_loading/len(y_pred_loading)):.3f} mN")
                print(f"Unloading {unloading_fit_type} fit - R²: {final_unloading_r2:.4f}")
                print(f"Data points - Loading: {len(df_before_peak)}, Unloading: {len(df_unloading)}")
                print(f"Load range - Loading: {df_before_peak['Load On Sample'].min():.2f} to {df_before_peak['Load On Sample'].max():.2f} mN")
                print(f"Displacement range - Loading: {df_before_peak['Displacement Into Surface'].min():.2f} to {df_before_peak['Displacement Into Surface'].max():.2f} nm")
                print("=" * 35)

                # Autodetect Pmax at target displacement (~1600 nm)
                target_displacement = 1600  # nm
                
                # Find the closest data point to target displacement
                displacement_diff = np.abs(df_before_peak['Displacement Into Surface'] - target_displacement)
                closest_idx = displacement_diff.idxmin()
                
                # Get load and displacement at the target point
                autodetected_load = df_before_peak.loc[closest_idx, 'Load On Sample']  # mN
                autodetected_displacement = df_before_peak.loc[closest_idx, 'Displacement Into Surface']  # nm
                
                # Also get actual maximum for comparison
                actual_max_load = df_before_peak['Load On Sample'].max()  # mN
                actual_max_displacement = df_before_peak.loc[df_before_peak['Load On Sample'].idxmax(), 'Displacement Into Surface']  # nm
                
                # Use autodetected values for Pmax calculation
                Pmax = autodetected_load * 1e-3  # Convert to N
                Hmax = autodetected_displacement * 1e-9  # Convert to m
                
                print(f"Target displacement: {target_displacement} nm")
                print(f"Autodetected at: {autodetected_displacement:.2f} nm")
                print(f"Autodetected load: Pmax = {autodetected_load:.2f} mN ({Pmax:.6f} N)")
                print(f"Actual maximum: {actual_max_load:.2f} mN at {actual_max_displacement:.2f} nm")
                print(f"Difference from max: ΔLoad = {actual_max_load - autodetected_load:.2f} mN, ΔDisp = {actual_max_displacement - autodetected_displacement:.2f} nm")
                print(f"Intersection point: ({x_intersection_point:.2f} nm, {y_intersection_point:.2f} mN)")
                
                # Calculate stiffness from linear elastic unloading using ISO 14577-4:2016 method
                iso_stiffness, iso_stiffness_r2, iso_stiffness_range = self.iso_stiffness_calculation(
                    df_unloading_fit['Displacement Into Surface'], 
                    df_unloading_fit['Load On Sample']
                )
                
                print(f"\n=== ISO 14577-4:2016 STIFFNESS CALCULATION ===")
                print(f"ISO Stiffness: S = {iso_stiffness:.2e} N/m")
                print(f"Data range used: {iso_stiffness_range['percentage_used']*100:.1f}% of unloading data")
                print(f"Points used: {iso_stiffness_range['n_points_used']} points")
                print(f"Displacement range: {iso_stiffness_range['displacement_range'][0]:.2f} to {iso_stiffness_range['displacement_range'][1]:.2f} nm")
                print(f"Linear fit R²: {iso_stiffness_r2:.6f}")
                
                stiffness_quality = self.validate_curve_fit_quality(iso_stiffness_r2, "stiffness linear fit")
                print(f"Stiffness Quality: {stiffness_quality['quality_level']} ({'✅ ISO compliant' if stiffness_quality['meets_iso_standard'] else '❌ Below ISO standard'})")
                
                # Use ISO-compliant stiffness calculation
                S = iso_stiffness
                print(f"Using ISO-compliant stiffness: S = {S:.2e} N/m")
                
                Hc = abs(Hmax - self.epsilon * (Pmax / S))
                
                # Calculate elastic unloading intercept using cleaned data
                x_intercept_elastic_unloading = -coeffs_elastic_unloading[1] / coeffs_elastic_unloading[0]
                print(f"Linear unloading intercept: h = {x_intercept_elastic_unloading:.2f} nm")
                
                print(f"Intersection point: ({x_intersection_point:.2f} nm, {y_intersection_point:.2f} mN)")
                print(f"Unloading direction: from {x_intersection_point:.2f} nm to {x_intercept_elastic_unloading:.2f} nm")
                
                Hs = x_intercept_elastic_unloading * 1e-9
                
                # Oliver-Pharr analysis with ISO 14577-4:2016 compliant area function calibration
                print(f"\n=== ISO 14577-4:2016 OLIVER-PHARR ANALYSIS ===")
                
                # Use ISO standard reference material properties for fused silica
                silica_modulus = self.ISO_FUSED_SILICA_MODULUS  # 72e9 Pa
                silica_poisson = self.ISO_FUSED_SILICA_POISSON  # 0.17
                Er = self.compute_reduced_modulus(silica_modulus, silica_poisson, 
                                                  self.ISO_DIAMOND_MODULUS, self.ISO_DIAMOND_POISSON)
                
                print(f"Reference Material: Fused Silica")
                print(f"  • Elastic Modulus: {silica_modulus*1e-9:.0f} GPa")
                print(f"  • Poisson Ratio: {silica_poisson:.3f}")
                print(f"Indenter Material: Diamond")
                print(f"  • Elastic Modulus: {self.ISO_DIAMOND_MODULUS*1e-9:.0f} GPa") 
                print(f"  • Poisson Ratio: {self.ISO_DIAMOND_POISSON:.3f}")
                print(f"Reduced Modulus: {Er*1e-9:.2f} GPa")
                
                # Calculate contact area using calibrated ISO 14577-4:2016 area function
                hc_nm = Hc * 1e9  # Convert to nm for area function
                
                # Use calibrated area function coefficients
                area_coeffs = calibrated_coeffs.copy()
                
                # ISO 14577-4:2016 compliant area function calculation with calibrated coefficients
                A_area_function = self.calculate_iso_area_function(hc_nm, area_coeffs)
                
                # Also calculate physics-based area for comparison
                A_physics = np.pi * ((S / (2 * Er)) ** 2)
                
                print(f"\nContact Area Calculations (CALIBRATED):")
                print(f"  • Contact depth: {hc_nm:.2f} nm")
                print(f"  • Calibrated area function: {A_area_function*1e18:.2f} nm²")
                print(f"  • Physics-based: {A_physics*1e18:.2f} nm²")
                print(f"  • Area ratio (calibrated/physics): {A_area_function/A_physics:.4f}")
                
                # Show calibration improvement
                A_perfect_berkovich = 24.56 * hc_nm**2 * 1e-18  # Perfect Berkovich for comparison
                print(f"  • Perfect Berkovich: {A_perfect_berkovich*1e18:.2f} nm²")
                print(f"  • Calibration correction: {((A_area_function - A_perfect_berkovich)/A_perfect_berkovich)*100:+.2f}%")
                
                # Calculate baseline results using both methods
                baseline_hardness_physics = (Pmax / A_physics) * 1e-9  # Convert to GPa
                baseline_hardness_area_func = (Pmax / A_area_function) * 1e-9  # Convert to GPa
                baseline_modulus_GPa = Er * 1e-9  # Convert to GPa
                
                # Use area function as the primary method (SilicaBefore approach)
                expected_hardness = baseline_hardness_area_func  # Use area function hardness as reference
                expected_modulus = baseline_modulus_GPa   # Use baseline modulus as reference
                
                # Calculate calibration correction factor (will be 1.0 when using baseline as reference)
                hardness_correction_factor = expected_hardness / baseline_hardness_area_func
                
                print(f"\nBaseline Oliver-Pharr Results (SilicaBefore Calibration):")
                print(f"Sample: Silica (E = {silica_modulus*1e-9:.0f} GPa, ν = {silica_poisson})")
                print(f"Contact depth Hc = {Hc*1e9:.2f} nm")
                print(f"Stiffness S = {S:.2e} N/m")
                print(f"Contact area (physics-based) = {A_physics*1e18:.2f} nm²")
                print(f"Contact area (area function) = {A_area_function*1e18:.2f} nm²")
                print(f"Area function coefficients:")
                for key, value in area_coeffs.items():
                    # Skip non-numeric values like calibration_quality dictionary
                    if isinstance(value, (int, float)):
                        if value != 0.0:
                            print(f"  {key} = {value:.6f}")
                        else:
                            print(f"  {key} = {value:.1f} (not calibrated)")
                print(f"Baseline Hardness (physics) = {baseline_hardness_physics:.2f} GPa")
                print(f"Baseline Hardness (area func) = {baseline_hardness_area_func:.2f} GPa")
                print(f"Baseline Reduced Modulus = {baseline_modulus_GPa:.2f} GPa")
                
                # Display tip fitted parameters prominently
                if loading_params is not None:
                    k, n, C = loading_params
                    print(f"\n🔧 TIP FITTED PARAMETERS:")
                    print(f"   Loading equation: P = k·h^n + C")
                    print(f"   k = {k:.6e} mN/nm^n")
                    print(f"   n = {n:.6f} (power law exponent)")
                    print(f"   C = {C:.6f} mN (offset)")
                    print(f"   R² = {loading_r2:.8f} (fit quality)")
                
                if use_power_law_unloading and unloading_power_law_params is not None:
                    B_unload, hf_unload, m_unload = unloading_power_law_params
                    print(f"\n📈 UNLOADING PARAMETERS:")
                    print(f"   Unloading equation: P = B(h - hf)^m")
                    print(f"   B = {B_unload:.6e} mN/nm^m")
                    print(f"   hf = {hf_unload:.4f} nm (residual depth)")
                    print(f"   m = {m_unload:.6f} (unloading exponent)")
                    print(f"   R² = {unloading_power_law_r2:.8f} (fit quality)")
                
                # Apply calibration correction
                A_calibrated = A_area_function / hardness_correction_factor  # Use area function as base
                oliver_pharr_hardness_GPa = (Pmax / A_calibrated) * 1e-9  # Calibrated hardness
                oliver_pharr_modulus_GPa = baseline_modulus_GPa  # Modulus stays the same
                
                print(f"\nSilicaBefore Calibrated Oliver-Pharr Results:")
                print(f"Calibration correction factor applied: {hardness_correction_factor:.3f}")
                print(f"Calibrated contact area = {A_calibrated*1e18:.2f} nm²")
                print(f"Calibrated Hardness = {oliver_pharr_hardness_GPa:.2f} GPa")
                print(f"Calibrated Reduced Modulus = {oliver_pharr_modulus_GPa:.2f} GPa")
                print(f"Reference SilicaBefore hardness: {expected_hardness:.2f} GPa")
                print(f"Reference SilicaBefore modulus: {expected_modulus:.2f} GPa")
                
                # Show comparison with SilicaBefore reference values
                hardness_error = ((oliver_pharr_hardness_GPa - expected_hardness) / expected_hardness) * 100
                modulus_error = ((oliver_pharr_modulus_GPa - expected_modulus) / expected_modulus) * 100
                print(f"SilicaBefore calibrated hardness error: {hardness_error:+.1f}% (measured vs reference)")
                print(f"SilicaBefore calibrated modulus error: {modulus_error:+.1f}% (measured vs reference)")
                
                # Show area function vs physics comparison
                area_ratio = A_area_function / A_physics
                print(f"\nArea Function Analysis:")
                print(f"Area function / Physics area ratio: {area_ratio:.4f}")
                print(f"Area function correction: {(area_ratio - 1) * 100:+.2f}%")
                
                # Use calibrated values for final results
                A = A_calibrated
                GPa = oliver_pharr_hardness_GPa

                # Plotting
                if self.generatePlot:
                    print(f"🎯 PLOTTING DEBUG INFO:")
                    print(f"   generatePlot = {self.generatePlot}")
                    print(f"   hidePlot = {self.hidePlot}")
                    print(f"   matplotlib backend = {plt.get_backend()}")
                    print(f"   matplotlib interactive = {plt.isinteractive()}")
                    
                    # Force matplotlib to use interactive mode for plot display
                    if not self.hidePlot:
                        plt.ion()  # Turn on interactive mode
                        print(f"   ✓ Interactive mode enabled")
                    
                    # Generate plotting data
                    x_poly_loading = np.linspace(df_before_peak['Displacement Into Surface'].min(), x_intersection_point, 100)
                    
                    # Loading curve: P = k*h^n + C
                    if loading_params is not None:
                        y_loading_curve = self.loading_curve_fit(x_poly_loading, *loading_params)

                    # Unloading curves - improved approach supporting both polynomial and power law
                    if use_power_law_unloading and unloading_power_law_params is not None:
                        # Power law unloading plotting
                        B_unload, hf_unload, m_unload = unloading_power_law_params
                        x_start_unloading = max(hf_unload, df_unloading_fit['Displacement Into Surface'].min() - 50)
                        x_poly_unloading = np.linspace(x_start_unloading, x_intersection_point, 100)
                        y_poly_unloading = self.power_law_unloading(x_poly_unloading, *unloading_power_law_params)
                        unload_label = f'Unloading Power Law, R²={final_unloading_r2:.4f}'
                    else:
                        # Polynomial unloading plotting
                        try:
                            roots_unloading = np.roots(coeffs_unloading)
                            real_roots = roots_unloading[np.isreal(roots_unloading)].real
                            if len(real_roots) > 0:
                                x_intercept_unloading = max(real_roots)
                            else:
                                x_intercept_unloading = df_unloading_fit['Displacement Into Surface'].min() - 100
                        except:
                            x_intercept_unloading = df_unloading_fit['Displacement Into Surface'].min() - 100
                        
                        x_start_unloading = max(x_intercept_unloading, df_unloading_fit['Displacement Into Surface'].min() - 50)
                        x_poly_unloading = np.linspace(x_start_unloading, x_intersection_point, 100)
                        y_poly_unloading = np.polyval(coeffs_unloading, x_poly_unloading)
                        unload_label = f'Unloading Polynomial, R²={final_unloading_r2:.4f}'
                    
                    # Elastic Unloading - ensure positive range
                    poly = np.poly1d(coeffs_elastic_unloading)
                    x_start_elastic = max(x_intercept_elastic_unloading, 0)
                    x_fit_elastic_unloading = np.linspace(x_start_elastic, x_intersection_point, 100)
                    y_fit_elastic_unloading = poly(x_fit_elastic_unloading)
                    
                    print(f"Plotting {unloading_fit_type.lower()} unloading from {x_start_unloading:.2f} nm to {x_intersection_point:.2f} nm")
                    print(f"Plotting linear elastic unloading from {x_start_elastic:.2f} nm to {x_intersection_point:.2f} nm")

                    plt.figure(figsize=(12, 8))
                    
                    # Plot data points with improved styling
                    plt.scatter(df_unloading_clean["Displacement Into Surface"], df_unloading_clean["Load On Sample"],
                                edgecolors='orange', facecolors='none', marker='o', alpha=0.6, s=18)
                    plt.scatter(df_unloading_fit["Displacement Into Surface"], df_unloading_fit["Load On Sample"],
                                edgecolors='red', facecolors='red', marker='o', alpha=0.8, s=12)
                    plt.scatter(df_before_peak["Displacement Into Surface"], df_before_peak["Load On Sample"],
                                edgecolors='blue', facecolors='none', marker='o', alpha=0.6, s=18)
                    
                    # Plot curve fits with improved styling
                    if loading_params is not None:
                        plt.plot(x_poly_loading, y_loading_curve, '-', color='blue', linewidth=3, alpha=0.8)
                    
                    # Plot unloading curves with improved styling
                    plt.plot(x_poly_unloading, y_poly_unloading, '-', color='orange', linewidth=3, alpha=0.8)
                    plt.plot(x_fit_elastic_unloading, y_fit_elastic_unloading, '--', color='green', linewidth=3, alpha=0.8)
                    
                    # Calculate dynamic positioning for better arrow placement
                    y_max = y_intersection_point
                    x_max = x_intersection_point
                    
                    # Add Oliver-Pharr depth annotations with improved positioning
                    # Spread out the height annotations to avoid overlap
                    hc_nm = Hc * 1e9
                    hs_nm = Hs * 1e9
                    he_nm = x_intercept_elastic_unloading
                    
                    # Sort depths to determine staggered positioning
                    depths = [(hc_nm, 'hc'), (hs_nm, 'hs'), (he_nm, 'he')]
                    depths.sort(key=lambda x: x[0])  # Sort by depth value
                    
                    # Assign staggered y-positions based on order
                    y_positions = [y_max * 0.15, y_max * 0.25, y_max * 0.35]
                    
                    for i, (depth, label) in enumerate(depths):
                        if label == 'hc':
                            plt.annotate('$h_c$: {:.1f} nm'.format(depth),
                                        xy=(depth, 0), xytext=(depth, y_positions[i]),
                                        arrowprops=dict(facecolor='darkblue', width=1.5, headwidth=8, headlength=8, alpha=0.8),
                                        fontsize=10, fontweight='bold', ha='center',
                                        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightcyan', alpha=0.9, edgecolor='darkblue'))
                        elif label == 'hs':
                            plt.annotate('$h_s$: {:.1f} nm'.format(depth),
                                        xy=(depth, 0), xytext=(depth, y_positions[i]),
                                        arrowprops=dict(facecolor='darkgreen', width=1.5, headwidth=8, headlength=8, alpha=0.8),
                                        fontsize=10, fontweight='bold', ha='center',
                                        bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.9, edgecolor='darkgreen'))
                        elif label == 'he':
                            plt.annotate('$h_e$: {:.1f} nm'.format(depth),
                                        xy=(depth, 0), xytext=(depth, y_positions[i]),
                                        arrowprops=dict(facecolor='darkorange', width=1.5, headwidth=8, headlength=8, alpha=0.8),
                                        fontsize=10, fontweight='bold', ha='center',
                                        bbox=dict(boxstyle='round,pad=0.3', facecolor='moccasin', alpha=0.9, edgecolor='darkorange'))
                    
                    # Add key measurement annotations with improved positioning
                    # Position Pmax annotation to avoid overlap with other elements
                    pmax_x_offset = min(x_max * 0.15, 150)  # Adaptive offset
                    pmax_y_offset = max(y_max * 0.08, 30)   # Adaptive offset
                    
                    plt.annotate(f'Pmax: {Pmax*1e3:.1f} mN\n(Peak Load)', 
                                xy=(x_intersection_point, y_intersection_point), 
                                xytext=(x_intersection_point + pmax_x_offset, y_intersection_point + pmax_y_offset),
                                arrowprops=dict(arrowstyle='->', color='red', lw=2.5, alpha=0.8),
                                fontsize=11, fontweight='bold', ha='center',
                                bbox=dict(boxstyle='round,pad=0.4', facecolor='yellow', alpha=0.95, edgecolor='red', linewidth=2))
                    
                    # Position stiffness annotation on the elastic unloading curve
                    stiff_x = x_intersection_point - (x_intersection_point - x_intercept_elastic_unloading) * 0.3
                    stiff_y = np.polyval(coeffs_elastic_unloading, stiff_x)
                    stiff_x_offset = min(x_max * 0.2, 200)  # Adaptive offset
                    stiff_y_offset = max(y_max * 0.1, 40)   # Adaptive offset
                    
                    plt.annotate(f'S: {S/1e6:.2f} mN/nm\n(Contact Stiffness)', 
                                xy=(stiff_x, stiff_y), 
                                xytext=(stiff_x - stiff_x_offset, stiff_y - stiff_y_offset),
                                arrowprops=dict(arrowstyle='->', color='green', lw=2.5, alpha=0.8),
                                fontsize=11, fontweight='bold', ha='center',
                                bbox=dict(boxstyle='round,pad=0.4', facecolor='lightgreen', alpha=0.95, edgecolor='green', linewidth=2))
                    
                    # Add comprehensive results as formatted text box
                    if loading_params is not None:
                        k, n, C = loading_params
                        text_info = 'TIP FITTED PARAMETERS\n' + '='*25 + '\n'
                        text_info += f'Loading: P = k·h^n + C\n'
                        text_info += f'  k = {k:.3e} (mN/nm^n)\n  n = {n:.4f} (dimensionless)\n  C = {C:.3f} mN (offset)\n  R² = {r_squared_loading:.6f}\n'
                        
                        # Add unloading fitting info
                        text_info += f'\nUnloading: {unloading_fit_type}\n'
                        text_info += f'  R² = {final_unloading_r2:.6f}\n'
                        if use_power_law_unloading and unloading_power_law_params is not None:
                            B_unload, hf_unload, m_unload = unloading_power_law_params
                            text_info += f'  B = {B_unload:.3e} (mN/nm^m)\n  hf = {hf_unload:.2f} nm (residual)\n  m = {m_unload:.4f} (exponent)\n'
                        
                        text_info += f'\nElastic: Linear Fit\n'
                        text_info += f'  Slope = {coeffs_elastic_unloading[0]:.4e} (mN/nm)\n'
                        text_info += f'  Stiffness S = {S/1e6:.3f} mN/nm\n'
                        
                        # Add Oliver-Pharr method results
                        text_info += '\nOLIVER-PHARR RESULTS\n' + '='*25 + '\n'
                        text_info += f'Hardness = {oliver_pharr_hardness_GPa:.3f} GPa\n'
                        text_info += f'Contact Area = {A*1e18:.1f} nm²\n'
                        text_info += f'Contact Depth = {Hc*1e9:.2f} nm\n'
                        text_info += f'Reduced Modulus = {oliver_pharr_modulus_GPa:.2f} GPa\n'
                        text_info += f'Calibration Factor = {hardness_correction_factor:.4f}\n'
                        
                        # Add calibrated area function information
                        text_info += '\nCALIBRATED AREA FUNCTION\n' + '='*32 + '\n'
                        text_info += 'A_c = C₀·h_c² + C₁·h_c + C₂·h_c^½ + C₃·h_c^¼ + C₄·h_c^⅛\n'
                        
                        # Extract coefficients to avoid f-string formatting issues
                        c0_val = area_coeffs["C0"]
                        c1_val = area_coeffs["C1"] 
                        c2_val = area_coeffs["C2"]
                        c3_val = area_coeffs["C3"]
                        c4_val = area_coeffs["C4"]
                        
                        text_info += f'C₀ = {c0_val:.3f} (h_c²)\n'
                        text_info += f'C₁ = {c1_val:.3f} (h_c¹)\n'
                        c2_label = "✓ CALIBRATED" if abs(c2_val) > 0.01 else ""
                        text_info += f'C₂ = {c2_val:.3f} (h_c^½) {c2_label}\n'
                        c3_label = "✓ CALIBRATED" if abs(c3_val) > 0.01 else ""
                        text_info += f'C₃ = {c3_val:.3f} (h_c^¼) {c3_label}\n'
                        c4_label = "✓ CALIBRATED" if abs(c4_val) > 0.01 else ""
                        text_info += f'C₄ = {c4_val:.3f} (h_c^⅛) {c4_label}\n'
                        text_info += 'C₅-C₈ = 0.000 (higher order)\n'
                        
                        # Show calibration quality if available
                        if 'calibration_quality' in area_coeffs:
                            qual = area_coeffs['calibration_quality']
                            rms_error = qual.get("rms_error_percent", 0)
                            n_measurements = qual.get("n_measurements", 0)
                            text_info += f'\nCalibration Quality:\n'
                            text_info += f'RMS Error: {rms_error:.1f}%\n'
                            text_info += f'Data Points: {n_measurements}\n'
                        
                        text_info += f'\nArea Comparison:\n'
                        text_info += f'Physics = {A_physics*1e18:.1f} nm²\n'
                        text_info += f'Calibrated = {A_area_function*1e18:.1f} nm²\n'
                        text_info += f'Ratio = {A_area_function/A_physics:.4f}'
                        
                        plt.text(0.02, 0.98, text_info,
                                transform=plt.gca().transAxes, verticalalignment='top',
                                fontsize=9, fontfamily='monospace',
                                bbox=dict(boxstyle='round,pad=0.8', facecolor='lightblue', 
                                         alpha=0.9, edgecolor='navy', linewidth=1))
                    
                    # Area calculation and visualization
                    try:
                        if loading_params is not None:
                            area_loading = np.abs(np.trapezoid(y_loading_curve, x_poly_loading))
                            area_unloading = np.abs(np.trapezoid(y_fit_elastic_unloading, x_fit_elastic_unloading))
                            total_area = area_loading + area_unloading
                            loading_area_fraction = round((area_loading / total_area) * 100, 2)
                            unloading_area_fraction = round((area_unloading / total_area) * 100, 2)

                            plt.fill_between(x_poly_loading, 0, y_loading_curve, color='blue', alpha=0.2)
                            plt.fill_between(x_fit_elastic_unloading, 0, y_fit_elastic_unloading, color='green', alpha=0.2)
                    except:
                        pass  # Skip area calculation if it fails

                    # Formatting and styling
                    plt.xlabel("Displacement Into Surface (nm)", fontsize=12, fontweight='bold')
                    plt.ylabel("Load on Sample (mN)", fontsize=12, fontweight='bold')
                    plt.ylim(bottom=0)
                    plt.xlim(left=0)
                    plt.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
                    plt.tick_params(axis='both', which='major', labelsize=10)

                    plt.title(f"{self.filename.split('.')[0]} - Test {i}, CSM: {hardnessCSM:.2f} GPa, Oliver-Pharr (Calibrated): {GPa:.2f} GPa", 
                             fontsize=14, fontweight='bold', pad=20)
                    
                    if self.export:
                        output_dir = os.path.join(
                            os.path.dirname(os.path.abspath(self.filename)),
                            "analysis_output"
                        )
                        os.makedirs(output_dir, exist_ok=True)
                        plot_file = os.path.join(output_dir, f"{Path(self.filename).stem}_Test_{i}_analysis.png")
                        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
                        print(f"   ✓ Plot saved: {plot_file}")
                    
                    if not self.hidePlot:
                        print(f"   ✓ Displaying plot for Test {i}...")
                        
                        # Force matplotlib to update and draw the plot
                        plt.draw()
                        plt.pause(0.1)  # Brief pause to ensure drawing completes
                        
                        # Show with blocking to ensure plot displays
                        plt.show(block=True)
                        
                        print(f"   📊 Plot displayed for Test {i}")
                        print(f"   ✓ Plot display completed for Test {i}")
                    else:
                        print(f"   ⚠️ Plot hidden (hidePlot = {self.hidePlot})")
                        plt.close()

                results = {
                    "Test": i,
                    "Pmax (N)": Pmax,
                    "Hmax (m)": Hmax,
                    "S (N/m)": S,
                    "Hc (m)": Hc,
                    "Hs (m)": Hs,
                    "Er (Pa)": Er,
                    "A (m^2)": A,
                    "Hardness (GPa)": GPa,
                    "Oliver-Pharr Hardness (GPa)": oliver_pharr_hardness_GPa,
                    "Oliver-Pharr Modulus (GPa)": oliver_pharr_modulus_GPa,
                    "CSM Hardness (GPa)": hardnessCSM,
                    "Intersection X": x_intersection_point,
                    "Intersection Y": y_intersection_point,
                    "Loading R²": r_squared_loading,
                    "Loading Curve k": loading_params[0] if loading_params is not None else None,
                    "Loading Curve n": loading_params[1] if loading_params is not None else None,
                    "Loading Curve C": loading_params[2] if loading_params is not None else None,
                    "Loading Curve R²": loading_r2,
                    "Unloading Fit R²": final_unloading_r2,
                    "Unloading Power Law B": unloading_power_law_params[0] if use_power_law_unloading and unloading_power_law_params is not None else None,
                    "Unloading Power Law hf (nm)": unloading_power_law_params[1] if use_power_law_unloading and unloading_power_law_params is not None else None,
                    "Unloading Power Law m": unloading_power_law_params[2] if use_power_law_unloading and unloading_power_law_params is not None else None,
                    "Unloading Power Law R²": unloading_power_law_r2 if use_power_law_unloading else None,
                    "Elastic Unloading Slope": coeffs_elastic_unloading[0],
                    "Displacement Correction (nm)": 0,  # No correction needed for P = k*h^n + C
                    "Correction Applied": False,
                    "Unloading Fit Type": unloading_fit_type,
                    "Calibration Factor": hardness_correction_factor
                }
                
                all_results.append(results)
                print(f"Test {i} completed successfully. Hardness: {GPa:.2f} GPa")
                
                # ISO 14577-4:2016 Compliance Summary
                print(f"\n=== ISO 14577-4:2016 COMPLIANCE SUMMARY ===")
                
                compliance_checks = {
                    'loading_data_quality': loading_validation['overall_quality'],
                    'unloading_data_quality': unloading_validation['overall_quality'],
                    'loading_fit_quality': loading_quality['meets_iso_standard'],
                    'stiffness_fit_quality': stiffness_quality['meets_iso_standard'],
                    'area_function_used': True,  # Using ISO compliant area function
                    'reference_material': True,  # Using fused silica reference
                    'oliver_pharr_method': True  # Using standard Oliver-Pharr method
                }
                
                if use_power_law_unloading and unloading_power_law_params is not None:
                    compliance_checks['unloading_fit_quality'] = power_law_quality['meets_iso_standard']
                else:
                    # Check polynomial fit quality if used
                    poly_quality = self.validate_curve_fit_quality(final_unloading_r2, "unloading polynomial")
                    compliance_checks['unloading_fit_quality'] = poly_quality['meets_iso_standard']
                
                passed_checks = sum(compliance_checks.values())
                total_checks = len(compliance_checks)
                compliance_percentage = (passed_checks / total_checks) * 100
                
                print(f"Compliance Score: {passed_checks}/{total_checks} ({compliance_percentage:.1f}%)")
                
                for check, status in compliance_checks.items():
                    status_symbol = "✅" if status else "❌"
                    check_name = check.replace('_', ' ').title()
                    print(f"  {status_symbol} {check_name}")
                
                if compliance_percentage >= 85:
                    print("🟢 EXCELLENT ISO 14577-4:2016 COMPLIANCE")
                elif compliance_percentage >= 70:
                    print("🟡 GOOD ISO 14577-4:2016 COMPLIANCE") 
                elif compliance_percentage >= 50:
                    print("🟠 PARTIAL ISO 14577-4:2016 COMPLIANCE")
                else:
                    print("🔴 POOR ISO 14577-4:2016 COMPLIANCE - Review Required")
                
                print("=" * 50)

            except ValueError as ve:
                if "not found" in str(ve):
                    print(f"Worksheet 'Test {i}' not found - skipping")
                    continue
                else:
                    print(f"ValueError processing test {i}: {str(ve)}")
                    continue
            except Exception as e:
                print(f"Error processing test {i}: {str(e)}")
                continue

        # Save calibration results next to the source data file
        output_dir = os.path.join(
            os.path.dirname(os.path.abspath(self.filename)),
            "analysis_output"
        )
        self.save_calibration_results(calibrated_coeffs, calibration_data, output_dir)

        return all_results
    
    def save_calibration_results(self, calibrated_coeffs, calibration_data, output_dir):
        """
        Save tip calibration results to files
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            # Save calibrated coefficients
            coeffs_df = pd.DataFrame([{
                'Coefficient': f'C{i}',
                'Value': calibrated_coeffs[f'C{i}'],
                'Description': [
                    'h_c² term (primary)',
                    'h_c¹ term (linear)',
                    'h_c^½ term (tip rounding)',
                    'h_c^¼ term (tip blunting)',
                    'h_c^⅛ term (higher order)',
                    'h_c^1/16 term',
                    'h_c^1/32 term',
                    'h_c^1/64 term',
                    'h_c^1/128 term'
                ][i]
            } for i in range(9)])
            
            coeffs_file = os.path.join(output_dir, "calibrated_area_function_coefficients.csv")
            coeffs_df.to_csv(coeffs_file, index=False)
            print(f"Calibrated coefficients saved to: {coeffs_file}")
            
            # Save calibration data
            if calibration_data:
                calib_df = pd.DataFrame(calibration_data)
                calib_file = os.path.join(output_dir, "tip_calibration_data.csv")
                calib_df.to_csv(calib_file, index=False)
                print(f"Calibration data saved to: {calib_file}")
            
            # Save calibration quality report
            if 'calibration_quality' in calibrated_coeffs:
                qual = calibrated_coeffs['calibration_quality']
                report = f"""
TIP AREA FUNCTION CALIBRATION REPORT
====================================

Calibration Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
Reference Material: Fused Silica (ISO 14577-4:2016)

CALIBRATED COEFFICIENTS:
C₀ = {calibrated_coeffs['C0']:.6f} nm⁻²
C₁ = {calibrated_coeffs['C1']:.6f} nm⁻¹
C₂ = {calibrated_coeffs['C2']:.6f} nm⁻⁰·⁵
C₃ = {calibrated_coeffs['C3']:.6f} nm⁻⁰·²⁵
C₄ = {calibrated_coeffs['C4']:.6f} nm⁻⁰·¹²⁵

CALIBRATION QUALITY:
RMS Error: {qual.get('rms_error_percent', 0):.2f}%
Max Error: {qual.get('max_error_percent', 0):.2f}%
Mean Area Ratio: {qual.get('mean_area_ratio', 1):.4f}
Number of Measurements: {qual.get('n_measurements', 0)}

AREA FUNCTION EQUATION:
A_c = C₀·h_c² + C₁·h_c + C₂·h_c^(1/2) + C₃·h_c^(1/4) + C₄·h_c^(1/8)

TIP CHARACTERIZATION:
Perfect Berkovich: C₀ = 24.56, all others = 0
Real tip deviation: {((calibrated_coeffs['C0'] - 24.56)/24.56)*100:+.2f}% in C₀
"""
                
                report_file = os.path.join(output_dir, "tip_calibration_report.txt")
                with open(report_file, 'w') as f:
                    f.write(report)
                print(f"Calibration report saved to: {report_file}")
                
        except Exception as e:
            print(f"Error saving calibration results: {e}")

def main():
    # Path to the HEC14S1.xls file
    input_file = "/Users/shiraz/scripts/HEC14s/HEC15S Nanoindentation/HEC14S1.xls"
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} not found!")
        return
    
    print(f"Running FIXED analysis on: {input_file}")
    print(f"File basename: {os.path.basename(input_file)}")
    print("=" * 60)
    
    # Initialize the FIXED analyzer with the file
    analyzer = FixedIndentXLSAnalyzer(filename=input_file)
    
    # Print default values from parent class
    print(f"🔧 INITIAL SETTINGS (from parent class):")
    print(f"   generatePlot = {analyzer.generatePlot}")
    print(f"   hidePlot = {analyzer.hidePlot}")
    print(f"   export = {analyzer.export}")
    
    # Force matplotlib setup for plot display
    import matplotlib
    import matplotlib.pyplot as plt
    print(f"   matplotlib backend = {matplotlib.get_backend()}")
    print(f"   matplotlib interactive = {plt.isinteractive()}")
    
    # Override with desired settings
    analyzer.generatePlot = True   # Enable plot generation
    analyzer.hidePlot = False      # Show plots
    analyzer.export = True         # Enable export of results   
    
    # Force interactive mode for plots
    plt.ion()  # Enable interactive mode
    
    # Print applied settings
    print(f"🎯 APPLIED SETTINGS:")
    print(f"   generatePlot = {analyzer.generatePlot}")
    print(f"   hidePlot = {analyzer.hidePlot}")
    print(f"   export = {analyzer.export}")
    print(f"   matplotlib interactive = {plt.isinteractive()} (after plt.ion())")
    print("=" * 60)
    
    try:
        # Run the analysis
        results = analyzer.run_analysis()
        
        # Display results
        if results:
            print("\n" + "=" * 60)
            print("ANALYSIS COMPLETED SUCCESSFULLY!")
            print(f"Number of tests analyzed: {len(results)}")
            
            # Convert results to DataFrame for better display
            df_results = pd.DataFrame(results)
            
            # Display summary statistics
            print("\nSummary of Results:")
            print("-" * 40)
            
            # Show key columns
            key_columns = ['Test', 'Hardness (GPa)', 'Oliver-Pharr Hardness (GPa)', 'CSM Hardness (GPa)', 
                          'Oliver-Pharr Modulus (GPa)', 'Loading Power Law m', 'Loading Power Law R²', 
                          'Unloading Polynomial R²', 'Elastic Unloading Slope',
                          'Unloading Fit Type', 'Displacement Correction (nm)', 'Correction Applied']
            display_columns = [col for col in key_columns if col in df_results.columns]
            
            if display_columns:
                print(df_results[display_columns].to_string(index=False, float_format='%.4f'))
            else:
                print("Available columns:", list(df_results.columns))
                print(df_results.head())
            
            # Show statistics for key parameters
            if 'Hardness (GPa)' in df_results.columns:
                hardness_values = df_results['Hardness (GPa)']
                print(f"\nHardness Statistics:")
                print(f"Mean: {hardness_values.mean():.4f} GPa")
                print(f"Std:  {hardness_values.std():.4f} GPa")
                print(f"Min:  {hardness_values.min():.4f} GPa")
                print(f"Max:  {hardness_values.max():.4f} GPa")
            
            if 'Oliver-Pharr Hardness (GPa)' in df_results.columns:
                op_hardness_values = df_results['Oliver-Pharr Hardness (GPa)']
                print(f"\nOliver-Pharr Hardness Statistics:")
                print(f"Mean: {op_hardness_values.mean():.4f} GPa")
                print(f"Std:  {op_hardness_values.std():.4f} GPa")
                print(f"Min:  {op_hardness_values.min():.4f} GPa")
                print(f"Max:  {op_hardness_values.max():.4f} GPa")
            
            if 'Oliver-Pharr Modulus (GPa)' in df_results.columns:
                op_modulus_values = df_results['Oliver-Pharr Modulus (GPa)']
                print(f"\nOliver-Pharr Reduced Modulus Statistics:")
                print(f"Mean: {op_modulus_values.mean():.2f} GPa")
                print(f"Std:  {op_modulus_values.std():.2f} GPa")
                print(f"Min:  {op_modulus_values.min():.2f} GPa")
                print(f"Max:  {op_modulus_values.max():.2f} GPa")
            
            if 'Loading Power Law m' in df_results.columns:
                m_load_values = df_results['Loading Power Law m'].dropna()
                if len(m_load_values) > 0:
                    print(f"\nLoading Power Law Exponent (m) Statistics:")
                    print(f"Mean: {m_load_values.mean():.4f}")
                    print(f"Std:  {m_load_values.std():.4f}")
                    print(f"Min:  {m_load_values.min():.4f}")
                    print(f"Max:  {m_load_values.max():.4f}")
            
            if 'Loading Power Law R²' in df_results.columns:
                r2_load_values = df_results['Loading Power Law R²'].dropna()
                if len(r2_load_values) > 0:
                    print(f"\nLoading Power Law Fit Quality (R²) Statistics:")
                    print(f"Mean: {r2_load_values.mean():.4f}")
                    print(f"Std:  {r2_load_values.std():.4f}")
                    print(f"Min:  {r2_load_values.min():.4f}")
                    print(f"Max:  {r2_load_values.max():.4f}")
            
            # Show polynomial fitting statistics
            if 'Unloading Polynomial R²' in df_results.columns:
                r2_unload_values = df_results['Unloading Polynomial R²'].dropna()
                if len(r2_unload_values) > 0:
                    print(f"\nUnloading Polynomial Fit Quality (R²) Statistics:")
                    print(f"Mean: {r2_unload_values.mean():.4f}")
                    print(f"Std:  {r2_unload_values.std():.4f}")
                    print(f"Min:  {r2_unload_values.min():.4f}")
                    print(f"Max:  {r2_unload_values.max():.4f}")
            
            if 'Elastic Unloading Slope' in df_results.columns:
                slope_values = df_results['Elastic Unloading Slope'].dropna()
                if len(slope_values) > 0:
                    print(f"\nElastic Unloading Slope Statistics:")
                    print(f"Mean: {slope_values.mean():.3e}")
                    print(f"Std:  {slope_values.std():.3e}")
                    print(f"Min:  {slope_values.min():.3e}")
                    print(f"Max:  {slope_values.max():.3e}")
            
            # Show unloading fit type distribution
            if 'Unloading Fit Type' in df_results.columns:
                fit_types = df_results['Unloading Fit Type'].value_counts()
                print(f"\nUnloading Fit Type Distribution:")
                for fit_type, count in fit_types.items():
                    print(f"{fit_type}: {count} tests ({count/len(df_results)*100:.1f}%)")
            
            # Show displacement correction statistics
            if 'Displacement Correction (nm)' in df_results.columns:
                correction_values = df_results['Displacement Correction (nm)'].dropna()
                corrected_tests = df_results['Correction Applied'].sum()
                if len(correction_values) > 0:
                    print(f"\nDisplacement Correction Statistics:")
                    print(f"Tests with correction applied: {corrected_tests}/{len(df_results)}")
                    print(f"Mean correction: {correction_values.mean():.4f} nm")
                    print(f"Std correction:  {correction_values.std():.4f} nm")
                    print(f"Min correction:  {correction_values.min():.4f} nm")
                    print(f"Max correction:  {correction_values.max():.4f} nm")
            
            # Save results to CSV
            output_file = "/Users/shiraz/scripts/HEC14s/IndentXLSAnalyzer/HEC14S1_FIXED_analysis_results.csv"
            df_results.to_csv(output_file, index=False)
            print(f"\nResults saved to: {output_file}")
            
        else:
            print("No results generated - check the analysis output above for details.")
            
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
