#!/usr/bin/env python3
"""
Tip Calibration Validation Script
Compares experimental data with optimized tip area function to verify calibration quality
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import sys
import os

# Add src to path for imports
sys.path.append('src')
import __init__  # Initialize package paths
from src.core.standards import ISO14577Constants
from src.analysis.legacy_analyzer import IndentXLSAnalyzer
from src.calibration.nist_methods import NISTCalibrationMethods

def load_experimental_data(xls_file):
    """Load and extract experimental data from XLS file"""
    print(f"📊 Loading experimental data from: {xls_file}")
    
    try:
        analyzer = IndentXLSAnalyzer()
        results = analyzer.analyze_file(xls_file)
        
        if not results['valid']:
            print("❌ Could not load experimental data")
            return None
            
        # Extract experimental data points
        experimental_data = []
        for test_name, test_data in results['tests'].items():
            if test_name.startswith('Test '):
                contact_depth = test_data.get('contact_depth_nm', 0)
                contact_area = test_data.get('contact_area_nm2', 0)
                hardness = test_data.get('hardness_GPa', 0)
                modulus = test_data.get('elastic_modulus_GPa', 0)
                
                if contact_depth > 0 and contact_area > 0:
                    experimental_data.append({
                        'test_name': test_name,
                        'contact_depth_nm': contact_depth,
                        'contact_area_nm2': contact_area,
                        'hardness_GPa': hardness,
                        'elastic_modulus_GPa': modulus
                    })
        
        print(f"✅ Loaded {len(experimental_data)} experimental data points")
        return experimental_data
        
    except Exception as e:
        print(f"❌ Error loading experimental data: {e}")
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
            print(f"   C₀ = {coeffs['C0_nm2_per_nm2']:.3f} nm²/nm²")
            print(f"   C₁ = {coeffs['C1_nm2_per_nm']:.3f} nm²/nm")
            print(f"   C₂ = {coeffs['C2_nm2_per_nm05']:.3f} nm²/nm^0.5")
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
    
    # Material property validation for fused silica
    mean_hardness = np.mean(exp_hardness)
    mean_modulus = np.mean(exp_modulus)
    std_hardness = np.std(exp_hardness)
    std_modulus = np.std(exp_modulus)
    
    print(f"\n🔬 MATERIAL PROPERTIES (Fused Silica):")
    print(f"   Hardness: {mean_hardness:.2f} ± {std_hardness:.2f} GPa")
    print(f"   Modulus: {mean_modulus:.1f} ± {std_modulus:.1f} GPa")
    print(f"   Expected: H ≈ 9.0 GPa, E ≈ 72 GPa")
    
    # Validation assessment
    hardness_error = abs(mean_hardness - 9.0) / 9.0 * 100
    modulus_error = abs(mean_modulus - 72.0) / 72.0 * 100
    
    print(f"\n✅ VALIDATION RESULTS:")
    print(f"   Hardness deviation: {hardness_error:.1f}%")
    print(f"   Modulus deviation: {modulus_error:.1f}%")
    
    if r_squared > 0.98 and hardness_error < 10 and modulus_error < 10:
        print(f"   🎉 EXCELLENT CALIBRATION - Ready for use!")
    elif r_squared > 0.95 and hardness_error < 15 and modulus_error < 15:
        print(f"   ✅ GOOD CALIBRATION - Acceptable for analysis")
    else:
        print(f"   ⚠️  CALIBRATION NEEDS ATTENTION - Check tip condition")
    
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

def create_validation_plots(validation_results, coefficients):
    """Create comprehensive validation plots"""
    print("\n📊 Creating validation plots...")
    
    exp_data = validation_results['experimental_data']
    theo_areas = validation_results['theoretical_areas']
    
    fig = plt.figure(figsize=(16, 12))
    
    # Plot 1: Area function validation
    ax1 = plt.subplot(2, 3, 1)
    plt.scatter(exp_data['depths'], exp_data['areas'], color='red', alpha=0.7, s=50, 
               label='Experimental Data', zorder=5)
    
    # Create smooth theoretical curve
    depth_range = np.linspace(min(exp_data['depths']), max(exp_data['depths']), 100)
    smooth_areas = calculate_theoretical_areas(depth_range, coefficients)
    plt.plot(depth_range, smooth_areas, 'b-', linewidth=2, 
             label='Calibrated Tip Function', zorder=3)
    
    # Perfect Berkovich for comparison
    perfect_areas = 24.56 * np.array(depth_range)**2
    plt.plot(depth_range, perfect_areas, 'g--', linewidth=1, alpha=0.7,
             label='Perfect Berkovich (24.56·h²)', zorder=2)
    
    plt.xlabel('Contact Depth (nm)')
    plt.ylabel('Contact Area (nm²)')
    plt.title('Tip Area Function Validation')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot 2: Residuals
    ax2 = plt.subplot(2, 3, 2)
    plt.scatter(exp_data['depths'], validation_results['residuals'], color='purple', alpha=0.7)
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    plt.xlabel('Contact Depth (nm)')
    plt.ylabel('Residuals (nm²)')
    plt.title('Fit Residuals')
    plt.grid(True, alpha=0.3)
    
    # Plot 3: Parity plot
    ax3 = plt.subplot(2, 3, 3)
    plt.scatter(exp_data['areas'], theo_areas, color='orange', alpha=0.7)
    min_area = min(min(exp_data['areas']), min(theo_areas))
    max_area = max(max(exp_data['areas']), max(theo_areas))
    plt.plot([min_area, max_area], [min_area, max_area], 'k--', alpha=0.5)
    plt.xlabel('Experimental Area (nm²)')
    plt.ylabel('Theoretical Area (nm²)')
    plt.title('Parity Plot')
    plt.grid(True, alpha=0.3)
    
    # Plot 4: Hardness distribution
    ax4 = plt.subplot(2, 3, 4)
    plt.hist(exp_data['hardness'], bins=8, alpha=0.7, color='skyblue', edgecolor='black')
    plt.axvline(x=9.0, color='red', linestyle='--', linewidth=2, label='Expected (9.0 GPa)')
    plt.axvline(x=np.mean(exp_data['hardness']), color='green', linestyle='-', linewidth=2, 
               label=f'Measured ({np.mean(exp_data["hardness"]):.2f} GPa)')
    plt.xlabel('Hardness (GPa)')
    plt.ylabel('Frequency')
    plt.title('Hardness Distribution')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot 5: Modulus distribution
    ax5 = plt.subplot(2, 3, 5)
    plt.hist(exp_data['modulus'], bins=8, alpha=0.7, color='lightcoral', edgecolor='black')
    plt.axvline(x=72.0, color='red', linestyle='--', linewidth=2, label='Expected (72 GPa)')
    plt.axvline(x=np.mean(exp_data['modulus']), color='green', linestyle='-', linewidth=2,
               label=f'Measured ({np.mean(exp_data["modulus"]):.1f} GPa)')
    plt.xlabel('Elastic Modulus (GPa)')
    plt.ylabel('Frequency')
    plt.title('Modulus Distribution')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot 6: Summary statistics
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')
    
    summary_text = f"""
