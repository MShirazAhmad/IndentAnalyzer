#!/usr/bin/env python3
"""
Quick debug test for verification script
"""

import sys
from pathlib import Path

print("🔍 QUICK DEBUG TEST")
print("=" * 50)

# Check current directory
print(f"Current directory: {Path.cwd()}")
print(f"Python version: {sys.version}")

# Check if unified files exist
unified_files = [
    'src/analysis/unified_analyzer.py',
    'src/core/unified_validation.py',
    'src/core/unified_utils.py', 
    'tests/unified_test_suite.py',
    'CONSOLIDATED_README.md'
]

print("\n📁 Checking unified files:")
for file_path in unified_files:
    if Path(file_path).exists():
        size_kb = Path(file_path).stat().st_size / 1024
        print(f"   ✅ {file_path} ({size_kb:.1f} KB)")
    else:
        print(f"   ❌ {file_path} (MISSING)")

# Try to import verification
print("\n🔬 Testing verification import:")
try:
    import verify_consolidation
    print("   ✅ verify_consolidation module imported successfully")
    
    # Test verification function
    print("\n🧪 Testing verification function:")
    success = verify_consolidation.verify_consolidation(debug_mode=True, verbose=True)
    print(f"   Verification result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
except Exception as e:
    print(f"   ❌ Import/execution failed: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n🎯 Debug test complete!")
