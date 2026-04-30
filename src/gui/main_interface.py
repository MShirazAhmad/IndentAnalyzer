#!/usr/bin/env python3
"""
Nanoindentation Analysis GUI
A comprehensive PyQt5 interface for the FixedIndentXLSAnalyzer
ISO 14577-4:2016 compliant nanoindentation analysis with advanced tip calibration
"""

import sys
import os
import json
import configparser
from pathlib import Path
import traceback
from typing import Optional, Dict, Any, List
import webbrowser
import logging
import time
from datetime import datetime

# PyQt5 imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog,
    QProgressBar, QTabWidget, QTableWidget, QTableWidgetItem, QCheckBox,
    QGroupBox, QSplitter, QMessageBox, QScrollArea, QSpinBox, QDoubleSpinBox,
    QComboBox, QFrame, QSizePolicy, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

# Scientific computing imports
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')  # Use Qt5 backend for matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

# Add the current directory to Python path for local imports
# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our new modular analyzer components
FixedIndentXLSAnalyzer = None
NanoindentationAnalyzer = None
ISO14577Constants = None
AnalysisConfig = None
MechanicalPropertiesCalculator = None
NISTCalibrationMethods = None

try:
    from ..analysis.main_analyzer import NanoindentationAnalyzer, analyze_nanoindentation_file
    from ..core.standards import ISO14577Constants, AnalysisConfig
    from ..analysis.mechanical_calculator import MechanicalPropertiesCalculator
    from ..calibration.nist_methods import NISTCalibrationMethods
    # Keep the old analyzer for backward compatibility
    from ..analysis.enhanced_analyzer import FixedIndentXLSAnalyzer
except ImportError as e:
    print(f"Warning: Could not import new modular components: {e}")
    # Fallback to absolute imports
    try:
        from analysis.main_analyzer import NanoindentationAnalyzer, analyze_nanoindentation_file
        from core.standards import ISO14577Constants, AnalysisConfig
        from analysis.mechanical_calculator import MechanicalPropertiesCalculator
        from calibration.nist_methods import NISTCalibrationMethods
        from analysis.enhanced_analyzer import FixedIndentXLSAnalyzer
    except ImportError as e2:
        print(f"Warning: Could not import with absolute imports either: {e2}")
        # Final fallback - import enhanced analyzer directly by adding to path
        try:
            import os
            analysis_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'analysis')
            sys.path.insert(0, analysis_dir)
            from enhanced_analyzer import FixedIndentXLSAnalyzer
            print("✅ Successfully imported FixedIndentXLSAnalyzer using direct path")
        except ImportError as e3:
            print(f"Critical: Could not import FixedIndentXLSAnalyzer: {e3}")
            FixedIndentXLSAnalyzer = None


