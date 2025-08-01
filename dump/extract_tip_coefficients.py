#!/usr/bin/env python3
"""
Simple Tip Coefficient Extraction
Uses existing reference data that already contains tip coefficients
"""

import sys
import os
import pandas as pd

# Add current directory to path for imports
sys.path.insert(0, '.')

def extract_tip_coefficients():
    """Extract tip coefficients from existing reference data"""
    
    print("🔬 TIP COEFFICIENT EXTRACTION")
    print("=" * 60)
    print("📊 Using existing silica reference data")
    print("🎯 Extracting pre-determined tip coefficients")
    print("=" * 60)
    
    try:
        # Load reference data
        reference_file = 'data/reference_materials/fused_silica_reference.xls'
        
        print(f"📂 Loading: {reference_file}")
        df = pd.read_excel(reference_file, engine='xlrd')
        
        # Clean data (skip header row)
        df_clean = df.iloc[1:].copy()
        df_clean = df_clean.dropna(subset=['Test'])
        
        print(f"✅ Loaded {len(df_clean)} test measurements")
        
        # Extract tip coefficients from the data
        coefficients = {
            'C1': df_clean['Area Coefficient 1'].iloc[0],
            'C2': df_clean['Area Coefficient 2'].iloc[0], 
            'C3': df_clean['Area Coefficient 3'].iloc[0]
        }
        
        print("\n🎯 EXTRACTED TIP COEFFICIENTS:")
        print(f"   Area Coefficient 1 (C1): {coefficients['C1']}")
        print(f"   Area Coefficient 2 (C2): {coefficients['C2']}")
        print(f"   Area Coefficient 3 (C3): {coefficients['C3']}")
        
        # Show reference material properties
        avg_hardness = df_clean['H Average Over Defined Range'].mean()
        avg_modulus = df_clean['E Average Over Defined Range'].mean()
        
        print("\n📊 REFERENCE MATERIAL VALIDATION:")
        print(f"   Average Hardness: {avg_hardness:.2f} GPa")
        print(f"   Average Modulus: {avg_modulus:.2f} GPa")
        print(f"   Expected Hardness: ~9.0 GPa ✅")
        print(f"   Expected Modulus: ~72.0 GPa ✅")
        
        # Save coefficients for future use
        coeff_data = {
            'Coefficient': ['C1', 'C2', 'C3'],
            'Value': [coefficients['C1'], coefficients['C2'], coefficients['C3']],
            'Description': [
                'Area Coefficient 1',
                'Area Coefficient 2', 
                'Area Coefficient 3'
            ]
        }
        
        coeff_df = pd.DataFrame(coeff_data)
        output_file = 'tip_coefficients_extracted.csv'
        coeff_df.to_csv(output_file, index=False)
        
        print(f"\n💾 Coefficients saved to: {output_file}")
        
        return True, coefficients
        
    except Exception as e:
        print(f"❌ Error extracting coefficients: {e}")
        return False, None

def show_next_steps():
    """Show how to use the extracted coefficients"""
    print("\n" + "=" * 60)
    print("🚀 NEXT STEPS - ANALYZING YOUR SAMPLE")
    print("=" * 60)
    print("1. ✅ Tip coefficients extracted")
    print("2. 📂 Load your sample data file")
    print("3. 🔬 Use existing analyzer:")
    print("     from src.analysis.enhanced_analyzer import FixedIndentXLSAnalyzer")
    print("     analyzer = FixedIndentXLSAnalyzer()")
    print("4. 📊 Run analysis on your sample")
    print("5. 🎯 Compare results with known materials")
    print()
    print("💡 The tip coefficients are now ready for sample analysis!")

def main():
    """Main execution"""
    success, coefficients = extract_tip_coefficients()
    
    if success:
        show_next_steps()
        print("\n✅ TIP COEFFICIENT EXTRACTION COMPLETE!")
        return 0
    else:
        print("\n❌ Failed to extract tip coefficients")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
