#!/usr/bin/env python3
"""
Command-line test script for nanoindentation analysis
Tests the core analysis functionality without GUI
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the analyzer
from run_hec14s1_analysis import FixedIndentXLSAnalyzer

def test_analysis(file_path, show_plots=False):
    """
    Test the nanoindentation analysis on a given file
    
    Args:
        file_path (str): Path to the Excel file
        show_plots (bool): Whether to show matplotlib plots
    """
    
    print("🔬 Nanoindentation Analysis - Command Line Test")
    print("=" * 60)
    print(f"📁 Input file: {file_path}")
    print(f"📊 Show plots: {show_plots}")
    print("=" * 60)
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"❌ Error: File {file_path} not found!")
        return False
    
    try:
        # Initialize analyzer
        print("🔧 Initializing analyzer...")
        analyzer = FixedIndentXLSAnalyzer(filename=file_path)
        
        # Configure settings
        analyzer.generatePlot = show_plots
        analyzer.hidePlot = not show_plots
        analyzer.export = True
        
        print(f"   ✅ File loaded: {os.path.basename(file_path)}")
        print(f"   📈 Generate plots: {analyzer.generatePlot}")
        print(f"   💾 Export results: {analyzer.export}")
        
        # Run analysis
        print("\n🚀 Running analysis...")
        results = analyzer.run_analysis()
        
        if results and len(results) > 0:
            print(f"\n✅ Analysis completed successfully!")
            print(f"📊 Number of tests analyzed: {len(results)}")
            
            # Display results summary
            df_results = pd.DataFrame(results)
            
            # Key metrics to display
            key_metrics = [
                'Test',
                'Hardness (GPa)',
                'Oliver-Pharr Hardness (GPa)', 
                'Oliver-Pharr Modulus (GPa)',
                'Loading Power Law R²',
                'Unloading Fit R²'
            ]
            
            # Filter available columns
            available_metrics = [col for col in key_metrics if col in df_results.columns]
            
            if available_metrics:
                print(f"\n📋 Results Summary:")
                print("-" * 80)
                print(df_results[available_metrics].to_string(index=False, float_format='%.4f'))
                
                # Statistics for hardness
                if 'Hardness (GPa)' in df_results.columns:
                    hardness = df_results['Hardness (GPa)']
                    print(f"\n📈 Hardness Statistics:")
                    print(f"   Mean: {hardness.mean():.4f} ± {hardness.std():.4f} GPa")
                    print(f"   Range: {hardness.min():.4f} - {hardness.max():.4f} GPa")
                
                # Statistics for modulus
                if 'Oliver-Pharr Modulus (GPa)' in df_results.columns:
                    modulus = df_results['Oliver-Pharr Modulus (GPa)']
                    print(f"\n🔧 Modulus Statistics:")
                    print(f"   Mean: {modulus.mean():.4f} ± {modulus.std():.4f} GPa")
                    print(f"   Range: {modulus.min():.4f} - {modulus.max():.4f} GPa")
                
                # Quality indicators
                if 'Loading Power Law R²' in df_results.columns:
                    loading_r2 = df_results['Loading Power Law R²']
                    print(f"\n✅ Quality Indicators:")
                    print(f"   Loading fit R²: {loading_r2.mean():.4f} (avg)")
                    
                if 'Unloading Fit R²' in df_results.columns:
                    unloading_r2 = df_results['Unloading Fit R²']
                    print(f"   Unloading fit R²: {unloading_r2.mean():.4f} (avg)")
                
            else:
                print(f"\n📋 Available result columns:")
                for col in df_results.columns:
                    print(f"   - {col}")
            
            return True
            
        else:
            print("❌ No results obtained from analysis")
            return False
            
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    
    # Default file - use the sample file in current directory
    default_file = Path(__file__).parent / "Silica Before.xls"
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = str(default_file)
    
    # Check for plot flag
    show_plots = "--plots" in sys.argv or "-p" in sys.argv
    
    # Run test
    success = test_analysis(input_file, show_plots=show_plots)
    
    if success:
        print(f"\n🎉 Test completed successfully!")
    else:
        print(f"\n💥 Test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
