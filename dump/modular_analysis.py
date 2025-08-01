#!/usr/bin/env python3
"""
Command Line Interface for Modular Nanoindentation Analyzer
ISO 14577-4:2016 compliant analysis with enhanced features
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Any
import logging

# Import the new modular components
from nanoindentation_analyzer import NanoindentationAnalyzer, analyze_nanoindentation_file
from iso_constants import ISO14577Constants, AnalysisConfig, MaterialProperties
from mechanical_properties import MechanicalPropertiesCalculator


def setup_logging(verbose: bool = False):
    """Set up logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=level, format=format_str)


def print_results_summary(results: Dict[str, Any], detailed: bool = False):
    """Print a formatted summary of analysis results"""
    print("\n" + "="*80)
    print("🔬 NANOINDENTATION ANALYSIS RESULTS")
    print("="*80)
    
    if not results.get('overall_success', False):
        print("❌ Analysis failed!")
        if 'errors' in results:
            print("\nErrors:")
            for error in results['errors']:
                print(f"  • {error}")
        return
    
    # File summary
    if 'file_summary' in results:
        summary = results['file_summary']
        print(f"\n📁 File: {Path(results['file_path']).name}")
        print(f"   Tests analyzed: {summary['successful_tests']}/{summary['total_tests']}")
        print(f"   Success rate: {summary['success_rate']:.1%}")
    
    # Test results
    successful_tests = []
    for test_name, test_result in results.get('tests', {}).items():
        if test_result.get('success', False):
            successful_tests.append((test_name, test_result))
    
    if not successful_tests:
        print("\n❌ No successful tests found")
        return
    
    print(f"\n📊 MECHANICAL PROPERTIES SUMMARY ({len(successful_tests)} tests)")
    print("-" * 60)
    
    # Collect properties for statistics
    hardness_values = []
    modulus_values = []
    stiffness_values = []
    r_squared_values = []
    
    for test_name, test_result in successful_tests:
        try:
            props = test_result['mechanical_properties']
            fitting = test_result['curve_fitting']
            
            hardness = props['hardness']['hardness_gpa']
            modulus = props['sample_modulus']['sample_modulus_gpa']
            stiffness = fitting['stiffness']
            r_squared = fitting['r_squared']
            
            hardness_values.append(hardness)
            modulus_values.append(modulus)
            stiffness_values.append(stiffness)
            r_squared_values.append(r_squared)
            
            if detailed:
                print(f"\n🔬 Test: {test_name}")
                print(f"   Hardness: {hardness:.2f} GPa")
                print(f"   Modulus:  {modulus:.1f} GPa")
                print(f"   Stiffness: {stiffness:.1f} mN/nm")
                print(f"   R² fit:   {r_squared:.4f}")
                
                # Quality assessment
                quality = test_result.get('quality_assessment', {})
                grade = quality.get('overall_grade', 'unknown')
                iso_compliant = quality.get('iso_compliance', False)
                
                grade_icon = {
                    'excellent': '🌟', 'good': '✅', 'acceptable': '⚠️', 
                    'poor': '❌', 'unknown': '❓'
                }.get(grade, '❓')
                
                print(f"   Quality:  {grade_icon} {grade.upper()}")
                print(f"   ISO compliant: {'✅ Yes' if iso_compliant else '❌ No'}")
        
        except KeyError as e:
            if detailed:
                print(f"\n❌ Test {test_name}: Missing data ({e})")
    
    # Overall statistics
    if hardness_values:
        import numpy as np
        
        print(f"\n📈 OVERALL STATISTICS")
        print("-" * 40)
        print(f"Hardness:     {np.mean(hardness_values):.2f} ± {np.std(hardness_values):.2f} GPa")
        print(f"Modulus:      {np.mean(modulus_values):.1f} ± {np.std(modulus_values):.1f} GPa")
        print(f"Stiffness:    {np.mean(stiffness_values):.1f} ± {np.std(stiffness_values):.1f} mN/nm")
        print(f"Avg R²:       {np.mean(r_squared_values):.4f}")
        
        # ISO compliance
        iso_compliant = sum(1 for r2 in r_squared_values if r2 >= 0.98)
        print(f"ISO compliant: {iso_compliant}/{len(r_squared_values)} tests ({iso_compliant/len(r_squared_values):.1%})")
        
        # Material assessment
        avg_hardness = np.mean(hardness_values)
        avg_modulus = np.mean(modulus_values)
        he_ratio = avg_hardness * 1e9 / (avg_modulus * 1e9)
        
        print(f"\n🔍 MATERIAL ASSESSMENT")
        print("-" * 40)
        print(f"H/E ratio:    {he_ratio:.3f}")
        
        # Material identification hint
        if 8.5 <= avg_hardness <= 9.5:
            print("📝 Material: Likely fused silica (reference material)")
        elif avg_hardness < 1:
            print("📝 Material: Likely soft polymer or metal")
        elif avg_hardness > 15:
            print("📝 Material: Likely hard ceramic or crystal")
        else:
            print("📝 Material: Intermediate hardness material")


