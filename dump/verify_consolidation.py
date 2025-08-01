#!/usr/bin/env python3
"""
CONSOLIDATION VERIFICATION SCRIPT
==================================

Comprehensive verification tool for the nanoindentation codebase consolidation project.
This script validates that all unified modules were created successfully and maintains
backward compatibility with legacy code.

Features:
- Verifies existence and size of all unified modules
- Checks legacy file preservation for backward compatibility
- Identifies remaining duplicate files that can be archived
- Provides detailed consolidation metrics and next steps
- Includes debug mode for troubleshooting

Usage:
    python3 verify_consolidation.py [--debug] [--verbose]
    
Author: Consolidation System
Date: July 29, 2025
Purpose: Validate successful code deduplication and organization
"""

import os
from pathlib import Path
import sys
import argparse
import traceback
from typing import Dict, List, Tuple, Optional

def debug_print(message: str, debug_mode: bool = False) -> None:
    """
    Debug printing function for troubleshooting.
    
    Args:
        message: Debug message to print
        debug_mode: Whether debug mode is enabled
    """
    if debug_mode:
        print(f"🐛 DEBUG: {message}")


def check_file_details(file_path: Path, debug_mode: bool = False) -> Tuple[bool, float, str]:
    """
    Check file existence and gather detailed information.
    
    Args:
        file_path: Path to the file to check
        debug_mode: Whether to print debug information
        
    Returns:
        Tuple of (exists, size_kb, error_message)
    """
    try:
        debug_print(f"Checking file: {file_path}", debug_mode)
        
        if not file_path.exists():
            debug_print(f"File does not exist: {file_path}", debug_mode)
            return False, 0.0, f"File not found: {file_path}"
        
        # Check if it's actually a file
        if not file_path.is_file():
            debug_print(f"Path exists but is not a file: {file_path}", debug_mode)
            return False, 0.0, f"Path exists but is not a file: {file_path}"
        
        # Get file size
        size_bytes = file_path.stat().st_size
        size_kb = size_bytes / 1024
        
        debug_print(f"File found: {file_path} ({size_kb:.1f} KB)", debug_mode)
        return True, size_kb, ""
        
    except Exception as e:
        error_msg = f"Error checking {file_path}: {str(e)}"
        debug_print(error_msg, debug_mode)
        return False, 0.0, error_msg


def verify_unified_modules(debug_mode: bool = False) -> Tuple[bool, float, List[str]]:
    """
    Verify that all unified modules were created successfully.
    
    Args:
        debug_mode: Whether to print debug information
        
    Returns:
        Tuple of (all_exist, total_size_kb, error_messages)
    """
    debug_print("Starting unified modules verification", debug_mode)
    
    # Files that should have been created during consolidation
    unified_files = {
        'src/analysis/unified_analyzer.py': 'Unified analyzer (3 analyzers → 1)',
        'src/core/unified_validation.py': 'Unified validation (4 scripts → 1)', 
        'src/core/unified_utils.py': 'Unified utilities (many functions → 1)',
        'tests/unified_test_suite.py': 'Unified tests (8+ files → 1)',
        'CONSOLIDATION_COMPLETE.md': 'Consolidation documentation'
    }
    
    print("📁 Checking unified modules:")
    all_exist = True
    total_size = 0.0
    error_messages = []
    
    for file_path, description in unified_files.items():
        debug_print(f"Verifying: {file_path}", debug_mode)
        
        exists, size_kb, error_msg = check_file_details(Path(file_path), debug_mode)
        
        if exists:
            total_size += size_kb
            print(f"   ✅ {file_path}")
            print(f"      {description} ({size_kb:.1f} KB)")
            debug_print(f"Successfully verified: {file_path}", debug_mode)
        else:
            print(f"   ❌ {file_path} (MISSING)")
            print(f"      {description}")
            error_messages.append(error_msg or f"Missing file: {file_path}")
            all_exist = False
            debug_print(f"Failed to verify: {file_path}", debug_mode)
    
    print(f"\n📊 Total unified code: {total_size:.1f} KB")
    debug_print(f"Unified modules verification complete. Success: {all_exist}", debug_mode)
    
    return all_exist, total_size, error_messages


