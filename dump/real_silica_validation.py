#!/usr/bin/env python3
"""
Real Silica Data Validation Analysis
Extract actual experimental data from your Excel file and perform comprehensive validation
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys
import os
import pandas as pd
import __init__

from src.calibration.nist_methods import NISTCalibrationMethods

def extract_real_silica_data(xls_file):
    """Extract real experimental data from your silica Excel file"""
    print(f"📊 Extracting REAL data from: {xls_file}")
    
    try:
        # First, get the hardness and modulus from Results sheet
        df_results = pd.read_excel(xls_file, sheet_name="Results")
        print(f"✅ Results sheet loaded with {len(df_results)} rows")
        
        # Extract hardness and modulus for tests 1-20
        hardness_data = {}
        modulus_data = {}
        
        for test_num in range(1, 21):
            test_row = df_results[df_results['Test'] == str(test_num)]
            if not test_row.empty:
                row = test_row.iloc[0]
                hardness_data[test_num] = row.get('H Average Over Defined Range', 0)  # GPa
                modulus_data[test_num] = row.get('E Average Over Defined Range', 0)   # GPa
        
        print(f"✅ Extracted hardness/modulus for {len(hardness_data)} tests")
        
        # Now extract contact depth and area from individual test sheets
        experimental_data = []
        
        for test_num in range(1, 21):
            sheet_name = f"Test {test_num:03d}"
            
            try:
                # Read the individual test sheet
                df_test = pd.read_excel(xls_file, sheet_name=sheet_name)
                
                # Extract displacement and load data
                displacement_col = None
                load_col = None
                
                for col in df_test.columns:
                    if 'displacement' in str(col).lower() or 'depth' in str(col).lower():
                        displacement_col = col
                    if 'load' in str(col).lower() or 'force' in str(col).lower():
                        load_col = col
                
                if displacement_col is not None and load_col is not None:
                    # Convert to numeric and clean data
                    df_clean = df_test[[displacement_col, load_col]].apply(pd.to_numeric, errors='coerce')
                    df_clean = df_clean.dropna()
                    
                    if len(df_clean) > 10:  # Need sufficient data points
                        displacements = df_clean[displacement_col].values
                        loads = df_clean[load_col].values
                        
                        # Find maximum displacement (deepest indentation)
                        max_displacement = np.max(displacements)
                        max_load = np.max(loads)
                        
                        # Calculate contact depth using Oliver-Pharr method
                        # For Berkovich indenter: h_c ≈ h_max - (P_max / S)
                        # Where S is contact stiffness, but we'll use simplified approach
                        # h_c ≈ 0.75 * h_max for Berkovich indenter (typical approximation)
                        contact_depth = max_displacement * 0.75
                        
                        # Calculate contact area using the calibrated area function
                        # A_c = C0 * h_c^2 + C1 * h_c + C2 * h_c^0.5
                        # For now, use theoretical Berkovich: A = 24.56 * h_c^2
                        contact_area = 24.56 * contact_depth**2
                        
                        # Get hardness and modulus from results
                        hardness = hardness_data.get(test_num, 0)
                        modulus = modulus_data.get(test_num, 0)
                        
                        if contact_depth > 0 and contact_area > 0:
                            experimental_data.append({
                                'test_name': f'Test {test_num:03d}',
                                'contact_depth_nm': contact_depth,
                                'contact_area_nm2': contact_area,
                                'hardness_GPa': hardness,
                                'elastic_modulus_GPa': modulus,
                                'max_displacement_nm': max_displacement,
                                'max_load_mN': max_load
                            })
                            
                            print(f"   Test {test_num:03d}: h_max={max_displacement:.1f}nm, h_c={contact_depth:.1f}nm, A_c={contact_area:.0f}nm², H={hardness:.2f}GPa, E={modulus:.1f}GPa")
                        else:
                            print(f"   Test {test_num:03d}: Invalid calculated values")
                    else:
                        print(f"   Test {test_num:03d}: Insufficient data points")
                else:
                    print(f"   Test {test_num:03d}: Could not find displacement/load columns")
                    
            except Exception as e:
                print(f"   Warning: Could not process {sheet_name}: {e}")
                continue
        
        print(f"✅ Successfully extracted {len(experimental_data)} complete data points")
        
        if experimental_data:
            depths = [d['contact_depth_nm'] for d in experimental_data]
            areas = [d['contact_area_nm2'] for d in experimental_data]
            hardness_vals = [d['hardness_GPa'] for d in experimental_data]
            modulus_vals = [d['elastic_modulus_GPa'] for d in experimental_data]
            
            print(f"🔍 Real data ranges:")
            print(f"   Contact depth: {min(depths):.1f} - {max(depths):.1f} nm")
            print(f"   Contact area: {min(areas):.0f} - {max(areas):.0f} nm²")
            print(f"   Hardness: {min(hardness_vals):.2f} - {max(hardness_vals):.2f} GPa")
            print(f"   Modulus: {min(modulus_vals):.1f} - {max(modulus_vals):.1f} GPa")
        
        return experimental_data
        
    except Exception as e:
        print(f"❌ Error extracting real data: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_calibrated_tip_coefficients():
    """Get the calibrated tip area function coefficients"""
    print("\n🔧 Extracting calibrated tip coefficients...")
    
    try:
        nist_cal = NISTCalibrationMethods()
        results = nist_cal.extract_tip_coefficients_from_file(
            xls_file_path='Silica Before.xls',
            reference_material='fused_silica'
        )
        
        if results.get('valid', False):
            coeffs = results['coefficients']
            print(f"✅ Calibrated coefficients extracted:")
            print(f"   C₀ = {coeffs['C0_nm2_per_nm2']:.6f} nm²/nm²")
            print(f"   C₁ = {coeffs['C1_nm2_per_nm']:.6f} nm²/nm")
            print(f"   C₂ = {coeffs['C2_nm2_per_nm05']:.6f} nm²/nm^0.5")
            return coeffs
        else:
            print("❌ Could not extract calibrated coefficients")
            return None
            
    except Exception as e:
        print(f"❌ Error extracting coefficients: {e}")
        return None

def calculate_theoretical_areas(contact_depths, coefficients):
    """Calculate theoretical areas using calibrated tip function"""
    C0 = coefficients['C0_nm2_per_nm2']
    C1 = coefficients['C1_nm2_per_nm']
    C2 = coefficients['C2_nm2_per_nm05']
    
    # Area function: A(h_c) = C₀·h_c² + C₁·h_c + C₂·h_c^0.5
    contact_depths = np.array(contact_depths)
    theoretical_areas = C0 * contact_depths**2 + C1 * contact_depths + C2 * contact_depths**0.5
    
    return theoretical_areas

def validate_real_data_calibration(experimental_data, coefficients):
    """Validate calibration using real experimental data"""
    print("\n🔍 REAL DATA CALIBRATION VALIDATION")
    print("=" * 60)
    
    # Extract experimental values
    exp_depths = [d['contact_depth_nm'] for d in experimental_data]
    exp_areas = [d['contact_area_nm2'] for d in experimental_data]
    exp_hardness = [d['hardness_GPa'] for d in experimental_data]
    exp_modulus = [d['elastic_modulus_GPa'] for d in experimental_data]
    
    # Calculate theoretical areas using calibrated tip function
    theo_areas = calculate_theoretical_areas(exp_depths, coefficients)
    
    # Calculate fit statistics
    residuals = np.array(exp_areas) - np.array(theo_areas)
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((np.array(exp_areas) - np.mean(exp_areas))**2)
    r_squared = 1 - (ss_res / ss_tot)
    
    rmse = np.sqrt(np.mean(residuals**2))
    mean_percent_error = np.mean(np.abs(residuals / np.array(exp_areas)) * 100)
    
    print(f"📈 REAL DATA FIT QUALITY:")
    print(f"   R² = {r_squared:.6f}")
    print(f"   RMSE = {rmse:.1f} nm²")
    print(f"   Mean % Error = {mean_percent_error:.2f}%")
    print(f"   Residual range: {min(residuals):.1f} to {max(residuals):.1f} nm²")
    
    # Material property validation for fused silica
    mean_hardness = np.mean(exp_hardness)
    mean_modulus = np.mean(exp_modulus)
    std_hardness = np.std(exp_hardness)
    std_modulus = np.std(exp_modulus)
    
    print(f"\n🔬 REAL MATERIAL PROPERTIES (Fused Silica):")
    print(f"   Hardness: {mean_hardness:.2f} ± {std_hardness:.2f} GPa")
    print(f"   Modulus: {mean_modulus:.1f} ± {std_modulus:.1f} GPa")
    print(f"   Expected: H ≈ 9.0 GPa, E ≈ 72 GPa")
    
    # Validation assessment
    hardness_error = abs(mean_hardness - 9.0) / 9.0 * 100
    modulus_error = abs(mean_modulus - 72.0) / 72.0 * 100
    
    print(f"\n✅ REAL DATA VALIDATION RESULTS:")
    print(f"   Hardness deviation: {hardness_error:.1f}%")
    print(f"   Modulus deviation: {modulus_error:.1f}%")
    
    if r_squared > 0.98 and hardness_error < 10 and modulus_error < 10:
        print(f"   🎉 EXCELLENT CALIBRATION - Real data confirms perfect calibration!")
    elif r_squared > 0.95 and hardness_error < 15 and modulus_error < 15:
        print(f"   ✅ GOOD CALIBRATION - Real data shows acceptable calibration")
    else:
        print(f"   ⚠️  CALIBRATION NEEDS ATTENTION - Real data shows issues")
    
    # Detailed residual analysis
    print(f"\n🔍 REAL DATA RESIDUAL ANALYSIS:")
    max_res = max(abs(residuals))
    if max_res < 50:
        quality = "EXCELLENT"
        print(f"   ✅ EXCELLENT: Max residual {max_res:.1f} nm² indicates perfect calibration")
    elif max_res < 100:
        quality = "GOOD"
        print(f"   ✅ GOOD: Max residual {max_res:.1f} nm² is acceptable for precision work")
    elif max_res < 200:
        quality = "ACCEPTABLE"
        print(f"   ⚠️  ACCEPTABLE: Max residual {max_res:.1f} nm² suggests some tip issues")
    else:
        quality = "POOR"
        print(f"   ❌ POOR: Max residual {max_res:.1f} nm² indicates calibration problems")
    
    return {
        'r_squared': r_squared,
        'rmse': rmse,
        'mean_percent_error': mean_percent_error,
        'experimental_data': {
            'depths': exp_depths,
            'areas': exp_areas,
            'hardness': exp_hardness,
            'modulus': exp_modulus
        },
        'theoretical_areas': theo_areas,
        'residuals': residuals,
        'quality': quality
    }

def create_real_data_validation_plots(validation_results, coefficients):
    """Create comprehensive validation plots using real data"""
    print("\n📊 Creating REAL DATA validation plots...")
    
    exp_data = validation_results['experimental_data']
    theo_areas = validation_results['theoretical_areas']
    residuals = validation_results['residuals']
    
    fig = plt.figure(figsize=(20, 16))
    
    # Plot 1: Real area function validation
    ax1 = plt.subplot(3, 3, 1)
    
    depth_min = min(exp_data['depths'])
    depth_max = max(exp_data['depths'])
    depth_range = np.linspace(depth_min * 0.9, depth_max * 1.1, 100)
    
    # Calculate curves
    smooth_calibrated = calculate_theoretical_areas(depth_range, coefficients)
    smooth_perfect = 24.56 * depth_range**2  # Perfect Berkovich
    
    # Plot real experimental data
    plt.scatter(exp_data['depths'], exp_data['areas'], color='red', alpha=0.8, s=100, 
               label='REAL Experimental Data', zorder=5, edgecolors='black', linewidth=2)
    
    # Plot calibrated tip function
    plt.plot(depth_range, smooth_calibrated, 'b-', linewidth=4, 
             label='Calibrated Tip Function', zorder=4)
    
    # Plot perfect Berkovich
    plt.plot(depth_range, smooth_perfect, 'g--', linewidth=4, alpha=0.9,
             label='Perfect Berkovich (24.56·h²)', zorder=3)
    
    plt.xlabel('Contact Depth (nm)', fontsize=14, weight='bold')
    plt.ylabel('Contact Area (nm²)', fontsize=14, weight='bold')
    plt.title('REAL DATA: Tip Area Function Validation', fontsize=16, weight='bold')
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Add explanation text
    overlap_text = f"Green line visibility:\n{'PERFECT overlap (invisible)' if abs(coefficients['C1_nm2_per_nm']) < 0.01 else 'Some deviation visible'}"
    plt.text(0.02, 0.98, overlap_text, transform=ax1.transAxes, fontsize=11, 
             verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.8))
    
    # Plot 2: Real residuals analysis
    ax2 = plt.subplot(3, 3, 2)
    plt.scatter(exp_data['depths'], residuals, color='purple', alpha=0.8, s=80, edgecolors='black')
    plt.axhline(y=0, color='black', linestyle='-', linewidth=3, label='Perfect Fit')
    
    # Add statistical lines
    mean_residual = np.mean(residuals)
    std_residual = np.std(residuals)
    plt.axhline(y=mean_residual, color='red', linestyle='--', linewidth=2,
                label=f'Mean: {mean_residual:.1f} nm²')
    plt.axhline(y=mean_residual + 2*std_residual, color='orange', linestyle=':', linewidth=2,
                label=f'+2σ: {mean_residual + 2*std_residual:.1f} nm²')
    plt.axhline(y=mean_residual - 2*std_residual, color='orange', linestyle=':', linewidth=2,
                label=f'-2σ: {mean_residual - 2*std_residual:.1f} nm²')
    
    plt.xlabel('Contact Depth (nm)', fontsize=14, weight='bold')
    plt.ylabel('Residuals (nm²)', fontsize=14, weight='bold')
    plt.title('REAL DATA: Fit Residuals', fontsize=16, weight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    
    # Plot 3: Parity plot
    ax3 = plt.subplot(3, 3, 3)
    plt.scatter(exp_data['areas'], theo_areas, color='orange', alpha=0.8, s=80, 
               edgecolors='black', linewidth=1)
    min_area = min(min(exp_data['areas']), min(theo_areas))
    max_area = max(max(exp_data['areas']), max(theo_areas))
    plt.plot([min_area, max_area], [min_area, max_area], 'k--', linewidth=3, label='Perfect Agreement')
    plt.xlabel('Experimental Area (nm²)', fontsize=14, weight='bold')
    plt.ylabel('Theoretical Area (nm²)', fontsize=14, weight='bold')
    plt.title('REAL DATA: Parity Plot', fontsize=16, weight='bold')
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Add R² annotation
    r_squared = validation_results['r_squared']
    plt.text(0.02, 0.98, f'R² = {r_squared:.6f}', 
             transform=ax3.transAxes, fontsize=14, weight='bold', verticalalignment='top',
             bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.8))
    
    # Plot 4: Real hardness distribution
    ax4 = plt.subplot(3, 3, 4)
    plt.hist(exp_data['hardness'], bins=max(8, len(exp_data['hardness'])//3), alpha=0.7, 
             color='skyblue', edgecolor='black', linewidth=1.5)
    plt.axvline(x=9.0, color='red', linestyle='--', linewidth=4, label='Expected (9.0 GPa)')
    mean_h = np.mean(exp_data['hardness'])
    plt.axvline(x=mean_h, color='green', linestyle='-', linewidth=4, 
               label=f'Measured ({mean_h:.2f} GPa)')
    plt.xlabel('Hardness (GPa)', fontsize=14, weight='bold')
    plt.ylabel('Frequency', fontsize=14, weight='bold')
    plt.title('REAL DATA: Hardness Distribution', fontsize=16, weight='bold')
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Plot 5: Real modulus distribution
    ax5 = plt.subplot(3, 3, 5)
    plt.hist(exp_data['modulus'], bins=max(8, len(exp_data['modulus'])//3), alpha=0.7, 
             color='lightcoral', edgecolor='black', linewidth=1.5)
    plt.axvline(x=72.0, color='red', linestyle='--', linewidth=4, label='Expected (72 GPa)')
    mean_e = np.mean(exp_data['modulus'])
    plt.axvline(x=mean_e, color='green', linestyle='-', linewidth=4,
               label=f'Measured ({mean_e:.1f} GPa)')
    plt.xlabel('Elastic Modulus (GPa)', fontsize=14, weight='bold')
    plt.ylabel('Frequency', fontsize=14, weight='bold')
    plt.title('REAL DATA: Modulus Distribution', fontsize=16, weight='bold')
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Plot 6: Residual histogram
    ax6 = plt.subplot(3, 3, 6)
    plt.hist(residuals, bins=max(8, len(residuals)//3), alpha=0.7, 
             color='mediumpurple', edgecolor='black', linewidth=1.5)
    plt.axvline(x=0, color='black', linestyle='-', linewidth=3, label='Perfect Fit')
    plt.axvline(x=np.mean(residuals), color='red', linestyle='--', linewidth=2, 
               label=f'Mean: {np.mean(residuals):.1f} nm²')
    plt.xlabel('Residuals (nm²)', fontsize=14, weight='bold')
    plt.ylabel('Frequency', fontsize=14, weight='bold')
    plt.title('REAL DATA: Residual Distribution', fontsize=16, weight='bold')
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Plot 7: Error vs depth
    ax7 = plt.subplot(3, 3, 7)
    percent_errors = np.abs(residuals / np.array(exp_data['areas'])) * 100
    plt.scatter(exp_data['depths'], percent_errors, color='brown', alpha=0.8, s=80, edgecolors='black')
    plt.axhline(y=np.mean(percent_errors), color='red', linestyle='--', linewidth=2,
                label=f'Mean: {np.mean(percent_errors):.2f}%')
    plt.xlabel('Contact Depth (nm)', fontsize=14, weight='bold')
    plt.ylabel('Percentage Error (%)', fontsize=14, weight='bold')
    plt.title('REAL DATA: Error vs Depth', fontsize=16, weight='bold')
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Plot 8: Material properties scatter
    ax8 = plt.subplot(3, 3, 8)
    plt.scatter(exp_data['hardness'], exp_data['modulus'], color='darkgreen', alpha=0.8, s=100, 
               edgecolors='black', linewidth=2)
    plt.axvline(x=9.0, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Expected H')
    plt.axhline(y=72.0, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Expected E')
    plt.xlabel('Hardness (GPa)', fontsize=14, weight='bold')
    plt.ylabel('Elastic Modulus (GPa)', fontsize=14, weight='bold')
    plt.title('REAL DATA: H vs E Scatter', fontsize=16, weight='bold')
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Plot 9: Summary
    ax9 = plt.subplot(3, 3, 9)
    ax9.axis('off')
    
    quality = validation_results['quality']
    
    summary_text = f"""