def print_batch_summary(results: Dict[str, Any]):
    """Print summary for batch analysis"""
    print("\n" + "="*80)
    print("📁 BATCH ANALYSIS RESULTS")
    print("="*80)
    
    summary = results.get('batch_summary', {})
    print(f"Directory: {results.get('directory_path', 'Unknown')}")
    print(f"Files processed: {summary.get('successful_files', 0)}/{summary.get('total_files', 0)}")
    print(f"Tests analyzed: {summary.get('successful_tests', 0)}/{summary.get('total_tests', 0)}")
    print(f"Overall success rate: {summary.get('overall_success_rate', 0):.1%}")
    
    # Statistical analysis
    if 'statistical_analysis' in results:
        stats = results['statistical_analysis']
        print(f"\n📊 STATISTICAL SUMMARY ({stats.get('sample_size', 0)} tests)")
        print("-" * 60)
        
        for prop in ['hardness', 'modulus', 'stiffness']:
            prop_stats = stats.get(f'{prop}_statistics', {})
            if prop_stats:
                mean = prop_stats.get('mean', 0)
                std = prop_stats.get('std', 0)
                cv = prop_stats.get('cv_percent', 0)
                
                unit = {'hardness': 'GPa', 'modulus': 'GPa', 'stiffness': 'mN/nm'}[prop]
                print(f"{prop.capitalize():12}: {mean:.2f} ± {std:.2f} {unit} (CV: {cv:.1f}%)")


def main():
    """Main command line interface"""
    parser = argparse.ArgumentParser(
        description="Modular Nanoindentation Analyzer - ISO 14577-4:2016 Compliant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s single_file.xls
  %(prog)s --directory /path/to/files --pattern "*.xlsx"
  %(prog)s file.xls --method auto --poisson 0.25 --detailed
  %(prog)s file.xls --export results.json --format json
        """
    )
    
    # Input arguments
    parser.add_argument('input', nargs='?', help='Input file or directory path')
    parser.add_argument('--directory', '-d', help='Analyze all files in directory')
    parser.add_argument('--pattern', default='*.xls*', help='File pattern for directory analysis (default: *.xls*)')
    
    # Analysis parameters
    parser.add_argument('--method', choices=['oliver_pharr', 'power_law', 'auto'], 
                       default='oliver_pharr', help='Curve fitting method (default: oliver_pharr)')
    parser.add_argument('--poisson', type=float, default=0.3, 
                       help='Sample Poisson ratio (default: 0.3)')
    parser.add_argument('--indenter', default='diamond', 
                       help='Indenter material (default: diamond)')
    
    # Area function calibration
    parser.add_argument('--area-c0', type=float, help='Area function C0 coefficient')
    parser.add_argument('--area-c1', type=float, help='Area function C1 coefficient')
    parser.add_argument('--area-c2', type=float, help='Area function C2 coefficient')
    
    # Output options
    parser.add_argument('--export', help='Export results to file')
    parser.add_argument('--format', choices=['json', 'excel', 'csv'], default='json',
                       help='Export format (default: json)')
    parser.add_argument('--detailed', action='store_true', 
                       help='Show detailed results for each test')
    
    # Other options
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--validate-only', action='store_true', 
                       help='Only validate data without full analysis')
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Validate input
    if not args.input and not args.directory:
        parser.error("Must specify either input file or --directory")
    
    # Prepare area function coefficients
    area_coefficients = None
    if any([args.area_c0, args.area_c1, args.area_c2]):
        area_coefficients = {}
        if args.area_c0 is not None:
            area_coefficients['C0'] = args.area_c0
        if args.area_c1 is not None:
            area_coefficients['C1'] = args.area_c1
        if args.area_c2 is not None:
            area_coefficients['C2'] = args.area_c2
    
    # Create analyzer
    analyzer = NanoindentationAnalyzer(
        area_function_coefficients=area_coefficients,
        sample_poisson=args.poisson,
        indenter_material=args.indenter
    )
    
    try:
        # Perform analysis
        if args.directory or (args.input and Path(args.input).is_dir()):
            # Directory analysis
            directory_path = args.directory or args.input
            print(f"🔍 Analyzing directory: {directory_path}")
            print(f"📄 File pattern: {args.pattern}")
            
            results = analyzer.analyze_directory(
                directory_path, 
                file_pattern=args.pattern,
                fitting_method=args.method
            )
            
            print_batch_summary(results)
            
        else:
            # Single file analysis
            file_path = Path(args.input)
            if not file_path.exists():
                print(f"❌ Error: File not found: {file_path}")
                sys.exit(1)
            
            print(f"🔍 Analyzing file: {file_path.name}")
            
            if args.validate_only:
                # Quick validation
                from data_processing import ExcelDataLoader
                from data_validation import DataValidator
                
                loader = ExcelDataLoader()
                validator = DataValidator()
                
                load_result = loader.load_excel_file(file_path)
                if load_result['success']:
                    print("✅ File loaded successfully")
                    for sheet_name, sheet_data in load_result['data'].items():
                        validation = validator.validate_data_completeness(sheet_data)
                        status = "✅" if validation['valid'] else "❌"
                        print(f"  {status} Sheet '{sheet_name}': {len(sheet_data)} data points")
                else:
                    print("❌ File validation failed")
                    for error in load_result['errors']:
                        print(f"  • {error}")
                return
            
            results = analyzer.analyze_file(file_path, fitting_method=args.method)
            print_results_summary(results, detailed=args.detailed)
        
        # Export results if requested
        if args.export:
            export_path = Path(args.export)
            success = analyzer.export_results(export_path, format=args.format)
            if success:
                print(f"\n💾 Results exported to: {export_path}")
            else:
                print(f"\n❌ Export failed")
        
        # Summary recommendations
        if results.get('overall_success', False):
            print(f"\n🎯 RECOMMENDATIONS")
            print("-" * 40)
            
            # Collect all recommendations
            all_recommendations = set()
            
            if 'tests' in results:
                for test_result in results['tests'].values():
                    if test_result.get('success', False):
                        quality = test_result.get('quality_assessment', {})
                        recs = quality.get('recommendations', [])
                        all_recommendations.update(recs)
            
            if all_recommendations:
                for rec in sorted(all_recommendations):
                    print(f"  • {rec}")
            else:
                print("  • All tests meet quality standards")
        
    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
