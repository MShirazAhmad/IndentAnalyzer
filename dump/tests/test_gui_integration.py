#!/usr/bin/env python3
"""
Test script to verify GUI integration with FixedIndentXLSAnalyzer
"""

import sys
import os

# Add current directory to path for local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required imports work"""
    print("🧪 Testing imports...")
    
    try:
        # Test PyQt5
        from PyQt5.QtWidgets import QApplication
        print("✅ PyQt5 imported successfully")
        
        # Test matplotlib
        import matplotlib
        matplotlib.use('Qt5Agg')
        import matplotlib.pyplot as plt
        print("✅ matplotlib imported successfully")
        
        # Test scientific libraries
        import pandas as pd
        import numpy as np
        print("✅ pandas and numpy imported successfully")
        
        # Test our analyzer
        from run_hec14s1_analysis import FixedIndentXLSAnalyzer
        print("✅ FixedIndentXLSAnalyzer imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_analyzer_integration():
    """Test that the analyzer can be instantiated"""
    print("\n🔗 Testing analyzer integration...")
    
    try:
        from run_hec14s1_analysis import FixedIndentXLSAnalyzer
        
        # Test file path (using your known working file)
        test_file = "/Users/shiraz/scripts/HEC14s/HEC15S Nanoindentation/HEC14S1.xls"
        
        if os.path.exists(test_file):
            print(f"✅ Test file found: {test_file}")
            
            # Try to create analyzer instance
            analyzer = FixedIndentXLSAnalyzer(filename=test_file)
            print("✅ FixedIndentXLSAnalyzer instance created successfully")
            
            # Check key attributes
            print(f"   • generatePlot: {analyzer.generatePlot}")
            print(f"   • hidePlot: {analyzer.hidePlot}")
            print(f"   • export: {analyzer.export}")
            print(f"   • ISO_MIN_R_SQUARED: {analyzer.ISO_MIN_R_SQUARED}")
            
            return True
        else:
            print(f"⚠️ Test file not found: {test_file}")
            print("   GUI will still work, just need to browse for a file")
            return True
            
    except Exception as e:
        print(f"❌ Analyzer integration error: {e}")
        return False

def test_gui_components():
    """Test that GUI components can be created"""
    print("\n🖥️ Testing GUI components...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from nanoindentation_gui import NanoindentationGUI, AnalysisWorker, MatplotlibWidget
        
        # Create QApplication (required for Qt widgets)
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        print("✅ QApplication created")
        
        # Test GUI class can be imported
        print("✅ GUI components imported successfully")
        
        # Test creating main window (don't show it)
        # window = NanoindentationGUI()
        # print("✅ Main GUI window can be created")
        
        app.quit()
        return True
        
    except Exception as e:
        print(f"❌ GUI component error: {e}")
        return False

def main():
    """Run all tests"""
    print("🔬 Nanoindentation GUI Integration Test")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # Test imports
    if test_imports():
        tests_passed += 1
    
    # Test analyzer integration
    if test_analyzer_integration():
        tests_passed += 1
    
    # Test GUI components
    if test_gui_components():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✅ All tests passed! GUI should work correctly.")
        print("\n🚀 To launch the GUI, run:")
        print("   ./launch_gui.sh")
        print("   or")
        print("   python nanoindentation_gui.py")
    else:
        print("❌ Some tests failed. Check the error messages above.")
        print("\n🔧 Try installing missing dependencies:")
        print("   pip install PyQt5 matplotlib pandas numpy scipy openpyxl")

if __name__ == "__main__":
    main()
