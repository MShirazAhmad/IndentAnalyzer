#!/usr/bin/env python3
"""
Unified Test Suite - Compact Version
Single test file covering all essential functionality
"""

import sys
import os
sys.path.insert(0, '.')

def test_all():
    """Run all essential tests"""
    print("🧪 UNIFIED TEST SUITE")
    print("=" * 40)
    
    tests = []
    
    # Test 1: Imports
    try:
        from src.core.standards import ISO14577Constants
        from src.gui.main_interface import NanoindentationGUI
        from src.calibration.tip_calibrator import run_complete_tip_calibration
        tests.append(("Imports", True))
    except Exception as e:
        tests.append(("Imports", False, str(e)))
    
    # Test 2: GUI Creation
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        gui = NanoindentationGUI()
        gui.close()
        tests.append(("GUI", True))
    except Exception as e:
        tests.append(("GUI", False, str(e)))
    
    # Test 3: File Access
    try:
        ref_file = "data/reference/fused_silica_reference.xls"
        exists = os.path.exists(ref_file)
        tests.append(("Data Access", exists))
    except Exception as e:
        tests.append(("Data Access", False, str(e)))
    
    # Results
    passed = sum(1 for test in tests if len(test) == 2 and test[1])
    total = len(tests)
    
    for test in tests:
        status = "✅ PASS" if (len(test) == 2 and test[1]) else "❌ FAIL"
        print(f"{test[0]:<15}: {status}")
        if len(test) == 3:
            print(f"    Error: {test[2]}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    return passed == total

if __name__ == "__main__":
    success = test_all()
    sys.exit(0 if success else 1)
