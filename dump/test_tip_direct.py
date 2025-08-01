#!/usr/bin/env python3
"""
Optimized Tip Coefficient Extraction Test
Using consolidated NIST calibration functionality
"""

def test_tip_coefficients():
    print("🔬 OPTIMIZED TIP COEFFICIENT EXTRACTION")
    print("=" * 50)
    
    try:
        # Test 1: Basic imports
        import numpy as np
        import sys
        import os
        sys.path.insert(0, os.getcwd())
        print("✅ Environment setup complete")
        
        # Test 2: Import consolidated NIST calibration
        from nist_calibration import NISTCalibrationMethods
        print("✅ NIST calibration methods imported")
        
        # Test 3: File exists check
        xls_file = 'Silica Before.xls'
        if not os.path.exists(xls_file):
            print(f"❌ XLS file not found: {xls_file}")
            return False
        print(f"✅ XLS file found: {xls_file}")
        
        # Test 4: Initialize NIST calibration
        nist_cal = NISTCalibrationMethods()
        print("✅ NIST calibration initialized")
        
        # Test 5: Extract tip coefficients using consolidated method
        print("\n🔄 Extracting tip coefficients from silica data...")
        
        # Suppress logging during analysis
        import logging
        logging.getLogger('nanoindentation_analyzer').setLevel(logging.ERROR)
        
        results = nist_cal.extract_tip_coefficients_from_file(
            xls_file_path=xls_file,
            reference_material='fused_silica'
        )
        
        # Test 6: Display results
        if results.get('valid', False):
            print("✅ Tip coefficient extraction successful!")
            
            coeffs = results['coefficients']
            quality = results['quality_metrics']
            
            print(f"\n📊 EXTRACTED TIP AREA FUNCTION COEFFICIENTS:")
            print("=" * 50)
            print(f"📁 File analyzed: {results['file_analyzed']}")
            print(f"🧪 Reference material: {results['reference_material']}")
            print(f"📈 Data points used: {quality['n_data_points']}")
            print(f"📏 Fit quality (R²): {quality['r_squared']:.4f}")
            
            print(f"\n🔢 AREA FUNCTION: A(h_c) = C₀·h_c² + C₁·h_c + C₂·h_c^0.5")
            print("-" * 50)
            print(f"   C₀ = {coeffs['C0_nm2_per_nm2']:.2f} nm²/nm²")
            print(f"   C₁ = {coeffs['C1_nm2_per_nm']:.2f} nm²/nm")
            print(f"   C₂ = {coeffs['C2_nm2_per_nm05']:.2f} nm²/nm^0.5")
            
            print(f"\n📋 COMPARISON:")
            print(f"   Theoretical Berkovich C₀: 24.56 nm²/nm²")
            print(f"   Measured C₀: {coeffs['C0_nm2_per_nm2']:.2f} nm²/nm²")
            deviation = ((coeffs['C0_nm2_per_nm2'] - 24.56) / 24.56) * 100
            print(f"   Deviation: {deviation:+.1f}%")
            
            # Quality assessment
            print(f"\n🎯 QUALITY ASSESSMENT:")
            r2 = quality['r_squared']
            if r2 > 0.98:
                print("   ✅ Excellent fit quality (R² > 0.98)")
            elif r2 > 0.95:
                print("   ✅ Good fit quality (R² > 0.95)")
            elif r2 > 0.90:
                print("   ⚠️  Acceptable fit quality (R² > 0.90)")
            else:
                print("   ❌ Poor fit quality (R² < 0.90)")
            
            if abs(deviation) < 5:
                print("   ✅ C₀ within reasonable range (±5%)")
            else:
                print("   ⚠️  C₀ deviates significantly from theoretical")
            
            # Warnings and errors
            if results.get('warnings'):
                print(f"\n⚠️  WARNINGS:")
                for warning in results['warnings']:
                    print(f"   - {warning}")
            
            if results.get('errors'):
                print(f"\n❌ ERRORS:")
                for error in results['errors']:
                    print(f"   - {error}")
            
            print(f"\n" + "=" * 50)
            print("✅ TIP COEFFICIENT EXTRACTION COMPLETE!")
            print("Use these coefficients in your nanoindentation analysis")
            print("for accurate mechanical property measurements.")
            
            return True
            
        else:
            print("❌ Tip coefficient extraction failed")
            if results.get('errors'):
                for error in results['errors']:
                    print(f"   Error: {error}")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def compute_tip_parameters_from_silica():
    """
    Main function to compute tip parameters from silica XLS data
    """
    print("🔬 COMPUTING TIP PARAMETERS FROM SILICA XLS")
    print("=" * 60)
    
    success = test_tip_coefficients()
    
    if success:
        print("\n� SUCCESS: Tip parameters computed successfully!")
        print("\n📝 Next steps:")
        print("1. Use the extracted C₀, C₁, C₂ coefficients in your analysis software")
        print("2. Set tip area function to: A = C₀·h_c² + C₁·h_c + C₂·h_c^0.5")
        print("3. Validate with known reference materials")
    else:
        print("\n❌ FAILED: Could not compute tip parameters")
        print("Check the errors above and verify your XLS file")

if __name__ == "__main__":
    compute_tip_parameters_from_silica()
