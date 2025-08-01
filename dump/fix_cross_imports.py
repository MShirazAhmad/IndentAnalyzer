#!/usr/bin/env python3
"""
Comprehensive Import Fix Script
Updates all import statements to work with the new package structure
"""

import os
import re
from pathlib import Path

def fix_cross_module_imports():
    """Fix cross-module imports throughout the package"""
    
    # Define the mapping of modules to their new locations
    module_locations = {
        'standards': 'core.standards',
        'data_processor': 'core.data_processor', 
        'validators': 'core.validators',
        'main_analyzer': 'analysis.main_analyzer',
        'curve_fitting': 'analysis.curve_fitting',
        'mechanical_calculator': 'analysis.mechanical_calculator',
        'legacy_analyzer': 'analysis.legacy_analyzer',
        'enhanced_analyzer': 'analysis.enhanced_analyzer',
        'nist_methods': 'calibration.nist_methods',
        'tip_calibrator': 'calibration.tip_calibrator',
        'main_interface': 'gui.main_interface'
    }
    
    # Process each Python file in src
    src_dir = Path('src')
    for py_file in src_dir.rglob('*.py'):
        if py_file.name == '__init__.py':
            continue
            
        with open(py_file, 'r') as f:
            content = f.read()
        
        original_content = content
        current_package = str(py_file.parent).replace('src/', '').replace('src', '').strip('/')
        
        # Fix imports based on the current file's location
        for module_name, full_path in module_locations.items():
            current_module = current_package.replace('/', '.')
            target_module = full_path
            
            # Skip if trying to import from same module
            if current_module == target_module.split('.')[0]:
                # Same package, use relative import
                if current_module == 'core':
                    # Within core package
                    pattern = rf'from \.?{module_name} import'
                    if module_name in ['data_processor', 'validators', 'standards']:
                        replacement = f'from .{module_name.split(".")[-1]} import'
                    else:
                        replacement = f'from ..{target_module.replace(".", ".")} import'
                elif current_module == 'analysis':
                    # Within analysis package  
                    if module_name in ['main_analyzer', 'curve_fitting', 'mechanical_calculator', 'legacy_analyzer', 'enhanced_analyzer']:
                        replacement = f'from .{module_name.split(".")[-1]} import'
                    else:
                        replacement = f'from ..{target_module} import'
                elif current_module == 'calibration':
                    # Within calibration package
                    if module_name in ['nist_methods', 'tip_calibrator']:
                        replacement = f'from .{module_name.split(".")[-1]} import'
                    else:
                        replacement = f'from ..{target_module} import'
                elif current_module == 'gui':
                    # Within GUI package
                    if module_name == 'main_interface':
                        replacement = f'from .{module_name} import'
                    else:
                        replacement = f'from ..{target_module} import'
            else:
                # Different package, use absolute import from src
                replacement = f'from ..{target_module} import'
            
            # Apply the pattern replacement
            pattern = rf'from \.?{module_name} import'
            content = re.sub(pattern, replacement, content)
            
            # Also handle standalone imports
            pattern_standalone = rf'import \.?{module_name}'
            replacement_standalone = f'import ..{target_module}'
            content = re.sub(pattern_standalone, replacement_standalone, content)
        
        # Write back if changed
        if content != original_content:
            with open(py_file, 'w') as f:
                f.write(content)
            print(f"Fixed cross-module imports in: {py_file}")

def simplify_imports():
    """Simplify imports by making them more direct"""
    src_dir = Path('src')
    
    for py_file in src_dir.rglob('*.py'):
        if py_file.name == '__init__.py':
            continue
            
        with open(py_file, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Get the current package path
        rel_path = py_file.relative_to(src_dir)
        current_package = str(rel_path.parent).replace('/', '.')
        
        # Simplify specific imports based on file location
        if 'analysis' in str(py_file):
            # For analysis files, import core modules directly
            content = re.sub(r'from \.?standards import', 'from ..core.standards import', content)
            content = re.sub(r'from \.?data_processor import', 'from ..core.data_processor import', content)
            content = re.sub(r'from \.?validators import', 'from ..core.validators import', content)
            
        elif 'calibration' in str(py_file):
            # For calibration files, import core and analysis modules
            content = re.sub(r'from \.?standards import', 'from ..core.standards import', content)
            content = re.sub(r'from \.?data_processor import', 'from ..core.data_processor import', content)
            content = re.sub(r'from \.?main_analyzer import', 'from ..analysis.main_analyzer import', content)
            
        elif 'gui' in str(py_file):
            # For GUI files, import from all other modules
            content = re.sub(r'from \.?standards import', 'from ..core.standards import', content)
            content = re.sub(r'from \.?main_analyzer import', 'from ..analysis.main_analyzer import', content)
            content = re.sub(r'from \.?tip_calibrator import', 'from ..calibration.tip_calibrator import', content)
        
        # Write back if changed
        if content != original_content:
            with open(py_file, 'w') as f:
                f.write(content)
            print(f"Simplified imports in: {py_file}")

def main():
    print("Fixing cross-module imports...")
    fix_cross_module_imports()
    
    print("\nSimplifying import paths...")
    simplify_imports()
    
    print("\nImport fixes completed!")

if __name__ == "__main__":
    main()