# Configure debug logging
def setup_debug_logging():
    """Set up comprehensive debug logging for the GUI application"""
    # Create logs directory if it doesn't exist
    log_dir = Path.home() / "IndentXLSAnalyzer_logs"
    log_dir.mkdir(exist_ok=True)
    
    # Create timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"gui_debug_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)8s | %(name)20s | %(funcName)20s:%(lineno)4d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create GUI-specific logger
    logger = logging.getLogger('NanoindentationGUI')
    logger.info("="*80)
    logger.info(f"GUI Application Started - Log file: {log_file}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info("="*80)
    
    return logger


# Initialize debug logging
debug_logger = setup_debug_logging()


class AnalysisWorker(QThread):
    """
    Worker thread for running nanoindentation analysis
    Supports both legacy and new modular analyzers
    """
    
    # Signals for communication with main thread
    progress_update = pyqtSignal(int)  # Progress percentage
    status_update = pyqtSignal(str)    # Status message
    result_ready = pyqtSignal(object)  # Analysis results
    error_occurred = pyqtSignal(str)   # Error message
    plot_ready = pyqtSignal(object)    # Plot data
    
    def __init__(self, analyzer=None, file_path=None, use_new_analyzer=True,
                 area_function_coefficients=None, sample_poisson=0.3,
                 indenter_material='diamond', fitting_method='oliver_pharr',
                 min_r_squared=0.98, fit_percent=25.0):
        super().__init__()
        self.analyzer = analyzer
        self.file_path = file_path
        self.use_new_analyzer = use_new_analyzer
        self.area_function_coefficients = area_function_coefficients
        self.sample_poisson = sample_poisson
        self.indenter_material = indenter_material
        self.fitting_method = fitting_method
        self.min_r_squared = float(min_r_squared)
        self.fit_percent = float(fit_percent)
        self.is_cancelled = False
        self.logger = logging.getLogger('AnalysisWorker')
        
        # Debug log initialization
        self.logger.debug(f"AnalysisWorker initialized:")
        self.logger.debug(f"  - file_path: {file_path}")
        self.logger.debug(f"  - use_new_analyzer: {use_new_analyzer}")
        self.logger.debug(f"  - analyzer type: {type(analyzer).__name__ if analyzer else 'None'}")
        self.logger.debug(f"  - fitting_method: {fitting_method}")
        self.logger.debug(f"  - min_r_squared: {self.min_r_squared}")
        self.logger.debug(f"  - fit_percent: {self.fit_percent}")
    
    def run(self):
        """Execute the analysis in a separate thread"""
        start_time = time.time()
        self.logger.info("="*60)
        self.logger.info("ANALYSIS WORKER THREAD STARTED")
        self.logger.info("="*60)
        
        try:
            self.status_update.emit("🔬 Starting ISO 14577-4:2016 compliant analysis...")
            self.progress_update.emit(10)
            self.logger.debug("Initial progress update sent (10%)")
            
            if self.use_new_analyzer and self.file_path:
                self.logger.info("Using NEW MODULAR ANALYZER")
                self._run_new_analyzer()
            else:
                self.logger.info("Using LEGACY ANALYZER")
                self._run_legacy_analyzer()
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.logger.error(f"ANALYSIS FAILED after {elapsed_time:.2f} seconds")
            self.logger.error(f"Exception type: {type(e).__name__}")
            self.logger.error(f"Exception message: {str(e)}")
            self.logger.error("Full traceback:")
            self.logger.error(traceback.format_exc())
            
            error_msg = f"Analysis failed: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            self.error_occurred.emit(error_msg)
        
        finally:
            elapsed_time = time.time() - start_time
            self.logger.info("="*60)
            self.logger.info(f"ANALYSIS WORKER THREAD COMPLETED in {elapsed_time:.2f} seconds")
            self.logger.info("="*60)
    
    def _run_new_analyzer(self):
        """Run analysis using the new modular analyzer"""
        self.logger.debug("Entering _run_new_analyzer method")
        
        # Use new modular analyzer
        self.status_update.emit("📊 Using new modular analyzer...")
        self.progress_update.emit(25)
        self.logger.debug("Progress updated to 25% - new analyzer selected")
        
        # Create new analyzer instance
        self.logger.debug("Creating NanoindentationAnalyzer instance")
        new_analyzer = NanoindentationAnalyzer(
            area_function_coefficients=self.area_function_coefficients,
            sample_poisson=self.sample_poisson,
            indenter_material=self.indenter_material
        )
        # Apply GUI-selected quality threshold so only accepted fits are used
        # for downstream hardness/modulus computation and plotting.
        new_analyzer.iso.MIN_R_SQUARED = self.min_r_squared
        new_analyzer.iso.STIFFNESS_RANGE_PERCENT = max(0.05, min(self.fit_percent / 100.0, 1.0))
        if hasattr(new_analyzer, 'curve_fitter') and hasattr(new_analyzer.curve_fitter, 'iso'):
            new_analyzer.curve_fitter.iso.MIN_R_SQUARED = self.min_r_squared
            new_analyzer.curve_fitter.iso.STIFFNESS_RANGE_PERCENT = max(0.05, min(self.fit_percent / 100.0, 1.0))
        self.logger.info(f"New analyzer created: {type(new_analyzer).__name__}")
        
        self.status_update.emit("🔍 Processing file with enhanced validation...")
        self.progress_update.emit(50)
        self.logger.debug("Progress updated to 50% - about to analyze file")
        self.logger.info(f"Analyzing file: {self.file_path}")
        
        # Check if file exists and is readable
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        file_size = os.path.getsize(self.file_path)
        self.logger.debug(f"File size: {file_size} bytes")
        
        # Run analysis
        results = new_analyzer.analyze_file(self.file_path, self.fitting_method)
        self.logger.info(f"Analysis completed - results type: {type(results)}")
        
        if hasattr(results, '__len__'):
            self.logger.info(f"Number of results: {len(results)}")
        
        if self.is_cancelled:
            self.logger.warning("Analysis was cancelled by user")
            return
        
        self.progress_update.emit(80)
        self.status_update.emit("✅ New modular analysis completed!")
        self.logger.debug("Progress updated to 80% - analysis completed")
        
        self.progress_update.emit(100)
        self.result_ready.emit(results)
        self.logger.info("Results emitted to main thread")
    
    def _run_legacy_analyzer(self):
        """Run analysis using the legacy analyzer"""
        self.logger.debug("Entering _run_legacy_analyzer method")
        
        # Use legacy analyzer
        self.status_update.emit("📊 Using legacy analyzer...")
        self.progress_update.emit(25)
        self.logger.debug("Progress updated to 25% - legacy analyzer selected")
        
        if not self.analyzer:
            raise ValueError("Legacy analyzer not provided")
        
        self.logger.info(f"Legacy analyzer type: {type(self.analyzer).__name__}")
        
        # Disable plotting in analyzer to handle it in GUI
        if hasattr(self.analyzer, 'generatePlot'):
            original_generate_plot = self.analyzer.generatePlot
            self.analyzer.generatePlot = False
            self.logger.debug(f"Set generatePlot = False (was {original_generate_plot})")
            
        if hasattr(self.analyzer, 'hidePlot'):
            original_hide_plot = self.analyzer.hidePlot
            self.analyzer.hidePlot = True
            self.logger.debug(f"Set hidePlot = True (was {original_hide_plot})")
        
        self.status_update.emit("📊 Loading data and performing tip calibration...")
        self.progress_update.emit(50)
        self.logger.debug("Progress updated to 50% - about to run legacy analysis")
        
        # Run the legacy analysis
        self.logger.info("Calling analyzer.run_analysis()")
        results = self.analyzer.run_analysis()
        self.logger.info(f"Legacy analysis completed - results type: {type(results)}")
        
        if hasattr(results, '__len__'):
            self.logger.info(f"Number of results: {len(results)}")
        
        if self.is_cancelled:
            self.logger.warning("Analysis was cancelled by user")
            return
            
        self.progress_update.emit(80)
        self.status_update.emit("✅ Legacy analysis completed successfully!")
        self.logger.debug("Progress updated to 80% - legacy analysis completed")
        
        self.progress_update.emit(100)
        self.result_ready.emit(results)
        self.logger.info("Results emitted to main thread")
    
    def cancel(self):
        """Cancel the analysis"""
        self.logger.warning("CANCEL REQUEST RECEIVED")
        self.is_cancelled = True
        self.logger.info("Analysis worker marked for cancellation")
        self.quit()
        self.logger.debug("QThread.quit() called")


class MatplotlibWidget(QWidget):
    """
    Custom widget for embedding matplotlib plots in PyQt5
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger('MatplotlibWidget')
        self.logger.debug("MatplotlibWidget initializing")
        
        # Create matplotlib figure and canvas with white background
        self.figure = Figure(figsize=(12, 8), dpi=100, facecolor='white')
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Set canvas background to white
        self.canvas.setStyleSheet("background-color: white;")
        
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.logger.debug("MatplotlibWidget initialized successfully")
    
    def clear_plot(self):
        """Clear the current plot"""
        self.logger.debug("Clearing plot")
        self.figure.clear()
        self.canvas.draw()
        self.logger.debug("Plot cleared")
    
    def plot_nanoindentation_curve(self, analyzer: FixedIndentXLSAnalyzer, test_data: Dict[str, Any]):
        """
        Plot nanoindentation curve using the analyzer data
        """
        test_id = test_data.get('Test', 'Unknown')
        self.logger.info(f"Plotting nanoindentation curve for Test {test_id}")
        self.logger.debug(f"Test data keys: {list(test_data.keys())}")
        self.logger.debug(f"Analyzer type: {type(analyzer).__name__}")
        
        plot_start_time = time.time()
        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # Set labels and title
            ax.set_xlabel("Displacement Into Surface (nm)", fontsize=12, fontweight='bold')
            ax.set_ylabel("Load on Sample (mN)", fontsize=12, fontweight='bold')
            ax.set_title(f"Nanoindentation Analysis - Test {test_data.get('Test', 'N/A')}", 
                        fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            # Prefer raw data carried with modular results
            loading_disp_raw = test_data.get('Raw Loading Displacement (nm)', [])
            loading_load_raw = test_data.get('Raw Loading Load (mN)', [])
            unloading_disp_raw = test_data.get('Raw Unloading Displacement (nm)', [])
            unloading_load_raw = test_data.get('Raw Unloading Load (mN)', [])

            loading_fit_disp = test_data.get('Loading Fit Displacement (nm)', [])
            loading_fit_load = test_data.get('Loading Fit Load (mN)', [])
            unloading_fit_disp = test_data.get('Unloading Fit Displacement (nm)', [])
            unloading_fit_load = test_data.get('Unloading Fit Load (mN)', [])

            has_curve_data = False
            if loading_disp_raw and loading_load_raw:
                ax.scatter(loading_disp_raw, loading_load_raw, s=8, alpha=0.65, label='Loading raw data')
                has_curve_data = True
            if unloading_disp_raw and unloading_load_raw:
                ax.scatter(unloading_disp_raw, unloading_load_raw, s=8, alpha=0.65, label='Unloading raw data')
                has_curve_data = True

            if loading_fit_disp and loading_fit_load:
                ax.plot(loading_fit_disp, loading_fit_load, 'b--', linewidth=1.8, alpha=0.9, label='Loading fit')
                has_curve_data = True
            if unloading_fit_disp and unloading_fit_load:
                ax.plot(unloading_fit_disp, unloading_fit_load, 'r--', linewidth=1.8, alpha=0.9, label='Unloading fit')
                has_curve_data = True
            
            # Plot tangent line (stiffness line at peak load) if available
            tangent_disp = test_data.get('Tangent Displacement (nm)', [])
            tangent_load = test_data.get('Tangent Load (mN)', [])
            if tangent_disp and tangent_load:
                ax.plot(tangent_disp, tangent_load, 'g-', linewidth=2.0, alpha=0.8, label='Tangent (Stiffness)')
                has_curve_data = True

            # Try to get actual curve data from the analyzer
            test_number = test_data.get('Test', 'N/A')
            
            
            # If analyzer has curve data, overlay it (or use it as fallback)
            if analyzer and hasattr(analyzer, 'curve_data') and analyzer.curve_data:
                for curve_test_id, curve_info in analyzer.curve_data.items():
                    if str(curve_test_id) == str(test_number):
                        # Plot loading and unloading curves
                        if 'loading_displacement' in curve_info and 'loading_load' in curve_info:
                            ax.plot(curve_info['loading_displacement'], curve_info['loading_load'], 
                                   'b-', linewidth=1.5, label='Loading curve', alpha=0.6)
                            has_curve_data = True
                        
                        if 'unloading_displacement' in curve_info and 'unloading_load' in curve_info:
                            ax.plot(curve_info['unloading_displacement'], curve_info['unloading_load'], 
                                   'r-', linewidth=1.5, label='Unloading curve', alpha=0.6)
                            has_curve_data = True
                        
                        # Plot fits if available
                        if 'loading_fit_displacement' in curve_info and 'loading_fit_load' in curve_info:
                            ax.plot(curve_info['loading_fit_displacement'], curve_info['loading_fit_load'], 
                                   'b--', linewidth=1.8, label='Loading fit', alpha=0.9)
                            has_curve_data = True
                        
                        if 'unloading_fit_displacement' in curve_info and 'unloading_fit_load' in curve_info:
                            ax.plot(curve_info['unloading_fit_displacement'], curve_info['unloading_fit_load'], 
                                   'r--', linewidth=1.8, label='Unloading fit', alpha=0.9)
                            has_curve_data = True
                        
                        # Plot tangent line if available (stiffness line at peak load)
                        if 'tangent_displacement' in curve_info and 'tangent_load' in curve_info:
                            ax.plot(curve_info['tangent_displacement'], curve_info['tangent_load'],
                                   'g-', linewidth=2.0, label='Tangent (Stiffness)', alpha=0.8)
                            has_curve_data = True
                        
                        break
            
            # If no curve data available, create a placeholder plot
            if not has_curve_data:
                # Create sample curve shape for visualization
                max_disp = test_data.get('Max Displacement (nm)', 1000)
                max_load = test_data.get('Max Load (mN)', 100)
                
                # Generate sample loading curve (power law)
                loading_disp = np.linspace(0, max_disp, 100)
                loading_load = max_load * (loading_disp / max_disp) ** 2
                
                # Generate sample unloading curve (Oliver-Pharr style)
                unloading_disp = np.linspace(max_disp, max_disp * 0.3, 50)
                unloading_load = max_load * ((unloading_disp - max_disp * 0.25) / (max_disp * 0.75)) ** 1.5
                unloading_load = np.maximum(unloading_load, 0)
                
                ax.plot(loading_disp, loading_load, 'b-', linewidth=2, label='Loading (Simulated)', alpha=0.7)
                ax.plot(unloading_disp, unloading_load, 'r-', linewidth=2, label='Unloading (Simulated)', alpha=0.7)
                ax.text(0.5, 0.5, 'Simulated Curve\n(Raw data not available)', 
                       transform=ax.transAxes, ha='center', va='center',
                       bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7))

            if has_curve_data:
                ax.legend()
            
            # Add results text box
            result_text = f"""File: {test_data.get('Source File', 'N/A')}
Test: {test_data.get('Test', 'N/A')}
Hardness: {test_data.get('Hardness (GPa)', 0):.3f} GPa
Modulus: {test_data.get('Oliver-Pharr Modulus (GPa)', 0):.1f} GPa
Max Load: {test_data.get('Max Load (mN)', 0):.2f} mN
Max Disp: {test_data.get('Max Displacement (nm)', 0):.1f} nm
Contact Area: {test_data.get('A (m^2)', 0)*1e18:.0f} nm²
Stiffness: {test_data.get('S (N/m)', 0)/1e6:.2f} mN/nm
Loading R²: {test_data.get('Loading R²', 0):.4f}
Unloading R²: {test_data.get('Unloading Fit R²', 0):.4f}
Raw data shown: {'Yes' if (loading_disp_raw or unloading_disp_raw) else 'No (simulated)'}"""
            
            ax.text(0.02, 0.98, result_text, transform=ax.transAxes, 
                   verticalalignment='top', fontsize=9, fontfamily='monospace',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.8))
            
            # Set reasonable axis limits
            ax.set_xlim(left=0)
            ax.set_ylim(bottom=0)
            
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error plotting Test {test_data.get('Test', 'N/A')}: {e}")
            # Create error plot
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, f'Error plotting Test {test_data.get("Test", "N/A")}:\n{str(e)}', 
                   transform=ax.transAxes, ha='center', va='center',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='red', alpha=0.7))
            ax.set_title(f"Test {test_data.get('Test', 'N/A')} - Plot Error")
            self.canvas.draw()


class ResultsTableWidget(QTableWidget):
    """
    Custom table widget for displaying analysis results
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configure table appearance
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSortingEnabled(True)
        
        # Set font with fallbacks for cross-platform compatibility
        font = QFont()
        font.setFamily("Monaco")  # macOS monospace font
        font.setStyleHint(QFont.Monospace)  # Fallback to system monospace
        font.setPointSize(9)
        self.setFont(font)
    
    def load_results(self, results: List[Dict[str, Any]]):
        """Load analysis results into the table"""
        if not results:
            return
        
        # Set up table dimensions
        self.setRowCount(len(results))
        
        # Define the exact columns to show in Results Table (no extra columns after Analysis Success)
        display_keys = [
            'Source File',
            'Test',
            'Hardness (GPa)',
            'Oliver-Pharr Hardness (GPa)',
            'Oliver-Pharr Modulus (GPa)',
            'CSM Hardness (GPa)',
            'Loading R²',
            'Unloading Fit R²',
            'Max Load (mN)',
            'Max Displacement (nm)',
            'S (N/m)',
            'A (m^2)',
            'Hc (m)',
            'Pmax (N)',
            'Calibration Factor',
            'Analysis Success'
        ]
        ordered_keys = [k for k in display_keys if any(k in result for result in results)]
        
        self.setColumnCount(len(ordered_keys))
        self.setHorizontalHeaderLabels(ordered_keys)
        
        # Populate table
        for row, result in enumerate(results):
            for col, key in enumerate(ordered_keys):
                value = result.get(key, '')
                
                # Format numeric values
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    if abs(value) > 1e-3 and abs(value) < 1e6:
                        formatted_value = f"{value:.4f}"
                    else:
                        formatted_value = f"{value:.2e}"
                else:
                    formatted_value = str(value)
                
                item = QTableWidgetItem(formatted_value)
                item.setData(Qt.UserRole, value)  # Store original value
                self.setItem(row, col, item)
        
        # Auto-resize columns
        self.resizeColumnsToContents()
        
        # Set minimum column widths
        header = self.horizontalHeader()
        for col in range(self.columnCount()):
            current_width = header.sectionSize(col)
            header.resizeSection(col, max(current_width, 80))


class NanoindentationGUI(QMainWindow):
    """
    Main GUI application for nanoindentation analysis
    """
    MAX_INDIVIDUAL_PLOT_TABS = 12
    
    def __init__(self):
        super().__init__()
        
        # Initialize attributes
        self.analyzer: Optional[FixedIndentXLSAnalyzer] = None
        self.analysis_worker: Optional[AnalysisWorker] = None
        self.current_results: List[Dict[str, Any]] = []
        self.plots_tab_widget: Optional[QTabWidget] = None
        self.results_panel_tabs: Optional[QTabWidget] = None
        self.workflow_tabs: Optional[QTabWidget] = None
        self.step4_plot_buttons_layout: Optional[QGridLayout] = None
        self.step4_plot_buttons_note: Optional[QLabel] = None
        self.nist_calibrator = NISTCalibrationMethods() if NISTCalibrationMethods else None
        self.calibration_source = "Default Berkovich"
        self.calibration_file_path: Optional[str] = None
        self.calibration_coefficients = self.get_default_calibration_coefficients()
        self.manual_coeff_inputs: Dict[str, QDoubleSpinBox] = {}
        self.calibration_status_text: Optional[QTextEdit] = None
        self.sample_name_edit: Optional[QLineEdit] = None
        self.research_goal_combo: Optional[QComboBox] = None
        self.sample_poisson_spinbox: Optional[QDoubleSpinBox] = None
        self.indenter_combo: Optional[QComboBox] = None
        self.fitting_method_combo: Optional[QComboBox] = None
        self.fit_curve_percent_spinbox: Optional[QDoubleSpinBox] = None
        self.readiness_text: Optional[QTextEdit] = None
        self.config_values: Dict[str, Any] = self.load_analysis_config()
        self.current_analysis_file_path: Optional[str] = None
        self.pending_analysis_context: Optional[str] = None
        self.calibration_plot_widget: Optional[MatplotlibWidget] = None
        
        # Set up the GUI
        self.init_ui()
        self.setStyleSheet(self.get_stylesheet())
        
        # Center the window
        self.center_window()

    def get_default_calibration_coefficients(self) -> Dict[str, float]:
        return {
            'C0': 24.56,
            'C1': 0.0,
            'C2': 0.0,
            'C3': 0.0,
            'C4': 0.0,
            'C5': 0.0,
            'C6': 0.0,
            'C7': 0.0,
            'C8': 0.0
        }

    def load_analysis_config(self) -> Dict[str, Any]:
        defaults = {
            "min_r_squared": 0.98,
            "fit_curve_percent": 25.0,
            "sample_poisson": 0.30,
            "default_indenter": "diamond",
            "default_fitting_method": "oliver_pharr"
        }
        config_path = Path("config/analysis_settings.ini")
        if not config_path.exists():
            return defaults

        parser = configparser.ConfigParser()
        parser.read(config_path)
        if parser.has_section("analysis"):
            defaults["min_r_squared"] = parser.getfloat("analysis", "min_r_squared", fallback=defaults["min_r_squared"])
            defaults["fit_curve_percent"] = parser.getfloat("analysis", "fit_curve_percent", fallback=defaults["fit_curve_percent"])
        if parser.has_section("calibration"):
            defaults["sample_poisson"] = parser.getfloat("calibration", "reference_poisson", fallback=defaults["sample_poisson"])
        return defaults

    def update_readiness_summary(self):
        if not self.readiness_text:
            return

        checks = [
            ("Calibration selected", self.calibration_source is not None),
            ("Experiment file selected", bool(self.file_path_edit and self.file_path_edit.text())),
            ("Sample name entered", bool(self.sample_name_edit and self.sample_name_edit.text().strip())),
            ("Poisson ratio set", self.sample_poisson_spinbox is not None),
            ("Fitting method selected", self.fitting_method_combo is not None)
        ]
        lines = ["Before running analysis, confirm these items:"]
        for label, ok in checks:
            lines.append(f"{'✅' if ok else '⬜'} {label}")

        if self.sample_name_edit:
            lines.append(f"\nSample: {self.sample_name_edit.text().strip() or 'not provided'}")
        if self.research_goal_combo:
            lines.append(f"Goal: {self.research_goal_combo.currentText()}")
        if self.sample_poisson_spinbox:
            lines.append(f"Poisson ratio: {self.sample_poisson_spinbox.value():.3f}")
        if self.indenter_combo:
            lines.append(f"Indenter: {self.indenter_combo.currentText()}")
        if self.fitting_method_combo:
            lines.append(f"Fitting method: {self.fitting_method_combo.currentText()}")
        if self.fit_curve_percent_spinbox:
            lines.append(f"Fit curve percentage used (loading+unloading): {self.fit_curve_percent_spinbox.value():.1f}%")

        self.readiness_text.setPlainText("\n".join(lines))

    def update_calibration_status(self):
        if not self.calibration_status_text:
            return

        C = [self.calibration_coefficients.get(f'C{i}', 0.0) for i in range(9)]
        c0_dev = abs(C[0] - 24.5) / 24.5 * 100
        n_corrections = sum(1 for c in C[1:] if abs(c) > 1e-10)

        if c0_dev < 1 and n_corrections == 0:
            quality = "EXCELLENT  (ideal Berkovich geometry)"
        elif c0_dev < 5:
            quality = f"GOOD  (C0 within {c0_dev:.1f}% of ideal, {n_corrections} correction term(s) active)"
        elif c0_dev < 15:
            quality = f"FAIR  (C0 deviates {c0_dev:.1f}% from ideal, {n_corrections} correction term(s) active)"
        else:
            quality = f"REVIEW NEEDED  (C0 deviates {c0_dev:.1f}% from ideal)"

        coeff_lines = []
        descriptions = [
            "Main area scaling  (ideal = 24.5 for Berkovich)",
            "Linear correction   (tip rounding / blunting)",
            "hc^0.5 correction  (shallow-depth regime)",
            "hc^0.25 correction",
            "hc^0.125 correction",
            "hc^0.0625 correction",
            "hc^0.03 correction",
            "hc^0.016 correction",
            "hc^0.008 correction",
        ]
        for i in range(9):
            val = C[i]
            flag = "  ← non-zero" if i > 0 and abs(val) > 1e-10 else ""
            coeff_lines.append(f"  C{i} = {val:>14.6g}    {descriptions[i]}{flag}")

        file_display = self.calibration_file_path or "not saved / not loaded from file"
        self.calibration_status_text.setPlainText(
            f"Source : {self.calibration_source}\n"
            f"File   : {file_display}\n"
            f"Quality: {quality}\n\n"
            "Area function  A(hc) = C0·hc² + C1·hc + C2·hc^0.5 + … + C8·hc^0.008\n"
            + "\n".join(coeff_lines) +
            "\n\nSee 'Calibration Profile' tab on the right for a visual reliability assessment."
        )

    def show_calibration_reliability_plot(self):
        """Render a 4-panel reliability chart for the active calibration in the right panel."""
        if not self.calibration_plot_widget:
            return

        C = [self.calibration_coefficients.get(f'C{i}', 0.0) for i in range(9)]
        exponents = [2, 1, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625, 0.0078125]

        hc = np.linspace(1, 2000, 600)  # contact depth range in nm
        A_loaded = sum(C[i] * hc ** exponents[i] for i in range(9))
        A_ideal = 24.5 * hc ** 2          # perfect Berkovich geometry
        deviation_pct = (A_loaded - A_ideal) / A_ideal * 100
        max_dev = float(np.max(np.abs(deviation_pct)))

        fig = self.calibration_plot_widget.figure
        fig.clear()
        fig.patch.set_facecolor('#f8f9fa')

        ax1 = fig.add_subplot(2, 2, 1)
        ax2 = fig.add_subplot(2, 2, 2)
        ax3 = fig.add_subplot(2, 2, 3)
        ax4 = fig.add_subplot(2, 2, 4)

        # ── Panel 1: Area function curve ──────────────────────────────────
        ax1.plot(hc, A_ideal / 1e6, 'k--', linewidth=1.5, alpha=0.55,
                 label='Ideal Berkovich  (C0=24.5, rest=0)')
        ax1.plot(hc, A_loaded / 1e6, color='steelblue', linewidth=2.2,
                 label='Loaded calibration')
        ax1.set_xlabel('Contact Depth  hc (nm)')
        ax1.set_ylabel('Projected Area  A  (µm²)')
        ax1.set_title('Tip Area Function  A(hc)\nLoaded vs. Ideal Geometry', fontweight='bold')
        ax1.legend(fontsize=8)
        ax1.grid(True, alpha=0.3)

        # ── Panel 2: % deviation from ideal ───────────────────────────────
        pos_mask = deviation_pct >= 0
        ax2.fill_between(hc, deviation_pct, 0,
                         where=pos_mask, alpha=0.25, color='tomato', label='Above ideal')
        ax2.fill_between(hc, deviation_pct, 0,
                         where=~pos_mask, alpha=0.25, color='steelblue', label='Below ideal')
        ax2.plot(hc, deviation_pct, color='darkorange', linewidth=1.8)
        ax2.axhline(0,  color='black',  linestyle='--', linewidth=0.9, alpha=0.6)
        ax2.axhline(5,  color='red',    linestyle=':',  linewidth=1.0, alpha=0.7)
        ax2.axhline(-5, color='red',    linestyle=':',  linewidth=1.0, alpha=0.7, label='±5 % threshold')
        ax2.set_xlabel('Contact Depth  hc (nm)')
        ax2.set_ylabel('Deviation from Ideal  (%)')
        ax2.set_title('Deviation from Perfect Geometry\n0 % = tip matches ideal Berkovich exactly',
                      fontweight='bold')
        ax2.legend(fontsize=8)
        ax2.grid(True, alpha=0.3)

        # ── Panel 3: Coefficient bar chart ────────────────────────────────
        coeff_names = [f'C{i}' for i in range(9)]
        colors = ['#2980b9' if v >= 0 else '#e74c3c' for v in C]
        ax3.bar(coeff_names, C, color=colors, edgecolor='black', linewidth=0.6)
        ax3.axhline(0, color='black', linewidth=0.8)
        ax3.set_xlabel('Coefficient  (C0 … C8)')
        ax3.set_ylabel('Value')
        ax3.set_title('Area Function Coefficients\nC0 dominates; C1–C8 correct for tip imperfection',
                      fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='y')
        # annotate each bar with its value
        for idx, (name, val) in enumerate(zip(coeff_names, C)):
            if abs(val) > 1e-10:
                ax3.annotate(f'{val:.3g}', xy=(idx, val),
                             ha='center', va='bottom' if val >= 0 else 'top',
                             fontsize=7, color='black')

        # ── Panel 4: Quality summary table ────────────────────────────────
        ax4.axis('off')
        n_active = sum(1 for c in C[1:] if abs(c) > 1e-10)
        c0_dev_pct = abs(C[0] - 24.5) / 24.5 * 100

        if max_dev < 2 and c0_dev_pct < 1:
            verdict, verdict_color = 'EXCELLENT', '#27ae60'
        elif max_dev < 10:
            verdict, verdict_color = 'GOOD', '#2ecc71'
        elif max_dev < 20:
            verdict, verdict_color = 'FAIR', '#e67e22'
        else:
            verdict, verdict_color = 'REVIEW NEEDED', '#e74c3c'

        rows = [
            ['C0  (primary scale)', f'{C[0]:.4f}', '24.5 (ideal)', f'{c0_dev_pct:.2f} % from ideal'],
            ['Active corrections\n(C1 – C8)',       f'{n_active} / 8',  '0 = pure ideal',   'Higher = more tip wear'],
            ['Max area deviation\n(0–2000 nm)',     f'{max_dev:.2f} %', '< 5 % preferred',  'Across full depth range'],
            ['Overall verdict',                     verdict,            '',                  'See colour →'],
        ]
        col_labels = ['Metric', 'Your Value', 'Reference', 'Interpretation']
        tbl = ax4.table(cellText=rows, colLabels=col_labels,
                        loc='center', cellLoc='center')
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(8.5)
        tbl.scale(1, 2.1)

        for (r, c_idx), cell in tbl.get_celld().items():
            cell.set_edgecolor('#cccccc')
            if r == 0:
                cell.set_facecolor('#2c3e50')
                cell.get_text().set_color('white')
                cell.get_text().set_fontweight('bold')
            elif r == len(rows) and c_idx == 1:
                cell.set_facecolor(verdict_color)
                cell.get_text().set_color('white')
                cell.get_text().set_fontweight('bold')
            elif r % 2 == 0:
                cell.set_facecolor('#f0f4f8')

        ax4.set_title('Calibration Quality Assessment', fontweight='bold', pad=12)

        # ── Overall figure title ───────────────────────────────────────────
        fname = Path(self.calibration_file_path).name if self.calibration_file_path else 'manual / default'
        fig.suptitle(
            f'Calibration Reliability  —  {self.calibration_source}  |  {fname}',
            fontsize=11, fontweight='bold', y=0.99
        )
        fig.tight_layout(rect=[0, 0, 1, 0.97])
        self.calibration_plot_widget.canvas.draw()

        # Switch focus to this tab
        if self.results_panel_tabs:
            for i in range(self.results_panel_tabs.count()):
                if self.results_panel_tabs.tabText(i).startswith('🔧'):
                    self.results_panel_tabs.setCurrentIndex(i)
                    break

    def unlock_workflow_step(self, step_index: int, move_to_step: bool = False):
        if not self.workflow_tabs:
            return
        if 0 <= step_index < self.workflow_tabs.count():
            self.workflow_tabs.setTabEnabled(step_index, True)
            if move_to_step:
                self.workflow_tabs.setCurrentIndex(step_index)

    def confirm_current_calibration(self):
        if self.calibration_source == "Default Berkovich":
            self.calibration_source = "Default Berkovich (confirmed by user)"
            self.update_calibration_status()
        self.update_readiness_summary()
        self.unlock_workflow_step(1, move_to_step=True)
        self.status_bar.showMessage("Step 1 completed. Continue to Step 2: Load experiment file.")

    def apply_manual_coefficients(self):
        try:
            for key, widget in self.manual_coeff_inputs.items():
                self.calibration_coefficients[key] = float(widget.value())
            self.calibration_source = "Manual entry"
            self.calibration_file_path = None
            self.update_calibration_status()
            self.show_calibration_reliability_plot()
            self.log_widget.append("✅ Manual calibration coefficients applied")
            self.update_readiness_summary()
            self.unlock_workflow_step(1, move_to_step=False)
            self.status_bar.showMessage("Calibration applied. See 'Calibration Profile' tab on the right for reliability assessment.")
        except Exception as e:
            QMessageBox.critical(self, "Calibration Error", f"Failed to apply manual coefficients:\n{str(e)}")

    def load_calibration_file(self):
        samples_dir = str(Path(__file__).resolve().parent.parent.parent / "samples")
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Calibration File",
            samples_dir,
            "Calibration Files (*.json *.csv);;All Files (*)"
        )
        if not file_path:
            return

        try:
            loaded_coeffs = self.get_default_calibration_coefficients()
            if file_path.lower().endswith(".json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                source_coeffs = payload.get("coefficients", payload)
                for key in loaded_coeffs:
                    if key in source_coeffs:
                        loaded_coeffs[key] = float(source_coeffs[key])
            else:
                df = pd.read_csv(file_path)
                if "Coefficient" in df.columns and "Value" in df.columns:
                    for _, row in df.iterrows():
                        k = str(row["Coefficient"]).strip()
                        if k in loaded_coeffs:
                            loaded_coeffs[k] = float(row["Value"])
                else:
                    for key in loaded_coeffs:
                        if key in df.columns and len(df[key]) > 0:
                            loaded_coeffs[key] = float(df[key].iloc[0])

            self.calibration_coefficients = loaded_coeffs
            self.calibration_source = "Loaded from calibration file"
            self.calibration_file_path = file_path
            for key, widget in self.manual_coeff_inputs.items():
                widget.setValue(self.calibration_coefficients.get(key, 0.0))
            self.update_calibration_status()
            self.show_calibration_reliability_plot()
            self.update_readiness_summary()
            self.log_widget.append(f"✅ Calibration loaded from file: {file_path}")
            self.unlock_workflow_step(1, move_to_step=False)
            self.status_bar.showMessage("Calibration loaded. See 'Calibration Profile' tab on the right for reliability assessment.")
        except Exception as e:
            QMessageBox.critical(self, "Calibration Error", f"Failed to load calibration file:\n{str(e)}")

    def save_calibration_file(self):
        default_name = "calibration_profile.json"
        samples_dir = str(Path(__file__).resolve().parent.parent.parent / "samples")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Calibration File",
            str(Path(samples_dir) / default_name),
            "JSON Files (*.json);;CSV Files (*.csv)"
        )
        if not file_path:
            return

        try:
            output = {
                "source": self.calibration_source,
                "saved_at": datetime.now().isoformat(),
                "coefficients": self.calibration_coefficients
            }

            if file_path.lower().endswith(".csv"):
                pd.DataFrame(
                    [{"Coefficient": k, "Value": v} for k, v in self.calibration_coefficients.items()]
                ).to_csv(file_path, index=False)
            else:
                if not file_path.lower().endswith(".json"):
                    file_path += ".json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(output, f, indent=2)

            self.calibration_file_path = file_path
            self.update_calibration_status()
            self.log_widget.append(f"💾 Calibration saved: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Calibration Error", f"Failed to save calibration file:\n{str(e)}")

    def generate_calibration_from_silica(self):
        samples_dir = str(Path(__file__).resolve().parent.parent.parent / "samples")
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Standard Silica XLS/XLSX File",
            samples_dir,
            "Excel Files (*.xls *.xlsx);;All Files (*)"
        )
        if not file_path:
            return
        if not self.nist_calibrator:
            QMessageBox.critical(self, "Calibration Error", "NIST calibration module is not available.")
            return

        try:
            self.status_bar.showMessage("Generating calibration from standard silica file...")
            calibration = self.nist_calibrator.extract_tip_coefficients_from_file(file_path, "fused_silica")
            if not calibration.get("valid", False):
                errors_list = calibration.get("errors", [])
                if not errors_list:
                    errors_list = calibration.get("warnings", ["Unknown calibration failure"])
                errors = "\n".join(errors_list)
                raise ValueError(errors)

            coeffs = self.get_default_calibration_coefficients()
            coeffs["C0"] = float(calibration["coefficients"].get("C0_nm2_per_nm2", coeffs["C0"]))
            # Show/use silica-generated tiny correction terms in SI-style magnitude,
            # matching researcher expectation for near-perfect Berkovich calibration.
            coeffs["C1"] = float(
                calibration["coefficients"].get(
                    "C1_SI",
                    calibration["coefficients"].get("C1_nm2_per_nm", coeffs["C1"])
                )
            )
            coeffs["C2"] = float(
                calibration["coefficients"].get(
                    "C2_SI",
                    calibration["coefficients"].get("C2_nm2_per_nm05", coeffs["C2"])
                )
            )
            self.calibration_coefficients = coeffs
            self.calibration_source = "Generated from standard silica file"
            self.calibration_file_path = str(Path(file_path).resolve())
            for key, widget in self.manual_coeff_inputs.items():
                widget.setValue(self.calibration_coefficients.get(key, 0.0))
            self.update_calibration_status()
            self.show_calibration_reliability_plot()
            self.update_readiness_summary()

            r2 = calibration.get("quality_metrics", {}).get("r_squared", 0.0)
            npts = calibration.get("quality_metrics", {}).get("n_data_points", 0)
            self.log_widget.append(
                f"✅ Calibration generated from silica file: {Path(file_path).name} "
                f"(R²={r2:.4f}, points={npts})"
            )
            # Auto-run analysis on the same silica file using the newly generated calibration
            self.file_path_edit.setText(str(Path(file_path).resolve()))
            self.reload_button.setEnabled(True)
            self.analyze_button.setEnabled(True)
            self.step2_next_button.setEnabled(True)
            self.pending_analysis_context = (
                f"Calibration self-check on file: {Path(file_path).name}"
            )
            self.unlock_workflow_step(1, move_to_step=False)
            self.unlock_workflow_step(2, move_to_step=False)
            self.unlock_workflow_step(3, move_to_step=False)
            self.log_widget.append("🔁 Auto-run: analyzing the same silica file with the new calibration...")
            self.status_bar.showMessage("Calibration generated. Running analysis on the same silica file...")
            self.start_analysis()
        except Exception as e:
            QMessageBox.critical(self, "Calibration Error", f"Failed to generate calibration:\n{str(e)}")
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Nanoindentation Analysis - ISO 14577-4:2016 Compliant")
        self.setMinimumSize(1400, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create header
        header_layout = self.create_header()
        main_layout.addLayout(header_layout)
        
        # Create splitter for main content
        main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Left panel - Controls
        left_panel = self.create_control_panel()
        main_splitter.addWidget(left_panel)
        
        # Right panel - Results and plots
        right_panel = self.create_results_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([400, 1000])
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready - Select an Excel file to begin analysis")
        
        # Progress bar in status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
    
    def create_header(self):
        """Create the header section"""
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("🔬 Nanoindentation Analysis Suite")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 8px;
                margin: 5px;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("ISO 14577-4:2016 Compliant • Advanced Tip Calibration • Oliver-Pharr Method")
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #7f8c8d;
                padding: 5px;
                text-align: center;
            }
        """)
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)
        
        return layout
    
    def create_control_panel(self):
        """Create the control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        self.workflow_tabs = QTabWidget()

        # STEP 1: Calibration — wrapped in a scroll area so nothing is hidden
        step1_outer = QWidget()
        step1_outer_layout = QVBoxLayout(step1_outer)
        step1_outer_layout.setContentsMargins(0, 0, 0, 0)

        step1_scroll = QScrollArea()
        step1_scroll.setWidgetResizable(True)
        step1_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        step1_scroll.setFrameShape(QFrame.NoFrame)

        step1_inner = QWidget()
        step1_layout = QVBoxLayout(step1_inner)
        step1_layout.setSpacing(8)
        step1_layout.setContentsMargins(6, 6, 6, 6)

        step1_intro = QLabel(
            "<b>Step 1 of 5 — Tip Area Function Calibration</b><br>"
            "A(h<sub>c</sub>) converts contact depth to projected contact area "
            "(ISO 14577-1:2015 §4.2). Choose one option:"
        )
        step1_intro.setWordWrap(True)
        step1_intro.setTextFormat(Qt.RichText)
        step1_layout.addWidget(step1_intro)

        # ── Option A ──────────────────────────────────────────────────────
        load_group = QGroupBox("Option A — Load a previously saved calibration profile")
        load_group_layout = QVBoxLayout(load_group)
        load_group_layout.setSpacing(4)
        lbl_a = QLabel(
            "Use this when you have a validated .json or .csv file\n"
            "from a prior session on a reference material (e.g. fused silica)."
        )
        lbl_a.setWordWrap(True)
        load_group_layout.addWidget(lbl_a)
        self.load_calibration_button = QPushButton("Load Calibration File  (.json / .csv)")
        self.load_calibration_button.setToolTip("Load a JSON or CSV file containing C0...C8 coefficients.")
        self.load_calibration_button.clicked.connect(self.load_calibration_file)
        load_group_layout.addWidget(self.load_calibration_button)
        step1_layout.addWidget(load_group)

        # ── Option B ──────────────────────────────────────────────────────
        gen_group = QGroupBox("Option B — Generate calibration from a reference indentation file")
        gen_group_layout = QVBoxLayout(gen_group)
        gen_group_layout.setSpacing(4)
        lbl_b = QLabel(
            "Use this when you have raw XLS/XLSX indentations on fused silica\n"
            "(E = 72 GPa, v = 0.17). Coefficients C0...C8 are fitted automatically;\n"
            "the same file is then re-analysed as a built-in self-check."
        )
        lbl_b.setWordWrap(True)
        gen_group_layout.addWidget(lbl_b)
        self.generate_calibration_button = QPushButton("Generate from Fused-Silica XLS/XLSX")
        self.generate_calibration_button.setToolTip(
            "Select an XLS/XLSX file of indentations on fused silica reference material.")
        self.generate_calibration_button.clicked.connect(self.generate_calibration_from_silica)
        gen_group_layout.addWidget(self.generate_calibration_button)
        step1_layout.addWidget(gen_group)

        # ── Option C ──────────────────────────────────────────────────────
        manual_group = QGroupBox("Option C — Enter coefficients manually  (lab protocol / instrument software)")
        manual_layout = QGridLayout(manual_group)
        manual_layout.setSpacing(4)
        manual_layout.setColumnStretch(1, 1)
        manual_layout.setColumnStretch(3, 1)

        coeff_tooltips = [
            "C0 · hc2  —  primary term; ideal Berkovich = 24.5",
            "C1 · hc   —  linear correction (tip rounding/blunting)",
            "C2 · hc^0.5  —  dominant at shallow depths",
            "C3 · hc^0.25",
            "C4 · hc^0.125",
            "C5 · hc^0.0625",
            "C6 · hc^0.03125",
            "C7 · hc^0.016",
            "C8 · hc^0.008",
        ]
        # 2 coefficients per row → 5 rows (row 4 has only C8)
        for idx in range(9):
            key = f"C{idx}"
            row, col_pair = divmod(idx, 2)
            label = QLabel(f"<b>{key}</b>")
            label.setTextFormat(Qt.RichText)
            label.setToolTip(coeff_tooltips[idx])
            label.setFixedWidth(26)
            spin = QDoubleSpinBox()
            spin.setDecimals(6)
            spin.setRange(-1e6, 1e6)
            spin.setSingleStep(0.1 if idx == 0 else 0.001)
            spin.setValue(self.calibration_coefficients.get(key, 0.0))
            spin.setMinimumWidth(120)
            spin.setToolTip(coeff_tooltips[idx])
            self.manual_coeff_inputs[key] = spin
            manual_layout.addWidget(label, row, col_pair * 2)
            manual_layout.addWidget(spin,  row, col_pair * 2 + 1)

        manual_buttons_layout = QHBoxLayout()
        self.apply_manual_button = QPushButton("Apply These Coefficients")
        self.apply_manual_button.setToolTip("Apply values and display reliability chart on the right.")
        self.apply_manual_button.clicked.connect(self.apply_manual_coefficients)
        manual_buttons_layout.addWidget(self.apply_manual_button)
        self.save_calibration_button = QPushButton("Save Profile to File")
        self.save_calibration_button.setToolTip("Save active coefficients as .json or .csv for future sessions.")
        self.save_calibration_button.clicked.connect(self.save_calibration_file)
        manual_buttons_layout.addWidget(self.save_calibration_button)
        manual_layout.addLayout(manual_buttons_layout, 5, 0, 1, 4)
        step1_layout.addWidget(manual_group)

        # ── Status summary ────────────────────────────────────────────────
        status_group = QGroupBox("Active calibration summary")
        status_group_layout = QVBoxLayout(status_group)
        self.calibration_status_text = QTextEdit()
        self.calibration_status_text.setReadOnly(True)
        self.calibration_status_text.setFixedHeight(120)
        self.calibration_status_text.setToolTip(
            "Quality summary of the active tip area function. "
            "See 'Calibration Profile' tab (right) for the full visual assessment.")
        status_group_layout.addWidget(self.calibration_status_text)
        step1_layout.addWidget(status_group)
        self.update_calibration_status()

        step1_layout.addStretch()

        step1_scroll.setWidget(step1_inner)
        step1_outer_layout.addWidget(step1_scroll)

        step1_next = QPushButton("Confirm Calibration and Continue to Step 2  ►")
        step1_next.setToolTip("Proceed once you are satisfied with the calibration shown above.")
        step1_next.clicked.connect(self.confirm_current_calibration)
        step1_outer_layout.addWidget(step1_next)

        self.workflow_tabs.addTab(step1_outer, "1. Calibration")

        # STEP 2: File selection
        step2 = QWidget()
        step2_layout = QVBoxLayout(step2)
        step2_layout.addWidget(QLabel(
            "Step 2 of 5: Research context + data file\n"
            "Question: What is your analysis goal and which sample file should be analyzed?"
        ))
        self.research_goal_combo = QComboBox()
        self.research_goal_combo.addItems([
            "Measure unknown sample properties",
            "Validate instrument on fused silica",
            "Compare multiple processing conditions"
        ])
        self.research_goal_combo.currentIndexChanged.connect(self.update_readiness_summary)
        step2_layout.addWidget(self.research_goal_combo)
        self.sample_name_edit = QLineEdit()
        self.sample_name_edit.setPlaceholderText("Sample name / ID (e.g., Ti64-HeatTreatment-A)")
        self.sample_name_edit.textChanged.connect(self.update_readiness_summary)
        step2_layout.addWidget(self.sample_name_edit)
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select experiment file...")
        self.file_path_edit.setReadOnly(True)
        step2_layout.addWidget(self.file_path_edit)
        file_button_layout = QHBoxLayout()
        self.browse_button = QPushButton("Browse File")
        self.browse_button.clicked.connect(self.browse_file)
        file_button_layout.addWidget(self.browse_button)
        self.reload_button = QPushButton("Reload")
        self.reload_button.clicked.connect(self.reload_file)
        self.reload_button.setEnabled(False)
        file_button_layout.addWidget(self.reload_button)
        step2_layout.addLayout(file_button_layout)
        self.step2_next_button = QPushButton("Continue to Analysis Settings ▶")
        self.step2_next_button.setEnabled(False)
        self.step2_next_button.clicked.connect(lambda: self.unlock_workflow_step(2, move_to_step=True))
        step2_layout.addWidget(self.step2_next_button)
        self.workflow_tabs.addTab(step2, "2. Load File")

        # STEP 3: Settings
        step3 = QWidget()
        step3_layout = QVBoxLayout(step3)
        step3_layout.addWidget(QLabel(
            "Step 3 of 5: Analysis parameters\n"
            "Question: What material assumptions and fitting strategy should be used?"
        ))
        settings_group = QGroupBox("Analysis Settings")
        settings_layout = QGridLayout(settings_group)
        self.generate_plots_cb = QCheckBox("Generate Plots")
        self.generate_plots_cb.setChecked(True)
        settings_layout.addWidget(self.generate_plots_cb, 0, 0)
        self.export_plots_cb = QCheckBox("Export Plot Images")
        self.export_plots_cb.setChecked(True)
        settings_layout.addWidget(self.export_plots_cb, 0, 1)
        settings_layout.addWidget(QLabel("Min R² for fits:"), 1, 0)
        self.min_r2_spinbox = QDoubleSpinBox()
        self.min_r2_spinbox.setRange(0.90, 0.999)
        self.min_r2_spinbox.setValue(float(self.config_values.get("min_r_squared", 0.98)))
        self.min_r2_spinbox.setDecimals(3)
        self.min_r2_spinbox.setSingleStep(0.001)
        settings_layout.addWidget(self.min_r2_spinbox, 1, 1)
        settings_layout.addWidget(QLabel("Percentage of unloading/loading curve used for calculations (%):"), 2, 0)
        self.fit_curve_percent_spinbox = QDoubleSpinBox()
        self.fit_curve_percent_spinbox.setRange(5.0, 100.0)
        self.fit_curve_percent_spinbox.setDecimals(1)
        self.fit_curve_percent_spinbox.setSingleStep(1.0)
        self.fit_curve_percent_spinbox.setValue(float(self.config_values.get("fit_curve_percent", 25.0)))
        self.fit_curve_percent_spinbox.valueChanged.connect(self.update_readiness_summary)
        settings_layout.addWidget(self.fit_curve_percent_spinbox, 2, 1)
        settings_layout.addWidget(QLabel("Sample Poisson ratio (ν):"), 3, 0)
        self.sample_poisson_spinbox = QDoubleSpinBox()
        self.sample_poisson_spinbox.setRange(0.0, 0.5)
        self.sample_poisson_spinbox.setDecimals(3)
        self.sample_poisson_spinbox.setSingleStep(0.01)
        self.sample_poisson_spinbox.setValue(float(self.config_values.get("sample_poisson", 0.30)))
        self.sample_poisson_spinbox.valueChanged.connect(self.update_readiness_summary)
        settings_layout.addWidget(self.sample_poisson_spinbox, 3, 1)
        settings_layout.addWidget(QLabel("Indenter material:"), 4, 0)
        self.indenter_combo = QComboBox()
        self.indenter_combo.addItems(["diamond", "sapphire"])
        default_indenter = str(self.config_values.get("default_indenter", "diamond")).lower()
        self.indenter_combo.setCurrentText(default_indenter if default_indenter in ["diamond", "sapphire"] else "diamond")
        self.indenter_combo.currentIndexChanged.connect(self.update_readiness_summary)
        settings_layout.addWidget(self.indenter_combo, 4, 1)
        settings_layout.addWidget(QLabel("Unloading fitting method:"), 5, 0)
        self.fitting_method_combo = QComboBox()
        self.fitting_method_combo.addItems(["oliver_pharr", "power_law", "auto"])
        default_method = str(self.config_values.get("default_fitting_method", "oliver_pharr")).lower()
        self.fitting_method_combo.setCurrentText(default_method if default_method in ["oliver_pharr", "power_law", "auto"] else "oliver_pharr")
        self.fitting_method_combo.currentIndexChanged.connect(self.update_readiness_summary)
        settings_layout.addWidget(self.fitting_method_combo, 5, 1)
        step3_layout.addWidget(settings_group)
        step3_next = QPushButton("Continue to Run Analysis ▶")
        step3_next.clicked.connect(lambda: self.unlock_workflow_step(3, move_to_step=True))
        step3_layout.addWidget(step3_next)
        self.workflow_tabs.addTab(step3, "3. Settings")

        # STEP 4: Results
        step4 = QWidget()
        step4_layout = QVBoxLayout(step4)
        step4_layout.addWidget(QLabel("Step 4 of 5: Results\nRun analysis and open each test plot from the list below."))
        self.readiness_text = QTextEdit()
        self.readiness_text.setReadOnly(True)
        self.readiness_text.setMinimumHeight(140)
        step4_layout.addWidget(self.readiness_text)
        self.analyze_button = QPushButton("🔬 Start Analysis")
        self.analyze_button.clicked.connect(self.start_analysis)
        self.analyze_button.setEnabled(False)
        step4_layout.addWidget(self.analyze_button)
        self.cancel_button = QPushButton("❌ Cancel Analysis")
        self.cancel_button.clicked.connect(self.cancel_analysis)
        self.cancel_button.setEnabled(False)
        step4_layout.addWidget(self.cancel_button)
        self.step4_next_button = QPushButton("Continue to Export Results ▶")
        self.step4_next_button.setEnabled(False)
        self.step4_next_button.clicked.connect(lambda: self.unlock_workflow_step(4, move_to_step=True))
        step4_layout.addWidget(self.step4_next_button)

        plot_buttons_group = QGroupBox("Open test plot (button = test name)")
        plot_buttons_group_layout = QVBoxLayout(plot_buttons_group)
        self.step4_plot_buttons_note = QLabel("Run analysis to populate test plot buttons.")
        self.step4_plot_buttons_note.setWordWrap(True)
        plot_buttons_group_layout.addWidget(self.step4_plot_buttons_note)

        plot_buttons_scroll = QScrollArea()
        plot_buttons_scroll.setWidgetResizable(True)
        plot_buttons_container = QWidget()
        self.step4_plot_buttons_layout = QGridLayout(plot_buttons_container)
        self.step4_plot_buttons_layout.setAlignment(Qt.AlignTop)
        self.step4_plot_buttons_layout.setHorizontalSpacing(8)
        self.step4_plot_buttons_layout.setVerticalSpacing(6)
        plot_buttons_scroll.setWidget(plot_buttons_container)
        plot_buttons_group_layout.addWidget(plot_buttons_scroll)
        step4_layout.addWidget(plot_buttons_group)

        self.workflow_tabs.addTab(step4, "4. Results")

        # STEP 5: Export
        step5 = QWidget()
        step5_layout = QVBoxLayout(step5)
        step5_layout.addWidget(QLabel("Step 5 of 5: Export final results after successful analysis."))
        self.export_excel_button = QPushButton("📊 Export to Excel")
        self.export_excel_button.clicked.connect(self.export_to_excel)
        self.export_excel_button.setEnabled(False)
        step5_layout.addWidget(self.export_excel_button)
        self.export_csv_button = QPushButton("📄 Export to CSV")
        self.export_csv_button.clicked.connect(self.export_to_csv)
        self.export_csv_button.setEnabled(False)
        step5_layout.addWidget(self.export_csv_button)
        help_text = QLabel(
            "Tip: Review Results Table and Plots tabs on the right before exporting.\n"
            "If needed, return to earlier workflow tabs to update settings and rerun."
        )
        help_text.setWordWrap(True)
        step5_layout.addWidget(help_text)
        self.workflow_tabs.addTab(step5, "5. Export")

        # lock workflow to strict sequential progression
        for idx in range(1, self.workflow_tabs.count()):
            self.workflow_tabs.setTabEnabled(idx, False)
        self.workflow_tabs.setCurrentIndex(0)
        self.update_readiness_summary()

        layout.addWidget(self.workflow_tabs)
        return panel
    
    def create_results_panel(self):
        """Create the results panel with tabs"""
        tab_widget = QTabWidget()
        self.results_panel_tabs = tab_widget

        # Calibration profile tab — populated when calibration is applied
        self.calibration_plot_widget = MatplotlibWidget()
        tab_widget.addTab(self.calibration_plot_widget, "🔧 Calibration Profile")
        self._draw_calibration_placeholder()

        # Results table tab
        self.results_table = ResultsTableWidget()
        tab_widget.addTab(self.results_table, "📊 Results Table")

        # Plot tabs container - this will hold subtabs for each test
        self.plots_tab_widget = QTabWidget()
        tab_widget.addTab(self.plots_tab_widget, "📈 Test Plots")

        # Log tab
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        log_font = QFont()
        log_font.setFamily("Monaco")
        log_font.setStyleHint(QFont.Monospace)
        log_font.setPointSize(9)
        self.log_widget.setFont(log_font)
        tab_widget.addTab(self.log_widget, "📝 Analysis Log")

        return tab_widget

    def _draw_calibration_placeholder(self):
        """Show an instructional placeholder in the calibration plot tab."""
        if not self.calibration_plot_widget:
            return
        fig = self.calibration_plot_widget.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.axis('off')
        ax.text(
            0.5, 0.6,
            "Calibration Profile",
            ha='center', va='center', fontsize=18, fontweight='bold',
            transform=ax.transAxes, color='#2c3e50'
        )
        ax.text(
            0.5, 0.45,
            "Load a calibration file or apply coefficients in Step 1\n"
            "to see the tip area function, deviation from ideal Berkovich,\n"
            "coefficient magnitudes, and an overall quality assessment.",
            ha='center', va='center', fontsize=11,
            transform=ax.transAxes, color='#555555'
        )
        self.calibration_plot_widget.canvas.draw()
    
    def get_stylesheet(self):
        """Return the application stylesheet - Dark Mode"""
        return """
            /* Main Window Dark Theme */
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            
            /* All widgets get dark background and light text */
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            
            /* Group Boxes */
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #353535;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ffffff;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #0d7377;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #14a085;
            }
            QPushButton:pressed {
                background-color: #0a5d61;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
            
            /* Input Fields */
            QLineEdit {
                border: 2px solid #555555;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
                background-color: #404040;
                color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #0d7377;
            }
            
            /* Spin Boxes */
            QSpinBox, QDoubleSpinBox {
                border: 2px solid #555555;
                border-radius: 4px;
                padding: 4px;
                background-color: #404040;
                color: #ffffff;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #0d7377;
            }
            
            /* Combo Boxes */
            QComboBox {
                border: 2px solid #555555;
                border-radius: 4px;
                padding: 4px;
                background-color: #404040;
                color: #ffffff;
            }
            QComboBox:focus {
                border-color: #0d7377;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #555555;
            }
            QComboBox::down-arrow {
                border: none;
                background-color: transparent;
            }
            
            /* Tab Widget */
            QTabWidget::pane {
                border: 1px solid #555555;
                border-radius: 4px;
                background-color: #353535;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border: 1px solid #555555;
            }
            QTabBar::tab:selected {
                background-color: #0d7377;
                color: white;
                border-bottom: none;
            }
            QTabBar::tab:hover {
                background-color: #555555;
            }
            
            /* Text Areas */
            QTextEdit {
                border: 2px solid #555555;
                border-radius: 4px;
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', 'Monaco', monospace;
            }
            
            /* Tables */
            QTableWidget {
                border: 1px solid #555555;
                background-color: #353535;
                alternate-background-color: #404040;
                color: #ffffff;
                gridline-color: #555555;
            }
            QTableWidget::item {
                padding: 4px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #0d7377;
                color: white;
            }
            QHeaderView::section {
                background-color: #404040;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #555555;
                font-weight: bold;
            }
            
            /* Progress Bar */
            QProgressBar {
                border: 2px solid #555555;
                border-radius: 4px;
                background-color: #404040;
                color: #ffffff;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0d7377;
                border-radius: 2px;
            }
            
            /* Check Boxes */
            QCheckBox {
                color: #ffffff;
                spacing: 4px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #555555;
                border-radius: 3px;
                background-color: #404040;
            }
            QCheckBox::indicator:checked {
                background-color: #0d7377;
                border-color: #0d7377;
            }
            
            /* Labels */
            QLabel {
                color: #ffffff;
            }
            
            /* Scrollbars */
            QScrollBar:vertical {
                background-color: #404040;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #0d7377;
            }
            QScrollBar:horizontal {
                background-color: #404040;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #555555;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #0d7377;
            }
            
            /* Status Bar */
            QStatusBar {
                background-color: #353535;
                color: #ffffff;
                border-top: 1px solid #555555;
            }
            
            /* Splitter */
            QSplitter::handle {
                background-color: #555555;
            }
            QSplitter::handle:horizontal {
                width: 2px;
            }
            QSplitter::handle:vertical {
                height: 2px;
            }
            
            /* Matplotlib Canvas - Keep white background */
            QWidget[objectName="qt_scrollarea_viewport"] {
                background-color: white;
            }
            
            /* Navigation Toolbar for matplotlib */
            QToolBar {
                background-color: #404040;
                border: 1px solid #555555;
                color: #ffffff;
            }
            QToolBar QToolButton {
                background-color: transparent;
                color: #ffffff;
                border: none;
                padding: 4px;
            }
            QToolBar QToolButton:hover {
                background-color: #555555;
            }
        """
    
    def center_window(self):
        """Center the window on the screen"""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
    
    def clear_plot_tabs(self):
        """Clear all existing plot tabs"""
        while self.plots_tab_widget.count() > 0:
            widget = self.plots_tab_widget.widget(0)
            self.plots_tab_widget.removeTab(0)
            if widget:
                widget.deleteLater()

    def clear_step4_plot_buttons(self):
        """Clear all test-plot buttons in Step 4."""
        if self.step4_plot_buttons_layout is None:
            return
        while self.step4_plot_buttons_layout.count() > 0:
            item = self.step4_plot_buttons_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def populate_step4_plot_buttons(self, results: List[Dict[str, Any]]):
        """Populate Step 4 with one button per test result."""
        self.clear_step4_plot_buttons()
        if self.step4_plot_buttons_layout is None:
            return

        if self.step4_plot_buttons_note:
            self.step4_plot_buttons_note.setText(
                "Click a test name to open its plot on the right."
            )

        buttons_per_row = 3
        for idx, result in enumerate(results):
            test_name = str(result.get('Test', f'Test {idx + 1}'))
            button = QPushButton(test_name)
            button.clicked.connect(lambda _checked=False, result_index=idx: self.open_test_plot_from_step4(result_index))
            row = idx // buttons_per_row
            col = idx % buttons_per_row
            self.step4_plot_buttons_layout.addWidget(button, row, col)

    def open_test_plot_from_step4(self, result_index: int):
        """Open (or focus) the selected test plot on the right panel."""
        if result_index < 0 or result_index >= len(self.current_results):
            return
        if self.plots_tab_widget is None:
            return

        result = self.current_results[result_index]
        test_name = str(result.get('Test', f'Test {result_index + 1}'))
        tab_name = test_name

        existing_index = -1
        for i in range(self.plots_tab_widget.count()):
            if self.plots_tab_widget.tabText(i) == tab_name:
                existing_index = i
                break

        if existing_index == -1:
            plot_widget = MatplotlibWidget()
            try:
                plot_widget.plot_nanoindentation_curve(self.analyzer, result)
            except Exception as e:
                self.log_widget.append(f"⚠️ Error plotting {tab_name}: {str(e)}")
                return
            existing_index = self.plots_tab_widget.addTab(plot_widget, tab_name)

        if self.results_panel_tabs and self.plots_tab_widget:
            self.results_panel_tabs.setCurrentWidget(self.plots_tab_widget)
        self.plots_tab_widget.setCurrentIndex(existing_index)
    
    def create_plot_tabs(self, results: List[Dict[str, Any]]):
        """Create summary plot and prepare per-test plots for on-demand opening."""
        self.clear_plot_tabs()
        
        if not results:
            # Add a placeholder tab if no results
            placeholder = QLabel("No plots available")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("color: #888888; font-size: 14px;")
            self.plots_tab_widget.addTab(placeholder, "No Data")
            self.clear_step4_plot_buttons()
            if self.step4_plot_buttons_note:
                self.step4_plot_buttons_note.setText("No analysis results available yet.")
            return
        
        # Create summary tab first
        self.create_summary_plot_tab(results)
        self.populate_step4_plot_buttons(results)
        self.log_widget.append(f"📊 Summary plot ready. Use Step 4 test buttons to open individual plots.")
    
    def create_summary_plot_tab(self, results: List[Dict[str, Any]]):
        """Create a 4-panel reliability benchmark summary for all tests in the dataset."""
        summary_widget = MatplotlibWidget()

        try:
            fig = summary_widget.figure
            fig.clear()
            fig.patch.set_facecolor('#f8f9fa')

            file_label = Path(self.current_analysis_file_path).name if self.current_analysis_file_path else (
                results[0].get('Source File', 'selected file') if results else 'selected file'
            )
            n_tests = len(results)
            fig.suptitle(
                f'Analysis Reliability Benchmarks  —  {file_label}  ({n_tests} test(s))',
                fontsize=13, fontweight='bold', y=0.99
            )

            hardness_values = [r.get('Hardness (GPa)', 0) for r in results if r.get('Hardness (GPa)')]
            modulus_values  = [r.get('Oliver-Pharr Modulus (GPa)', 0) for r in results if r.get('Oliver-Pharr Modulus (GPa)')]
            loading_r2      = [r.get('Loading R²', 0) for r in results if r.get('Loading R²')]
            unloading_r2    = [r.get('Unloading Fit R²', 0) for r in results if r.get('Unloading Fit R²')]

            ax1 = fig.add_subplot(2, 2, 1)
            ax2 = fig.add_subplot(2, 2, 2)
            ax3 = fig.add_subplot(2, 2, 3)
            ax4 = fig.add_subplot(2, 2, 4)

            # ── Hardness distribution ─────────────────────────────────────
            if hardness_values:
                ax1.hist(hardness_values, bins=min(10, len(hardness_values)),
                         alpha=0.72, color='#2980b9', edgecolor='white')
                mu_h, sd_h = np.mean(hardness_values), np.std(hardness_values)
                ax1.axvline(mu_h, color='#e74c3c', linewidth=1.8, linestyle='--', label=f'Mean {mu_h:.2f} GPa')
                ax1.set_xlabel('Hardness  H  (GPa)  [ISO 14577-1 §4.1]')
                ax1.set_ylabel('Number of tests')
                ax1.set_title(
                    f'Hardness Distribution\n'
                    f'Mean {mu_h:.2f} ± {sd_h:.2f} GPa   CV = {sd_h/mu_h*100:.1f} %' if mu_h else
                    'Hardness Distribution', fontweight='bold'
                )
                ax1.legend(fontsize=8)
                ax1.grid(True, alpha=0.3)
            else:
                ax1.text(0.5, 0.5, 'No hardness data', ha='center', va='center',
                         transform=ax1.transAxes, color='grey')
                ax1.set_title('Hardness Distribution', fontweight='bold')

            # ── Reduced modulus distribution ──────────────────────────────
            if modulus_values:
                ax2.hist(modulus_values, bins=min(10, len(modulus_values)),
                         alpha=0.72, color='#27ae60', edgecolor='white')
                mu_e, sd_e = np.mean(modulus_values), np.std(modulus_values)
                ax2.axvline(mu_e, color='#e74c3c', linewidth=1.8, linestyle='--', label=f'Mean {mu_e:.1f} GPa')
                ax2.set_xlabel('Reduced Modulus  Er  (GPa)  [ISO 14577-1 §4.2]')
                ax2.set_ylabel('Number of tests')
                ax2.set_title(
                    f'Reduced Modulus Distribution\n'
                    f'Mean {mu_e:.1f} ± {sd_e:.1f} GPa   CV = {sd_e/mu_e*100:.1f} %' if mu_e else
                    'Reduced Modulus Distribution', fontweight='bold'
                )
                ax2.legend(fontsize=8)
                ax2.grid(True, alpha=0.3)
            else:
                ax2.text(0.5, 0.5, 'No modulus data', ha='center', va='center',
                         transform=ax2.transAxes, color='grey')
                ax2.set_title('Reduced Modulus Distribution', fontweight='bold')

            # ── Loading curve fit quality (R²) ────────────────────────────
            if loading_r2:
                idx_list = list(range(1, len(loading_r2) + 1))
                colors_l = ['#e74c3c' if v < 0.99 else '#2980b9' for v in loading_r2]
                ax3.bar(idx_list, loading_r2, color=colors_l, width=0.7, edgecolor='none')
                ax3.axhline(0.99, color='orange', linestyle='--', linewidth=1.2, label='R² = 0.99 threshold')
                ax3.axhline(1.00, color='black',  linestyle='-',  linewidth=0.6, alpha=0.4)
                ax3.set_xlabel('Test index')
                ax3.set_ylabel('Loading curve  R²')
                ax3.set_title(
                    f'Loading Fit Quality  (R²)\n'
                    f'Mean {np.mean(loading_r2):.4f}   Min {np.min(loading_r2):.4f}'
                    f'   {"✓ all ≥ 0.99" if all(v >= 0.99 for v in loading_r2) else "⚠ some below 0.99"}',
                    fontweight='bold'
                )
                ax3.set_ylim(max(0.95, min(loading_r2) - 0.01), 1.002)
                ax3.legend(fontsize=8)
                ax3.grid(True, alpha=0.3, axis='y')
            else:
                ax3.text(0.5, 0.5, 'No loading R² data', ha='center', va='center',
                         transform=ax3.transAxes, color='grey')
                ax3.set_title('Loading Fit Quality', fontweight='bold')

            # ── Unloading curve fit quality (R²) ──────────────────────────
            if unloading_r2:
                idx_list = list(range(1, len(unloading_r2) + 1))
                colors_u = ['#e74c3c' if v < 0.99 else '#e67e22' for v in unloading_r2]
                ax4.bar(idx_list, unloading_r2, color=colors_u, width=0.7, edgecolor='none')
                ax4.axhline(0.99, color='steelblue', linestyle='--', linewidth=1.2, label='R² = 0.99 threshold')
                ax4.axhline(1.00, color='black',     linestyle='-',  linewidth=0.6, alpha=0.4)
                ax4.set_xlabel('Test index')
                ax4.set_ylabel('Unloading curve  R²  (Oliver-Pharr fit)')
                ax4.set_title(
                    f'Unloading Fit Quality  (R²)  [ISO 14577-1 §A.8]\n'
                    f'Mean {np.mean(unloading_r2):.4f}   Min {np.min(unloading_r2):.4f}'
                    f'   {"✓ all ≥ 0.99" if all(v >= 0.99 for v in unloading_r2) else "⚠ some below 0.99"}',
                    fontweight='bold'
                )
                ax4.set_ylim(max(0.95, min(unloading_r2) - 0.01), 1.002)
                ax4.legend(fontsize=8)
                ax4.grid(True, alpha=0.3, axis='y')
            else:
                ax4.text(0.5, 0.5, 'No unloading R² data', ha='center', va='center',
                         transform=ax4.transAxes, color='grey')
                ax4.set_title('Unloading Fit Quality', fontweight='bold')

            fig.text(
                0.5, 0.005,
                "Red bars = R² below 0.99 threshold.  "
                "High CV (>10 %) in H or Er may indicate surface roughness, indentation size effect, or pile-up.",
                ha='center', fontsize=8, color='#555555'
            )
            fig.tight_layout(rect=[0, 0.03, 1, 0.97])
            summary_widget.canvas.draw()

        except Exception as e:
            summary_widget.figure.clear()
            ax = summary_widget.figure.add_subplot(111)
            ax.text(0.5, 0.5, f'Error creating summary plot:\n{str(e)}',
                    transform=ax.transAxes, ha='center', va='center',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='salmon', alpha=0.7))
            ax.set_title("Summary Plot Error")
            summary_widget.canvas.draw()

        self.plots_tab_widget.addTab(summary_widget, "📊 Reliability Summary")
    
    def browse_file(self):
        """Open file dialog to select Excel file"""
        samples_dir = str(Path(__file__).resolve().parent.parent.parent / "samples")
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Nanoindentation Data File",
            samples_dir,
            "Excel Files (*.xls *.xlsx);;All Files (*)"
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
            self.reload_button.setEnabled(True)
            self.analyze_button.setEnabled(True)
            self.step2_next_button.setEnabled(True)
            self.unlock_workflow_step(2)
            self.unlock_workflow_step(3)
            self.update_readiness_summary()
            self.log_widget.append(f"📁 Selected file: {file_path}")
            self.status_bar.showMessage(f"File selected: {Path(file_path).name}")
    
    def reload_file(self):
        """Reload the current file"""
        if self.file_path_edit.text():
            self.log_widget.append(f"🔄 Reloading file: {self.file_path_edit.text()}")
            self.status_bar.showMessage("File reloaded")
    
    def start_analysis(self):
        """Start the nanoindentation analysis"""
        file_path = self.file_path_edit.text()
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Error", "Please select a valid Excel file.")
            return
        
        try:
            self.current_analysis_file_path = str(Path(file_path).resolve())
            use_new_analyzer = NanoindentationAnalyzer is not None
            if not use_new_analyzer and FixedIndentXLSAnalyzer is not None:
                self.analyzer = FixedIndentXLSAnalyzer(filename=file_path)
                self.analyzer.generatePlot = self.generate_plots_cb.isChecked()
                self.analyzer.hidePlot = True
                self.analyzer.export = self.export_plots_cb.isChecked()
                self.analyzer.ISO_MIN_R_SQUARED = self.min_r2_spinbox.value()
            elif not use_new_analyzer:
                raise RuntimeError("No analysis backend is available.")
            
            # Clear previous results
            self.current_results.clear()
            self.results_table.setRowCount(0)
            self.clear_plot_tabs()
            self.log_widget.clear()
            
            # Setup UI for analysis
            self.analyze_button.setEnabled(False)
            self.cancel_button.setEnabled(True)
            self.step4_next_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            self.log_widget.append("🔬 Starting nanoindentation analysis...")
            self.log_widget.append(f"📁 File: {file_path}")
            if self.sample_name_edit and self.sample_name_edit.text().strip():
                self.log_widget.append(f"🧷 Sample: {self.sample_name_edit.text().strip()}")
            if self.research_goal_combo:
                self.log_widget.append(f"🎯 Goal: {self.research_goal_combo.currentText()}")
            self.log_widget.append(f"🧪 Calibration source: {self.calibration_source}")
            if self.pending_analysis_context:
                self.log_widget.append(f"🧭 Context: {self.pending_analysis_context}")
                self.pending_analysis_context = None
            self.log_widget.append(
                f"⚙️ Settings: Plots={self.generate_plots_cb.isChecked()}, "
                f"Export={self.export_plots_cb.isChecked()}, Min R²={self.min_r2_spinbox.value()}, "
                f"Fit segment={self.fit_curve_percent_spinbox.value() if self.fit_curve_percent_spinbox else 25.0}%"
            )
            self.log_widget.append("=" * 60)
            
            # Create and start worker thread
            self.analysis_worker = AnalysisWorker(
                analyzer=self.analyzer,
                file_path=file_path if use_new_analyzer else None,
                use_new_analyzer=use_new_analyzer,
                area_function_coefficients=self.calibration_coefficients if use_new_analyzer else None,
                sample_poisson=self.sample_poisson_spinbox.value() if self.sample_poisson_spinbox else 0.30,
                indenter_material=self.indenter_combo.currentText() if self.indenter_combo else 'diamond',
                fitting_method=self.fitting_method_combo.currentText() if self.fitting_method_combo else 'oliver_pharr',
                min_r_squared=self.min_r2_spinbox.value() if self.min_r2_spinbox else 0.98,
                fit_percent=self.fit_curve_percent_spinbox.value() if self.fit_curve_percent_spinbox else 25.0
            )
            self.analysis_worker.progress_update.connect(self.update_progress)
            self.analysis_worker.status_update.connect(self.update_status)
            self.analysis_worker.result_ready.connect(self.handle_results)
            self.analysis_worker.error_occurred.connect(self.handle_error)
            self.analysis_worker.finished.connect(self.analysis_finished)
            
            self.analysis_worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start analysis:\n{str(e)}")
            self.analysis_finished()

    def normalize_results_for_gui(self, results: Any) -> List[Dict[str, Any]]:
        if isinstance(results, list):
            return results

        if not isinstance(results, dict):
            return []

        tests = results.get('tests', {})
        normalized = []
        for test_name, test_data in tests.items():
            if not test_data.get('success', False):
                continue

            props = test_data.get('mechanical_properties', {})
            hardness = props.get('hardness', {})
            sample_mod = props.get('sample_modulus', {})
            contact = props.get('contact_area', {})
            curve = test_data.get('curve_fitting', {})

            stiffness_mn_nm = curve.get('stiffness', 0.0)
            stiffness_n_m = stiffness_mn_nm * 1e6 if stiffness_mn_nm else 0.0
            contact_depth_nm = curve.get('contact_depth', 0.0)
            area_nm2 = contact.get('area_nm2', 0.0)
            loading_df = (
                test_data.get('data_processing', {})
                .get('phases', {})
                .get('loading', {})
                .get('filtered_data', pd.DataFrame())
            )
            unloading_df = (
                test_data.get('data_processing', {})
                .get('phases', {})
                .get('unloading', {})
                .get('filtered_data', pd.DataFrame())
            )
            loading_phase = test_data.get('data_processing', {}).get('phases', {}).get('loading', {})
            max_load_mn = loading_phase.get('max_load', 0.0)
            max_disp_nm = loading_phase.get('max_displacement', 0.0)

            if (not max_load_mn) and isinstance(loading_df, pd.DataFrame) and not loading_df.empty:
                max_load_mn = float(loading_df.get('Load (mN)', pd.Series(dtype=float)).max() or 0.0)
            if (not max_disp_nm) and isinstance(loading_df, pd.DataFrame) and not loading_df.empty:
                load_series = loading_df.get('Load (mN)', pd.Series(dtype=float))
                disp_series = loading_df.get('Displacement (nm)', pd.Series(dtype=float))
                if not load_series.empty and not disp_series.empty:
                    max_idx = load_series.idxmax()
                    if max_idx in disp_series.index:
                        max_disp_nm = float(disp_series.loc[max_idx] or 0.0)

            raw_loading_disp = loading_df.get('Displacement (nm)', pd.Series(dtype=float)).tolist() if isinstance(loading_df, pd.DataFrame) else []
            raw_loading_load = loading_df.get('Load (mN)', pd.Series(dtype=float)).tolist() if isinstance(loading_df, pd.DataFrame) else []
            raw_unloading_disp = unloading_df.get('Displacement (nm)', pd.Series(dtype=float)).tolist() if isinstance(unloading_df, pd.DataFrame) else []
            raw_unloading_load = unloading_df.get('Load (mN)', pd.Series(dtype=float)).tolist() if isinstance(unloading_df, pd.DataFrame) else []

            loading_fit_disp = []
            loading_fit_load = []
            loading_r2_value = curve.get('r_squared', 0.0)
            if raw_loading_disp and raw_loading_load and len(raw_loading_disp) >= 4:
                h_loading = np.asarray(raw_loading_disp, dtype=float)
                p_loading = np.asarray(raw_loading_load, dtype=float)
                valid_loading = np.isfinite(h_loading) & np.isfinite(p_loading) & (h_loading >= 0) & (p_loading >= 0)
                h_loading = h_loading[valid_loading]
                p_loading = p_loading[valid_loading]
                if h_loading.size >= 4 and np.max(h_loading) > 0:
                    # Use all loading points so the loading fit covers the complete loading curve.
                    h_loading_fit_segment = h_loading
                    p_loading_fit_segment = p_loading
                    coeff_loading = np.polyfit(h_loading_fit_segment, p_loading_fit_segment, 3)
                    
                    # Find the y=0 intercept (where polynomial crosses P=0)
                    roots = np.roots(coeff_loading)
                    real_positive_roots = roots[np.isreal(roots) & (roots.real > 0)].real
                    h_intercept = float(np.min(real_positive_roots)) if len(real_positive_roots) > 0 else 0.0
                    
                    # Extend loading fit from y=0 intercept to max displacement
                    h_min_extended = max(h_intercept, 0.0)
                    h_max_extended = float(np.max(h_loading_fit_segment))
                    h_fit_loading = np.linspace(h_min_extended, h_max_extended, 160)
                    
                    p_fit_loading = np.polyval(coeff_loading, h_fit_loading)
                    loading_fit_disp = h_fit_loading.tolist()
                    loading_fit_load = np.maximum(p_fit_loading, 0.0).tolist()
                    p_pred_segment = np.polyval(coeff_loading, h_loading_fit_segment)
                    ss_res = float(np.sum((p_loading_fit_segment - p_pred_segment) ** 2))
                    ss_tot = float(np.sum((p_loading_fit_segment - np.mean(p_loading_fit_segment)) ** 2))
                    loading_r2_value = (1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0

            unloading_fit_disp = []
            unloading_fit_load = []
            if raw_unloading_disp:
                h_unloading = np.asarray(raw_unloading_disp, dtype=float)
                p_fit_unloading = np.asarray(curve.get('fitted_curve', []), dtype=float)
                h_fit_segment = np.asarray(curve.get('fit_displacement', []), dtype=float)
                p_fit_segment = np.asarray(curve.get('fit_curve', []), dtype=float)
                if h_fit_segment.size == p_fit_segment.size and h_fit_segment.size > 0:
                    unloading_fit_disp = h_fit_segment.tolist()
                    unloading_fit_load = np.maximum(p_fit_segment, 0.0).tolist()
                elif p_fit_unloading.size == h_unloading.size and p_fit_unloading.size > 0:
                    unloading_fit_disp = h_unloading.tolist()
                    unloading_fit_load = np.maximum(p_fit_unloading, 0.0).tolist()

                params = curve.get('parameters', {}) if isinstance(curve.get('parameters', {}), dict) else {}
                h_f = params.get('h_f', None)
                if h_f is not None:
                    h_f = float(h_f)
                    if not unloading_fit_disp:
                        method_used = curve.get('method_used') or curve.get('method') or ''
                        h_max = float(np.max(h_unloading))
                        h_fit_unloading = np.linspace(h_max, h_f, 160)
                        if method_used == 'oliver_pharr' and all(k in params for k in ('A', 'm')):
                            a_fit = float(params['A'])
                            m_fit = float(params['m'])
                            p_fit_model = a_fit * np.maximum(h_fit_unloading - h_f, 0.0) ** m_fit
                            unloading_fit_disp = h_fit_unloading.tolist()
                            unloading_fit_load = np.maximum(p_fit_model, 0.0).tolist()
                        elif method_used == 'power_law' and all(k in params for k in ('P_max', 'm')):
                            p_max_fit = float(params['P_max'])
                            m_fit = float(params['m'])
                            denom = max(h_max - h_f, 1e-12)
                            ratio = np.maximum((h_fit_unloading - h_f) / denom, 0.0)
                            p_fit_model = p_max_fit * np.power(ratio, m_fit)
                            unloading_fit_disp = h_fit_unloading.tolist()
                            unloading_fit_load = np.maximum(p_fit_model, 0.0).tolist()
                    elif abs(float(unloading_fit_disp[-1]) - h_f) > 1e-9:
                        unloading_fit_disp.append(h_f)
                        unloading_fit_load.append(0.0)
            
            # Extract tangent line data (stiffness line at peak load)
            tangent_disp = []
            tangent_load = []
            if 'tangent_displacement' in curve and 'tangent_load' in curve:
                h_tangent = np.asarray(curve.get('tangent_displacement', []), dtype=float)
                p_tangent = np.asarray(curve.get('tangent_load', []), dtype=float)
                if h_tangent.size == p_tangent.size and h_tangent.size > 0:
                    tangent_disp = h_tangent.tolist()
                    tangent_load = np.maximum(p_tangent, 0.0).tolist()

            normalized.append({
                'Test': test_name,
                'Source File': Path(results.get('file_path', '')).name if results.get('file_path') else '',
                'Hardness (GPa)': hardness.get('hardness_gpa', 0.0),
                'Oliver-Pharr Modulus (GPa)': sample_mod.get('sample_modulus_gpa', 0.0),
                'Loading R²': loading_r2_value,
                'Unloading Fit R²': curve.get('r_squared', 0.0),
                'Max Load (mN)': max_load_mn,
                'Max Displacement (nm)': max_disp_nm,
                'S (N/m)': stiffness_n_m,
                'Hc (m)': contact_depth_nm * 1e-9 if contact_depth_nm else 0.0,
                'A (m^2)': area_nm2 * 1e-18 if area_nm2 else 0.0,
                'Raw Loading Displacement (nm)': raw_loading_disp,
                'Raw Loading Load (mN)': raw_loading_load,
                'Raw Unloading Displacement (nm)': raw_unloading_disp,
                'Raw Unloading Load (mN)': raw_unloading_load,
                'Loading Fit Displacement (nm)': loading_fit_disp,
                'Loading Fit Load (mN)': loading_fit_load,
                'Unloading Fit Displacement (nm)': unloading_fit_disp,
                'Unloading Fit Load (mN)': unloading_fit_load,
                'Tangent Displacement (nm)': tangent_disp,
                'Tangent Load (mN)': tangent_load,
                'Analysis Success': True
            })

        return normalized
    
    def cancel_analysis(self):
        """Cancel the running analysis"""
        if self.analysis_worker and self.analysis_worker.isRunning():
            self.analysis_worker.cancel()
            self.log_widget.append("❌ Analysis cancelled by user")
            self.status_bar.showMessage("Analysis cancelled")
    
    def update_progress(self, value: int):
        """Update the progress bar"""
        self.progress_bar.setValue(value)
    
    def update_status(self, message: str):
        """Update the status and log"""
        self.status_bar.showMessage(message)
        self.log_widget.append(message)
        # Auto-scroll to bottom
        self.log_widget.verticalScrollBar().setValue(
            self.log_widget.verticalScrollBar().maximum()
        )
    
    def handle_results(self, results: Any):
        """Handle analysis results"""
        total_tests = len(results.get('tests', {})) if isinstance(results, dict) else None
        normalized_results = self.normalize_results_for_gui(results)
        self.current_results = normalized_results
        
        if normalized_results:
            # Load results into table
            self.results_table.load_results(normalized_results)
            
            # Enable export buttons
            self.export_excel_button.setEnabled(True)
            self.export_csv_button.setEnabled(True)
            self.unlock_workflow_step(4)
            self.step4_next_button.setEnabled(True)
            
            # Log summary
            self.log_widget.append("=" * 60)
            self.log_widget.append(f"✅ Analysis completed successfully!")
            self.log_widget.append(f"📊 {len(normalized_results)} tests analyzed")
            if total_tests is not None and self.min_r2_spinbox:
                excluded = max(total_tests - len(normalized_results), 0)
                self.log_widget.append(
                    f"🧮 Min R² filter ({self.min_r2_spinbox.value():.3f}): "
                    f"{len(normalized_results)} accepted, {excluded} excluded"
                )
            
            # Calculate summary statistics
            hardness_values = [r.get('Hardness (GPa)', 0) for r in normalized_results if r.get('Hardness (GPa)')]
            if hardness_values:
                mean_hardness = np.mean(hardness_values)
                std_hardness = np.std(hardness_values)
                self.log_widget.append(f"📈 Average Hardness: {mean_hardness:.2f} ± {std_hardness:.2f} GPa")
            
            modulus_values = [r.get('Oliver-Pharr Modulus (GPa)', 0) for r in normalized_results if r.get('Oliver-Pharr Modulus (GPa)')]
            if modulus_values:
                mean_modulus = np.mean(modulus_values)
                std_modulus = np.std(modulus_values)
                self.log_widget.append(f"📈 Average Modulus: {mean_modulus:.2f} ± {std_modulus:.2f} GPa")
            
            # Plot first test as example
            if normalized_results:
                self.create_plot_tabs(normalized_results)
        
        else:
            self.log_widget.append("⚠️ No valid results obtained from analysis")
    
    def handle_error(self, error_message: str):
        """Handle analysis errors"""
        self.log_widget.append(f"❌ Error: {error_message}")
        QMessageBox.critical(self, "Analysis Error", error_message)
    
    def analysis_finished(self):
        """Clean up after analysis finishes"""
        self.analyze_button.setEnabled(bool(self.file_path_edit.text()))
        self.cancel_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        if self.analysis_worker:
            self.analysis_worker.deleteLater()
            self.analysis_worker = None
    
    def export_to_excel(self):
        """Export results to Excel file"""
        if not self.current_results:
            QMessageBox.warning(self, "No Data", "No analysis results to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results to Excel",
            "nanoindentation_results.xlsx",
            "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if file_path:
            try:
                df = pd.DataFrame(self.current_results)
                df.to_excel(file_path, index=False, engine='openpyxl')
                self.log_widget.append(f"📊 Results exported to: {file_path}")
                QMessageBox.information(self, "Export Successful", f"Results exported to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export to Excel:\n{str(e)}")
    
    def export_to_csv(self):
        """Export results to CSV file"""
        if not self.current_results:
            QMessageBox.warning(self, "No Data", "No analysis results to export.")
            return
        
        samples_dir = str(Path(__file__).resolve().parent.parent.parent / "samples")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results to CSV",
            str(Path(samples_dir) / "nanoindentation_results.csv"),
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                df = pd.DataFrame(self.current_results)
                df.to_csv(file_path, index=False)
                self.log_widget.append(f"📄 Results exported to: {file_path}")
                QMessageBox.information(self, "Export Successful", f"Results exported to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export to CSV:\n{str(e)}")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Nanoindentation Analysis")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Research Lab")
    
    # Create and show main window
    window = NanoindentationGUI()
    window.show()
    
    # Start event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
