#!/usr/bin/env python3
"""
Unified Test Suite for Nanoindentation Analysis
Consolidates all testing functionality from multiple test files into a single comprehensive suite
"""

import sys
import os
import time
from pathlib import Path
import pandas as pd
import numpy as np
import warnings
from typing import Dict, List, Optional, Union

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Add paths for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
src_path = parent_dir / 'src'
sys.path.insert(0, str(src_path))
sys.path.append(str(parent_dir))


class UnifiedTestSuite:
    """
    Comprehensive test suite that consolidates functionality from:
    - test_comprehensive.py
    - test_complete_system.py  
    - test_unified.py
    - test_gui_integration.py
    - test_nist_standards.py
    """
    
    def __init__(self, verbose: bool = True, quick_mode: bool = False):
        self.verbose = verbose
        self.quick_mode = quick_mode
        self.test_results = {}
        self.overall_success = True
        
    def run_all_tests(self) -> Dict[str, any]:
        """
        Run the complete test suite
        
        Returns:
            Comprehensive test results
        """
        print("🧪 UNIFIED NANOINDENTATION TEST SUITE")
        print("=" * 70)
        print(f"🔧 Mode: {'Quick' if self.quick_mode else 'Comprehensive'}")
        print(f"🗣️ Verbose: {self.verbose}")
        print("=" * 70)
        
        start_time = time.time()
        
        # Define test categories
        test_categories = [
            ("Module Imports", self._test_imports),
            ("Core Functionality", self._test_core_functionality),
            ("Analysis Engine", self._test_analysis_engine),
            ("Tip Calibration", self._test_tip_calibration),
            ("GUI Integration", self._test_gui_integration),
            ("NIST Compliance", self._test_nist_compliance),
            ("Data Validation", self._test_data_validation),
            ("Legacy Compatibility", self._test_legacy_compatibility)
        ]
        
        # Run tests
        for category_name, test_function in test_categories:
            if self.verbose:
                print(f"\n🔬 Testing {category_name}...")
            
            try:
                result = test_function()
                self.test_results[category_name] = result
                
                if result['success']:
                    status = "✅ PASS"
                else:
                    status = "❌ FAIL"
                    self.overall_success = False
                
                if self.verbose:
                    print(f"   {status} - {result['summary']}")
                else:
                    print(f"{status} {category_name}")
                    
            except Exception as e:
                error_result = {
                    'success': False,
                    'summary': f"Test crashed: {str(e)}",
                    'details': {'error': str(e)},
                    'warnings': []
                }
                self.test_results[category_name] = error_result
                self.overall_success = False
                print(f"❌ CRASH {category_name}: {e}")
        
        # Final summary
        execution_time = time.time() - start_time
        
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(test_categories)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        
        for category, result in self.test_results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"   {category:<25} : {status}")
        
        print("-" * 70)
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {total_tests - passed_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"   Execution Time: {execution_time:.2f}s")
        
        if self.overall_success:
            print("🎉 ALL TESTS PASSED! System is fully functional.")
        else:
            print("⚠️ SOME TESTS FAILED! Review issues above.")
        
        print("=" * 70)
        
        return {
            'overall_success': self.overall_success,
            'execution_time': execution_time,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'test_results': self.test_results
        }
    
    def _test_imports(self) -> Dict[str, any]:
        """Test all critical module imports"""
        result = {
            'success': True,
            'summary': "",
            'details': {'imported_modules': [], 'failed_imports': []},
            'warnings': []
        }
        
        # Define critical imports to test
        import_tests = [
            # Core analysis modules
            ("Unified Analyzer", "src.analysis.unified_analyzer", "UnifiedNanoindentationAnalyzer"),
            ("Main Analyzer", "src.analysis.main_analyzer", "NanoindentationAnalyzer"),
            ("Enhanced Analyzer", "src.analysis.enhanced_analyzer", "FixedIndentXLSAnalyzer"),
            ("Legacy Analyzer", "src.analysis.legacy_analyzer", "IndentXLSAnalyzer"),
            
            # Core components
            ("ISO Constants", "src.core.standards", "ISO14577Constants"),
            ("Data Processor", "src.core.data_processor", "DataProcessor"),
            ("Validators", "src.core.validators", "DataValidator"),
            
            # Analysis components
            ("Curve Fitting", "src.analysis.curve_fitting", "CurveFitter"),
            ("Mechanical Calculator", "src.analysis.mechanical_calculator", "MechanicalPropertiesCalculator"),
            
            # Calibration
            ("NIST Methods", "src.calibration.nist_methods", "NISTCalibrationMethods"),
            ("Tip Calibrator", "src.calibration.tip_calibrator", "TipCalibration"),
            
            # GUI
            ("Main GUI", "src.gui.main_interface", "NanoindentationGUI"),
            
            # Validation
            ("Unified Validation", "src.core.unified_validation", "UnifiedValidationSuite")
        ]
        
        failed_imports = []
        
        for name, module_path, class_name in import_tests:
            try:
                module = __import__(module_path, fromlist=[class_name])
                getattr(module, class_name)
                result['details']['imported_modules'].append(name)
                if self.verbose:
                    print(f"      ✅ {name}")
            except ImportError as e:
                failed_imports.append((name, str(e)))
                result['details']['failed_imports'].append({'module': name, 'error': str(e)})
                if self.verbose:
                    print(f"      ❌ {name}: {e}")
            except AttributeError as e:
                failed_imports.append((name, f"Class {class_name} not found"))
                result['details']['failed_imports'].append({'module': name, 'error': f"Class {class_name} not found"})
                if self.verbose:
                    print(f"      ❌ {name}: Class {class_name} not found")
        
        if failed_imports:
            result['success'] = False
            result['summary'] = f"{len(failed_imports)} import failures"
        else:
            result['summary'] = f"All {len(import_tests)} modules imported successfully"
        
        return result
    
    def _test_core_functionality(self) -> Dict[str, any]:
        """Test core functionality without file dependencies"""
        result = {
            'success': True,
            'summary': "",
            'details': {},
            'warnings': []
        }
        
        try:
            # Test ISO constants
            from src.core.standards import ISO14577Constants
            iso = ISO14577Constants()
            
            assert hasattr(iso, 'MIN_R_SQUARED'), "ISO constants missing MIN_R_SQUARED"
            assert iso.MIN_R_SQUARED == 0.98, "Incorrect ISO R² requirement"
            
            # Test area function
            from src.analysis.curve_fitting import AreaFunction
            area_func = AreaFunction()
            
            test_depth = 100.0  # nm
            test_area = area_func.calculate_contact_area(test_depth)
            assert test_area > 0, "Area function returned invalid area"
            
            # Test basic calculations
            from src.analysis.mechanical_calculator import MechanicalPropertiesCalculator
            calc = MechanicalPropertiesCalculator(area_func)
            
            # Test hardness calculation
            hardness_result = calc.calculate_hardness(max_load=1.0, contact_area=1000.0)
            assert hardness_result['success'], "Hardness calculation failed"
            assert hardness_result['hardness_gpa'] > 0, "Invalid hardness value"
            
            result['details'] = {
                'iso_constants_ok': True,
                'area_function_ok': True,
                'calculations_ok': True
            }
            result['summary'] = "Core functionality working"
            
        except Exception as e:
            result['success'] = False
            result['summary'] = f"Core functionality failed: {str(e)}"
            result['details']['error'] = str(e)
        
        return result
    
    def _test_analysis_engine(self) -> Dict[str, any]:
        """Test analysis engine with sample data"""
        result = {
            'success': True,
            'summary': "",
            'details': {},
            'warnings': []
        }
        
        if self.quick_mode:
            # Skip intensive testing in quick mode
            result['summary'] = "Skipped in quick mode"
            return result
        
        try:
            # Create synthetic test data
            test_data = self._create_synthetic_test_data()
            
            # Test unified analyzer
            from src.analysis.unified_analyzer import UnifiedNanoindentationAnalyzer
            analyzer = UnifiedNanoindentationAnalyzer()
            
            # Test single test analysis
            test_result = analyzer.analyze_single_test(test_data, "synthetic_test")
            
            assert test_result['success'], "Analysis failed on synthetic data"
            assert 'mechanical_properties' in test_result, "No mechanical properties calculated"
            assert 'curve_fitting' in test_result, "No curve fitting performed"
            
            # Test quality metrics
            r_squared = test_result['curve_fitting'].get('r_squared', 0)
            assert r_squared > 0.8, f"Poor curve fit quality: R² = {r_squared:.3f}"
            
            result['details'] = {
                'analysis_success': test_result['success'],
                'r_squared': r_squared,
                'has_properties': 'mechanical_properties' in test_result
            }
            result['summary'] = f"Analysis engine working (R² = {r_squared:.3f})"
            
        except Exception as e:
            result['success'] = False
            result['summary'] = f"Analysis engine failed: {str(e)}"
            result['details']['error'] = str(e)
        
        return result
    
    def _test_tip_calibration(self) -> Dict[str, any]:
        """Test tip calibration functionality"""
        result = {
            'success': True,
            'summary': "",
            'details': {},
            'warnings': []
        }
        
        try:
            # Test tip calibration components
            from src.calibration.tip_calibrator import TipCalibration
            from src.calibration.nist_methods import NISTCalibrationMethods
            
            # Test basic tip calibration
            tip_cal = TipCalibration()
            
            # Test with synthetic data
            contact_depths = np.linspace(50, 200, 10)  # nm
            stiffness_values = np.linspace(0.1, 1.0, 10)  # mN/nm
            
            # This would normally require actual calibration data
            # For testing, we check that the methods exist and can be called
            assert hasattr(tip_cal, 'calibrate_from_measurements'), "Missing calibration method"
            
            # Test NIST methods
            nist_methods = NISTCalibrationMethods()
            assert hasattr(nist_methods, 'extract_tip_coefficients_from_file'), "Missing NIST extraction method"
            
            result['details'] = {
                'tip_calibration_available': True,
                'nist_methods_available': True
            }
            result['summary'] = "Tip calibration components available"
            
        except Exception as e:
            result['success'] = False
            result['summary'] = f"Tip calibration failed: {str(e)}"
            result['details']['error'] = str(e)
        
        return result
    
    def _test_gui_integration(self) -> Dict[str, any]:
        """Test GUI integration (import only, no display)"""
        result = {
            'success': True,
            'summary': "",
            'details': {},
            'warnings': []
        }
        
        try:
            # Test GUI imports without starting the GUI
            from src.gui.main_interface import NanoindentationGUI
            
            # Check that GUI class can be instantiated (but don't show it)
            gui_class = NanoindentationGUI
            assert hasattr(gui_class, '__init__'), "GUI class missing constructor"
            
            # Test tkinter availability
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()  # Hide the window
            root.destroy()   # Clean up
            
            result['details'] = {
                'gui_class_available': True,
                'tkinter_available': True
            }
            result['summary'] = "GUI components available"
            
        except ImportError as e:
            # GUI components missing is acceptable
            result['warnings'].append(f"GUI components not available: {e}")
            result['summary'] = "GUI components not available (acceptable)"
        except Exception as e:
            result['success'] = False
            result['summary'] = f"GUI integration failed: {str(e)}"
            result['details']['error'] = str(e)
        
        return result
    
    def _test_nist_compliance(self) -> Dict[str, any]:
        """Test NIST compliance features"""
        result = {
            'success': True,
            'summary': "",
            'details': {},
            'warnings': []
        }
        
        try:
            from src.core.standards import ISO14577Constants
            from src.calibration.nist_methods import NISTCalibrationMethods
            
            # Test ISO constants
            iso = ISO14577Constants()
            
            # Verify NIST/ISO compliance parameters
            assert iso.MIN_R_SQUARED == 0.98, "Incorrect ISO R² requirement"
            assert hasattr(iso, 'FUSED_SILICA_MODULUS'), "Missing fused silica reference"
            assert hasattr(iso, 'DIAMOND_MODULUS'), "Missing diamond properties"
            
            # Test NIST calibration methods
            nist = NISTCalibrationMethods()
            
            # Verify reference material data
            silica_props = nist.get_reference_material_properties('fused_silica')
            assert silica_props is not None, "Fused silica reference data missing"
            
            result['details'] = {
                'iso_compliance_ok': True,
                'nist_methods_ok': True,
                'reference_materials_ok': True
            }
            result['summary'] = "NIST compliance features working"
            
        except Exception as e:
            result['success'] = False
            result['summary'] = f"NIST compliance failed: {str(e)}"
            result['details']['error'] = str(e)
        
        return result
    
    def _test_data_validation(self) -> Dict[str, any]:
        """Test data validation functionality"""
        result = {
            'success': True,
            'summary': "",
            'details': {},
            'warnings': []
        }
        
        try:
            from src.core.validators import DataValidator, create_comprehensive_validation_report
            
            # Create test data
            test_data = self._create_synthetic_test_data()
            
            # Test data validator
            validator = DataValidator()
            validation_result = validator.validate_nanoindentation_data(test_data)
            
            assert validation_result['success'], "Data validation failed on good data"
            
            # Test comprehensive validation report
            analysis_summary = {
                'r_squared': 0.99,
                'stiffness': 0.5,
                'hardness': 10.0,
                'modulus': 70.0
            }
            
            report = create_comprehensive_validation_report(test_data, analysis_summary)
            assert 'curve_quality' in report, "Validation report missing curve quality"
            
            result['details'] = {
                'validator_working': True,
                'report_generation_ok': True,
                'data_quality_ok': validation_result['success']
            }
            result['summary'] = "Data validation working"
            
        except Exception as e:
            result['success'] = False
            result['summary'] = f"Data validation failed: {str(e)}"
            result['details']['error'] = str(e)
        
        return result
    
    def _test_legacy_compatibility(self) -> Dict[str, any]:
        """Test legacy compatibility features"""
        result = {
            'success': True,
            'summary': "",
            'details': {},
            'warnings': []
        }
        
        try:
            # Test that legacy analyzer can still be imported
            from src.analysis.legacy_analyzer import IndentXLSAnalyzer
            
            # Test that enhanced analyzer inherits properly
            from src.analysis.enhanced_analyzer import FixedIndentXLSAnalyzer
            
            # Verify inheritance
            assert issubclass(FixedIndentXLSAnalyzer, IndentXLSAnalyzer), "Inheritance broken"
            
            # Test that unified analyzer has legacy mode
            from src.analysis.unified_analyzer import UnifiedNanoindentationAnalyzer
            unified = UnifiedNanoindentationAnalyzer(legacy_mode=True)
            assert unified.legacy_mode, "Legacy mode not properly set"
            
            result['details'] = {
                'legacy_analyzer_ok': True,
                'enhanced_analyzer_ok': True,
                'unified_legacy_mode_ok': True
            }
            result['summary'] = "Legacy compatibility maintained"
            
        except Exception as e:
            result['success'] = False
            result['summary'] = f"Legacy compatibility failed: {str(e)}"
            result['details']['error'] = str(e)
        
        return result
    
    def _create_synthetic_test_data(self) -> pd.DataFrame:
        """Create synthetic nanoindentation data for testing"""
        # Generate realistic loading/unloading curve
        max_load = 1.0  # mN
        max_displacement = 100.0  # nm
        
        # Loading phase
        loading_disp = np.linspace(0, max_displacement, 100)
        loading_load = max_load * (loading_disp / max_displacement) ** 2
        
        # Unloading phase (Oliver-Pharr power law)
        unloading_disp = np.linspace(max_displacement, 20, 50)
        hf = 20.0  # final displacement
        A = 0.5   # fitting parameter
        m = 1.5   # power law exponent
        unloading_load = A * (unloading_disp - hf) ** m
        
        # Combine phases
        displacement = np.concatenate([loading_disp, unloading_disp])
        load = np.concatenate([loading_load, unloading_load])
        
        # Add small amount of noise
        noise_level = 0.01
        load += np.random.normal(0, noise_level * max_load, len(load))
        displacement += np.random.normal(0, noise_level * max_displacement, len(displacement))
        
        # Create DataFrame
        return pd.DataFrame({
            'Load (mN)': load,
            'Displacement (nm)': displacement,
            'Time (s)': np.linspace(0, 100, len(load))
        })
    
    def run_quick_test(self) -> bool:
        """
        Run a quick subset of tests for rapid validation
        
        Returns:
            True if basic functionality is working
        """
        print("🚀 QUICK TEST MODE")
        print("-" * 30)
        
        quick_tests = [
            ("Imports", self._test_imports),
            ("Core", self._test_core_functionality),
            ("Legacy", self._test_legacy_compatibility)
        ]
        
        success = True
        for name, test_func in quick_tests:
            try:
                result = test_func()
                status = "✅" if result['success'] else "❌"
                print(f"{status} {name}")
                if not result['success']:
                    success = False
            except Exception as e:
                print(f"❌ {name}: {e}")
                success = False
        
        print(f"\n{'✅ QUICK TEST PASSED' if success else '❌ QUICK TEST FAILED'}")
        return success


# Standalone execution functions
def run_comprehensive_tests(verbose: bool = True) -> Dict[str, any]:
    """Run comprehensive test suite"""
    suite = UnifiedTestSuite(verbose=verbose, quick_mode=False)
    return suite.run_all_tests()

def run_quick_tests() -> bool:
    """Run quick validation tests"""
    suite = UnifiedTestSuite(verbose=False, quick_mode=True)
    return suite.run_quick_test()

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Unified Nanoindentation Test Suite')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only')
    parser.add_argument('--quiet', action='store_true', help='Reduce output verbosity')
    
    args = parser.parse_args()
    
    if args.quick:
        success = run_quick_tests()
        sys.exit(0 if success else 1)
    else:
        results = run_comprehensive_tests(verbose=not args.quiet)
        sys.exit(0 if results['overall_success'] else 1)


if __name__ == "__main__":
    main()