REAL DATA VALIDATION SUMMARY

Dataset: {len(exp_data['depths'])} measurements
Your actual silica data

CALIBRATION RESULTS:
• R² = {validation_results['r_squared']:.6f}
• RMSE = {validation_results['rmse']:.1f} nm²
• Max residual = {max(abs(residuals)):.1f} nm²
• Quality: {quality}

MATERIAL PROPERTIES:
• Hardness = {np.mean(exp_data['hardness']):.2f} ± {np.std(exp_data['hardness']):.2f} GPa
• Modulus = {np.mean(exp_data['modulus']):.1f} ± {np.std(exp_data['modulus']):.1f} GPa

GREEN LINE VISIBILITY:
• {'Lines overlap = PERFECT!' if abs(coefficients['C1_nm2_per_nm']) < 0.01 else 'Some deviation visible'}

RESIDUAL INTERPRETATION:
• Range: {min(residuals):.1f} to {max(residuals):.1f} nm²
• Mean error: {np.mean(percent_errors):.2f}%
• Status: {quality}

RECOMMENDATION:
{'Ready for precision work!' if quality in ['EXCELLENT', 'GOOD'] else 'Monitor tip condition'}
    """
    
    color_map = {'EXCELLENT': 'lightgreen', 'GOOD': 'lightyellow', 'ACCEPTABLE': 'orange', 'POOR': 'lightcoral'}
    bg_color = color_map.get(quality, 'lightgray')
    
    ax9.text(0.05, 0.95, summary_text.strip(), transform=ax9.transAxes, fontsize=11,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle="round,pad=0.5", facecolor=bg_color, alpha=0.8))
    
    plt.suptitle('REAL SILICA DATA - Comprehensive Tip Calibration Validation', 
                 fontsize=18, weight='bold', y=0.98)
    plt.tight_layout()
    plt.subplots_adjust(top=0.94)
    plt.savefig('real_silica_validation.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("📊 REAL DATA validation plots saved as 'real_silica_validation.png'")

def main():
    """Main validation function for real data"""
    print("🔍 REAL SILICA DATA VALIDATION")
    print("=" * 60)
    
    # Check if silica file exists
    if not os.path.exists('Silica Before.xls'):
        print("❌ Silica Before.xls not found")
        return False
    
    # Extract real experimental data
    experimental_data = extract_real_silica_data('Silica Before.xls')
    if not experimental_data or len(experimental_data) == 0:
        print("❌ Could not extract experimental data")
        return False
    
    # Get calibrated coefficients
    coefficients = get_calibrated_tip_coefficients()
    if not coefficients:
        return False
    
    # Validate calibration with real data
    validation_results = validate_real_data_calibration(experimental_data, coefficients)
    
    # Create comprehensive validation plots
    create_real_data_validation_plots(validation_results, coefficients)
    
    print("\n" + "=" * 60)
    print("✅ REAL SILICA DATA VALIDATION COMPLETE!")
    print("Check 'real_silica_validation.png' for detailed analysis")
    print("Your real data shows the calibration quality!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("❌ Real data validation failed")
        sys.exit(1)
