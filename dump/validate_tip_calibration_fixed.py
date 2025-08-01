#!/usr/bin/env python3
"""
Fixed Tip Calibration Validation with Debug Information
Addresses:
1. Green dashed line visibility issue
2. Large residuals interpretation
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys
import os
import __init__

from src.calibration.nist_methods import NISTCalibrationMethods
from src.analysis.legacy_analyzer import IndentXLSAnalyzer

def load_experimental_data_fixed(xls_file):
    """Fixed version to load experimental data"""
    print(f"📊 Loading experimental data from: {xls_file}")
    
    try:
        analyzer = IndentXLSAnalyzer(filename=xls_file)
        # Use correct method - no parameters needed
        results = analyzer.run_analysis()
        
        if not results.get('valid', False):
            print("❌ Could not load experimental data")
            return None
            
        # Extract experimental data points with debugging
        experimental_data = []
        print(f"🔍 Debug: Available tests in results:")
        
        for test_name, test_data in results.get('tests', {}).items():
            print(f"   - {test_name}: {type(test_data)}")
            
            if 'Test ' in test_name and isinstance(test_data, dict):
                contact_depth = test_data.get('contact_depth_nm', 0)
                contact_area = test_data.get('contact_area_nm2', 0)
                hardness = test_data.get('hardness_GPa', 0)
                modulus = test_data.get('elastic_modulus_GPa', 0)
                
                print(f"     Depth: {contact_depth}, Area: {contact_area}")
                
                if contact_depth > 0 and contact_area > 0:
                    experimental_data.append({
                        'test_name': test_name,
                        'contact_depth_nm': contact_depth,
                        'contact_area_nm2': contact_area,
                        'hardness_GPa': hardness,
                        'elastic_modulus_GPa': modulus
                    })
        
        print(f"✅ Loaded {len(experimental_data)} experimental data points")
        
        # Debug: Show range of values
        if experimental_data:
            depths = [d['contact_depth_nm'] for d in experimental_data]
            areas = [d['contact_area_nm2'] for d in experimental_data]
            print(f"🔍 Debug: Depth range: {min(depths):.1f} - {max(depths):.1f} nm")
            print(f"🔍 Debug: Area range: {min(areas):.1f} - {max(areas):.1f} nm²")
        
        return experimental_data
        
    except Exception as e:
        print(f"❌ Error loading experimental data: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_calibrated_tip_coefficients():
    """Get the calibrated tip area function coefficients"""
    print("🔧 Extracting calibrated tip coefficients...")
    
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

def create_fixed_validation_plots(validation_results, coefficients):
    """Create fixed validation plots addressing visibility and residual issues"""
    print("\n📊 Creating FIXED validation plots...")
    
    exp_data = validation_results['experimental_data']
    theo_areas = validation_results['theoretical_areas']
    residuals = validation_results['residuals']
    
    fig = plt.figure(figsize=(18, 12))
    
    # Plot 1: Area function validation (FIXED)
    ax1 = plt.subplot(2, 3, 1)
    
    # Create depth range for smooth curves
    depth_min = min(exp_data['depths'])
    depth_max = max(exp_data['depths'])
    depth_range = np.linspace(depth_min, depth_max, 100)
    
    # Calculate curves
    smooth_calibrated = calculate_theoretical_areas(depth_range, coefficients)
    smooth_perfect = 24.56 * depth_range**2  # Perfect Berkovich
    
    # Plot experimental data points
    plt.scatter(exp_data['depths'], exp_data['areas'], color='red', alpha=0.8, s=60, 
               label='Experimental Data', zorder=5, edgecolors='darkred')
    
    # Plot calibrated tip function
    plt.plot(depth_range, smooth_calibrated, 'b-', linewidth=3, 
             label='Calibrated Tip Function', zorder=4)
    
    # Plot perfect Berkovich (FIXED: Make more visible)
    plt.plot(depth_range, smooth_perfect, 'g--', linewidth=3, alpha=0.9,
             label='Perfect Berkovich (24.56·h²)', zorder=3)
    
    plt.xlabel('Contact Depth (nm)', fontsize=12)
    plt.ylabel('Contact Area (nm²)', fontsize=12)
    plt.title('Tip Area Function Validation (FIXED)', fontsize=14, weight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    
    # Add text annotation about line visibility
    plt.text(0.02, 0.98, 'Note: Blue and green lines may overlap\nif calibration is perfect', 
             transform=ax1.transAxes, fontsize=9, verticalalignment='top',
             bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
    
    # Plot 2: Residuals (ENHANCED with interpretation)
    ax2 = plt.subplot(2, 3, 2)
    plt.scatter(exp_data['depths'], residuals, color='purple', alpha=0.7, s=50)
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.8, linewidth=2)
    
    # Add statistical lines
    mean_residual = np.mean(residuals)
    std_residual = np.std(residuals)
    plt.axhline(y=mean_residual, color='red', linestyle='--', alpha=0.6, 
                label=f'Mean: {mean_residual:.1f} nm²')
    plt.axhline(y=mean_residual + 2*std_residual, color='orange', linestyle=':', alpha=0.6,
                label=f'+2σ: {mean_residual + 2*std_residual:.1f} nm²')
    plt.axhline(y=mean_residual - 2*std_residual, color='orange', linestyle=':', alpha=0.6,
                label=f'-2σ: {mean_residual - 2*std_residual:.1f} nm²')
    
    plt.xlabel('Contact Depth (nm)', fontsize=12)
    plt.ylabel('Residuals (nm²)', fontsize=12)
    plt.title('Fit Residuals with Statistics', fontsize=14, weight='bold')
    plt.legend(fontsize=9)
    plt.grid(True, alpha=0.3)
    
    # Add interpretation text
    max_residual = max(abs(residuals))
    plt.text(0.02, 0.98, f'Max residual: ±{max_residual:.1f} nm²\nInterpretation below', 
             transform=ax2.transAxes, fontsize=9, verticalalignment='top',
             bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7))
    
    # Plot 3: Parity plot
    ax3 = plt.subplot(2, 3, 3)
    plt.scatter(exp_data['areas'], theo_areas, color='orange', alpha=0.7, s=50)
    min_area = min(min(exp_data['areas']), min(theo_areas))
    max_area = max(max(exp_data['areas']), max(theo_areas))
    plt.plot([min_area, max_area], [min_area, max_area], 'k--', alpha=0.8, linewidth=2)
    plt.xlabel('Experimental Area (nm²)', fontsize=12)
    plt.ylabel('Theoretical Area (nm²)', fontsize=12)
    plt.title('Parity Plot', fontsize=14, weight='bold')
    plt.grid(True, alpha=0.3)
    
    # Add R² annotation
    r_squared = validation_results['r_squared']
    plt.text(0.02, 0.98, f'R² = {r_squared:.6f}', 
             transform=ax3.transAxes, fontsize=12, verticalalignment='top',
             bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.7))
    
    # Plot 4: Hardness distribution
    ax4 = plt.subplot(2, 3, 4)
    plt.hist(exp_data['hardness'], bins=8, alpha=0.7, color='skyblue', edgecolor='black')
    plt.axvline(x=9.0, color='red', linestyle='--', linewidth=3, label='Expected (9.0 GPa)')
    mean_h = np.mean(exp_data['hardness'])
    plt.axvline(x=mean_h, color='green', linestyle='-', linewidth=3, 
               label=f'Measured ({mean_h:.2f} GPa)')
    plt.xlabel('Hardness (GPa)', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.title('Hardness Distribution', fontsize=14, weight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    
    # Plot 5: Modulus distribution
    ax5 = plt.subplot(2, 3, 5)
    plt.hist(exp_data['modulus'], bins=8, alpha=0.7, color='lightcoral', edgecolor='black')
    plt.axvline(x=72.0, color='red', linestyle='--', linewidth=3, label='Expected (72 GPa)')
    mean_e = np.mean(exp_data['modulus'])
    plt.axvline(x=mean_e, color='green', linestyle='-', linewidth=3,
               label=f'Measured ({mean_e:.1f} GPa)')
    plt.xlabel('Elastic Modulus (GPa)', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.title('Modulus Distribution', fontsize=14, weight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    
    # Plot 6: Residual analysis and interpretation
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')
    
    # Detailed residual interpretation
    mean_res = np.mean(residuals)
    std_res = np.std(residuals)
    max_res = max(abs(residuals))
    
    # Assess residual quality
    if max_res < 50:
        residual_quality = "EXCELLENT"
        res_color = "green"
    elif max_res < 100:
        residual_quality = "GOOD"
        res_color = "orange"
    else:
        residual_quality = "NEEDS ATTENTION"
        res_color = "red"
    
    summary_text = f"""
