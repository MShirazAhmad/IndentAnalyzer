#!/usr/bin/env python3
"""
Unified Validation Module
Consolidates all validation functionality from:
- validate_tip_calibration.py
- validate_tip_calibration_fixed.py  
- validate_comprehensive.py
- real_silica_validation.py
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import warnings

# Import core components
try:
    from src.core.standards import ISO14577Constants
    from src.analysis.legacy_analyzer import IndentXLSAnalyzer
    from src.calibration.nist_methods import NISTCalibrationMethods
except ImportError:
    # Fallback imports
    pass


class UnifiedValidationSuite:
    """
    Comprehensive validation suite that consolidates all validation methods
    """
    
    def __init__(self):
        self.iso = ISO14577Constants()
        self.nist_cal = NISTCalibrationMethods()
        
    def validate_tip_calibration_comprehensive(self, 
                                             xls_file: str,
                                             reference_material: str = 'fused_silica',
                                             generate_plots: bool = True,
                                             output_dir: str = '.') -> Dict[str, any]:
        """
        Comprehensive tip calibration validation combining all methods
        
        Args:
            xls_file: Path to Excel file with experimental data
            reference_material: Reference material used for calibration
            generate_plots: Whether to generate validation plots
            output_dir: Directory for saving plots and reports
        
        Returns:
            Complete validation report
        """
        validation_report = {
            'validation_timestamp': pd.Timestamp.now().isoformat(),
            'input_file': xls_file,
            'reference_material': reference_material,
            'data_extraction': {},
            'calibration_extraction': {},
            'theoretical_analysis': {},
            'experimental_comparison': {},
            'quality_assessment': {},
            'recommendations': [],
            'plots_generated': [],
            'overall_validity': False
        }
        
        print("🔍 COMPREHENSIVE TIP CALIBRATION VALIDATION")
        print("=" * 60)
        print(f"📁 Input file: {xls_file}")
        print(f"🎯 Reference material: {reference_material}")
        print("=" * 60)
        
        try:
            # Step 1: Extract experimental data (multiple methods)
            print("\n📊 Step 1: Extracting Experimental Data")
            experimental_data = self._extract_experimental_data_unified(xls_file)
            validation_report['data_extraction'] = experimental_data
            
            if not experimental_data['success']:
                validation_report['recommendations'].append("Could not extract experimental data")
                return validation_report
            
            # Step 2: Extract calibrated tip coefficients
            print("\n🔧 Step 2: Extracting Calibrated Tip Coefficients")
            calibration_data = self._extract_tip_coefficients_unified(xls_file, reference_material)
            validation_report['calibration_extraction'] = calibration_data
            
            if not calibration_data['success']:
                validation_report['recommendations'].append("Could not extract calibration coefficients")
                return validation_report
            
            # Step 3: Theoretical analysis
            print("\n🧮 Step 3: Theoretical Analysis")
            theoretical_analysis = self._perform_theoretical_analysis(
                experimental_data['data_points'],
                calibration_data['coefficients']
            )
            validation_report['theoretical_analysis'] = theoretical_analysis
            
            # Step 4: Experimental vs theoretical comparison
            print("\n⚖️ Step 4: Experimental vs Theoretical Comparison")
            comparison_analysis = self._compare_experimental_theoretical(
                experimental_data['data_points'],
                theoretical_analysis['theoretical_areas'],
                calibration_data['coefficients']
            )
            validation_report['experimental_comparison'] = comparison_analysis
            
            # Step 5: Quality assessment
            print("\n📈 Step 5: Quality Assessment")
            quality_assessment = self._assess_calibration_quality(
                experimental_data['data_points'],
                theoretical_analysis,
                comparison_analysis
            )
            validation_report['quality_assessment'] = quality_assessment
            
            # Step 6: Generate plots if requested
            if generate_plots:
                print("\n📊 Step 6: Generating Validation Plots")
                plots_generated = self._generate_validation_plots(
                    experimental_data['data_points'],
                    theoretical_analysis,
                    comparison_analysis,
                    calibration_data['coefficients'],
                    output_dir
                )
                validation_report['plots_generated'] = plots_generated
            
            # Step 7: Generate recommendations
            validation_report['recommendations'] = self._generate_recommendations(
                quality_assessment,
                comparison_analysis
            )
            
            # Overall validity assessment
            validation_report['overall_validity'] = self._assess_overall_validity(
                quality_assessment,
                comparison_analysis
            )
            
            print(f"\n🎉 VALIDATION COMPLETE")
            print(f"✅ Overall validity: {'PASS' if validation_report['overall_validity'] else 'NEEDS REVIEW'}")
            
        except Exception as e:
            validation_report['error'] = f"Validation failed: {str(e)}"
            print(f"❌ Validation failed: {e}")
        
        return validation_report
    
    def _extract_experimental_data_unified(self, xls_file: str) -> Dict[str, any]:
        """
        Unified experimental data extraction combining multiple approaches
        """
        result = {
            'success': False,
            'method_used': None,
            'data_points': [],
            'data_summary': {},
            'errors': []
        }
        
        # Try multiple extraction methods
        extraction_methods = [
            ('direct_excel', self._extract_data_direct_excel),
            ('analyzer_legacy', self._extract_data_analyzer_legacy),
            ('analyzer_enhanced', self._extract_data_analyzer_enhanced)
        ]
        
        for method_name, method_func in extraction_methods:
            try:
                print(f"   Trying method: {method_name}")
                data_points = method_func(xls_file)
                
                if data_points and len(data_points) > 0:
                    result['success'] = True
                    result['method_used'] = method_name
                    result['data_points'] = data_points
                    result['data_summary'] = self._summarize_data_points(data_points)
                    print(f"   ✅ Success with {method_name}: {len(data_points)} data points")
                    break
                else:
                    print(f"   ❌ {method_name} returned no data")
                    
            except Exception as e:
                print(f"   ❌ {method_name} failed: {e}")
                result['errors'].append(f"{method_name}: {str(e)}")
                continue
        
        return result
    
    def _extract_data_direct_excel(self, xls_file: str) -> List[Dict]:
        """Extract data directly from Excel file"""
        df_results = pd.read_excel(xls_file, sheet_name="Results")
        data_points = []
        
        for test_num in range(1, 21):
            test_row = df_results[df_results['Test'] == test_num]
            
            if not test_row.empty:
                row = test_row.iloc[0]
                
                contact_depth = row.get('Hc (nm)', 0)
                contact_area = row.get('Ac (nm²)', 0)
                hardness = row.get('H Average Over Defined Range', 0)
                modulus = row.get('E Average Over Defined Range', 0)
                
                # Convert units if necessary
                if hardness > 1e6:  # Likely in Pa, convert to GPa
                    hardness = hardness / 1e9
                if modulus > 1e6:  # Likely in Pa, convert to GPa
                    modulus = modulus / 1e9
                
                if contact_depth > 0 and contact_area > 0:
                    data_points.append({
                        'test_name': f'Test {test_num:03d}',
                        'test_number': test_num,
                        'contact_depth_nm': contact_depth,
                        'contact_area_nm2': contact_area,
                        'hardness_GPa': hardness,
                        'elastic_modulus_GPa': modulus,
                        'extraction_method': 'direct_excel'
                    })
        
        return data_points
    
    def _extract_data_analyzer_legacy(self, xls_file: str) -> List[Dict]:
        """Extract data using legacy analyzer"""
        analyzer = IndentXLSAnalyzer()
        results = analyzer.analyze_file(xls_file)
        
        data_points = []
        if results.get('valid', False):
            for test_name, test_data in results['tests'].items():
                if test_name.startswith('Test '):
                    contact_depth = test_data.get('contact_depth_nm', 0)
                    contact_area = test_data.get('contact_area_nm2', 0)
                    hardness = test_data.get('hardness_GPa', 0)
                    modulus = test_data.get('elastic_modulus_GPa', 0)
                    
                    if contact_depth > 0 and contact_area > 0:
                        data_points.append({
                            'test_name': test_name,
                            'test_number': int(test_name.split()[-1]) if test_name.split()[-1].isdigit() else 0,
                            'contact_depth_nm': contact_depth,
                            'contact_area_nm2': contact_area,
                            'hardness_GPa': hardness,
                            'elastic_modulus_GPa': modulus,
                            'extraction_method': 'analyzer_legacy'
                        })
        
        return data_points
    
    def _extract_data_analyzer_enhanced(self, xls_file: str) -> List[Dict]:
        """Extract data using enhanced analyzer"""
        try:
            from src.analysis.enhanced_analyzer import FixedIndentXLSAnalyzer
            analyzer = FixedIndentXLSAnalyzer(filename=xls_file)
            results = analyzer.analyze_file()
            
            data_points = []
            # Process results and extract data points
            # This would need to be implemented based on the enhanced analyzer structure
            
            return data_points
        except ImportError:
            return []
    
    def _extract_tip_coefficients_unified(self, xls_file: str, 
                                        reference_material: str) -> Dict[str, any]:
        """
        Unified tip coefficient extraction
        """
        result = {
            'success': False,
            'coefficients': {},
            'calibration_quality': {},
            'method_used': None,
            'errors': []
        }
        
        try:
            # Extract coefficients using NIST calibration methods
            results = self.nist_cal.extract_tip_coefficients_from_file(
                xls_file_path=xls_file,
                reference_material=reference_material
            )
            
            if results.get('valid', False):
                result['success'] = True
                result['coefficients'] = results['coefficients']
                result['calibration_quality'] = results.get('quality_metrics', {})
                result['method_used'] = 'nist_calibration'
                
                print(f"   ✅ Calibrated coefficients extracted:")
                coeffs = result['coefficients']
                print(f"      C₀ = {coeffs.get('C0_nm2_per_nm2', 0):.6f} nm²/nm²")
                print(f"      C₁ = {coeffs.get('C1_nm2_per_nm', 0):.6f} nm²/nm")
                print(f"      C₂ = {coeffs.get('C2_nm2_per_nm05', 0):.6f} nm²/nm^0.5")
                
            else:
                result['errors'].append("NIST calibration method failed")
                
        except Exception as e:
            result['errors'].append(f"Coefficient extraction failed: {str(e)}")
        
        return result
    
    def _perform_theoretical_analysis(self, data_points: List[Dict], 
                                    coefficients: Dict) -> Dict[str, any]:
        """
        Perform theoretical analysis using calibrated tip function
        """
        analysis = {
            'theoretical_areas': [],
            'area_function_evaluation': {},
            'depth_range_analysis': {},
            'coefficient_validation': {}
        }
        
        # Extract contact depths
        contact_depths = [dp['contact_depth_nm'] for dp in data_points]
        
        # Calculate theoretical areas using tip function
        theoretical_areas = self._calculate_theoretical_areas(contact_depths, coefficients)
        analysis['theoretical_areas'] = theoretical_areas.tolist()
        
        # Evaluate area function performance
        analysis['area_function_evaluation'] = self._evaluate_area_function(
            contact_depths, theoretical_areas, coefficients
        )
        
        # Analyze depth range
        analysis['depth_range_analysis'] = {
            'min_depth': min(contact_depths),
            'max_depth': max(contact_depths),
            'depth_range': max(contact_depths) - min(contact_depths),
            'depth_distribution': self._analyze_depth_distribution(contact_depths)
        }
        
        # Validate coefficients
        analysis['coefficient_validation'] = self._validate_coefficients(coefficients)
        
        print(f"   ✅ Theoretical analysis complete")
        print(f"      Depth range: {analysis['depth_range_analysis']['min_depth']:.1f} - {analysis['depth_range_analysis']['max_depth']:.1f} nm")
        print(f"      Area range: {min(theoretical_areas):.1f} - {max(theoretical_areas):.1f} nm²")
        
        return analysis
    
    def _calculate_theoretical_areas(self, contact_depths: List[float], 
                                   coefficients: Dict) -> np.ndarray:
        """
        Calculate theoretical areas using calibrated tip function
        A(h_c) = C₀·h_c² + C₁·h_c + C₂·h_c^0.5 + C₃·h_c^0.25 + ...
        """
        C0 = coefficients.get('C0_nm2_per_nm2', 0)
        C1 = coefficients.get('C1_nm2_per_nm', 0)
        C2 = coefficients.get('C2_nm2_per_nm05', 0)
        C3 = coefficients.get('C3_nm2_per_nm025', 0)  # Optional higher-order terms
        
        contact_depths = np.array(contact_depths)
        
        # Standard area function (first 3 terms)
        theoretical_areas = (C0 * contact_depths**2 + 
                           C1 * contact_depths + 
                           C2 * contact_depths**0.5)
        
        # Add higher-order terms if available
        if C3 != 0:
            theoretical_areas += C3 * contact_depths**0.25
        
        return theoretical_areas
    
    def _compare_experimental_theoretical(self, data_points: List[Dict],
                                        theoretical_areas: List[float],
                                        coefficients: Dict) -> Dict[str, any]:
        """
        Compare experimental and theoretical data
        """
        comparison = {
            'area_comparison': {},
            'residual_analysis': {},
            'statistical_analysis': {},
            'correlation_analysis': {},
            'goodness_of_fit': {}
        }
        
        # Extract experimental areas
        experimental_areas = [dp['contact_area_nm2'] for dp in data_points]
        experimental_areas = np.array(experimental_areas)
        theoretical_areas = np.array(theoretical_areas)
        
        # Area comparison
        area_differences = experimental_areas - theoretical_areas
        area_percent_differences = (area_differences / experimental_areas) * 100
        
        comparison['area_comparison'] = {
            'experimental_areas': experimental_areas.tolist(),
            'theoretical_areas': theoretical_areas.tolist(),
            'absolute_differences': area_differences.tolist(),
            'percent_differences': area_percent_differences.tolist(),
            'mean_percent_difference': np.mean(np.abs(area_percent_differences)),
            'max_percent_difference': np.max(np.abs(area_percent_differences))
        }
        
        # Residual analysis
        comparison['residual_analysis'] = self._analyze_residuals(
            area_differences, experimental_areas
        )
        
        # Statistical analysis
        comparison['statistical_analysis'] = {
            'correlation_coefficient': np.corrcoef(experimental_areas, theoretical_areas)[0, 1],
            'rmse': np.sqrt(np.mean(area_differences**2)),
            'mae': np.mean(np.abs(area_differences)),
            'bias': np.mean(area_differences),
            'std_deviation': np.std(area_differences)
        }
        
        # R-squared calculation
        ss_res = np.sum(area_differences**2)
        ss_tot = np.sum((experimental_areas - np.mean(experimental_areas))**2)
        r_squared = 1 - (ss_res / ss_tot)
        
        comparison['goodness_of_fit'] = {
            'r_squared': r_squared,
            'adjusted_r_squared': 1 - (1 - r_squared) * (len(experimental_areas) - 1) / (len(experimental_areas) - 3 - 1),
            'fit_quality': self._interpret_r_squared(r_squared)
        }
        
        print(f"   ✅ Experimental vs theoretical comparison complete")
        print(f"      R² = {r_squared:.4f} ({comparison['goodness_of_fit']['fit_quality']})")
        print(f"      Mean percent difference: {comparison['area_comparison']['mean_percent_difference']:.2f}%")
        
        return comparison
    
    def _analyze_residuals(self, residuals: np.ndarray, 
                          experimental_areas: np.ndarray) -> Dict[str, any]:
        """
        Analyze residuals for patterns and meaning
        """
        analysis = {
            'residual_statistics': {
                'mean': np.mean(residuals),
                'std': np.std(residuals),
                'min': np.min(residuals),
                'max': np.max(residuals),
                'range': np.max(residuals) - np.min(residuals)
            },
            'normality_test': {},
            'pattern_analysis': {},
            'outlier_detection': {}
        }
        
        # Pattern analysis
        normalized_residuals = residuals / np.std(residuals)
        
        # Check for systematic bias
        if abs(np.mean(normalized_residuals)) > 0.5:
            analysis['pattern_analysis']['systematic_bias'] = "Detected"
        else:
            analysis['pattern_analysis']['systematic_bias'] = "None"
        
        # Check for heteroscedasticity (changing variance)
        first_half = normalized_residuals[:len(normalized_residuals)//2]
        second_half = normalized_residuals[len(normalized_residuals)//2:]
        
        variance_ratio = np.var(second_half) / np.var(first_half)
        if variance_ratio > 2 or variance_ratio < 0.5:
            analysis['pattern_analysis']['heteroscedasticity'] = "Detected"
        else:
            analysis['pattern_analysis']['heteroscedasticity'] = "None"
        
        # Outlier detection using IQR method
        Q1 = np.percentile(normalized_residuals, 25)
        Q3 = np.percentile(normalized_residuals, 75)
        IQR = Q3 - Q1
        outlier_threshold = 1.5 * IQR
        
        outliers = np.where((normalized_residuals < Q1 - outlier_threshold) | 
                           (normalized_residuals > Q3 + outlier_threshold))[0]
        
        analysis['outlier_detection'] = {
            'outlier_indices': outliers.tolist(),
            'outlier_count': len(outliers),
            'outlier_percentage': (len(outliers) / len(residuals)) * 100
        }
        
        return analysis
    
    def _assess_calibration_quality(self, data_points: List[Dict],
                                  theoretical_analysis: Dict,
                                  comparison_analysis: Dict) -> Dict[str, any]:
        """
        Assess overall calibration quality
        """
        assessment = {
            'overall_grade': 'unknown',
            'data_quality_grade': 'unknown',
            'fitting_grade': 'unknown',
            'consistency_grade': 'unknown',
            'iso_compliance': False,
            'quality_scores': {},
            'detailed_metrics': {}
        }
        
        # Data quality assessment
        n_points = len(data_points)
        if n_points >= 15:
            assessment['data_quality_grade'] = 'excellent'
        elif n_points >= 10:
            assessment['data_quality_grade'] = 'good'
        elif n_points >= 5:
            assessment['data_quality_grade'] = 'acceptable'
        else:
            assessment['data_quality_grade'] = 'poor'
        
        # Fitting quality assessment
        r_squared = comparison_analysis['goodness_of_fit']['r_squared']
        if r_squared >= 0.99:
            assessment['fitting_grade'] = 'excellent'
        elif r_squared >= 0.95:
            assessment['fitting_grade'] = 'good'
        elif r_squared >= 0.90:
            assessment['fitting_grade'] = 'acceptable'
        else:
            assessment['fitting_grade'] = 'poor'
        
        # Consistency assessment
        mean_percent_diff = comparison_analysis['area_comparison']['mean_percent_difference']
        if mean_percent_diff <= 2:
            assessment['consistency_grade'] = 'excellent'
        elif mean_percent_diff <= 5:
            assessment['consistency_grade'] = 'good'
        elif mean_percent_diff <= 10:
            assessment['consistency_grade'] = 'acceptable'
        else:
            assessment['consistency_grade'] = 'poor'
        
        # ISO compliance
        assessment['iso_compliance'] = r_squared >= self.iso.MIN_R_SQUARED
        
        # Overall grade (worst of individual grades)
        grades = ['excellent', 'good', 'acceptable', 'poor', 'unknown']
        individual_grades = [
            assessment['data_quality_grade'],
            assessment['fitting_grade'],
            assessment['consistency_grade']
        ]
        
        worst_grade_idx = len(grades) - 1
        for grade in individual_grades:
            if grade in grades:
                worst_grade_idx = min(worst_grade_idx, grades.index(grade))
        
        assessment['overall_grade'] = grades[worst_grade_idx]
        
        # Quality scores (0-100 scale)
        assessment['quality_scores'] = {
            'data_quality_score': min(100, (n_points / 20) * 100),
            'fitting_score': r_squared * 100,
            'consistency_score': max(0, 100 - mean_percent_diff * 2),
            'overall_score': np.mean([
                min(100, (n_points / 20) * 100),
                r_squared * 100,
                max(0, 100 - mean_percent_diff * 2)
            ])
        }
        
        print(f"   ✅ Quality assessment complete")
        print(f"      Overall grade: {assessment['overall_grade']}")
        print(f"      Overall score: {assessment['quality_scores']['overall_score']:.1f}/100")
        print(f"      ISO compliance: {'✅ PASS' if assessment['iso_compliance'] else '❌ FAIL'}")
        
        return assessment
    
    def _generate_validation_plots(self, data_points: List[Dict],
                                 theoretical_analysis: Dict,
                                 comparison_analysis: Dict,
                                 coefficients: Dict,
                                 output_dir: str) -> List[str]:
        """
        Generate comprehensive validation plots
        """
        plots_generated = []
        output_path = Path(output_dir)
        
        try:
            # Plot 1: Experimental vs Theoretical Areas
            plt.figure(figsize=(10, 8))
            
            experimental_areas = comparison_analysis['area_comparison']['experimental_areas']
            theoretical_areas = comparison_analysis['area_comparison']['theoretical_areas']
            
            plt.scatter(experimental_areas, theoretical_areas, alpha=0.7, s=50)
            
            # Perfect correlation line
            min_area = min(min(experimental_areas), min(theoretical_areas))
            max_area = max(max(experimental_areas), max(theoretical_areas))
            plt.plot([min_area, max_area], [min_area, max_area], 'r--', 
                    label='Perfect Correlation', linewidth=2)
            
            # R² annotation
            r_squared = comparison_analysis['goodness_of_fit']['r_squared']
            plt.text(0.05, 0.95, f'R² = {r_squared:.4f}', 
                    transform=plt.gca().transAxes, fontsize=12, 
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            plt.xlabel('Experimental Contact Area (nm²)', fontsize=12)
            plt.ylabel('Theoretical Contact Area (nm²)', fontsize=12)
            plt.title('Tip Calibration Validation: Experimental vs Theoretical Areas', fontsize=14)
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            plot_path = output_path / 'tip_calibration_validation.png'
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            plots_generated.append(str(plot_path))
            
            # Plot 2: Residual Analysis
            plt.figure(figsize=(12, 5))
            
            residuals = comparison_analysis['area_comparison']['absolute_differences']
            contact_depths = [dp['contact_depth_nm'] for dp in data_points]
            
            # Residuals vs contact depth
            plt.subplot(1, 2, 1)
            plt.scatter(contact_depths, residuals, alpha=0.7)
            plt.axhline(y=0, color='r', linestyle='--', alpha=0.7)
            plt.xlabel('Contact Depth (nm)')
            plt.ylabel('Residuals (nm²)')
            plt.title('Residuals vs Contact Depth')
            plt.grid(True, alpha=0.3)
            
            # Residual histogram
            plt.subplot(1, 2, 2)
            plt.hist(residuals, bins=10, alpha=0.7, edgecolor='black')
            plt.xlabel('Residuals (nm²)')
            plt.ylabel('Frequency')
            plt.title('Residual Distribution')
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plot_path = output_path / 'residual_analysis.png'
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            plots_generated.append(str(plot_path))
            
            print(f"   ✅ Generated {len(plots_generated)} validation plots")
            
        except Exception as e:
            print(f"   ❌ Plot generation failed: {e}")
        
        return plots_generated
    
    def _generate_recommendations(self, quality_assessment: Dict,
                                comparison_analysis: Dict) -> List[str]:
        """
        Generate actionable recommendations based on validation results
        """
        recommendations = []
        
        # Based on overall grade
        overall_grade = quality_assessment['overall_grade']
        if overall_grade == 'poor':
            recommendations.append("⚠️ Calibration quality is poor - consider recalibrating with more reference measurements")
        elif overall_grade == 'acceptable':
            recommendations.append("🔄 Calibration is acceptable but could be improved")
        elif overall_grade in ['good', 'excellent']:
            recommendations.append("✅ Calibration quality is good - ready for production use")
        
        # Based on ISO compliance
        if not quality_assessment['iso_compliance']:
            recommendations.append("📋 Analysis does not meet ISO 14577-4:2016 standards - improve curve fitting")
        
        # Based on fitting quality
        r_squared = comparison_analysis['goodness_of_fit']['r_squared']
        if r_squared < 0.95:
            recommendations.append("📊 Low R² indicates poor tip function fit - check reference material properties")
        
        # Based on consistency
        mean_percent_diff = comparison_analysis['area_comparison']['mean_percent_difference']
        if mean_percent_diff > 5:
            recommendations.append("🎯 High variability detected - check measurement consistency and instrument stability")
        
        # Based on data quantity
        if quality_assessment['quality_scores']['data_quality_score'] < 75:
            recommendations.append("📈 Consider using more reference measurements for better calibration reliability")
        
        # Based on residual analysis
        if 'outlier_detection' in comparison_analysis.get('residual_analysis', {}):
            outlier_percentage = comparison_analysis['residual_analysis']['outlier_detection']['outlier_percentage']
            if outlier_percentage > 10:
                recommendations.append("🎯 High number of outliers detected - review measurement protocol")
        
        return recommendations
    
    def _assess_overall_validity(self, quality_assessment: Dict,
                               comparison_analysis: Dict) -> bool:
        """
        Assess overall validity of the calibration
        """
        # Multiple criteria for validity
        criteria = [
            quality_assessment['overall_grade'] in ['good', 'excellent'],
            quality_assessment['iso_compliance'],
            comparison_analysis['goodness_of_fit']['r_squared'] >= 0.90,
            comparison_analysis['area_comparison']['mean_percent_difference'] <= 10
        ]
        
        # Must meet at least 3 out of 4 criteria
        return sum(criteria) >= 3
    
    # Helper methods
    def _summarize_data_points(self, data_points: List[Dict]) -> Dict[str, any]:
        """Summarize extracted data points"""
        if not data_points:
            return {}
        
        contact_depths = [dp['contact_depth_nm'] for dp in data_points]
        contact_areas = [dp['contact_area_nm2'] for dp in data_points]
        
        return {
            'count': len(data_points),
            'depth_range': f"{min(contact_depths):.1f} - {max(contact_depths):.1f} nm",
            'area_range': f"{min(contact_areas):.1f} - {max(contact_areas):.1f} nm²",
            'depth_mean': np.mean(contact_depths),
            'area_mean': np.mean(contact_areas)
        }
    
    def _evaluate_area_function(self, contact_depths: List[float],
                               theoretical_areas: np.ndarray,
                               coefficients: Dict) -> Dict[str, any]:
        """Evaluate area function performance"""
        return {
            'coefficient_magnitude': {
                'C0': coefficients.get('C0_nm2_per_nm2', 0),
                'C1': coefficients.get('C1_nm2_per_nm', 0),
                'C2': coefficients.get('C2_nm2_per_nm05', 0)
            },
            'function_behavior': 'monotonic_increasing' if np.all(np.diff(theoretical_areas) > 0) else 'non_monotonic',
            'sensitivity_analysis': self._analyze_coefficient_sensitivity(contact_depths, coefficients)
        }
    
    def _analyze_depth_distribution(self, contact_depths: List[float]) -> Dict[str, any]:
        """Analyze distribution of contact depths"""
        depths = np.array(contact_depths)
        return {
            'mean': np.mean(depths),
            'std': np.std(depths),
            'cv_percent': (np.std(depths) / np.mean(depths)) * 100,
            'uniformity': 'uniform' if np.std(depths) / np.mean(depths) < 0.2 else 'non_uniform'
        }
    
    def _validate_coefficients(self, coefficients: Dict) -> Dict[str, any]:
        """Validate coefficient values"""
        validation = {
            'physically_reasonable': True,
            'warnings': []
        }
        
        C0 = coefficients.get('C0_nm2_per_nm2', 0)
        C1 = coefficients.get('C1_nm2_per_nm', 0)
        C2 = coefficients.get('C2_nm2_per_nm05', 0)
        
        # Check for reasonable values
        if C0 <= 0:
            validation['physically_reasonable'] = False
            validation['warnings'].append("C0 should be positive (represents ideal Berkovich geometry)")
        
        if abs(C1) > abs(C0) * 1000:  # C1 shouldn't dominate
            validation['warnings'].append("C1 coefficient is unusually large")
        
        if abs(C2) > abs(C0) * 10000:  # C2 shouldn't dominate
            validation['warnings'].append("C2 coefficient is unusually large")
        
        return validation
    
    def _analyze_coefficient_sensitivity(self, contact_depths: List[float],
                                       coefficients: Dict) -> Dict[str, any]:
        """Analyze sensitivity to coefficient changes"""
        # This is a simplified sensitivity analysis
        depths = np.array(contact_depths)
        base_areas = self._calculate_theoretical_areas(depths, coefficients)
        
        # 1% change in each coefficient
        sensitivity = {}
        for coeff_name in ['C0_nm2_per_nm2', 'C1_nm2_per_nm', 'C2_nm2_per_nm05']:
            if coeff_name in coefficients:
                modified_coeffs = coefficients.copy()
                modified_coeffs[coeff_name] *= 1.01  # 1% increase
                modified_areas = self._calculate_theoretical_areas(depths, modified_coeffs)
                
                percent_change = np.mean((modified_areas - base_areas) / base_areas) * 100
                sensitivity[coeff_name] = percent_change
        
        return sensitivity
    
    def _interpret_r_squared(self, r_squared: float) -> str:
        """Interpret R-squared value"""
        if r_squared >= 0.99:
            return "Excellent fit"
        elif r_squared >= 0.95:
            return "Good fit"
        elif r_squared >= 0.90:
            return "Acceptable fit"
        else:
            return "Poor fit"


# Convenience functions for backward compatibility
def validate_tip_calibration(xls_file: str, **kwargs) -> Dict[str, any]:
    """Backward compatible validation function"""
    validator = UnifiedValidationSuite()
    return validator.validate_tip_calibration_comprehensive(xls_file, **kwargs)

def calculate_theoretical_areas(contact_depths: List[float], coefficients: Dict) -> np.ndarray:
    """Backward compatible area calculation function"""
    validator = UnifiedValidationSuite()
    return validator._calculate_theoretical_areas(contact_depths, coefficients)

def analyze_residuals_meaning(residuals: np.ndarray, areas: np.ndarray) -> Dict[str, any]:
    """Backward compatible residual analysis function"""
    validator = UnifiedValidationSuite()
    return validator._analyze_residuals(residuals, areas)
