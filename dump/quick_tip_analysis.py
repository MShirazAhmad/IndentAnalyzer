#!/usr/bin/env python3
"""
Quick Tip Coefficient Extractor
"""

def quick_tip_analysis():
    print("🔬 Quick Tip Area Function Analysis")
    print("=" * 40)
    
    try:
        import sys
        import os
        import numpy as np
        from scipy.optimize import curve_fit
        
        # Add current directory to path
        sys.path.insert(0, os.getcwd())
        
        # Import analyzer
        from nanoindentation_analyzer import NanoindentationAnalyzer
        
        print("📂 Analyzing silica data...")
        analyzer = NanoindentationAnalyzer()
        
        # Quick analysis with minimal output
        import logging
        logging.getLogger().setLevel(logging.CRITICAL)  # Suppress INFO logs
        
        results = analyzer.analyze_file('Silica Before.xls')
        
        if not results or 'tests' not in results:
            print("❌ No results")
            return
            
        # Extract calibration data
        h_data = []  # contact depths in nm
        a_data = []  # contact areas in nm²
        
        for test_name, test_data in results['tests'].items():
            if (test_data.get('success', False) and 
                'mechanical_properties' in test_data):
                
                props = test_data['mechanical_properties']
                if props.get('overall_valid', False):
                    input_params = props.get('input_parameters', {})
                    reduced_mod = props.get('reduced_modulus', {})
                    
                    if ('contact_depth_nm' in input_params and 
                        'stiffness_mn_nm' in input_params and
                        'reduced_modulus_gpa' in reduced_mod):
                        
                        h_c = input_params['contact_depth_nm']
                        S = input_params['stiffness_mn_nm']
                        E_r = reduced_mod['reduced_modulus_gpa'] * 1000  # Convert to MPa
                        
                        if E_r > 0 and S > 0 and h_c > 0:
                            # Calculate area using Oliver-Pharr relation
                            beta = 1.034  # Berkovich geometry factor
                            area = (np.pi / 4) * (S * 1000 / (beta * E_r))**2  # nm²
                            
                            h_data.append(h_c)
                            a_data.append(area)
        
        print(f"✅ Found {len(h_data)} valid measurements")
        
        if len(h_data) < 3:
            print("❌ Insufficient data")
            return
            
        h_array = np.array(h_data)
        a_array = np.array(a_data)
        
        print(f"📏 Depth range: {h_array.min():.0f} - {h_array.max():.0f} nm")
        print(f"📐 Area range: {a_array.min():.0f} - {a_array.max():.0f} nm²")
        
        # Method 1: Simple C0 extraction
        C0_simple = np.mean(a_array / h_array**2)
        print(f"\n🔬 Method 1 - Simple Berkovich:")
        print(f"   C₀ = {C0_simple:.2f} nm²/nm²")
        print(f"   Theoretical = 24.56 nm²/nm²")
        print(f"   Difference = {((C0_simple - 24.56)/24.56)*100:.1f}%")
        
        # Method 2: Three-parameter fit
        def area_func(h, C0, C1, C2):
            return C0 * h**2 + C1 * h + C2 * h**0.5
            
        try:
            popt, pcov = curve_fit(area_func, h_array, a_array, 
                                 p0=[24.56, 0, 0], maxfev=2000)
            
            errors = np.sqrt(np.diag(pcov))
            
            print(f"\n🔬 Method 2 - Three-term fit:")
            print(f"   C₀ = {popt[0]:.2f} ± {errors[0]:.2f} nm²/nm²")
            print(f"   C₁ = {popt[1]:.2f} ± {errors[1]:.2f} nm²/nm")
            print(f"   C₂ = {popt[2]:.2f} ± {errors[2]:.2f} nm²/nm^0.5")
            
            # Calculate R²
            a_pred = area_func(h_array, *popt)
            ss_res = np.sum((a_array - a_pred)**2)
            ss_tot = np.sum((a_array - np.mean(a_array))**2)
            r_squared = 1 - (ss_res / ss_tot)
            print(f"   R² = {r_squared:.4f}")
            
        except Exception as e:
            print(f"❌ Curve fitting failed: {e}")
        
        print(f"\n📋 Summary:")
        print(f"   Data points: {len(h_data)}")
        print(f"   Recommended C₀: {C0_simple:.2f} nm²/nm²")
        print(f"   Quality: {'Good' if abs(C0_simple - 24.56) < 5 else 'Check data'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_tip_analysis()