RESIDUAL ANALYSIS & INTERPRETATION

Residual Statistics:
• Mean: {mean_res:.2f} nm²
• Std Dev: {std_res:.2f} nm²
• Max: ±{max_res:.1f} nm²
• Quality: {residual_quality}

What Residuals Mean:
• -100 to +150 nm² range indicates:
  - Some systematic differences
  - Possible tip wear effects
  - Data measurement variability

Green Line Visibility:
• If calibrated ≈ perfect Berkovich:
  - Blue and green lines overlap
  - This means EXCELLENT calibration
  - Tip geometry is near-perfect

Calibration Status:
R² = {validation_results['r_squared']:.6f}
RMSE = {validation_results['rmse']:.1f} nm²
    """
    
    ax6.text(0.05, 0.95, summary_text.strip(), transform=ax6.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle="round,pad=0.5", facecolor=res_color, alpha=0.2))
    
    plt.tight_layout()
    plt.savefig('tip_calibration_validation_fixed.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("📊 FIXED validation plots saved as 'tip_calibration_validation_fixed.png'")
    
    # Print residual interpretation
    print(f"\n🔍 RESIDUAL INTERPRETATION:")
    print(f"   Range: {min(residuals):.1f} to {max(residuals):.1f} nm²")
    print(f"   What this means:")
    if max_res < 50:
        print(f"   ✅ EXCELLENT: Residuals < 50 nm² indicate high-quality calibration")
    elif max_res < 100:
        print(f"   ✅ GOOD: Residuals < 100 nm² are acceptable for most applications")
    else:
        print(f"   ⚠️  ATTENTION: Large residuals may indicate:")
        print(f"      - Tip wear or damage")
        print(f"      - Systematic measurement errors")
        print(f"      - Need for recalibration")

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
        'residuals': residuals
    }

def main():
    """Main validation function"""
    print("🔍 FIXED TIP CALIBRATION VALIDATION")
    print("=" * 50)
    
    # Check if silica file exists
    if not os.path.exists('Silica Before.xls'):
        print("❌ Silica Before.xls not found")
        return False
    
    # Load experimental data
    experimental_data = load_experimental_data_fixed('Silica Before.xls')
    if not experimental_data:
        return False
    
    # Get calibrated coefficients
    coefficients = get_calibrated_tip_coefficients()
    if not coefficients:
        return False
    
    # Validate calibration
    validation_results = validate_calibration_quality(experimental_data, coefficients)
    
    # Create FIXED validation plots
    create_fixed_validation_plots(validation_results, coefficients)
    
    print("\n" + "=" * 50)
    print("✅ FIXED TIP CALIBRATION VALIDATION COMPLETE!")
    print("Check 'tip_calibration_validation_fixed.png' for detailed analysis")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("❌ Validation failed")
        sys.exit(1)
