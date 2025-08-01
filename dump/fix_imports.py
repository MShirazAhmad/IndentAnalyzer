#!/usr/bin/env python3
"""
Import Fix Script
Updates import statements to work with the restructured package
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix import statements in a single file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Define import mappings
    import_mappings = {
        'iso_constants': 'standards',
        'data_processing': 'data_processor', 
        'data_validation': 'validators',
        'mechanical_properties': 'mechanical_calculator',
        'nanoindentation_analyzer': 'main_analyzer',
        'nist_calibration': 'nist_methods',
        'final_tip_calibration': 'tip_calibrator',
        'nanoindentation_gui': 'main_interface',
        'run_hec14s1_analysis': 'enhanced_analyzer'
    }
    
    # Fix relative imports (from .old_module import ...)
    for old_name, new_name in import_mappings.items():
        # Pattern for relative imports
        pattern_rel = rf'from \.{old_name} import'
        replacement_rel = f'from .{new_name} import'
        content = re.sub(pattern_rel, replacement_rel, content)
        
        # Pattern for absolute imports  
        pattern_abs = rf'from {old_name} import'
        replacement_abs = f'from {new_name} import'
        content = re.sub(pattern_abs, replacement_abs, content)
        
        # Pattern for direct imports
        pattern_direct = rf'import {old_name}'
        replacement_direct = f'import {new_name}'
        content = re.sub(pattern_direct, replacement_direct, content)
    
    # Special case for IndentXLSAnalyzer import in enhanced_analyzer
    if 'enhanced_analyzer.py' in str(file_path):
        content = re.sub(r'from IndentXLSAnalyzer import IndentXLSAnalyzer', 
                        'from .legacy_analyzer import IndentXLSAnalyzer', content)
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Updated imports in: {file_path}")
        return True
    return False

def main():
    """Fix imports in all Python files in src directory"""
    src_dir = Path('src')
    
    if not src_dir.exists():
        print("src directory not found!")
        return
    
    updated_files = 0
    total_files = 0
    
    for py_file in src_dir.rglob('*.py'):
        total_files += 1
        if fix_imports_in_file(py_file):
            updated_files += 1
    
    print(f"\nProcessed {total_files} Python files")
    print(f"Updated imports in {updated_files} files")

if __name__ == "__main__":
    main()