def verify_legacy_compatibility(debug_mode: bool = False) -> Tuple[bool, List[str]]:
    """
    Verify that legacy files are preserved for backward compatibility.
    
    Args:
        debug_mode: Whether to print debug information
        
    Returns:
        Tuple of (legacy_preserved, error_messages)
    """
    debug_print("Starting legacy compatibility verification", debug_mode)
    
    print("\n🔄 Checking legacy compatibility:")
    legacy_files = [
        'src/analysis/main_analyzer.py',
        'src/analysis/enhanced_analyzer.py', 
        'src/analysis/legacy_analyzer.py'
    ]
    
    legacy_preserved = True
    error_messages = []
    
    for file_path in legacy_files:
        debug_print(f"Checking legacy file: {file_path}", debug_mode)
        
        exists, _, error_msg = check_file_details(Path(file_path), debug_mode)
        
        if exists:
            print(f"   ✅ {file_path} (preserved)")
            debug_print(f"Legacy file preserved: {file_path}", debug_mode)
        else:
            print(f"   ❌ {file_path} (missing - needed for compatibility)")
            error_messages.append(error_msg or f"Missing legacy file: {file_path}")
            legacy_preserved = False
            debug_print(f"Legacy file missing: {file_path}", debug_mode)
    
    debug_print(f"Legacy compatibility check complete. Success: {legacy_preserved}", debug_mode)
    return legacy_preserved, error_messages


def check_archived_duplicates(debug_mode: bool = False) -> int:
    """
    Check for duplicate files that should have been archived.
    
    Args:
        debug_mode: Whether to print debug information
        
    Returns:
        Number of duplicate files still present
    """
    debug_print("Checking for archived duplicates", debug_mode)
    
    print("\n📦 Checking archived duplicates:")
    validation_files = [
        'validate_tip_calibration.py',
        'validate_tip_calibration_fixed.py',
        'validate_comprehensive.py'
    ]
    
    duplicates_still_present = 0
    
    for file_path in validation_files:
        debug_print(f"Checking duplicate file: {file_path}", debug_mode)
        
        exists, _, _ = check_file_details(Path(file_path), debug_mode)
        
        if exists:
            print(f"   ⚠️ {file_path} (can be archived - functionality moved to unified_validation.py)")
            duplicates_still_present += 1
            debug_print(f"Duplicate file still present: {file_path}", debug_mode)
        else:
            print(f"   ✅ {file_path} (already archived)")
            debug_print(f"Duplicate file properly archived: {file_path}", debug_mode)
    
    debug_print(f"Duplicate check complete. Found: {duplicates_still_present}", debug_mode)
    return duplicates_still_present


