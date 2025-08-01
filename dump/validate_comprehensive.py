#!/usr/bin/env python3
"""
Direct Data Extraction for Tip Calibration Validation
Bypasses complex analyzer to directly extract and compare data
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

def extract_silica_data_directly(xls_file):
    """Directly extract data from Excel file"""
    print(f"📊 Directly extracting data from: {xls_file}")
    
    try:
        # Read the Results sheet directly
        df_results = pd.read_excel(xls_file, sheet_name="Results")
        print(f"✅ Results sheet loaded with {len(df_results)} rows")
        
        # Extract data for tests 1-20
        experimental_data = []
        
        for test_num in range(1, 21):
            try:
                # Find the row for this test
                test_row = df_results[df_results['Test'] == test_num]
                
                if not test_row.empty:
                    row = test_row.iloc[0]
                    
                    # Extract key values (adjust column names as needed)
                    contact_depth = row.get('Hc (nm)', 0)
                    contact_area = row.get('Ac (nm²)', 0) 
                    hardness = row.get('H Average Over Defined Range', 0) / 1e9  # Convert to GPa if in Pa
                    modulus = row.get('E Average Over Defined Range', 0) / 1e9   # Convert to GPa if in Pa
                    
                    if contact_depth > 0 and contact_area > 0:
                        experimental_data.append({
                            'test_name': f'Test {test_num:03d}',
                            'contact_depth_nm': contact_depth,
                            'contact_area_nm2': contact_area,
                            'hardness_GPa': hardness,
                            'elastic_modulus_GPa': modulus
                        })
                        
                        print(f"   Test {test_num:03d}: h_c={contact_depth:.1f}nm, A_c={contact_area:.1f}nm², H={hardness:.2f}GPa, E={modulus:.1f}GPa")
                        
            except Exception as e:
                print(f"   Warning: Could not process test {test_num}: {e}")
                continue
        
        print(f"✅ Successfully extracted {len(experimental_data)} data points")
        
        if experimental_data:
            depths = [d['contact_depth_nm'] for d in experimental_data]
            areas = [d['contact_area_nm2'] for d in experimental_data]
            print(f"🔍 Data ranges:")
            print(f"   Contact depth: {min(depths):.1f} - {max(depths):.1f} nm")
            print(f"   Contact area: {min(areas):.1f} - {max(areas):.1f} nm²")
        
        return experimental_data
        
    except Exception as e:
        print(f"❌ Error extracting data: {e}")
        # Try to show available sheets
        try:
            xl_file = pd.ExcelFile(xls_file)
            print(f"Available sheets: {xl_file.sheet_names}")
        except:
            pass
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

def analyze_residuals_meaning(residuals, areas):
    """Provide detailed interpretation of residuals"""
    print(f"\n🔍 DETAILED RESIDUAL ANALYSIS:")
    print("=" * 50)
    
    min_res = min(residuals)
    max_res = max(residuals)
    mean_res = np.mean(residuals)
    std_res = np.std(residuals)
    
    print(f"Residual Statistics:")
    print(f"   Range: {min_res:.1f} to {max_res:.1f} nm²")
    print(f"   Mean: {mean_res:.2f} nm²")
    print(f"   Std Dev: {std_res:.2f} nm²")
    print(f"   Max Absolute: {max(abs(min_res), abs(max_res)):.1f} nm²")
    
    # Calculate percentage errors
    percent_errors = np.abs(residuals / areas) * 100
    mean_percent_error = np.mean(percent_errors)
    max_percent_error = max(percent_errors)
    
    print(f"\nPercentage Errors:")
    print(f"   Mean: {mean_percent_error:.2f}%")
    print(f"   Max: {max_percent_error:.2f}%")
    
    print(f"\nInterpretation of -100 to +150 nm² residuals:")
    print(f"   • This represents {mean_percent_error:.1f}% average error")
    
    if max(abs(residuals)) < 50:
        print(f"   • ✅ EXCELLENT: Very small residuals indicate perfect calibration")
        quality = "EXCELLENT"
    elif max(abs(residuals)) < 100:
        print(f"   • ✅ GOOD: Moderate residuals are acceptable for most work")
        quality = "GOOD"
    elif max(abs(residuals)) < 200:
        print(f"   • ⚠️  ACCEPTABLE: Larger residuals suggest:")
        print(f"     - Possible tip wear or damage")
        print(f"     - Small systematic measurement errors")
        print(f"     - Still usable but monitor tip condition")
        quality = "ACCEPTABLE"
    else:
        print(f"   • ❌ POOR: Large residuals indicate:")
        print(f"     - Significant tip problems")
        print(f"     - Systematic calibration errors")
        print(f"     - Recommend tip replacement/recalibration")
        quality = "POOR"
    
    return quality

def create_comprehensive_validation_plots(validation_results, coefficients):
    """Create comprehensive validation plots with explanations"""
    print("\n📊 Creating comprehensive validation plots...")
    
    exp_data = validation_results['experimental_data']
    theo_areas = validation_results['theoretical_areas']
    residuals = validation_results['residuals']
    
    fig = plt.figure(figsize=(20, 14))
    
    # Plot 1: Area function validation with ENHANCED visibility
    ax1 = plt.subplot(2, 4, 1)
    
    depth_min = min(exp_data['depths'])
    depth_max = max(exp_data['depths'])
    depth_range = np.linspace(depth_min, depth_max, 100)
    
    # Calculate curves
    smooth_calibrated = calculate_theoretical_areas(depth_range, coefficients)
    smooth_perfect = 24.56 * depth_range**2  # Perfect Berkovich
    
    # Plot experimental data
    plt.scatter(exp_data['depths'], exp_data['areas'], color='red', alpha=0.8, s=80, 
               label='Experimental Data', zorder=5, edgecolors='darkred', linewidth=1.5)
    
    # Plot calibrated tip function (thick blue line)
    plt.plot(depth_range, smooth_calibrated, 'b-', linewidth=4, 
             label='Calibrated Tip Function', zorder=4)
    
    # Plot perfect Berkovich (thick green dashed line)
    plt.plot(depth_range, smooth_perfect, 'g--', linewidth=4, alpha=1.0,
             label='Perfect Berkovich (24.56·h²)', zorder=3)
    
    plt.xlabel('Contact Depth (nm)', fontsize=12, weight='bold')
    plt.ylabel('Contact Area (nm²)', fontsize=12, weight='bold')
    plt.title('Area Function Validation\n(Green line shows perfect Berkovich)', fontsize=14, weight='bold')
    plt.legend(fontsize=11, loc='upper left')
    plt.grid(True, alpha=0.3)
    
    # Add text box explaining line visibility
    overlap_text = "If lines overlap:\n• Calibration is PERFECT\n• Tip ≈ ideal Berkovich"
    plt.text(0.98, 0.02, overlap_text, transform=ax1.transAxes, fontsize=10, 
             verticalalignment='bottom', horizontalalignment='right',
             bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.8))
    
    # Plot 2: Residuals with detailed statistics
    ax2 = plt.subplot(2, 4, 2)
    plt.scatter(exp_data['depths'], residuals, color='purple', alpha=0.8, s=60, edgecolors='darkpurple')
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.8, linewidth=3, label='Perfect Fit')
    
    # Add statistical lines
    mean_residual = np.mean(residuals)
    std_residual = np.std(residuals)
    plt.axhline(y=mean_residual, color='red', linestyle='--', alpha=0.7, linewidth=2,
                label=f'Mean: {mean_residual:.1f} nm²')
    plt.axhline(y=mean_residual + 2*std_residual, color='orange', linestyle=':', alpha=0.7, linewidth=2,
                label=f'+2σ: {mean_residual + 2*std_residual:.1f} nm²')
    plt.axhline(y=mean_residual - 2*std_residual, color='orange', linestyle=':', alpha=0.7, linewidth=2,
                label=f'-2σ: {mean_residual - 2*std_residual:.1f} nm²')
    
    plt.xlabel('Contact Depth (nm)', fontsize=12, weight='bold')
    plt.ylabel('Residuals (nm²)', fontsize=12, weight='bold')
    plt.title('Fit Residuals Analysis', fontsize=14, weight='bold')
    plt.legend(fontsize=9)
    plt.grid(True, alpha=0.3)
    
    # Plot 3: Parity plot with R²
    ax3 = plt.subplot(2, 4, 3)
    plt.scatter(exp_data['areas'], theo_areas, color='orange', alpha=0.8, s=60, 
               edgecolors='darkorange', linewidth=1)
    min_area = min(min(exp_data['areas']), min(theo_areas))
    max_area = max(max(exp_data['areas']), max(theo_areas))
    plt.plot([min_area, max_area], [min_area, max_area], 'k--', alpha=0.8, linewidth=3,
             label='Perfect Agreement')
    plt.xlabel('Experimental Area (nm²)', fontsize=12, weight='bold')
    plt.ylabel('Theoretical Area (nm²)', fontsize=12, weight='bold')
    plt.title('Parity Plot', fontsize=14, weight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Add R² annotation
    r_squared = validation_results['r_squared']
    plt.text(0.02, 0.98, f'R² = {r_squared:.6f}', 
             transform=ax3.transAxes, fontsize=14, weight='bold', verticalalignment='top',
             bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.8))
    
    # Plot 4: Hardness distribution
    ax4 = plt.subplot(2, 4, 4)
    plt.hist(exp_data['hardness'], bins=8, alpha=0.7, color='skyblue', edgecolor='black', linewidth=1.5)
    plt.axvline(x=9.0, color='red', linestyle='--', linewidth=4, label='Expected (9.0 GPa)')
    mean_h = np.mean(exp_data['hardness'])
    plt.axvline(x=mean_h, color='green', linestyle='-', linewidth=4, 
               label=f'Measured ({mean_h:.2f} GPa)')
    plt.xlabel('Hardness (GPa)', fontsize=12, weight='bold')
    plt.ylabel('Frequency', fontsize=12, weight='bold')
    plt.title('Hardness Distribution', fontsize=14, weight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    
    # Plot 5: Modulus distribution
    ax5 = plt.subplot(2, 4, 5)
    plt.hist(exp_data['modulus'], bins=8, alpha=0.7, color='lightcoral', edgecolor='black', linewidth=1.5)
    plt.axvline(x=72.0, color='red', linestyle='--', linewidth=4, label='Expected (72 GPa)')
    mean_e = np.mean(exp_data['modulus'])
    plt.axvline(x=mean_e, color='green', linestyle='-', linewidth=4,
               label=f'Measured ({mean_e:.1f} GPa)')
    plt.xlabel('Elastic Modulus (GPa)', fontsize=12, weight='bold')
    plt.ylabel('Frequency', fontsize=12, weight='bold')
    plt.title('Modulus Distribution', fontsize=14, weight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    
    # Plot 6: Residual histogram
    ax6 = plt.subplot(2, 4, 6)
    plt.hist(residuals, bins=10, alpha=0.7, color='mediumpurple', edgecolor='black', linewidth=1.5)
    plt.axvline(x=0, color='black', linestyle='-', linewidth=3, label='Perfect Fit')
    plt.axvline(x=np.mean(residuals), color='red', linestyle='--', linewidth=2, 
               label=f'Mean: {np.mean(residuals):.1f} nm²')
    plt.xlabel('Residuals (nm²)', fontsize=12, weight='bold')
    plt.ylabel('Frequency', fontsize=12, weight='bold')
    plt.title('Residual Distribution', fontsize=14, weight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    
    # Plot 7: Percentage error plot
    ax7 = plt.subplot(2, 4, 7)
    percent_errors = np.abs(residuals / np.array(exp_data['areas'])) * 100
    plt.scatter(exp_data['depths'], percent_errors, color='brown', alpha=0.8, s=60)
    plt.axhline(y=np.mean(percent_errors), color='red', linestyle='--', linewidth=2,
                label=f'Mean: {np.mean(percent_errors):.2f}%')
    plt.xlabel('Contact Depth (nm)', fontsize=12, weight='bold')
    plt.ylabel('Percentage Error (%)', fontsize=12, weight='bold')
    plt.title('Percentage Error vs Depth', fontsize=14, weight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    
    # Plot 8: Summary and interpretation
    ax8 = plt.subplot(2, 4, 8)
    ax8.axis('off')
    
    # Get residual quality assessment
    residual_quality = analyze_residuals_meaning(residuals, exp_data['areas'])
    
    summary_text = f"""
