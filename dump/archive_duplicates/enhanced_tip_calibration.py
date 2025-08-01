#!/usr/bin/env python3
"""
Enhanced Tip Area Function Calibration with Visualization
Uses consolidated NIST calibration methods with plotting
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import sys
import os

# Import the consolidated NIST calibration
from nist_calibration import NISTCalibrationMethods

def create_calibration_plots(coefficients, quality_metrics, file_name):
    """
    Create comprehensive visualization plots for tip calibration
    """
    try:
        # Create sample data for visualization (since we have the coefficients)
        h_range = np.linspace(500, 800, 100)  # nm
        
        # Calculate areas using extracted coefficients
        C0 = coefficients['C0_nm2_per_nm2']
        C1 = coefficients['C1_nm2_per_nm']
        C2 = coefficients['C2_nm2_per_nm05']
        
        area_fitted = C0 * h_range**2 + C1 * h_range + C2 * h_range**0.5
        area_theoretical = 24.56 * h_range**2  # Perfect Berkovich
        
        # Create plots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Plot 1: Area function comparison
        ax1.plot(h_range, area_theoretical, 'r--', linewidth=2, label='Perfect Berkovich (24.56·h²)')
        ax1.plot(h_range, area_fitted, 'b-', linewidth=2, 
                label=f'Fitted ({C0:.1f}·h² + {C1:.1f}·h + {C2:.1f}·h^0.5)')
        ax1.set_xlabel('Contact Depth (nm)')
        ax1.set_ylabel('Contact Area (nm²)')
        ax1.set_title('Tip Area Function Calibration')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Plot 2: Coefficient comparison
        coeff_names = ['C₀\n(nm²/nm²)', 'C₁\n(nm²/nm)', 'C₂\n(nm²/nm^0.5)']
        fitted_values = [C0, C1, C2]
        theoretical_values = [24.56, 0, 0]
        
        x = np.arange(len(coeff_names))
        width = 0.35
        
        ax2.bar(x - width/2, theoretical_values, width, label='Theoretical', alpha=0.7, color='red')
        ax2.bar(x + width/2, fitted_values, width, label='Fitted', alpha=0.7, color='blue')
        ax2.set_xlabel('Coefficients')
        ax2.set_ylabel('Coefficient Values')
        ax2.set_title('Area Function Coefficients Comparison')
        ax2.set_xticks(x)
        ax2.set_xticklabels(coeff_names)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Quality metrics
        metrics = ['R²', 'Data Points', 'C₀ Deviation (%)']
        values = [
            quality_metrics['r_squared'],
            quality_metrics['n_data_points'] / 20,  # Normalized
            abs((C0 - 24.56) / 24.56 * 100) / 10    # Normalized
        ]
        colors = ['green', 'blue', 'orange']
        
        bars = ax3.bar(metrics, values, color=colors, alpha=0.7)
        ax3.set_ylabel('Normalized Values')
        ax3.set_title('Quality Metrics')
        ax3.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            if 'R²' in bar.get_x():
                ax3.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                        f'{quality_metrics["r_squared"]:.4f}', ha='center', va='bottom')
            elif 'Data' in bar.get_x():
                ax3.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                        f'{quality_metrics["n_data_points"]}', ha='center', va='bottom')
        
        # Plot 4: Summary text
        ax4.axis('off')
        summary_text = f"""
TIP AREA FUNCTION CALIBRATION SUMMARY

File: {file_name}
Reference Material: Fused Silica

EXTRACTED COEFFICIENTS:
• C₀ = {C0:.2f} nm²/nm²
• C₁ = {C1:.2f} nm²/nm
• C₂ = {C2:.2f} nm²/nm^0.5

QUALITY METRICS:
• R² = {quality_metrics['r_squared']:.4f}
• Data Points = {quality_metrics['n_data_points']}
• C₀ Deviation = {((C0 - 24.56)/24.56)*100:+.1f}%

