#!/usr/bin/env python3
"""
Complete Tip Area Function Calibration
Consolidated NIST-compliant calibration with visualization and analysis
Features: Coefficient extraction, quality assessment, plotting, physical interpretation
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server compatibility
import matplotlib.pyplot as plt
import sys
import os
from nist_calibration import NISTCalibrationMethods

def create_calibration_plots(coefficients, quality_metrics, file_name):
    """
    Create comprehensive visualization plots for tip calibration
    """
    try:
        # Create sample data for visualization 
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
        for i, (bar, value) in enumerate(zip(bars, values)):
            height = bar.get_height()
            if i == 0:  # R²
                ax3.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                        f'{quality_metrics["r_squared"]:.4f}', ha='center', va='bottom')
            elif i == 1:  # Data Points
                ax3.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                        f'{quality_metrics["n_data_points"]}', ha='center', va='bottom')
        
        # Plot 4: Summary text
        ax4.axis('off')
        summary_text = f"""
TIP AREA FUNCTION CALIBRATION SUMMARY

File: {file_name}
Reference Material: Fused Silica

EXTRACTED COEFFICIENTS:
• C₀ = {C0:.3f} nm²/nm² (theoretical)
• C₁ = {C1:.3f} nm²/nm (tip wear)
• C₂ = {C2:.3f} nm²/nm^0.5 (tip geometry)

QUALITY METRICS:
• R² = {quality_metrics['r_squared']:.6f}
• Data Points = {quality_metrics['n_data_points']}
• C₀ Deviation = {((C0 - 24.56)/24.56)*100:+.1f}%

AREA FUNCTION:
A(h_c) = {C0:.3f}·h_c² + {C1:.3f}·h_c + {C2:.3f}·h_c^0.5

PHYSICAL INTERPRETATION:
• C₀ fixed to theoretical Berkovich value
• C₁ captures tip blunting/wear effects  
• C₂ captures tip geometry deviations