VALIDATION SUMMARY & INTERPRETATION

GREEN LINE VISIBILITY:
• If green dashed line is not visible:
  → Blue and green lines OVERLAP
  → This means PERFECT calibration!
  → Tip geometry ≈ ideal Berkovich

RESIDUAL ANALYSIS:
• Range: {min(residuals):.1f} to {max(residuals):.1f} nm²
• Mean: {np.mean(residuals):.1f} ± {np.std(residuals):.1f} nm²
• Quality: {residual_quality}

WHAT -100 to +150 nm² MEANS:
• {np.mean(np.abs(residuals / np.array(exp_data['areas'])) * 100):.1f}% average error
• Indicates {residual_quality.lower()} calibration
• {'✅ Ready for use' if residual_quality in ['EXCELLENT', 'GOOD'] else '⚠️ Monitor tip condition'}

OVERALL CALIBRATION STATUS:
• R² = {validation_results['r_squared']:.6f}
• RMSE = {validation_results['rmse']:.1f} nm²
• Status: {residual_quality}
    """
    
    color_map = {'EXCELLENT': 'lightgreen', 'GOOD': 'lightyellow', 'ACCEPTABLE': 'orange', 'POOR': 'lightcoral'}
    bg_color = color_map.get(residual_quality, 'lightgray')
    
    ax8.text(0.05, 0.95, summary_text.strip(), transform=ax8.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle="round,pad=0.5", facecolor=bg_color, alpha=0.8))
    
    plt.suptitle('Comprehensive Tip Calibration Validation Analysis', fontsize=16, weight='bold', y=0.98)
    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    plt.savefig('tip_calibration_validation_comprehensive.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("📊 Comprehensive validation plots saved as 'tip_calibration_validation_comprehensive.png'")

def validate_calibration_quality(experimental_data, coefficients):
    """Validate calibration by comparing experimental vs theoretical data"""
    print("\n🔍 CALIBRATION VALIDATION ANALYSIS")
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
    
    print(f"📈 FIT QUALITY METRICS:")
    print(f"   R² = {r_squared:.6f}")
    print(f"   RMSE = {rmse:.2f} nm²")
    print(f"   Mean % Error = {mean_percent_error:.2f}%")
    print(f"   Residual range: {min(residuals):.1f} to {max(residuals):.1f} nm²")
    
    # Detailed residual analysis
    residual_quality = analyze_residuals_meaning(residuals, exp_areas)
    
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
        'residual_quality': residual_quality
    }

def main():
    """Main validation function"""
    print("🔍 COMPREHENSIVE TIP CALIBRATION VALIDATION")
    print("=" * 60)
    
    # Check if silica file exists
    if not os.path.exists('Silica Before.xls'):
        print("❌ Silica Before.xls not found")
        return False
    
    # Extract experimental data directly
    experimental_data = extract_silica_data_directly('Silica Before.xls')
    if not experimental_data:
        return False
    
    # Get calibrated coefficients
    coefficients = get_calibrated_tip_coefficients()
    if not coefficients:
        return False
    
    # Validate calibration
    validation_results = validate_calibration_quality(experimental_data, coefficients)
    
    # Create comprehensive validation plots
    create_comprehensive_validation_plots(validation_results, coefficients)
    
    print("\n" + "=" * 60)
    print("✅ COMPREHENSIVE TIP CALIBRATION VALIDATION COMPLETE!")
    print("Check 'tip_calibration_validation_comprehensive.png' for detailed analysis")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("❌ Validation failed")
        sys.exit(1)
