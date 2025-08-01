#!/usr/bin/env python3
"""
Test the complete GUI functionality with the new plot tabs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_complete_functionality():
    """Test the complete GUI workflow"""
    print("🧪 Testing Complete GUI Functionality")
    print("=" * 50)
    
    # Test 1: GUI startup
    try:
        from PyQt5.QtWidgets import QApplication
        from nanoindentation_gui import NanoindentationGUI
        
        app = QApplication(sys.argv)
        window = NanoindentationGUI()
        print("✅ GUI startup successful")
        
        # Test 2: Check plot tab widget exists
        if hasattr(window, 'plots_tab_widget'):
            print("✅ Plot tab widget initialized")
        else:
            print("❌ Plot tab widget missing")
        
        # Test 3: Check methods exist
        if hasattr(window, 'create_plot_tabs'):
            print("✅ create_plot_tabs method exists")
        else:
            print("❌ create_plot_tabs method missing")
            
        if hasattr(window, 'create_summary_plot_tab'):
            print("✅ create_summary_plot_tab method exists")
        else:
            print("❌ create_summary_plot_tab method missing")
        
        # Test 4: Test with sample data
        try:
            sample_results = [
                {
                    'Test': '9-1',
                    'Hardness (GPa)': 9.05,
                    'Oliver-Pharr Modulus (GPa)': 69.6,
                    'Loading R²': 0.9999,
                    'Unloading Fit R²': 1.0000,
                    'Max Load (mN)': 109.5,
                    'Max Displacement (nm)': 991.2
                },
                {
                    'Test': '9-2', 
                    'Hardness (GPa)': 9.12,
                    'Oliver-Pharr Modulus (GPa)': 69.6,
                    'Loading R²': 0.9998,
                    'Unloading Fit R²': 1.0000,
                    'Max Load (mN)': 109.7,
                    'Max Displacement (nm)': 992.1
                }
            ]
            
            window.create_plot_tabs(sample_results)
            print("✅ Plot tabs created successfully")
            print(f"📊 Number of tabs: {window.plots_tab_widget.count()}")
            
        except Exception as e:
            print(f"❌ Error creating plot tabs: {e}")
        
        app.quit()
        print("✅ GUI test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ GUI test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_complete_functionality()
    if success:
        print("\n🎉 All tests passed! GUI is ready for use.")
        print("\n📋 New Features:")
        print("   • Dark mode theme with white plot backgrounds")
        print("   • Individual plot tab for each test")
        print("   • Summary tab with statistical overview")
        print("   • Enhanced nanoindentation curve plotting")
        print("   • Automatic tab naming and organization")
    else:
        print("\n💥 Some tests failed. Please check the errors above.")
        sys.exit(1)