CALIBRATION VALIDATION SUMMARY

Tip Area Function:
A(h_c) = {coefficients['C0_nm2_per_nm2']:.3f}·h_c² + {coefficients['C1_nm2_per_nm']:.3f}·h_c + {coefficients['C2_nm2_per_nm05']:.3f}·h_c^0.5

Fit Quality:
• R² = {validation_results['r_squared']:.6f}
• RMSE = {validation_results['rmse']:.2f} nm²
• Mean Error = {validation_results['mean_percent_error']:.2f}%

Material Properties:
• Hardness = {np.mean(exp_data['hardness']):.2f} ± {np.std(exp_data['hardness']):.2f} GPa
• Modulus = {np.mean(exp_data['modulus']):.1f} ± {np.std(exp_data['modulus']):.1f} GPa

Status: {'🎉 EXCELLENT' if validation_results['r_squared'] > 0.98 else '✅ GOOD' if validation_results['r_squared'] > 0.95 else '⚠️ NEEDS ATTENTION'}
    """
    
    ax6.text(0.05, 0.95, summary_text.strip(), transform=ax6.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('tip_calibration_validation.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("📊 Validation plots saved as 'tip_calibration_validation.png'")

def main():
    """Main validation function"""
    print("🔍 TIP CALIBRATION VALIDATION")
    print("=" * 50)
    
    # Check if silica file exists
    if not os.path.exists('Silica Before.xls'):
        print("❌ Silica Before.xls not found")
        return False
    
    # Load experimental data
    experimental_data = load_experimental_data('Silica Before.xls')
    if not experimental_data:
        return False
    
    # Get calibrated coefficients
    coefficients = get_calibrated_tip_coefficients()
    if not coefficients:
        return False
    
    # Validate calibration
    validation_results = validate_calibration_quality(experimental_data, coefficients)
    
    # Create validation plots
    create_validation_plots(validation_results, coefficients)
    
    print("\n" + "=" * 50)
    print("✅ TIP CALIBRATION VALIDATION COMPLETE!")
    print("Check 'tip_calibration_validation.png' for detailed analysis")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("❌ Validation failed")
        sys.exit(1)