AREA FUNCTION:
A(h_c) = {C0:.2f}·h_c² + {C1:.2f}·h_c + {C2:.2f}·h_c^0.5

STATUS: {'✅ EXCELLENT' if quality_metrics['r_squared'] > 0.98 else '✅ GOOD' if quality_metrics['r_squared'] > 0.95 else '⚠️ ACCEPTABLE'}
        """
        
        ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.5))
        
        plt.tight_layout()
        plt.savefig('enhanced_tip_calibration.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Enhanced calibration plots saved as 'enhanced_tip_calibration.png'")
        
    except Exception as e:
        print(f"⚠️  Could not create plots: {str(e)}")

def main():
    """
    Main function to run enhanced tip calibration with visualization
    """
    print("🔬 Enhanced NIST Tip Area Function Calibration")
    print("=" * 60)
    print("Reference Material: Fused Silica")
    print("Area Function: A(h_c) = C₀h_c² + C₁h_c + C₂h_c^0.5")
    print()
    
    xls_file = "Silica Before.xls"
    
    if not os.path.exists(xls_file):
        print(f"❌ File not found: {xls_file}")
        return
    
    try:
        # Initialize NIST calibration
        nist_cal = NISTCalibrationMethods()
        
        # Extract tip coefficients using consolidated method
        print("🔄 Extracting tip coefficients with enhanced analysis...")
        
        # Suppress logging during analysis
        import logging
        logging.getLogger('nanoindentation_analyzer').setLevel(logging.ERROR)
        
        results = nist_cal.extract_tip_coefficients_from_file(
            xls_file_path=xls_file,
            reference_material='fused_silica'
        )
        
        if results.get('valid', False):
            coeffs = results['coefficients']
            quality = results['quality_metrics']
            
            print("✅ Enhanced tip calibration successful!")
            
            print(f"\n📊 DETAILED RESULTS:")
            print("=" * 50)
            print(f"📁 File: {results['file_analyzed']}")
            print(f"🧪 Reference: {results['reference_material']}")
            print(f"📈 Data points: {quality['n_data_points']}")
            print(f"📏 Fit quality (R²): {quality['r_squared']:.6f}")
            
            print(f"\n🔢 AREA FUNCTION COEFFICIENTS:")
            print("-" * 40)
            print(f"   C₀ = {coeffs['C0_nm2_per_nm2']:.3f} nm²/nm²")
            print(f"   C₁ = {coeffs['C1_nm2_per_nm']:.3f} nm²/nm")
            print(f"   C₂ = {coeffs['C2_nm2_per_nm05']:.3f} nm²/nm^0.5")
            
            print(f"\n📐 SI UNITS:")
            print(f"   C₀ = {coeffs['C0_SI']:.6e} m²/m²")
            print(f"   C₁ = {coeffs['C1_SI']:.6e} m²/m")
            print(f"   C₂ = {coeffs['C2_SI']:.6e} m²/m^0.5")
            
            # Create enhanced visualization
            create_calibration_plots(coeffs, quality, xls_file)
            
            # Display warnings and recommendations
            if results.get('warnings'):
                print(f"\n⚠️  NOTES:")
                for warning in results['warnings']:
                    print(f"   • {warning}")
            
            print(f"\n💡 RECOMMENDATIONS:")
            deviation = ((coeffs['C0_nm2_per_nm2'] - 24.56) / 24.56) * 100
            if abs(deviation) < 2:
                print("   ✅ Excellent tip condition - use fitted coefficients")
            elif abs(deviation) < 5:
                print("   ✅ Good tip condition - fitted coefficients recommended")
            else:
                print("   ⚠️  Significant tip deviation - consider tip replacement")
            
            print(f"\n✅ Enhanced calibration completed successfully!")
            
        else:
            print("❌ Enhanced tip calibration failed")
            if results.get('errors'):
                for error in results['errors']:
                    print(f"   Error: {error}")
        
    except Exception as e:
        print(f"❌ Enhanced calibration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
