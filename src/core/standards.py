#!/usr/bin/env python3
"""
ISO 14577-4:2016 Constants and Configuration
Nanoindentation Analysis - Material Properties and Standards
"""

import math

# ISO 14577-4:2016 Compliance Constants
class ISO14577Constants:
    """ISO 14577-4:2016 standard constants and requirements"""
    
    # Data Quality Requirements
    MIN_DATA_POINTS_LOADING = 50      # Minimum data points for loading curve
    MIN_DATA_POINTS_UNLOADING = 30    # Minimum data points for unloading curve
    MIN_R_SQUARED = 0.98              # Minimum R² for curve fits (ISO requirement)
    
    # Analysis Parameters - Based on NIST Guide recommendations
    STIFFNESS_RANGE_PERCENT = 0.25    # Use upper 25% of unloading for stiffness
    
    # NIST Guide Section 2.3: Power law exponents for different tip geometries
    POWER_LAW_EXPONENT_FLAT_PUNCH = 1.0        # m = 1 for flat-ended cylindrical punch
    POWER_LAW_EXPONENT_PARABOLOID = 1.5        # m = 1.5 for paraboloid of revolution  
    POWER_LAW_EXPONENT_CONE = 2.0              # m = 2 for cone (Berkovich/Vickers)
    
    # Geometric Constants for Different Indenters (NIST Guide Table 1)
    EPSILON_FLAT_PUNCH = 1.0          # ε = 1 for flat-ended cylindrical punch
    EPSILON_PARABOLOID = 0.75         # ε = 0.75 for paraboloid of revolution
    EPSILON_CONE = 2 * (math.pi - 2) / math.pi  # ε = 2(π-2)/π ≈ 0.727 for cone
    EPSILON_BERKOVICH = 0.75          # Commonly used value for Berkovich indenter
    EPSILON_VICKERS = 0.75            # Commonly used value for Vickers indenter  
    EPSILON_SPHERICAL = 0.75          # Commonly used value for spherical indenter
    
    # Reference Material Properties (Fused Silica)
    FUSED_SILICA_MODULUS = 72e9       # Reference material modulus (Pa)
    FUSED_SILICA_POISSON = 0.17       # Reference material Poisson ratio
    FUSED_SILICA_HARDNESS = 9.0       # Reference hardness (GPa)
    
    # Diamond Indenter Properties
    DIAMOND_MODULUS = 1140e9          # Diamond indenter modulus (Pa)
    DIAMOND_POISSON = 0.07            # Diamond indenter Poisson ratio
    
    # Perfect Berkovich Area Function Coefficients
    PERFECT_BERKOVICH_C0 = 24.56      # h_c^2 term for perfect Berkovich
    BERKOVICH_AREA_CONSTANT = 24.56   # Alias for compatibility
    
    @classmethod
    def get_tip_geometry_config(cls, tip_geometry: str) -> dict:
        """Get tip geometry configuration parameters"""
        tip_configs = {
            'berkovich': {
                'epsilon': cls.EPSILON_BERKOVICH,
                'power_law_exponent': cls.POWER_LAW_EXPONENT_CONE,
                'area_constant': cls.BERKOVICH_AREA_CONSTANT
            },
            'vickers': {
                'epsilon': cls.EPSILON_VICKERS,
                'power_law_exponent': cls.POWER_LAW_EXPONENT_CONE,
                'area_constant': 24.5
            },
            'cube_corner': {
                'epsilon': cls.EPSILON_BERKOVICH,
                'power_law_exponent': cls.POWER_LAW_EXPONENT_CONE,
                'area_constant': 2.598
            },
            'conical': {
                'epsilon': cls.EPSILON_CONE,
                'power_law_exponent': cls.POWER_LAW_EXPONENT_CONE,
                'area_constant': None  # Variable based on cone angle
            },
            'spherical': {
                'epsilon': cls.EPSILON_SPHERICAL,
                'power_law_exponent': cls.POWER_LAW_EXPONENT_PARABOLOID,
                'area_constant': None  # Variable based on radius
            }
        }
        return tip_configs.get(tip_geometry.lower(), tip_configs['berkovich'])
    
    @classmethod
    def get_reference_material(cls, material_name: str) -> dict:
        """Get reference material properties"""
        materials = {
            'fused_silica': {
                'modulus': cls.FUSED_SILICA_MODULUS,
                'poisson': cls.FUSED_SILICA_POISSON,
                'hardness': cls.FUSED_SILICA_HARDNESS * 1e9,  # Convert to Pa
                'name': 'Fused Silica'
            },
            'diamond': {
                'modulus': cls.DIAMOND_MODULUS,
                'poisson': cls.DIAMOND_POISSON,
                'name': 'Diamond'
            }
        }
        return materials.get(material_name.lower(), materials['fused_silica'])


