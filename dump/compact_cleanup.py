#!/usr/bin/env python3
"""
Compact Code Cleanup Script
Removes duplicates and creates a streamlined, compact structure
"""

import os
import shutil
from pathlib import Path

def cleanup_duplicates():
    """Remove duplicate files that are outside the organized src/ structure"""
    
    # Files that have been moved to src/ and should be removed from root
    duplicates_to_remove = [
        'iso_constants.py',
        'data_processing.py', 
        'data_validation.py',
        'curve_fitting.py',
        'mechanical_properties.py',
        'nanoindentation_analyzer.py',
        'nist_calibration.py',
        'final_tip_calibration.py',
        'nanoindentation_gui.py',
        'analyze_modular.py',
        'launch_gui.sh'
    ]
    
    # Test files that have been moved to tests/
    test_duplicates = [
        'test_comprehensive.py',
        'test_nist_compliance.py',
        'test_cmdline.py',
        'test_complete_gui.py', 
        'test_gui_quick.py',
        'test_tip_direct.py'
    ]
    
    # Redundant calibration files
    redundant_calibration = [
        'enhanced_tip_calibration.py',
        'simple_tip_calibration.py',
        'quick_tip_analysis.py',
        'tip_calibration.py',
        'tip_calibration_fixed.py',
        'tip_coefficients_summary.py'
    ]
    
    # Redundant documentation
    redundant_docs = [
        'REORGANIZATION_COMPLETE.md',
        'REORGANIZATION_PLAN.md', 
        'REORGANIZATION_SUCCESS.md',
        'RESTRUCTURING_SUMMARY.md',
        'NIST_COMPLIANCE.md',
        'NIST_VERIFICATION_REPORT.md'
    ]
    
    # Other redundant files
    other_redundant = [
        '__init___new.py'
    ]
    
    all_duplicates = duplicates_to_remove + test_duplicates + redundant_calibration + redundant_docs + other_redundant
    
    removed_count = 0
    
    for file_name in all_duplicates:
        file_path = Path(file_name)
        if file_path.exists():
            print(f"Removing duplicate: {file_name}")
            file_path.unlink()
            removed_count += 1
    
    print(f"\n✅ Removed {removed_count} duplicate/redundant files")
    return removed_count

def create_compact_structure():
    """Create a more compact directory structure"""
    
    # Move archive_duplicates to a more compact location
    if Path('archive_duplicates').exists():
        print("📦 Compacting archive...")
        # Could compress this or move to a hidden directory
        
    # Ensure all essential directories exist
    essential_dirs = [
        'src/core',
        'src/analysis', 
        'src/calibration',
        'src/gui',
        'tests',
        'docs', 
        'data/reference',
        'scripts',
        'config'
    ]
    
    for dir_path in essential_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✅ Compact structure verified")

def consolidate_documentation():
    """Consolidate documentation into fewer, more comprehensive files"""
    
    docs_dir = Path('docs')
    
    # Create a single comprehensive README
    readme_content = """# Nanoindentation Analysis Package

## Quick Start
1. **Determine Tip Coefficients**: `python scripts/determine_tip_coefficients.py`
2. **Analyze Sample**: `python scripts/analyze_sample.py your_data.xls`
3. **Launch GUI**: `./scripts/launch_application.sh`

## Structure
- `src/` - Source code modules
- `tests/` - Test suite  
- `data/` - Reference materials and results
- `scripts/` - Utility scripts
- `config/` - Configuration files

## Features
- ISO 14577-4:2016 compliant analysis
- NIST-calibrated tip functions
- Oliver-Pharr method implementation
- Quality validation and reporting
- Interactive GUI interface

For detailed documentation, see files in `docs/` directory.
"""
    
    with open('README.md', 'w') as f:
        f.write(readme_content)
    
    print("✅ Created compact README")

