# Code Reorganization Plan

## 🎯 Objectives
1. **Eliminate duplicate code** - Multiple tip calibration scripts doing the same thing
2. **Consolidate functionality** - Single source of truth for each feature
3. **Clean architecture** - Clear separation of concerns
4. **Reduce maintenance** - Less files, cleaner imports

## 📁 Current Duplications Identified

### Tip Calibration Scripts (HIGH DUPLICATION)
- `tip_calibration.py` - Original tip calibration script
- `tip_calibration_fixed.py` - Fixed version with plotting
- `enhanced_tip_calibration.py` - Enhanced with visualization
- `final_tip_calibration.py` - Final version using NIST methods
- `test_tip_direct.py` - Test script using NIST methods
- `simple_tip_calibration.py` - Simple version for testing

**ALL THESE DO THE SAME THING: Extract tip coefficients from silica data**

### Test Scripts (MODERATE DUPLICATION)
- `test_gui_quick.py` - Quick GUI test
- `test_complete_gui.py` - Complete GUI test  
- `test_gui_integration.py` - GUI integration test
- `test_cmdline.py` - Command line test
- `test_nist_compliance.py` - NIST compliance test

### Analysis Scripts (LOW DUPLICATION)
- `IndentXLSAnalyzer.py` - Original analyzer (legacy)
- `run_hec14s1_analysis.py` - Enhanced analyzer
- `analyze_modular.py` - Modular command-line interface

## 🎯 Reorganization Strategy

### 1. Consolidate Tip Calibration
**KEEP**: `final_tip_calibration.py` (most mature, uses NIST methods)
**REMOVE**: All other tip calibration scripts
**ENHANCE**: Add plotting capabilities to final version

### 2. Consolidate Testing  
**KEEP**: 
- `test_nist_compliance.py` (system validation)
- `test_gui_integration.py` (GUI testing)
**REMOVE**: Other test scripts
**CREATE**: `tests/` directory structure

### 3. Consolidate Analysis
**KEEP**:
- `nanoindentation_analyzer.py` (main analyzer)
- `analyze_modular.py` (CLI interface)
**REMOVE**: Legacy analyzers

### 4. Clean Core Modules
**OPTIMIZE**:
- Remove circular imports
- Consolidate constants
- Clean up duplicate functions

## 📋 Implementation Steps

### Step 1: Backup and Remove Duplicates
- Create backup of current state
- Remove duplicate tip calibration files
- Remove duplicate test files

### Step 2: Enhance Retained Files
- Add missing functionality from removed files
- Consolidate best features

### Step 3: Fix Imports and Dependencies
- Update all import statements
- Remove circular dependencies
- Clean __init__.py

### Step 4: Create Tests Directory
- Move tests to proper structure
- Consolidate test utilities

### Step 5: Documentation Update
- Update README files
- Create usage guide
- Document API

## 🎯 Expected Results
- **Reduce files from 44 to ~25** (45% reduction)
- **Eliminate code duplication** (estimated 60% duplicate code removal)
- **Cleaner imports** (no circular dependencies)
- **Single source of truth** for each functionality
- **Easier maintenance** and debugging