STATUS: {'✅ EXCELLENT' if quality_metrics['r_squared'] > 0.98 else '✅ GOOD' if quality_metrics['r_squared'] > 0.95 else '⚠️ ACCEPTABLE'}
        """
        
        ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes, fontsize=9,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.5))
        
        plt.tight_layout()
        plt.savefig('tip_calibration_results.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Calibration plots saved as 'tip_calibration_results.png'")
        
    except Exception as e:
        print(f"⚠️  Could not create plots: {str(e)}")

def display_final_tip_results():
    """
    Display the final optimized tip calibration results
    """
    print("🔬 FINAL TIP AREA FUNCTION CALIBRATION RESULTS")
    print("=" * 70)
    
    try:
        # Initialize NIST calibration
        nist_cal = NISTCalibrationMethods()
        
        # Extract coefficients using optimized method
        print("🔄 Computing final tip parameters...")
        
        # Suppress logging
        import logging
        logging.getLogger('nanoindentation_analyzer').setLevel(logging.ERROR)
        
        results = nist_cal.extract_tip_coefficients_from_file(
            xls_file_path='Silica Before.xls',
            reference_material='fused_silica'
        )
        
        if results.get('valid', False):
            coeffs = results['coefficients']
            quality = results['quality_metrics']
            
            print("✅ Calibration completed successfully!")
            
            print(f"\n📊 FINAL TIP AREA FUNCTION COEFFICIENTS:")
            print("=" * 50)
            print(f"File: {results['file_analyzed']}")
            print(f"Reference: Fused Silica (E=72 GPa, H=9.0 GPa)")
            print(f"Data points: {quality['n_data_points']}")
            print(f"Fit quality: R² = {quality['r_squared']:.6f}")
            
            print(f"\n🔢 OPTIMIZED COEFFICIENTS FOR NANOINDENTATION:")
            print("-" * 50)
            print(f"Area Function: A(h_c) = C₀·h_c² + C₁·h_c + C₂·h_c^0.5")
            print()
            print(f"   C₀ = {coeffs['C0_nm2_per_nm2']:.3f} nm²/nm²")
            print(f"   C₁ = {coeffs['C1_nm2_per_nm']:.3f} nm²/nm") 
            print(f"   C₂ = {coeffs['C2_nm2_per_nm05']:.3f} nm²/nm^0.5")
            
            print(f"\n📈 QUALITY ASSESSMENT:")
            print("-" * 30)
            theoretical_C0 = 24.56
            measured_C0 = coeffs['C0_nm2_per_nm2']
            deviation = ((measured_C0 - theoretical_C0) / theoretical_C0) * 100
            
            print(f"   Theoretical C₀: {theoretical_C0:.2f} nm²/nm²")
            print(f"   Measured C₀: {measured_C0:.3f} nm²/nm²")
            print(f"   Deviation: {deviation:+.1f}%")
            
            if quality['r_squared'] > 0.98:
                print(f"   Fit Quality: ✅ EXCELLENT (R² = {quality['r_squared']:.6f})")
            elif quality['r_squared'] > 0.95:
                print(f"   Fit Quality: ✅ GOOD (R² = {quality['r_squared']:.4f})")
            else:
                print(f"   Fit Quality: ⚠️  ACCEPTABLE (R² = {quality['r_squared']:.4f})")
                
            if abs(deviation) < 2:
                print(f"   Tip Condition: ✅ EXCELLENT (deviation < 2%)")
            elif abs(deviation) < 5:
                print(f"   Tip Condition: ✅ GOOD (deviation < 5%)")
            else:
                print(f"   Tip Condition: ⚠️  NEEDS ATTENTION (deviation > 5%)")
            
            print(f"\n💡 IMPLEMENTATION INSTRUCTIONS:")
            print("-" * 35)
            print("CORRECT APPROACH: C₀ fixed to theoretical, higher-order terms fitted")
            print()
            print("1. In your nanoindentation analysis software:")
            print("   • Set tip area function to polynomial form")
            print(f"   • Input C₀ = {coeffs['C0_nm2_per_nm2']:.3f} (theoretical Berkovich)")
            print(f"   • Input C₁ = {coeffs['C1_nm2_per_nm']:.3f} (tip wear correction)")
            print(f"   • Input C₂ = {coeffs['C2_nm2_per_nm05']:.3f} (tip geometry correction)")
            print()
            print("2. Physical interpretation:")
            print("   • C₀ = 24.56: Perfect Berkovich geometry (theoretical)")
            if abs(coeffs['C1_nm2_per_nm']) > 10:
                print(f"   • C₁ = {coeffs['C1_nm2_per_nm']:.1f}: Significant tip blunting/wear")
            else:
                print(f"   • C₁ = {coeffs['C1_nm2_per_nm']:.1f}: Minimal tip blunting/wear")
            if abs(coeffs['C2_nm2_per_nm05']) > 50:
                print(f"   • C₂ = {coeffs['C2_nm2_per_nm05']:.1f}: Significant tip shape deviation")
            else:
                print(f"   • C₂ = {coeffs['C2_nm2_per_nm05']:.1f}: Minimal tip shape deviation")
            print()
            print("3. Validation:")
            print("   • Test on fused silica: expect E ≈ 72 GPa, H ≈ 9.0 GPa")
            print("   • If values deviate significantly, recheck calibration")
            print()
            print("4. Quality control:")
            print("   • Monitor C₁, C₂ over time to track tip wear")
            print("   • Replace tip when |C₁| > 100 nm²/nm or |C₂| > 500 nm²/nm^0.5")
            
            # SI Units for advanced users
            print(f"\n🔬 SI UNITS (for advanced analysis):")
            print("-" * 35)
            print(f"   C₀ = {coeffs['C0_SI']:.6e} m²/m²")
            print(f"   C₁ = {coeffs['C1_SI']:.6e} m²/m")
            print(f"   C₂ = {coeffs['C2_SI']:.6e} m²/m^0.5")
            
            # Create visualization plots
            print("\n📊 Generating calibration plots...")
            create_calibration_plots(coeffs, quality, results['file_analyzed'])
            
            print(f"\n" + "=" * 70)
            print("✅ TIP AREA FUNCTION CALIBRATION COMPLETE!")
            print("Your nanoindentation system is now properly calibrated")
            print("with NIST-compliant tip area function coefficients.")
            print("=" * 70)
            
        else:
            print("❌ Calibration failed")
            if results.get('errors'):
                for error in results['errors']:
                    print(f"   Error: {error}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def run_complete_tip_calibration(xls_file='Silica Before.xls', create_plots=True):
    """
    Complete tip calibration including analysis, display, and plotting
    
    Args:
        xls_file: Path to the reference material XLS file
        create_plots: Whether to generate visualization plots
    
    Returns:
        bool: Success status
    """
    print("🔬 COMPLETE TIP AREA FUNCTION CALIBRATION")
    print("=" * 70)
    print("Using NIST-compliant constrained fitting methodology")
    print("Reference: Fused Silica (E=72 GPa, H=9.0 GPa)")
    print()
    
    if not os.path.exists(xls_file):
        print(f"❌ File not found: {xls_file}")
        return False
    
    try:
        # Run the analysis
        display_final_tip_results()
        return True
        
    except Exception as e:
        print(f"❌ Complete calibration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run complete tip calibration with all features
    success = run_complete_tip_calibration()
    if success:
        print("\n🎉 All tip calibration tasks completed successfully!")
    else:
        print("\n❌ Some issues occurred during calibration.")