class AnalysisConfig:
    """Configuration settings for nanoindentation analysis"""
    
    # Data Processing Settings
    LOAD_THRESHOLD_FACTOR = 0.1       # Fraction of max load for filtering
    MIN_LOAD_THRESHOLD = 40           # Minimum load threshold (mN)
    NOISE_THRESHOLD = 0.15            # Maximum relative noise level
    
    # Horizontal Segment Detection
    MIN_SEGMENT_LENGTH = 5            # Minimum points in horizontal segment
    MIN_DISPLACEMENT_SPAN = 10.0      # Minimum displacement span (nm)
    RELATIVE_THRESHOLD = 0.02         # 2% relative change threshold
    
    # Curve Fitting Settings (Enhanced per NIST Guide Section 2.3)
    UNLOADING_FIT_RANGE = 0.75        # Use upper 75% of unloading curve
    MIN_UNLOADING_POINTS = 10         # Minimum points for unloading fit
    RESIDUAL_THRESHOLD = 0.05         # Maximum residual for fit acceptance
    
    # NIST Guide Section 2.4: Calibration Requirements
    REFERENCE_MATERIAL_MODULUS_TOLERANCE = 0.05  # 5% tolerance on reference modulus
    MIN_INDENTS_FOR_CALIBRATION = 5   # Minimum indents for calibration
    LOAD_FRAME_COMPLIANCE_TOLERANCE = 0.1  # 10% tolerance on compliance
    MAX_FITTING_ITERATIONS = 10000    # Maximum curve fitting iterations
    CONVERGENCE_TOLERANCE = 1e-8      # Fitting convergence tolerance
    
    # Quality Control
    MAX_ADJUSTMENT_FACTOR = 0.2       # Max 20% of total displacement range
    MONOTONIC_VIOLATION_LIMIT = 0.1   # Allow up to 10% monotonic violations


class MaterialProperties:
    """Common material properties for nanoindentation analysis"""
    
    MATERIALS = {
        'fused_silica': {
            'modulus': 72e9,      # Pa
            'poisson': 0.17,
            'hardness': 9.0,      # GPa
            'name': 'Fused Silica'
        },
        'diamond': {
            'modulus': 1140e9,    # Pa  
            'poisson': 0.07,
            'name': 'Diamond'
        },
        'aluminum': {
            'modulus': 70e9,      # Pa
            'poisson': 0.33,
            'hardness': 0.2,      # GPa (approximate)
            'name': 'Aluminum'
        },
        'steel': {
            'modulus': 210e9,     # Pa
            'poisson': 0.30,
            'hardness': 2.0,      # GPa (approximate)
            'name': 'Steel'
        }
    }
    
    @classmethod
    def get_material(cls, material_name):
        """Get material properties by name"""
        return cls.MATERIALS.get(material_name.lower(), None)
    
    @classmethod
    def list_materials(cls):
        """List all available materials"""
        return list(cls.MATERIALS.keys())


class AreaFunctionCoefficients:
    """Default area function coefficients for different indenter conditions"""
    
    PERFECT_BERKOVICH = {
        'C0': 24.56,    # Perfect Berkovich coefficient (h_c^2 term)
        'C1': 0.0,      # Linear term (h_c^1)
        'C2': 0.0,      # h_c^{1/2} term
        'C3': 0.0,      # h_c^{1/4} term
        'C4': 0.0,      # h_c^{1/8} term
        'C5': 0.0,      # h_c^{1/16} term
        'C6': 0.0,      # h_c^{1/32} term
        'C7': 0.0,      # h_c^{1/64} term
        'C8': 0.0       # h_c^{1/128} term
    }
    
    BLUNT_BERKOVICH = {
        'C0': 26.43,    # Slightly blunt tip
        'C1': 5.32,     # Linear correction
        'C2': 50.0,     # Tip rounding
        'C3': 10.0,     # Tip blunting
        'C4': 2.0,      # Higher-order effects
        'C5': 0.0,      # Not typically calibrated
        'C6': 0.0,
        'C7': 0.0,
        'C8': 0.0
    }


class ValidationLimits:
    """Validation limits for data quality assessment"""
    
    # R-squared limits
    EXCELLENT_R2 = 0.99
    GOOD_R2 = 0.98
    ACCEPTABLE_R2 = 0.95
    
    # Noise level limits  
    LOW_NOISE = 0.05
    MODERATE_NOISE = 0.15
    HIGH_NOISE = 0.30
    
    # Data completeness
    MIN_LOADING_POINTS = 50
    MIN_UNLOADING_POINTS = 30
    RECOMMENDED_LOADING_POINTS = 200
    RECOMMENDED_UNLOADING_POINTS = 100
    
    # Physical reasonableness
    MIN_HARDNESS = 0.1      # GPa
    MAX_HARDNESS = 100.0    # GPa
    MIN_MODULUS = 1e9       # Pa
    MAX_MODULUS = 1000e9    # Pa