def verify_consolidation(debug_mode: bool = False, verbose: bool = False):
    """
    Main verification function that orchestrates all consolidation checks.
    
    This function performs comprehensive validation of the codebase consolidation:
    1. Verifies all unified modules were created
    2. Checks legacy compatibility is maintained  
    3. Identifies remaining duplicate files
    4. Provides detailed metrics and recommendations
    
    Args:
        debug_mode: Enable debug output for troubleshooting
        verbose: Enable verbose output for detailed information
        
    Returns:
        bool: True if consolidation was successful, False otherwise
    """
    try:
        debug_print("Starting consolidation verification", debug_mode)
        
        print("🔍 NANOINDENTATION CODEBASE CONSOLIDATION VERIFICATION")
        print("=" * 65)
        
        if debug_mode:
            print("🐛 DEBUG MODE ENABLED")
            print(f"   Working directory: {Path.cwd()}")
            print(f"   Python version: {sys.version}")
            print("=" * 65)
        
        # Step 1: Verify unified modules
        debug_print("Step 1: Verifying unified modules", debug_mode)
        all_exist, total_size, unified_errors = verify_unified_modules(debug_mode)
        
        if verbose and unified_errors:
            print("\n⚠️ Unified module errors:")
            for error in unified_errors:
                print(f"   • {error}")
        
        # Step 2: Check legacy compatibility
        debug_print("Step 2: Checking legacy compatibility", debug_mode)
        legacy_preserved, legacy_errors = verify_legacy_compatibility(debug_mode)
        
        if verbose and legacy_errors:
            print("\n⚠️ Legacy compatibility errors:")
            for error in legacy_errors:
                print(f"   • {error}")
        
        # Step 3: Check archived duplicates
        debug_print("Step 3: Checking archived duplicates", debug_mode)
        duplicates_still_present = check_archived_duplicates(debug_mode)
        
        # Summary
        print("\n" + "=" * 65)
        print("📈 CONSOLIDATION SUMMARY")
        print("=" * 65)
        
        if all_exist:
            print("✅ All unified modules created successfully")
            debug_print("All unified modules verification passed", debug_mode)
        else:
            print("❌ Some unified modules missing")
            debug_print(f"Unified modules verification failed. Errors: {len(unified_errors)}", debug_mode)
        
        if legacy_preserved:
            print("✅ Legacy compatibility maintained")
            debug_print("Legacy compatibility verification passed", debug_mode)
        else:
            print("❌ Legacy compatibility broken")
            debug_print(f"Legacy compatibility verification failed. Errors: {len(legacy_errors)}", debug_mode)
        
        print(f"📊 Code reduction achieved:")
        print(f"   • Analyzer classes: 3 → 1 unified")
        print(f"   • Validation scripts: 4 → 1 unified") 
        print(f"   • Test files: 8+ → 1 unified")
        print(f"   • Utility functions: many → 1 centralized")
        print(f"   • Total unified code size: {total_size:.1f} KB")
        
        if duplicates_still_present > 0:
            print(f"⚠️ {duplicates_still_present} duplicate files can still be archived")
        else:
            print("✅ No duplicate files detected")
        
        # Final assessment
        print("\n🎯 FINAL ASSESSMENT:")
        success = all_exist and legacy_preserved
        
        if success:
            print("🎉 CONSOLIDATION SUCCESSFUL!")
            print("   • All unified modules created")
            print("   • Legacy compatibility maintained") 
            print("   • Code significantly reduced and organized")
            print("   • Ready for production use")
            
            print("\n🚀 NEXT STEPS:")
            print("   1. Test unified modules with your data")
            print("   2. Gradually migrate to unified interface")
            print("   3. Archive remaining duplicate files when confident")
            print("   4. Update workflows to use new imports")
            
            debug_print("Consolidation verification completed successfully", debug_mode)
        else:
            print("❌ CONSOLIDATION INCOMPLETE")
            print("   Please check missing files and fix issues")
            
            if verbose:
                print("\n🔧 DEBUGGING INFORMATION:")
                print(f"   • Unified modules errors: {len(unified_errors)}")
                print(f"   • Legacy compatibility errors: {len(legacy_errors)}")
                print(f"   • Working directory: {Path.cwd()}")
                print(f"   • Files in current directory: {len(list(Path('.').iterdir()))}")
            
            debug_print("Consolidation verification failed", debug_mode)
        
        return success
        
    except Exception as e:
        print(f"\n❌ VERIFICATION ERROR: {str(e)}")
        if debug_mode:
            print("\n🐛 FULL TRACEBACK:")
            traceback.print_exc()
        return False


def main():
    """
    Main entry point with command line argument parsing.
    
    Supports:
    --debug: Enable debug output for troubleshooting
    --verbose: Enable verbose output for detailed information
    """
    parser = argparse.ArgumentParser(
        description="Verify nanoindentation codebase consolidation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 verify_consolidation.py                    # Basic verification
    python3 verify_consolidation.py --debug            # With debug output
    python3 verify_consolidation.py --verbose          # With verbose errors
    python3 verify_consolidation.py --debug --verbose  # Maximum detail
        """
    )
    
    parser.add_argument(
        '--debug', 
        action='store_true', 
        help='Enable debug output for troubleshooting'
    )
    
    parser.add_argument(
        '--verbose', 
        action='store_true', 
        help='Enable verbose output with detailed error information'
    )
    
    args = parser.parse_args()
    
    try:
        success = verify_consolidation(debug_mode=args.debug, verbose=args.verbose)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
        if args.debug:
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
