#!/usr/bin/env python3
"""
Modular Nanoindentation Analysis Package
ISO 14577-4:2016 compliant analysis with enhanced features

This package provides a comprehensive, modular architecture for nanoindentation
data analysis with improved code organization, validation, and maintainability.
"""

# Core analyzer components
try:
    from .nanoindentation_analyzer import NanoindentationAnalyzer, analyze_nanoindentation_file
    
    # ISO standards and configuration
    from .iso_constants import (
        ISO14577Constants, 
        AnalysisConfig, 
        MaterialProperties, 
        AreaFunctionCoefficients,
        ValidationLimits
    )
    
    # Data processing and validation
    from .data_processing import ExcelDataLoader, DataProcessor, BatchProcessor
    from .data_validation import (
        DataValidator, 
        HorizontalSegmentDetector,
        create_comprehensive_validation_report
    )
    
    # Curve fitting and mechanical properties
    from .curve_fitting import CurveFitter, LinearFitter, AreaFunction, fit_multiple_methods
    from .mechanical_properties import (
        MechanicalPropertiesCalculator,
        TipCalibration,
        analyze_property_trends
    )
    
    MODULAR_AVAILABLE = True
    
except ImportError as e:
    print(f"Warning: New modular components not available: {e}")
    MODULAR_AVAILABLE = False

# Legacy support
try:
    from .run_hec14s1_analysis import FixedIndentXLSAnalyzer
    LEGACY_AVAILABLE = True
except ImportError:
    FixedIndentXLSAnalyzer = None
    LEGACY_AVAILABLE = False

__version__ = "2.0.0"
__author__ = "Nanoindentation Analysis Team"
__description__ = "Modular ISO 14577-4:2016 compliant nanoindentation analysis"

# Package metadata
if MODULAR_AVAILABLE:
    __all__ = [
        # Main analyzer
        'NanoindentationAnalyzer',
        'analyze_nanoindentation_file',
        
        # Constants and configuration
        'ISO14577Constants',
        'AnalysisConfig', 
        'MaterialProperties',
        'AreaFunctionCoefficients',
        'ValidationLimits',
        
        # Data processing
        'ExcelDataLoader',
        'DataProcessor',
        'BatchProcessor',
        
        # Validation
        'DataValidator',
        'HorizontalSegmentDetector',
        'create_comprehensive_validation_report',
        
        # Curve fitting
        'CurveFitter',
        'LinearFitter',
        'AreaFunction',
        'fit_multiple_methods',
        
        # Mechanical properties
        'MechanicalPropertiesCalculator',
        'TipCalibration',
        'analyze_property_trends',
        
        # Legacy
        'FixedIndentXLSAnalyzer'
    ]
else:
    __all__ = ['FixedIndentXLSAnalyzer'] if LEGACY_AVAILABLE else []
