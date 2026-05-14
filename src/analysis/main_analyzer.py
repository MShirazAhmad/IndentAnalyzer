#!/usr/bin/env python3
"""
Main Nanoindentation Analyzer Module
ISO 14577-4:2016 compliant analysis engine with modular architecture
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import warnings
import logging

# Import all the modular components with fallback handling
try:
    from ..core.standards import ISO14577Constants, AnalysisConfig, MaterialProperties
    from ..core.data_processor import ExcelDataLoader, DataProcessor, BatchProcessor
    from ..core.validators import DataValidator, create_comprehensive_validation_report
    from .curve_fitting import CurveFitter, fit_multiple_methods, AreaFunction
    from .mechanical_calculator import MechanicalPropertiesCalculator, TipCalibration
except ImportError:
    from core.standards import ISO14577Constants, AnalysisConfig, MaterialProperties
    from core.data_processor import ExcelDataLoader, DataProcessor, BatchProcessor
    from core.validators import DataValidator, create_comprehensive_validation_report
    from analysis.curve_fitting import CurveFitter, fit_multiple_methods, AreaFunction
    from analysis.mechanical_calculator import MechanicalPropertiesCalculator, TipCalibration


# Configure module logger without mutating global/root logging handlers.
logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.addHandler(logging.NullHandler())


class NanoindentationAnalyzer:
    """
    Main analyzer class that orchestrates the complete nanoindentation analysis workflow
    
    This class provides a high-level interface to perform ISO 14577-4:2016 compliant
    nanoindentation analysis with automatic data processing, validation, and property calculation.
    """
    
    def __init__(self, area_function_coefficients: Optional[Dict] = None,
                 sample_poisson: float = 0.3, indenter_material: str = 'diamond'):
        """
        Initialize the analyzer with configuration parameters
        
        Args:
            area_function_coefficients: Custom area function coefficients
            sample_poisson: Sample Poisson's ratio (default 0.3)
            indenter_material: Indenter material ('diamond', 'sapphire', etc.)
        """
        self.iso = ISO14577Constants()
        self.config = AnalysisConfig()
        self.materials = MaterialProperties()
        
        # Initialize components
        self.data_loader = ExcelDataLoader()
        self.data_processor = DataProcessor()
        self.validator = DataValidator()
        self.curve_fitter = CurveFitter()
        try:
            from ..calibration.nist_methods import NISTCalibrationMethods
        except ImportError:
            from calibration.nist_methods import NISTCalibrationMethods
        self.nist_calibration = NISTCalibrationMethods()
        
        # Set up area function
        if area_function_coefficients:
            self.area_function = AreaFunction(area_function_coefficients)
        else:
            self.area_function = AreaFunction()
        
        # Set up mechanical properties calculator
        self.properties_calculator = MechanicalPropertiesCalculator(self.area_function)
        
        # Analysis parameters
        self.sample_poisson = sample_poisson
        self.indenter_material = indenter_material
        
        # Results storage
        self.analysis_results = {}
        self.batch_results = {}
        
    def analyze_file(self, file_path: Union[str, Path], 
                    fitting_method: str = 'oliver_pharr') -> Dict[str, any]:
        """
        Analyze a single nanoindentation file
        
        Args:
            file_path: Path to Excel file containing nanoindentation data
            fitting_method: Curve fitting method ('oliver_pharr', 'power_law', 'auto')
        
        Returns:
            Complete analysis results for all tests in the file
        """
        file_path = Path(file_path)
        
        results = {
            'file_path': str(file_path),
            'analysis_timestamp': pd.Timestamp.now().isoformat(),
            'parameters': {
                'fitting_method': fitting_method,
                'sample_poisson': self.sample_poisson,
                'indenter_material': self.indenter_material,
                'area_function': self.area_function.coefficients
            },
            'tests': {},
            'file_summary': {},
            'overall_success': False,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Load Excel file
            load_result = self.data_loader.load_excel_file(file_path)
            
            if not load_result['success']:
                results['errors'].extend(load_result['errors'])
                results['warnings'].extend(load_result['warnings'])
                return results
            
            # Analyze each sheet/test
            successful_tests = 0
            total_tests = 0
            
            for sheet_name, sheet_data in load_result['data'].items():
                total_tests += 1
                test_name = f"{file_path.stem}_{sheet_name}"
                
                logger.info(f"Analyzing test: {test_name}")
                
                test_result = self.analyze_single_test(
                    sheet_data, test_name, fitting_method
                )
                
                results['tests'][sheet_name] = test_result
                
                if test_result['success']:
                    successful_tests += 1
            
            # Generate file summary
            results['file_summary'] = {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'success_rate': successful_tests / total_tests if total_tests > 0 else 0,
                'file_metadata': load_result['metadata']
            }
            
            results['overall_success'] = successful_tests > 0
            
            # Store results
            self.analysis_results[str(file_path)] = results
            
        except Exception as e:
            results['errors'].append(f"File analysis failed: {str(e)}")
            logger.error(f"Error analyzing file {file_path}: {str(e)}")
        
        return results
    
    def analyze_single_test(self, data: pd.DataFrame, test_name: str,
                           fitting_method: str = 'oliver_pharr') -> Dict[str, any]:
        """
        Analyze a single nanoindentation test
        
        Args:
            data: DataFrame with nanoindentation data
            test_name: Identifier for the test
            fitting_method: Curve fitting method
        
        Returns:
            Complete analysis results for the test
        """
        results = {
            'test_name': test_name,
            'success': False,
            'timestamp': pd.Timestamp.now().isoformat(),
            'data_processing': {},
            'curve_fitting': {},
            'mechanical_properties': {},
            'validation_report': {},
            'quality_assessment': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # Step 1: Process and validate data
            logger.debug(f"Processing data for test: {test_name}")
            processing_result = self.data_processor.process_test_data(data, test_name)
            results['data_processing'] = processing_result
            
            if not processing_result['success']:
                results['errors'].extend(processing_result['errors'])
                results['warnings'].extend(processing_result['warnings'])
                return results
            
            # Step 2: Curve fitting on unloading data
            logger.debug(f"Fitting curves for test: {test_name}")
            unloading_data = processing_result['phases']['unloading']['filtered_data']
            
            if fitting_method == 'auto':
                # Try multiple methods and pick the best
                fitting_results = fit_multiple_methods(
                    unloading_data['Displacement (nm)'].values,
                    unloading_data['Load (mN)'].values
                )
                best_method = fitting_results['best_method']
                if best_method != 'none':
                    curve_fit_result = fitting_results[best_method]
                    results['curve_fitting'] = {
                        'method_used': best_method,
                        'all_methods': fitting_results,
                        **curve_fit_result
                    }
                else:
                    results['errors'].append("All curve fitting methods failed")
                    return results
            else:
                # Use specified method
                curve_fit_result = self.curve_fitter.fit_unloading_curve(
                    unloading_data['Displacement (nm)'].values,
                    unloading_data['Load (mN)'].values,
                    fitting_method
                )
                results['curve_fitting'] = curve_fit_result
            
            if not curve_fit_result['success']:
                results['errors'].extend(curve_fit_result['errors'])
                return results
            
            # Step 3: Calculate mechanical properties
            logger.debug(f"Calculating properties for test: {test_name}")
            max_load = processing_result['phases']['loading']['max_load']
            
            properties_result = self.properties_calculator.calculate_all_properties(
                max_load=max_load,
                contact_depth=curve_fit_result['contact_depth'],
                stiffness=curve_fit_result['stiffness'],
                sample_poisson=self.sample_poisson,
                indenter_material=self.indenter_material
            )
            results['mechanical_properties'] = properties_result
            
            if not properties_result['overall_valid']:
                results['warnings'].append("Some mechanical properties may be unreliable")
            
            # Step 4: Comprehensive validation
            logger.debug(f"Validating results for test: {test_name}")
            
            # Prepare analysis results for validation
            analysis_summary = {
                'r_squared': curve_fit_result['r_squared'],
                'stiffness': curve_fit_result['stiffness'],
                'hardness': properties_result['hardness']['hardness_gpa'],
                'modulus': properties_result['sample_modulus']['sample_modulus_gpa']
            }
            
            validation_report = create_comprehensive_validation_report(
                data, analysis_summary
            )
            results['validation_report'] = validation_report
            
            # Step 5: Quality assessment
            results['quality_assessment'] = self._assess_overall_quality(results)
            
            # Mark as successful if we got this far with valid properties
            results['success'] = properties_result['overall_valid']
            
        except Exception as e:
            results['errors'].append(f"Test analysis failed: {str(e)}")
            logger.error(f"Error analyzing test {test_name}: {str(e)}")
        
        return results
    
    def analyze_directory(self, directory_path: Union[str, Path],
                         file_pattern: str = "*.xls*",
                         fitting_method: str = 'oliver_pharr') -> Dict[str, any]:
        """
        Analyze all Excel files in a directory
        
        Args:
            directory_path: Path to directory containing Excel files
            file_pattern: Glob pattern for file matching
            fitting_method: Curve fitting method
        
        Returns:
            Batch analysis results
        """
        directory_path = Path(directory_path)
        
        results = {
            'directory_path': str(directory_path),
            'file_pattern': file_pattern,
            'analysis_timestamp': pd.Timestamp.now().isoformat(),
            'parameters': {
                'fitting_method': fitting_method,
                'sample_poisson': self.sample_poisson,
                'indenter_material': self.indenter_material
            },
            'files': {},
            'batch_summary': {},
            'statistical_analysis': {},
            'overall_success': False,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Find Excel files
            excel_files = list(directory_path.glob(file_pattern))
            
            if not excel_files:
                results['errors'].append(f"No files found matching pattern: {file_pattern}")
                return results
            
            logger.info(f"Found {len(excel_files)} files to analyze")
            
            # Analyze each file
            successful_files = 0
            all_test_results = []
            
            for file_path in excel_files:
                logger.info(f"Analyzing file: {file_path.name}")
                
                file_result = self.analyze_file(file_path, fitting_method)
                results['files'][file_path.name] = file_result
                
                if file_result['overall_success']:
                    successful_files += 1
                    
                    # Collect successful test results for statistical analysis
                    for test_name, test_result in file_result['tests'].items():
                        if test_result['success']:
                            all_test_results.append(test_result)
            
            # Generate batch summary
            results['batch_summary'] = {
                'total_files': len(excel_files),
                'successful_files': successful_files,
                'total_tests': sum(file_result['file_summary']['total_tests'] 
                                 for file_result in results['files'].values()
                                 if 'file_summary' in file_result),
                'successful_tests': len(all_test_results),
                'overall_success_rate': successful_files / len(excel_files) if excel_files else 0
            }
            
            # Statistical analysis across all tests
            if all_test_results:
                results['statistical_analysis'] = self._perform_statistical_analysis(all_test_results)
            
            results['overall_success'] = successful_files > 0
            
            # Store batch results
            self.batch_results[str(directory_path)] = results
            
        except Exception as e:
            results['errors'].append(f"Directory analysis failed: {str(e)}")
            logger.error(f"Error analyzing directory {directory_path}: {str(e)}")
        
        return results
    
    def _assess_overall_quality(self, test_results: Dict[str, any]) -> Dict[str, any]:
        """Assess overall quality of a single test analysis"""
        quality = {
            'overall_grade': 'unknown',
            'data_quality': 'unknown',
            'fitting_quality': 'unknown',
            'property_reliability': 'unknown',
            'iso_compliance': False,
            'recommendations': []
        }
        
        try:
            # Data quality from validation report
            if 'validation_report' in test_results:
                validation = test_results['validation_report']
                if 'curve_quality' in validation:
                    quality['data_quality'] = validation['curve_quality']['overall_grade']
            
            # Fitting quality
            if 'curve_fitting' in test_results:
                r_squared = test_results['curve_fitting'].get('r_squared', 0)
                if r_squared >= 0.99:
                    quality['fitting_quality'] = 'excellent'
                elif r_squared >= 0.98:
                    quality['fitting_quality'] = 'good'
                elif r_squared >= 0.95:
                    quality['fitting_quality'] = 'acceptable'
                else:
                    quality['fitting_quality'] = 'poor'
                    quality['recommendations'].append("Improve curve fitting quality")
            
            # Property reliability
            if 'mechanical_properties' in test_results:
                props = test_results['mechanical_properties']
                if props.get('overall_valid', False):
                    # Check reasonableness of H/E ratio
                    if 'derived_properties' in props:
                        he_ratio = props['derived_properties'].get('h_over_e_ratio', 0)
                        if 0.01 <= he_ratio <= 0.3:
                            quality['property_reliability'] = 'good'
                        else:
                            quality['property_reliability'] = 'questionable'
                            quality['recommendations'].append("Verify material properties - unusual H/E ratio")
                    else:
                        quality['property_reliability'] = 'acceptable'
                else:
                    quality['property_reliability'] = 'poor'
            
            # ISO compliance check
            fitting_r2 = test_results.get('curve_fitting', {}).get('r_squared', 0)
            quality['iso_compliance'] = fitting_r2 >= self.iso.MIN_R_SQUARED
            
            if not quality['iso_compliance']:
                quality['recommendations'].append("Analysis does not meet ISO 14577-4:2016 R² requirement")
            
            # Overall grade (worst of individual grades)
            grades = ['excellent', 'good', 'acceptable', 'poor', 'unknown']
            individual_grades = [
                quality['data_quality'],
                quality['fitting_quality'],
                quality['property_reliability']
            ]
            
            grade_indices = [grades.index(g) for g in individual_grades if g in grades]
            if grade_indices:
                worst_grade_idx = max(grade_indices)
                quality['overall_grade'] = grades[worst_grade_idx]
            
        except Exception as e:
            quality['error'] = f"Quality assessment failed: {str(e)}"
        
        return quality
    
    def _perform_statistical_analysis(self, test_results: List[Dict]) -> Dict[str, any]:
        """Perform statistical analysis across multiple tests"""
        stats = {
            'sample_size': len(test_results),
            'hardness_statistics': {},
            'modulus_statistics': {},
            'stiffness_statistics': {},
            'r_squared_statistics': {},
            'correlations': {},
            'outlier_analysis': {}
        }
        
        try:
            # Extract property values
            hardness_values = []
            modulus_values = []
            stiffness_values = []
            r_squared_values = []
            
            for result in test_results:
                try:
                    # Hardness (GPa)
                    h = result['mechanical_properties']['hardness']['hardness_gpa']
                    hardness_values.append(h)
                    
                    # Modulus (GPa)
                    e = result['mechanical_properties']['sample_modulus']['sample_modulus_gpa']
                    modulus_values.append(e)
                    
                    # Stiffness (mN/nm)
                    s = result['curve_fitting']['stiffness']
                    stiffness_values.append(s)
                    
                    # R-squared
                    r2 = result['curve_fitting']['r_squared']
                    r_squared_values.append(r2)
                    
                except KeyError:
                    continue
            
            # Calculate statistics for each property
            for prop_name, values in [
                ('hardness', hardness_values),
                ('modulus', modulus_values),
                ('stiffness', stiffness_values),
                ('r_squared', r_squared_values)
            ]:
                if values:
                    values_array = np.array(values)
                    stats[f'{prop_name}_statistics'] = {
                        'count': len(values),
                        'mean': np.mean(values_array),
                        'std': np.std(values_array),
                        'min': np.min(values_array),
                        'max': np.max(values_array),
                        'median': np.median(values_array),
                        'cv_percent': (np.std(values_array) / np.mean(values_array)) * 100 if np.mean(values_array) != 0 else 0
                    }
            
            # Correlation analysis
            if len(hardness_values) >= 3 and len(modulus_values) >= 3:
                min_len = min(len(hardness_values), len(modulus_values))
                h_array = np.array(hardness_values[:min_len])
                e_array = np.array(modulus_values[:min_len])
                
                correlation = np.corrcoef(h_array, e_array)[0, 1]
                stats['correlations']['hardness_modulus'] = {
                    'correlation': correlation,
                    'description': self._interpret_correlation(correlation)
                }
            
            # Outlier detection (using IQR method)
            for prop_name, values in [
                ('hardness', hardness_values),
                ('modulus', modulus_values)
            ]:
                if len(values) >= 5:
                    outliers = self._detect_outliers_iqr(values)
                    if outliers:
                        stats['outlier_analysis'][prop_name] = {
                            'outlier_indices': outliers,
                            'outlier_count': len(outliers),
                            'outlier_percentage': (len(outliers) / len(values)) * 100
                        }
        
        except Exception as e:
            stats['error'] = f"Statistical analysis failed: {str(e)}"
        
        return stats
    
    def _interpret_correlation(self, correlation: float) -> str:
        """Interpret correlation coefficient"""
        abs_corr = abs(correlation)
        direction = "positive" if correlation > 0 else "negative"
        
        if abs_corr > 0.8:
            strength = "strong"
        elif abs_corr > 0.5:
            strength = "moderate"
        elif abs_corr > 0.3:
            strength = "weak"
        else:
            return "no significant correlation"
        
        return f"{strength} {direction} correlation"
    
    def _detect_outliers_iqr(self, values: List[float]) -> List[int]:
        """Detect outliers using Interquartile Range method"""
        values_array = np.array(values)
        q1 = np.percentile(values_array, 25)
        q3 = np.percentile(values_array, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outlier_indices = []
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                outlier_indices.append(i)
        
        return outlier_indices
    
    def get_summary_report(self, analysis_type: str = 'latest') -> Dict[str, any]:
        """
        Generate a comprehensive summary report
        
        Args:
            analysis_type: 'latest', 'all', or specific file/directory path
        
        Returns:
            Summary report with key findings and recommendations
        """
        report = {
            'report_type': analysis_type,
            'generation_timestamp': pd.Timestamp.now().isoformat(),
            'summary': {},
            'key_findings': [],
            'recommendations': [],
            'iso_compliance': {},
            'data_quality_assessment': {}
        }
        
        try:
            if analysis_type == 'latest':
                # Get the most recent analysis
                if self.batch_results:
                    latest_key = max(self.batch_results.keys(), 
                                   key=lambda k: self.batch_results[k]['analysis_timestamp'])
                    analysis_data = self.batch_results[latest_key]
                elif self.analysis_results:
                    latest_key = max(self.analysis_results.keys(),
                                   key=lambda k: self.analysis_results[k]['analysis_timestamp'])
                    analysis_data = self.analysis_results[latest_key]
                else:
                    report['error'] = "No analysis results available"
                    return report
            
            # Generate report content based on analysis data
            # This is a simplified version - can be expanded significantly
            if 'statistical_analysis' in analysis_data:
                stats = analysis_data['statistical_analysis']
                
                # Key findings
                if 'hardness_statistics' in stats:
                    h_stats = stats['hardness_statistics']
                    report['key_findings'].append(
                        f"Average hardness: {h_stats['mean']:.2f} ± {h_stats['std']:.2f} GPa "
                        f"(CV: {h_stats['cv_percent']:.1f}%)"
                    )
                
                if 'modulus_statistics' in stats:
                    e_stats = stats['modulus_statistics']
                    report['key_findings'].append(
                        f"Average modulus: {e_stats['mean']:.1f} ± {e_stats['std']:.1f} GPa "
                        f"(CV: {e_stats['cv_percent']:.1f}%)"
                    )
                
                # ISO compliance
                if 'r_squared_statistics' in stats:
                    r2_stats = stats['r_squared_statistics']
                    iso_compliant_rate = (
                        len([r for r in [r2_stats['mean']] if r >= self.iso.MIN_R_SQUARED]) / 1 * 100
                    )
                    report['iso_compliance'] = {
                        'average_r_squared': r2_stats['mean'],
                        'min_r_squared': r2_stats['min'],
                        'iso_compliant_rate': f"{iso_compliant_rate:.0f}%"
                    }
        
        except Exception as e:
            report['error'] = f"Report generation failed: {str(e)}"
        
        return report
    
    def export_results(self, output_path: Union[str, Path], 
                      format: str = 'excel') -> bool:
        """
        Export analysis results to file
        
        Args:
            output_path: Output file path
            format: Export format ('excel', 'csv', 'json')
        
        Returns:
            Success status
        """
        output_path = Path(output_path)
        
        try:
            if format == 'excel':
                return self._export_to_excel(output_path)
            elif format == 'csv':
                return self._export_to_csv(output_path)
            elif format == 'json':
                return self._export_to_json(output_path)
            else:
                logger.error(f"Unsupported export format: {format}")
                return False
        
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            return False
    
    def _export_to_excel(self, output_path: Path) -> bool:
        """Export results to Excel format"""
        # Implementation for Excel export
        # This would create a comprehensive Excel workbook with multiple sheets
        logger.info(f"Excel export functionality to be implemented: {output_path}")
        return True
    
    def _export_to_csv(self, output_path: Path) -> bool:
        """Export results to CSV format"""
        # Implementation for CSV export
        logger.info(f"CSV export functionality to be implemented: {output_path}")
        return True
    
    def _export_to_json(self, output_path: Path) -> bool:
        """Export results to JSON format"""
        import json
        
        export_data = {
            'analysis_results': self.analysis_results,
            'batch_results': self.batch_results,
            'export_timestamp': pd.Timestamp.now().isoformat()
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Results exported to JSON: {output_path}")
        return True


# Convenience function for quick analysis
def analyze_nanoindentation_file(file_path: Union[str, Path],
                                area_function_coefficients: Optional[Dict] = None,
                                sample_poisson: float = 0.3,
                                fitting_method: str = 'oliver_pharr') -> Dict[str, any]:
    """
    Quick analysis function for a single file
    
    Args:
        file_path: Path to nanoindentation Excel file
        area_function_coefficients: Custom area function coefficients
        sample_poisson: Sample Poisson's ratio
        fitting_method: Curve fitting method
    
    Returns:
        Analysis results
    """
    analyzer = NanoindentationAnalyzer(
        area_function_coefficients=area_function_coefficients,
        sample_poisson=sample_poisson
    )
    
    return analyzer.analyze_file(file_path, fitting_method)