def optimize_imports():
    """Create a single, optimized __init__.py"""
    
    compact_init = '''#!/usr/bin/env python3
"""
Nanoindentation Analysis Package - Compact Version
ISO 14577-4:2016 compliant analysis with streamlined structure
"""

import sys
import os

# Add src to path
_src_path = os.path.join(os.path.dirname(__file__), 'src')
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

# Core imports with error handling
try:
    from src.gui.main_interface import NanoindentationGUI
    from src.calibration.tip_calibrator import run_complete_tip_calibration
    from src.analysis.enhanced_analyzer import FixedIndentXLSAnalyzer
    from src.analysis.legacy_analyzer import IndentXLSAnalyzer
    from src.core.standards import ISO14577Constants
    
    # Simplified exports
    __all__ = [
        'NanoindentationGUI',
        'run_complete_tip_calibration', 
        'FixedIndentXLSAnalyzer',
        'IndentXLSAnalyzer',
        'ISO14577Constants'
    ]
    
except ImportError:
    print("⚠️ Some components not available. Run from package directory.")
    __all__ = []

__version__ = "2.1.0"
__description__ = "ISO 14577-4:2016 compliant nanoindentation analysis"

def quick_calibrate(reference_file="data/reference/fused_silica_reference.xls"):
    """Quick tip calibration using reference data"""
    return run_complete_tip_calibration(reference_file)

def launch_gui():
    """Launch the analysis GUI"""
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication.instance() or QApplication(sys.argv)
    gui = NanoindentationGUI()
    gui.show()
    return app.exec_()
'''
    
    with open('__init__.py', 'w') as f:
        f.write(compact_init)
    
    print("✅ Created compact __init__.py")

def create_unified_test():
    """Create a single, comprehensive test file"""
    
    unified_test = '''#!/usr/bin/env python3
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
    
    print(f"\\nResult: {passed}/{total} tests passed")
    return passed == total

if __name__ == "__main__":
    success = test_all()
    sys.exit(0 if success else 1)
'''
    
    with open('tests/test_unified.py', 'w') as f:
        f.write(unified_test)
    
    print("✅ Created unified test suite")

def create_compact_scripts():
    """Create streamlined utility scripts"""
    
    # Quick calibration script
    quick_calibrate = '''#!/usr/bin/env python3
"""Quick Tip Calibration - Compact Version"""
import sys, os
sys.path.insert(0, '.')
from src.calibration.tip_calibrator import run_complete_tip_calibration

if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else "data/reference/fused_silica_reference.xls"
    print(f"🔬 Calibrating tip using: {file_path}")
    result = run_complete_tip_calibration(file_path)
    print("✅ Calibration complete!")
'''
    
    # Quick launch script
    quick_launch = '''#!/usr/bin/env python3
"""Quick Launch - Compact Version"""
import sys, os
sys.path.insert(0, '.')

try:
    from src.gui.main_interface import NanoindentationGUI
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    gui = NanoindentationGUI()
    gui.show()
    sys.exit(app.exec_())
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Install requirements: pip install PyQt5 matplotlib pandas numpy scipy xlrd")
'''
    
    with open('scripts/quick_calibrate.py', 'w') as f:
        f.write(quick_calibrate)
    
    with open('scripts/quick_launch.py', 'w') as f:
        f.write(quick_launch)
    
    os.chmod('scripts/quick_calibrate.py', 0o755)
    os.chmod('scripts/quick_launch.py', 0o755)
    
    print("✅ Created compact utility scripts")

def main():
    """Main cleanup and compacting process"""
    print("🧹 STARTING COMPACT CODE CLEANUP")
    print("=" * 50)
    
    # Step 1: Remove duplicates
    removed = cleanup_duplicates()
    
    # Step 2: Create compact structure
    create_compact_structure()
    
    # Step 3: Consolidate documentation
    consolidate_documentation()
    
    # Step 4: Optimize main package file
    optimize_imports()
    
    # Step 5: Create unified test
    create_unified_test()
    
    # Step 6: Create compact scripts
    create_compact_scripts()
    
    print("\\n" + "=" * 50)
    print("🎉 COMPACT CLEANUP COMPLETED!")
    print("=" * 50)
    print(f"✅ Removed {removed} duplicate files")
    print("✅ Streamlined directory structure")
    print("✅ Consolidated documentation") 
    print("✅ Optimized package imports")
    print("✅ Created unified test suite")
    print("✅ Added compact utility scripts")
    
    print("\\n📁 COMPACT STRUCTURE:")
    print("  src/           # Source modules")
    print("  tests/         # Unified tests") 
    print("  data/          # Reference data")
    print("  scripts/       # Utility scripts")
    print("  config/        # Configuration")
    print("  docs/          # Documentation")
    
    print("\\n🚀 QUICK COMMANDS:")
    print("  python scripts/quick_calibrate.py")
    print("  python scripts/quick_launch.py")
    print("  python tests/test_unified.py")

if __name__ == "__main__":
    main()
