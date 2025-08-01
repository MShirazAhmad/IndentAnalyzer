#!/usr/bin/env python3
"""
Tip Coefficient Determination - Step 1
Determines tip area function coefficients using fused silica reference data

This is the essential first step before analyzing any unknown samples.
The tip coefficients calibrate the indenter geometry for accurate contact area calculations.
"""

import sys
import os
import numpy as np
from pathlib import Path

# Add parent directory to path to use the working package structure
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

def determine_tip_coefficients():
    """
    Run tip coefficient determination using silica reference data
    
    This function:
    1. Loads the fused silica reference data
    2. Performs Oliver-Pharr analysis on multiple indents
    3. Extracts tip area function coefficients
    4. Validates against known silica properties
    5. Saves coefficients for future use
    """
    
    print("🔬 TIP COEFFICIENT DETERMINATION")
    print("=" * 60)
    print("Reference Material: Fused Silica")
    print("Expected Properties:")
    print("  • Hardness: ~9.0 GPa")
    print("  • Elastic Modulus: ~72 GPa") 
    print("  • Poisson Ratio: 0.17")
    print("=" * 60)
    
    try:
        # Import using the working package structure from our tests
        src_path = os.path.join(parent_dir, 'src')
        sys.path.insert(0, src_path)
        
        # Try both import methods to find what works
        try:
            from src.calibration.tip_calibrator import run_complete_tip_calibration, create_calibration_plots
            from src.core.standards import ISO14577Constants
        except:
            # Fallback to direct imports
            import calibration.tip_calibrator as tip_cal
            run_complete_tip_calibration = tip_cal.run_complete_tip_calibration
            create_calibration_plots = tip_cal.create_calibration_plots
        
        print("✅ Calibration modules loaded successfully")
        
        # Define reference data path
        reference_data_path = os.path.join(parent_dir, 'data', 'reference_materials', 'fused_silica_reference.xls')
        
        if not os.path.exists(reference_data_path):
            print(f"❌ Reference data not found at: {reference_data_path}")
            return False
        
        print(f"✅ Reference data found: {reference_data_path}")
        print()
        
        # Run complete tip calibration
        print("🔄 Running tip coefficient determination...")
        print("This process will:")
        print("  1. Analyze all indentation tests in the reference file")
        print("  2. Extract contact depth and area relationships")
        print("  3. Fit tip area function coefficients")
        print("  4. Validate against known silica properties")
        print("  5. Generate calibration plots")
        print()
        
        # Execute tip calibration
        calibration_result = run_complete_tip_calibration(reference_data_path)
        
        print()
        print("🎯 TIP COEFFICIENT DETERMINATION COMPLETED")
        print("=" * 60)
        
        # Check for calibration output files
        output_dir = parent_dir
        coeff_file = os.path.join(output_dir, 'calibrated_area_function_coefficients.csv')
        data_file = os.path.join(output_dir, 'tip_calibration_data.csv')
        report_file = os.path.join(output_dir, 'tip_calibration_report.txt')
        
        print("📊 OUTPUT FILES:")
        if os.path.exists(coeff_file):
            print(f"  ✅ Coefficients: {os.path.basename(coeff_file)}")
        if os.path.exists(data_file):
            print(f"  ✅ Calibration data: {os.path.basename(data_file)}")
        if os.path.exists(report_file):
            print(f"  ✅ Detailed report: {os.path.basename(report_file)}")
        
        # Try to create calibration plots
        try:
            print("\n📈 Generating calibration plots...")
            plot_result = create_calibration_plots(reference_data_path)
            print("  ✅ Calibration plots created")
        except Exception as e:
            print(f"  ⚠️ Plot generation: {e}")
        
        print("\n🎉 TIP CALIBRATION STEP 1 COMPLETE!")
        print("Your tip coefficients are now determined and ready for sample analysis.")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure the restructured package is properly set up.")
        return False
        
    except Exception as e:
        print(f"❌ Calibration error: {e}")
        return False

def show_next_steps():
    """Display what to do after tip coefficient determination"""
    print("\n" + "=" * 60)
    print("📋 NEXT STEPS")
    print("=" * 60)
    print("1. ✅ Tip coefficients determined (COMPLETED)")
    print("2. 📂 Load your sample data file (.xls format)")
    print("3. 🔬 Run nanoindentation analysis using:")
    print("     python3 scripts/analyze_sample.py your_sample.xls")
    print("4. 📊 View results in generated plots and reports")
    print("5. 🎯 Compare sample properties to known materials")
    print()
    print("💡 TIP: Keep the tip coefficients for all future analyses")
    print("    with the same indenter until tip maintenance/replacement.")

def main():
    """Main execution function"""
    print("🚀 STARTING TIP COEFFICIENT DETERMINATION")
    print("This is Step 1 of nanoindentation analysis workflow")
    print()
    
    success = determine_tip_coefficients()
    
    if success:
        show_next_steps()
        return 0
    else:
        print("\n❌ Tip coefficient determination failed.")
        print("Please check the error messages above and try again.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
