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
from scipy.optimize import curve_fit

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
        self.figure = Figure(figsize=(12, 8), dpi=100, facecolor='#1a1a1a')
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Set canvas background to white
        self.canvas.setStyleSheet("background-color: #1a1a1a;")
        
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
                ax.scatter(loading_disp_raw, loading_load_raw, s=8, alpha=0.65, )
                has_curve_data = True
            if unloading_disp_raw and unloading_load_raw:
                ax.scatter(unloading_disp_raw, unloading_load_raw, s=8, alpha=0.65, )
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


class TestPlotWidget(QWidget):
    """
    Custom widget for test plots with tabbed interface:
    Tab 1: Nanoindentation curve (clean, full-sized plot)
    Tab 2: Results summary (formatted data and statistics)
    """
    
    def __init__(self, analyzer: FixedIndentXLSAnalyzer, test_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.analyzer = analyzer
        self.test_data = test_data
        self.logger = logging.getLogger('TestPlotWidget')
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # ── TAB 1: Nanoindentation Curve (Clean plot) ──────────────────────
        self.plot_widget = MatplotlibWidget()
        self.plot_widget.plot_nanoindentation_curve(self.analyzer, self.test_data)
        
        # Remove the results text box from the plot by clearing and redrawing
        # Create a clean version of the plot without text overlay
        self._create_clean_plot()
        
        self.tabs.addTab(self.plot_widget, "📈 Nanoindentation Curve")
        
        # ── TAB 2: Results Summary ─────────────────────────────────────────
        self.results_widget = QWidget()
        results_layout = QVBoxLayout(self.results_widget)
        results_layout.setContentsMargins(15, 15, 15, 15)
        results_layout.setSpacing(12)
        
        # Results text display with scrolling
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: 1px solid #2a2a2a;
                border-radius: 5px;
                font-family: 'Monaco', 'Courier New', monospace;
                font-size: 10pt;
                padding: 10px;
            }
        """)
        self._populate_results_text()
        
        results_layout.addWidget(self.results_text)
        self.tabs.addTab(self.results_widget, "📋 Results Summary")
        
        # Set main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
    
    def _create_clean_plot(self):
        """Create a cleaner version of the plot without text overlays."""
        fig = self.plot_widget.figure
        fig.clear()
        fig.patch.set_facecolor('#1a1a1a')
        
        ax = fig.add_subplot(111)
        
        test_id = self.test_data.get('Test', 'Unknown')
        try:
            # Get loading/unloading data
            loading_disp_raw = self.test_data.get('Raw Loading Displacement (nm)', [])
            loading_load_raw = self.test_data.get('Raw Loading Load (mN)', [])
            unloading_disp_raw = self.test_data.get('Raw Unloading Displacement (nm)', [])
            unloading_load_raw = self.test_data.get('Raw Unloading Load (mN)', [])
            
            loading_fit_disp = self.test_data.get('Loading Fit Displacement (nm)', [])
            loading_fit_load = self.test_data.get('Loading Fit Load (mN)', [])
            unloading_fit_disp = self.test_data.get('Unloading Fit Displacement (nm)', [])
            unloading_fit_load = self.test_data.get('Unloading Fit Load (mN)', [])
            
            # Plot raw data points
            if loading_disp_raw and loading_load_raw:
                ax.scatter(loading_disp_raw, loading_load_raw, s=5, alpha=0.5, 
                          color='#00a8cc', label='Loading data', zorder=1)
            if unloading_disp_raw and unloading_load_raw:
                ax.scatter(unloading_disp_raw, unloading_load_raw, s=5, alpha=0.5, 
                          color='#00d9ff', label='Unloading data', zorder=1)
            
            # Plot fitted curves (smooth lines on top)
            if loading_fit_disp and loading_fit_load:
                ax.plot(loading_fit_disp, loading_fit_load, linewidth=2.5, 
                       color='#2980b9', label='Loading fit', alpha=0.85, zorder=2)
            if unloading_fit_disp and unloading_fit_load:
                ax.plot(unloading_fit_disp, unloading_fit_load, linewidth=2.5, 
                       color='#e74c3c', label='Unloading fit', alpha=0.85, zorder=2)
            
            # Plot tangent line if available
            tangent_disp = self.test_data.get('Tangent Displacement (nm)', [])
            tangent_load = self.test_data.get('Tangent Load (mN)', [])
            if tangent_disp and tangent_load:
                ax.plot(tangent_disp, tangent_load, linewidth=2.2, color='#27ae60', 
                       label='Stiffness (S)', alpha=0.8, linestyle='--', zorder=2)
            
            ax.set_xlabel('Displacement Into Surface (nm)', fontsize=12, fontweight='bold')
            ax.set_ylabel('Load on Sample (mN)', fontsize=12, fontweight='bold')
            ax.set_title(f'Test {test_id} — Nanoindentation Curve\n', fontsize=13, fontweight='bold')
            ax.grid(True, alpha=0.3, linestyle=':', color='white')
            ax.legend(fontsize=10, loc='upper left', framealpha=0.95,
                      facecolor='#1a1a1a', edgecolor='#3a3a3a', labelcolor='#e0e0e0')
            ax.set_xlim(left=0)
            ax.set_ylim(bottom=0)
            
        except Exception as e:
            self.logger.error(f"Error creating clean plot for Test {test_id}: {e}")
            ax.text(0.5, 0.5, f'Error: {str(e)}', transform=ax.transAxes, 
                   ha='center', va='center', fontsize=11, color='red')
        
        fig.tight_layout()
        self.plot_widget.canvas.draw()
    
    def _populate_results_text(self):
        """Populate the results summary text widget with formatted test data."""
        test_id = self.test_data.get('Test', 'N/A')
        
        # Format results as organized sections
        results_html = f"""
<h3 style="color: #00a8cc;">Test {test_id}</h3>
<hr style="border: 1px solid #2a2a2a;">

<h4 style="color: #00d9ff;">MECHANICAL PROPERTIES</h4>
<table style="width: 100%; color: #e0e0e0;">
  <tr><td>Hardness (H):</td><td style="text-align: right; color: #00a8cc;"><b>{self.test_data.get('Hardness (GPa)', 'N/A')} GPa</b></td></tr>
  <tr><td>Oliver-Pharr Modulus (E*):</td><td style="text-align: right; color: #00a8cc;"><b>{self.test_data.get('Oliver-Pharr Modulus (GPa)', 'N/A')} GPa</b></td></tr>
  <tr><td>CSM Hardness:</td><td style="text-align: right;">{self.test_data.get('CSM Hardness (GPa)', 'N/A')} GPa</td></tr>
</table>

<h4 style="color: #00d9ff;">MECHANICAL PARAMETERS</h4>
<table style="width: 100%; color: #e0e0e0;">
  <tr><td>Maximum Load (P<sub>max</sub>):</td><td style="text-align: right;">{self.test_data.get('Max Load (mN)', 'N/A')} mN</td></tr>
  <tr><td>Maximum Displacement (h<sub>max</sub>):</td><td style="text-align: right;">{self.test_data.get('Max Displacement (nm)', 'N/A')} nm</td></tr>
  <tr><td>Contact Area (A<sub>c</sub>):</td><td style="text-align: right;">{self.test_data.get('A (m^2)', 'N/A')} m²</td></tr>
  <tr><td>Contact Depth (h<sub>c</sub>):</td><td style="text-align: right;">{self.test_data.get('Hc (m)', 'N/A')} m</td></tr>
  <tr><td>Stiffness (S):</td><td style="text-align: right;">{self.test_data.get('S (N/m)', 'N/A')} N/m</td></tr>
</table>

<h4 style="color: #00d9ff;">CURVE FIT QUALITY (ISO 14577-1)</h4>
<table style="width: 100%; color: #e0e0e0;">
  <tr><td>Loading R²:</td><td style="text-align: right;"><b>{self.test_data.get('Loading R²', 'N/A')}</b></td></tr>
  <tr><td>Unloading R²:</td><td style="text-align: right;"><b>{self.test_data.get('Unloading Fit R²', 'N/A')}</b></td></tr>
</table>
<p style="color: #888; font-size: 9pt;">ISO threshold: R² ≥ 0.99</p>

<h4 style="color: #00d9ff;">CALIBRATION</h4>
<table style="width: 100%; color: #e0e0e0;">
  <tr><td>Calibration Factor:</td><td style="text-align: right;">{self.test_data.get('Calibration Factor', 'N/A')}</td></tr>
  <tr><td>Source File:</td><td style="text-align: right; font-size: 9pt;">{self.test_data.get('Source File', 'N/A')}</td></tr>
</table>

<h4 style="color: #00d9ff;">ANALYSIS STATUS</h4>
<table style="width: 100%; color: #e0e0e0;">
  <tr><td>Analysis Success:</td><td style="text-align: right;"><b>{self.test_data.get('Analysis Success', 'N/A')}</b></td></tr>
</table>
"""
        self.results_text.setHtml(results_html)


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
            self.setRowCount(0)
            self.setColumnCount(0)
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
            'Loading Power C',
            'Loading Power n',
            'Loading Offset h0 (nm)',
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
        self.plots_tab_widget: Optional[QTabWidget] = None  # unused; kept for safety
        self.results_panel_tabs: Optional[QTabWidget] = None
        self.reliability_widget: Optional[MatplotlibWidget] = None
        self.single_test_plot: Optional[MatplotlibWidget] = None
        self.current_test_index: int = 0
        self.test_nav_label: Optional[QLabel] = None
        self.test_nav_prev: Optional[QPushButton] = None
        self.test_nav_next: Optional[QPushButton] = None
        self.test_include_checkbox: Optional[QCheckBox] = None
        self.excluded_test_indices = set()
        self.workflow_tabs: Optional[QTabWidget] = None
        self.step4_plot_buttons_layout: Optional[QGridLayout] = None
        self.step4_plot_buttons_note: Optional[QLabel] = None
        self.step4_plot_buttons: Dict[int, QPushButton] = {}
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
        self.setup_matplotlib_style()
        
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
        """Render tabbed calibration charts: Area Function, Geometry Deviation, and Quality Assessment."""
        if not self.calibration_plot_widget:
            return

        C = [self.calibration_coefficients.get(f'C{i}', 0.0) for i in range(9)]
        exponents = [2, 1, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625, 0.0078125]
        hc = np.linspace(1, 2000, 600)
        A_loaded = sum(C[i] * hc ** exponents[i] for i in range(9))
        A_ideal = 24.5 * hc ** 2
        deviation_pct = (A_loaded - A_ideal) / A_ideal * 100
        max_dev = float(np.max(np.abs(deviation_pct)))

        fig = self.calibration_plot_widget.figure
        fig.clear()
        fig.patch.set_facecolor('#1a1a1a')

        fname = Path(self.calibration_file_path).name if self.calibration_file_path else 'manual / default'
        fig.suptitle(
            f'Calibration Reliability  —  {self.calibration_source}  |  {fname}',
            fontsize=11, fontweight='bold', y=0.98
        )

        # ── TAB 1: Area Function & Deviation (Full width) ──────────────────
        ax1a = fig.add_subplot(2, 2, 1)
        ax1a.plot(hc, A_ideal / 1e6, 'k--', linewidth=1.5, alpha=0.55,
                  label='Ideal Berkovich')
        ax1a.plot(hc, A_loaded / 1e6, color='#00a8cc', linewidth=2.2,
                  label='Loaded calibration')
        ax1a.set_xlabel('Contact Depth hc (nm)', fontsize=9)
        ax1a.set_ylabel('Projected Area A (µm²)', fontsize=9)
        ax1a.set_title('Tip Area Function  A(hc)', fontweight='bold', fontsize=10)
        ax1a.legend(fontsize=8, loc='upper left')
        ax1a.grid(True, alpha=0.3)

        # ── TAB 2: Deviation Analysis ──────────────────────────────────────
        ax1b = fig.add_subplot(2, 2, 2)
        pos_mask = deviation_pct >= 0
        ax1b.fill_between(hc, deviation_pct, 0, where=pos_mask, alpha=0.3, 
                          color='#e74c3c', label='Above ideal')
        ax1b.fill_between(hc, deviation_pct, 0, where=~pos_mask, alpha=0.3, 
                          color='#00a8cc', label='Below ideal')
        ax1b.plot(hc, deviation_pct, color='#e67e22', linewidth=2, label='Deviation')
        ax1b.axhline(0, color='white', linestyle='--', linewidth=0.8, alpha=0.5)
        ax1b.axhline(5, color='#e74c3c', linestyle=':', linewidth=1.2, alpha=0.7)
        ax1b.axhline(-5, color='#e74c3c', linestyle=':', linewidth=1.2, alpha=0.7, 
                     label='±5 % threshold')
        ax1b.set_xlabel('Contact Depth hc (nm)', fontsize=9)
        ax1b.set_ylabel('Deviation from Ideal (%)', fontsize=9)
        ax1b.set_title('Geometry Deviation Analysis', fontweight='bold', fontsize=10)
        ax1b.legend(fontsize=8, loc='best')
        ax1b.grid(True, alpha=0.3)

        # ── TAB 3: Coefficients ────────────────────────────────────────────
        ax2a = fig.add_subplot(2, 2, 3)
        coeff_names = [f'C{i}' for i in range(9)]
        colors_bar = ['#00a8cc' if v >= 0 else '#e74c3c' for v in C]
        bars = ax2a.bar(coeff_names, C, color=colors_bar, edgecolor='white', linewidth=0.8)
        ax2a.axhline(0, color='white', linewidth=0.8, alpha=0.5)
        ax2a.set_xlabel('Coefficient', fontsize=9)
        ax2a.set_ylabel('Value', fontsize=9)
        ax2a.set_title('Area Function Coefficients', fontweight='bold', fontsize=10)
        ax2a.grid(True, alpha=0.3, axis='y')
        for idx, (name, val) in enumerate(zip(coeff_names, C)):
            if abs(val) > 1e-10:
                ax2a.text(idx, val, f'{val:.2g}', ha='center', 
                         va='bottom' if val >= 0 else 'top', fontsize=7, color='white')

        # ── TAB 4: Quality Assessment ──────────────────────────────────────
        ax2b = fig.add_subplot(2, 2, 4)
        ax2b.axis('off')
        
        n_active = sum(1 for c in C[1:] if abs(c) > 1e-10)
        c0_dev_pct = abs(C[0] - 24.5) / 24.5 * 100
        
        if max_dev < 2 and c0_dev_pct < 1:
            verdict, verdict_color = '✓ EXCELLENT', '#27ae60'
        elif max_dev < 10:
            verdict, verdict_color = '✓ GOOD', '#2ecc71'
        elif max_dev < 20:
            verdict, verdict_color = '⚠ FAIR', '#e67e22'
        else:
            verdict, verdict_color = '✗ REVIEW', '#e74c3c'

        quality_text = f"""CALIBRATION QUALITY METRICS

Primary Scale (C0):
  Value: {C[0]:.4f}  |  Ideal: 24.5
  Error: {c0_dev_pct:.2f}%

Active Corrections (C1–C8):
  Active: {n_active} / 8
  (0 = pure ideal tip)

Depth Range Deviation:
  Max: {max_dev:.2f}%
  Range: 0–2000 nm
  Threshold: < 5%

OVERALL VERDICT
{verdict}
"""
        
        ax2b.text(0.1, 0.95, quality_text, transform=ax2b.transAxes,
                 fontfamily='monospace', fontsize=9, verticalalignment='top',
                 bbox=dict(boxstyle='round,pad=1', facecolor=verdict_color, alpha=0.3,
                          edgecolor=verdict_color, linewidth=2))

        fig.tight_layout(rect=[0, 0, 1, 0.97])
        self.calibration_plot_widget.canvas.draw()

        # Switch focus to this tab
        if self.results_panel_tabs:
            for i in range(self.results_panel_tabs.count()):
                if self.results_panel_tabs.tabText(i) == 'Calibration':
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
        """Create the results panel with flat top-level tabs (no nesting)."""
        tab_widget = QTabWidget()
        self.results_panel_tabs = tab_widget

        # ── Tab 0: Calibration profile ────────────────────────────────────
        self.calibration_plot_widget = MatplotlibWidget()
        tab_widget.addTab(self.calibration_plot_widget, "Calibration")
        self._draw_calibration_placeholder()

        # ── Tab 1: Results table ──────────────────────────────────────────
        self.results_table = ResultsTableWidget()
        tab_widget.addTab(self.results_table, "Results Table")

        # ── Tab 2: Reliability summary (populated after analysis) ─────────
        self.reliability_widget = MatplotlibWidget()
        tab_widget.addTab(self.reliability_widget, "Reliability")

        # ── Tab 3: Single test plot with prev/next navigation ─────────────
        test_plot_container = QWidget()
        vbox = QVBoxLayout(test_plot_container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        nav_bar = QWidget()
        nav_bar.setFixedHeight(36)
        nav_bar.setStyleSheet("background:#0d0d0d; border-bottom:1px solid #2a2a2a;")
        nav_h = QHBoxLayout(nav_bar)
        nav_h.setContentsMargins(8, 0, 8, 0)

        self.test_nav_prev = QPushButton("◀  Prev")
        self.test_nav_prev.setFixedWidth(80)
        self.test_nav_prev.setEnabled(False)
        self.test_nav_prev.clicked.connect(self._prev_test)

        self.test_nav_label = QLabel("No tests loaded")
        self.test_nav_label.setAlignment(Qt.AlignCenter)
        self.test_nav_label.setStyleSheet("color:#aaaaaa; font-size:11px;")

        self.test_nav_next = QPushButton("Next  ▶")
        self.test_nav_next.setFixedWidth(80)
        self.test_nav_next.setEnabled(False)
        self.test_nav_next.clicked.connect(self._next_test)

        self.test_include_checkbox = QCheckBox("Use in final calculations")
        self.test_include_checkbox.setChecked(True)
        self.test_include_checkbox.setEnabled(False)
        self.test_include_checkbox.setStyleSheet("color:#e0e0e0; font-size:11px;")
        self.test_include_checkbox.toggled.connect(self._current_test_inclusion_changed)

        nav_h.addWidget(self.test_nav_prev)
        nav_h.addStretch()
        nav_h.addWidget(self.test_nav_label)
        nav_h.addStretch()
        nav_h.addWidget(self.test_include_checkbox)
        nav_h.addWidget(self.test_nav_next)

        self.single_test_plot = MatplotlibWidget()

        vbox.addWidget(nav_bar)
        vbox.addWidget(self.single_test_plot)
        tab_widget.addTab(test_plot_container, "Test Plot")

        # ── Tab 4: Analysis log ───────────────────────────────────────────
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        log_font = QFont()
        log_font.setFamily("Monaco")
        log_font.setStyleHint(QFont.Monospace)
        log_font.setPointSize(9)
        self.log_widget.setFont(log_font)
        tab_widget.addTab(self.log_widget, "Log")

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
        """Return the application stylesheet - Modern Dark Theme"""
        return """
            /* ===== MODERN DARK THEME (2024) ===== */
            
            /* Main Window */
            QMainWindow {
                background-color: #0f0f0f;
                color: #e0e0e0;
            }
            
            /* Central Widget */
            QWidget {
                background-color: #0f0f0f;
                color: #e0e0e0;
            }
            
            /* Group Boxes - Modern flat design */
            QGroupBox {
                font-weight: 600;
                border: 1px solid #2a2a2a;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: #1a1a1a;
                color: #e0e0e0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #00d9ff;
                font-weight: 700;
            }
            
            /* Buttons - Modern gradient-like effect */
            QPushButton {
                background-color: #00a8cc;
                color: #ffffff;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #00d9ff;
                color: #000000;
            }
            QPushButton:pressed {
                background-color: #0088aa;
            }
            QPushButton:disabled {
                background-color: #333333;
                color: #666666;
            }
            
            /* Input Fields - Cleaner look */
            QLineEdit {
                border: 1px solid #2a2a2a;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 11px;
                background-color: #1a1a1a;
                color: #e0e0e0;
                selection-background-color: #00a8cc;
            }
            QLineEdit:focus {
                border: 2px solid #00d9ff;
                background-color: #222222;
            }
            
            /* Spin Boxes */
            QSpinBox, QDoubleSpinBox {
                border: 1px solid #2a2a2a;
                border-radius: 6px;
                padding: 8px;
                background-color: #1a1a1a;
                color: #e0e0e0;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #00d9ff;
                background-color: #222222;
            }
            
            /* Combo Boxes */
            QComboBox {
                border: 1px solid #2a2a2a;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #1a1a1a;
                color: #e0e0e0;
            }
            QComboBox:focus {
                border: 2px solid #00d9ff;
                background-color: #222222;
            }
            QComboBox::drop-down {
                border: none;
                background-color: transparent;
                width: 24px;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a1a;
                color: #e0e0e0;
                selection-background-color: #00a8cc;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
            }
            
            /* Tab Widget - Modern styling */
            QTabWidget::pane {
                border: 1px solid #2a2a2a;
                border-radius: 6px;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #141414;
                color: #808080;
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border: 1px solid #2a2a2a;
                font-weight: 500;
            }
            QTabBar::tab:hover {
                background-color: #1f1f1f;
                color: #b0b0b0;
            }
            QTabBar::tab:selected {
                background-color: #00a8cc;
                color: #ffffff;
                border-bottom: 3px solid #00d9ff;
                font-weight: 600;
            }
            QTabBar::tab:first {
                margin-left: 4px;
            }
            
            /* Text Areas */
            QTextEdit {
                border: 1px solid #2a2a2a;
                border-radius: 6px;
                background-color: #141414;
                color: #e0e0e0;
                font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
                font-size: 10px;
                padding: 8px;
            }
            QTextEdit:focus {
                border: 2px solid #00d9ff;
            }
            
            /* Tables - Modern alternating rows */
            QTableWidget {
                border: 1px solid #2a2a2a;
                background-color: #1a1a1a;
                alternate-background-color: #151515;
                color: #e0e0e0;
                gridline-color: #2a2a2a;
            }
            QTableWidget::item {
                padding: 6px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #00a8cc;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #0a0a0a;
                color: #00d9ff;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #00a8cc;
                font-weight: 600;
            }
            
            /* Progress Bar */
            QProgressBar {
                border: 1px solid #2a2a2a;
                border-radius: 6px;
                background-color: #1a1a1a;
                color: #e0e0e0;
                text-align: center;
                height: 24px;
            }
            QProgressBar::chunk {
                background-color: #00a8cc;
                border-radius: 4px;
            }
            
            /* Check Boxes */
            QCheckBox {
                color: #e0e0e0;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #2a2a2a;
                border-radius: 4px;
                background-color: #1a1a1a;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #00a8cc;
            }
            QCheckBox::indicator:checked {
                background-color: #00a8cc;
                border: 2px solid #00d9ff;
                image: none;
            }
            
            /* Labels */
            QLabel {
                color: #e0e0e0;
            }
            
            /* Scrollbars - Sleek design */
            QScrollBar:vertical {
                background-color: #0f0f0f;
                width: 14px;
                border-radius: 7px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #3a3a3a;
                border-radius: 7px;
                min-height: 24px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #00a8cc;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            
            QScrollBar:horizontal {
                background-color: #0f0f0f;
                height: 14px;
                border-radius: 7px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background-color: #3a3a3a;
                border-radius: 7px;
                min-width: 24px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #00a8cc;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }
            
            /* Status Bar */
            QStatusBar {
                background-color: #0a0a0a;
                color: #808080;
                border-top: 1px solid #2a2a2a;
            }
            
            /* Splitter - Thin dividers */
            QSplitter::handle {
                background-color: #2a2a2a;
            }
            QSplitter::handle:horizontal {
                width: 1px;
            }
            QSplitter::handle:vertical {
                height: 1px;
            }
            QSplitter::handle:hover {
                background-color: #00a8cc;
            }
            
            /* Matplotlib Canvas */
            QWidget[objectName="qt_scrollarea_viewport"] {
                background-color: #f5f5f5;
            }
            
            /* Toolbar */
            QToolBar {
                background-color: #0f0f0f;
                border: 1px solid #2a2a2a;
                color: #e0e0e0;
                spacing: 4px;
                padding: 4px;
            }
            QToolBar QToolButton {
                background-color: transparent;
                color: #e0e0e0;
                border: none;
                padding: 6px 8px;
                border-radius: 4px;
            }
            QToolBar QToolButton:hover {
                background-color: #2a2a2a;
                color: #00d9ff;
            }
            QToolBar QToolButton:pressed {
                background-color: #00a8cc;
                color: #ffffff;
            }
            
            /* Dialogs */
            QDialog {
                background-color: #0f0f0f;
                color: #e0e0e0;
            }
            
            /* Frame */
            QFrame {
                background-color: #0f0f0f;
                color: #e0e0e0;
            }
        """
    
    def setup_matplotlib_style(self):
        """Configure matplotlib for modern dark mode theme"""
        import matplotlib.pyplot as plt
        
        # Set matplotlib style parameters
        plt.rcParams.update({
            # Figure
            'figure.facecolor': '#1a1a1a',
            'figure.edgecolor': '#2a2a2a',
            'figure.figsize': (12, 8),
            'figure.dpi': 100,
            'savefig.facecolor': '#1a1a1a',
            
            # Axes
            'axes.facecolor': '#0f0f0f',
            'axes.edgecolor': '#2a2a2a',
            'axes.labelcolor': '#e0e0e0',
            'axes.prop_cycle': plt.cycler('color', [
                '#00d9ff', '#ff006e', '#ffbe0b', '#8338ec',
                '#3a86ff', '#fb5607', '#06ffa5', '#ff006e'
            ]),
            
            # Grid
            'grid.color': '#2a2a2a',
            'grid.alpha': 0.2,
            'grid.linestyle': ':',
            'grid.linewidth': 0.8,
            
            # Lines
            'lines.linewidth': 2.0,
            'lines.markersize': 6,
            'lines.color': '#e0e0e0',
            
            # Ticks
            'xtick.color': '#e0e0e0',
            'ytick.color': '#e0e0e0',
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            
            # Legend
            'legend.facecolor': '#1a1a1a',
            'legend.edgecolor': '#2a2a2a',
            'legend.labelcolor': '#e0e0e0',
            'legend.framealpha': 0.95,
            
            # Text
            'text.color': '#e0e0e0',
            'font.size': 10,
            'font.family': 'sans-serif',
            'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
            
            # Axes titles
            'axes.titlesize': 12,
            'axes.labelsize': 11,
        })
    
    def center_window(self):
        """Center the window on the screen"""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
    
    def clear_plot_tabs(self):
        """Clear the reliability summary and test plot widgets."""
        if self.reliability_widget:
            self.reliability_widget.figure.clear()
            self.reliability_widget.canvas.draw()
        if self.single_test_plot:
            self.single_test_plot.figure.clear()
            self.single_test_plot.canvas.draw()
        self.current_test_index = 0
        self.excluded_test_indices.clear()
        self._update_test_nav_label()

    def get_included_results(self) -> List[Dict[str, Any]]:
        """Return test results currently included in final calculations."""
        return [
            result
            for idx, result in enumerate(self.current_results)
            if idx not in self.excluded_test_indices
        ]

    def _test_log_label(self, result: Dict[str, Any], fallback_index: int) -> str:
        """Return a readable test label without duplicating the word Test."""
        test_name = str(result.get('Test', fallback_index + 1)).strip()
        if test_name.lower().startswith('test '):
            return test_name
        return f"Test {test_name}"

    def log_final_calculation_summary(self, included_results: List[Dict[str, Any]], reason: str = ""):
        """Log final summary statistics using only currently included tests."""
        included_count = len(included_results)
        total_count = len(self.current_results)
        excluded_labels = [
            self._test_log_label(self.current_results[idx], idx)
            for idx in sorted(self.excluded_test_indices)
            if 0 <= idx < total_count
        ]

        self.log_widget.append("=" * 60)
        if reason:
            self.log_widget.append(f"🧮 Final calculations recalculated: {reason}")
        else:
            self.log_widget.append("🧮 Final calculations")
        self.log_widget.append(f"📊 {included_count}/{total_count} tests included")
        if excluded_labels:
            self.log_widget.append(f"🚫 Excluded tests: {', '.join(excluded_labels)}")

        if not included_results:
            self.log_widget.append("⚠️ No tests selected for final calculations.")
            return

        hardness_values = [
            r.get('Hardness (GPa)', 0)
            for r in included_results
            if r.get('Hardness (GPa)')
        ]
        if hardness_values:
            mean_hardness = np.mean(hardness_values)
            std_hardness = np.std(hardness_values)
            self.log_widget.append(f"📈 Average Hardness: {mean_hardness:.2f} ± {std_hardness:.2f} GPa")

        modulus_values = [
            r.get('Oliver-Pharr Modulus (GPa)', 0)
            for r in included_results
            if r.get('Oliver-Pharr Modulus (GPa)')
        ]
        if modulus_values:
            mean_modulus = np.mean(modulus_values)
            std_modulus = np.std(modulus_values)
            self.log_widget.append(f"📈 Average Modulus: {mean_modulus:.2f} ± {std_modulus:.2f} GPa")

    def _update_test_nav_label(self):
        n = len(self.current_results)
        if self.test_nav_label:
            if n == 0:
                self.test_nav_label.setText("No tests loaded")
            else:
                self.test_nav_label.setText(
                    f"Test {self.current_test_index + 1} of {n}  —  "
                    f"{self.current_results[self.current_test_index].get('Test', '')}"
                )
        if self.test_nav_prev:
            self.test_nav_prev.setEnabled(self.current_test_index > 0)
        if self.test_nav_next:
            self.test_nav_next.setEnabled(self.current_test_index < n - 1)
        if self.test_include_checkbox:
            self.test_include_checkbox.blockSignals(True)
            self.test_include_checkbox.setEnabled(n > 0)
            self.test_include_checkbox.setChecked(
                n > 0 and self.current_test_index not in self.excluded_test_indices
            )
            self.test_include_checkbox.blockSignals(False)

    def _current_test_inclusion_changed(self, checked: bool):
        """Include/exclude the current test from final table, summary, and exports."""
        if not self.current_results:
            return

        test_label = self._test_log_label(
            self.current_results[self.current_test_index],
            self.current_test_index
        )
        if checked:
            self.excluded_test_indices.discard(self.current_test_index)
            action = "included"
        else:
            self.excluded_test_indices.add(self.current_test_index)
            action = "excluded"

        self.refresh_final_calculations()
        self.log_widget.append(f"{test_label} {action} in final calculations.")
        self.log_final_calculation_summary(
            self.get_included_results(),
            reason=f"{test_label} {action}"
        )

    def refresh_final_calculations(self):
        """Refresh final outputs that depend on the included-test subset."""
        included_results = self.get_included_results()
        included_count = len(included_results)
        total_count = len(self.current_results)

        if self.results_table:
            self.results_table.load_results(included_results)

        if included_results:
            self.create_summary_plot_tab(included_results)
        elif self.reliability_widget:
            self.reliability_widget.figure.clear()
            ax = self.reliability_widget.figure.add_subplot(111)
            ax.axis('off')
            ax.text(
                0.5, 0.5,
                "No tests selected for final calculations.",
                ha='center', va='center', fontsize=12, color='#e0e0e0',
                transform=ax.transAxes
            )
            self.reliability_widget.canvas.draw()

        if self.step4_plot_buttons_note:
            self.step4_plot_buttons_note.setText(
                f"Click a test name to open its plot. "
                f"{included_count}/{total_count} tests included in final calculations."
            )

        has_included = included_count > 0
        if self.export_excel_button:
            self.export_excel_button.setEnabled(has_included)
        if self.export_csv_button:
            self.export_csv_button.setEnabled(has_included)
        if self.step4_next_button:
            self.step4_next_button.setEnabled(has_included)
        self.update_step4_plot_button_styles()
        self._update_test_nav_label()

    def _prev_test(self):
        if self.current_test_index > 0:
            self.open_test_plot_from_step4(self.current_test_index - 1)

    def _next_test(self):
        if self.current_test_index < len(self.current_results) - 1:
            self.open_test_plot_from_step4(self.current_test_index + 1)

    def clear_step4_plot_buttons(self):
        """Clear all test-plot buttons in Step 4."""
        self.step4_plot_buttons.clear()
        if self.step4_plot_buttons_layout is None:
            return
        while self.step4_plot_buttons_layout.count() > 0:
            item = self.step4_plot_buttons_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def set_step4_plot_button_style(self, button: QPushButton, included: bool):
        """Style a test plot button according to final-calculation inclusion."""
        if included:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #00a8cc;
                    color: #ffffff;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #00d9ff;
                    color: #000000;
                }
                QPushButton:pressed {
                    background-color: #0088aa;
                }
            """)
        else:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #46636b;
                    color: #b7c6ca;
                    border: 1px solid #5f787f;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #5a747b;
                    color: #eef6f8;
                }
                QPushButton:pressed {
                    background-color: #3b555c;
                }
            """)

    def update_step4_plot_button_styles(self):
        """Refresh Step 4 plot button colors for included/excluded tests."""
        for idx, button in self.step4_plot_buttons.items():
            self.set_step4_plot_button_style(button, idx not in self.excluded_test_indices)

    def populate_step4_plot_buttons(self, results: List[Dict[str, Any]]):
        """Populate Step 4 with one button per test result."""
        self.clear_step4_plot_buttons()
        if self.step4_plot_buttons_layout is None:
            return

        if self.step4_plot_buttons_note:
            self.step4_plot_buttons_note.setText(
                f"Click a test name to open its plot. "
                f"{len(results)}/{len(results)} tests included in final calculations."
            )

        buttons_per_row = 3
        for idx, result in enumerate(results):
            test_name = str(result.get('Test', f'Test {idx + 1}'))
            button = QPushButton(test_name)
            self.step4_plot_buttons[idx] = button
            self.set_step4_plot_button_style(button, idx not in self.excluded_test_indices)
            button.clicked.connect(lambda _checked=False, result_index=idx: self.open_test_plot_from_step4(result_index))
            row = idx // buttons_per_row
            col = idx % buttons_per_row
            self.step4_plot_buttons_layout.addWidget(button, row, col)

    def open_test_plot_from_step4(self, result_index: int):
        """Render the selected test into the single test plot viewer."""
        if result_index < 0 or result_index >= len(self.current_results):
            return
        if self.single_test_plot is None:
            return

        self.current_test_index = result_index
        self._update_test_nav_label()

        result = self.current_results[result_index]
        try:
            self._render_test_plot(self.single_test_plot, result)
        except Exception as e:
            self.log_widget.append(f"Warning: Error plotting test: {str(e)}")

        # Switch to Test Plot tab
        if self.results_panel_tabs:
            for i in range(self.results_panel_tabs.count()):
                if self.results_panel_tabs.tabText(i) == "Test Plot":
                    self.results_panel_tabs.setCurrentIndex(i)
                    break

    def _render_test_plot(self, widget: MatplotlibWidget, test_data: dict):
        """Render a researcher-quality Oliver-Pharr load-displacement plot into widget."""
        fig = widget.figure
        fig.clear()
        fig.patch.set_facecolor('#1a1a1a')

        ax = fig.add_subplot(111)
        ax.set_facecolor('#0f0f0f')

        test_id = test_data.get('Test', 'Unknown')

        loading_disp_raw  = test_data.get('Raw Loading Displacement (nm)', [])
        loading_load_raw  = test_data.get('Raw Loading Load (mN)', [])
        unloading_disp_raw = test_data.get('Raw Unloading Displacement (nm)', [])
        unloading_load_raw = test_data.get('Raw Unloading Load (mN)', [])
        loading_fit_disp  = test_data.get('Loading Fit Displacement (nm)', [])
        loading_fit_load  = test_data.get('Loading Fit Load (mN)', [])
        unloading_fit_disp = test_data.get('Unloading Fit Displacement (nm)', [])
        unloading_fit_load = test_data.get('Unloading Fit Load (mN)', [])
        tangent_disp = test_data.get('Tangent Displacement (nm)', [])
        tangent_load = test_data.get('Tangent Load (mN)', [])

        h_max = test_data.get('Max Displacement (nm)', 0) or 0
        p_max = test_data.get('Max Load (mN)', 0) or 0
        h_c   = (test_data.get('Hc (m)', 0) or 0) * 1e9   # m → nm
        h_f   = test_data.get('hf (nm)', None)
        S_mN_nm = (test_data.get('S (N/m)', 0) or 0) / 1e6  # N/m → mN/nm
        H_gpa = test_data.get('Hardness (GPa)', 0) or 0
        Er_gpa = test_data.get('Oliver-Pharr Modulus (GPa)', 0) or 0
        loading_r2  = test_data.get('Loading R²', 0) or 0
        unloading_r2 = test_data.get('Unloading Fit R²', 0) or 0
        loading_n = test_data.get('Loading Power n', None)
        loading_h0 = test_data.get('Loading Offset h0 (nm)', None)
        unloading_plot_shift = test_data.get('Unloading Plot Shift (nm)', 0.0) or 0.0

        displacement_offset = 0.0
        if loading_h0 is not None:
            try:
                candidate_offset = float(loading_h0)
                if np.isfinite(candidate_offset):
                    displacement_offset = candidate_offset
            except (TypeError, ValueError):
                displacement_offset = 0.0

        def shifted_displacement(values):
            if values is None or len(values) == 0:
                return values
            return (np.asarray(values, dtype=float) - displacement_offset).tolist()

        loading_disp_raw = shifted_displacement(loading_disp_raw)
        unloading_disp_raw = shifted_displacement(unloading_disp_raw)
        loading_fit_disp = shifted_displacement(loading_fit_disp)
        unloading_fit_disp = shifted_displacement(unloading_fit_disp)
        tangent_disp = shifted_displacement(tangent_disp)
        h_max_plot = h_max - displacement_offset
        h_c_plot = h_c + unloading_plot_shift - displacement_offset
        h_f_plot = (h_f + unloading_plot_shift - displacement_offset) if h_f is not None else None
        p_max_plot = p_max
        if loading_disp_raw and loading_load_raw:
            try:
                loading_load_array = np.asarray(loading_load_raw, dtype=float)
                loading_disp_array = np.asarray(loading_disp_raw, dtype=float)
                if loading_load_array.size == loading_disp_array.size and loading_load_array.size > 0:
                    plot_peak_idx = int(np.nanargmax(loading_load_array))
                    h_max_plot = float(loading_disp_array[plot_peak_idx])
                    p_max_plot = float(loading_load_array[plot_peak_idx])
            except (TypeError, ValueError):
                p_max_plot = p_max

        # ── Raw data scatter ──────────────────────────────────────────────
        if loading_disp_raw and loading_load_raw:
            ax.scatter(loading_disp_raw, loading_load_raw, s=6, alpha=0.5,
                       color='#00a8cc', zorder=2, label='Loading data')
        if unloading_disp_raw and unloading_load_raw:
            ax.scatter(unloading_disp_raw, unloading_load_raw, s=6, alpha=0.5,
                       color='#ff6b6b', zorder=2, label='Unloading data')

        # ── Fitted curves ─────────────────────────────────────────────────
        if loading_fit_disp and loading_fit_load:
            ax.plot(loading_fit_disp, loading_fit_load, '-', linewidth=2.2,
                    color='#00d9ff', zorder=3, label=f'Loading fit  (R²={loading_r2:.4f})')
        if unloading_fit_disp and unloading_fit_load:
            ax.plot(unloading_fit_disp, unloading_fit_load, '-', linewidth=2.2,
                    color='#ff4757', zorder=3, label=f'Oliver-Pharr fit  (R²={unloading_r2:.4f})')

        # ── Stiffness tangent line ────────────────────────────────────────
        if tangent_disp and tangent_load:
            ax.plot(tangent_disp, tangent_load, '--', linewidth=1.6,
                    color='#2ecc71', zorder=4, alpha=0.9, label=f'S = {S_mN_nm:.3f} mN/nm')

        # ── Key depth markers ─────────────────────────────────────────────
        if h_max_plot > 0 and p_max_plot > 0:
            ax.annotate('', xy=(h_max_plot, p_max_plot), xytext=(h_max_plot, 0),
                        arrowprops=dict(arrowstyle='->', color='#888888', lw=1.2))
            ax.text(h_max_plot * 1.01, p_max_plot * 0.5, 'hₘₐₓ',
                    fontsize=8, color='#aaaaaa', va='center')

        if h_c_plot > 0:
            ax.axvline(h_c_plot, color='#a29bfe', linestyle=':', linewidth=1.4, alpha=0.8)
            ax.text(h_c_plot, 0, ' hc', fontsize=8, color='#a29bfe', va='bottom')

        if h_f_plot is not None and h_f_plot > 0:
            ax.axvline(h_f_plot, color='#fdcb6e', linestyle=':', linewidth=1.4, alpha=0.8)
            ax.text(h_f_plot, 0, ' hf', fontsize=8, color='#fdcb6e', va='bottom')

        # ── Axes styling for dark theme ───────────────────────────────────
        for spine in ax.spines.values():
            spine.set_edgecolor('#2a2a2a')
        ax.tick_params(colors='#e0e0e0', labelsize=9)
        ax.xaxis.label.set_color('#e0e0e0')
        ax.yaxis.label.set_color('#e0e0e0')
        ax.title.set_color('#e0e0e0')

        ax.set_xlabel('Corrected displacement  h - h0  (nm)', fontsize=11, fontweight='bold', labelpad=6)
        ax.set_ylabel('Load on Sample  P  (mN)', fontsize=11, fontweight='bold', labelpad=6)
        ax.set_title(f'Test {test_id}  —  Load-Displacement Curve  [ISO 14577-1]',
                     fontsize=12, fontweight='bold', pad=10)
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        ax.grid(True, alpha=0.15, linestyle=':', color='#ffffff')

        # ── Results annotation box ────────────────────────────────────────
        r2_flag = 'pass' if loading_r2 >= 0.99 and unloading_r2 >= 0.99 else 'check'
        info = (
            f"H    = {H_gpa:.3f} GPa\n"
            f"Er   = {Er_gpa:.2f} GPa\n"
            f"S    = {S_mN_nm:.3f} mN/nm\n"
            f"hmax = {h_max_plot:.1f} nm\n"
            f"hc   = {h_c_plot:.1f} nm\n"
            f"Pmax = {p_max_plot:.2f} mN\n"
            f"R²(L/U) = {loading_r2:.4f} / {unloading_r2:.4f}  [{r2_flag}]"
        )
        if loading_n is not None and loading_h0 is not None:
            info += f"\nLoad fit: n={loading_n:.3f}, h0={loading_h0:.2f} nm"
        ax.text(0.015, 0.96, info, transform=ax.transAxes,
                fontsize=8.5, fontfamily='monospace', color='#e0e0e0',
                verticalalignment='top', horizontalalignment='left',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='#0f0f0f',
                          edgecolor='#00a8cc', linewidth=1.2, alpha=0.92))

        fig.tight_layout(pad=1.4)
        widget.canvas.draw()
    
    def create_plot_tabs(self, results: List[Dict[str, Any]]):
        """Render reliability summary and auto-open first test plot."""
        self.clear_plot_tabs()

        if not results:
            self.clear_step4_plot_buttons()
            if self.step4_plot_buttons_note:
                self.step4_plot_buttons_note.setText("No analysis results available yet.")
            return

        self.create_summary_plot_tab(results)
        self.populate_step4_plot_buttons(results)
        self.log_widget.append("Summary plot ready. Click a test name in Step 4 to view its curve.")
        # Auto-show first test
        self.current_test_index = 0
        self.open_test_plot_from_step4(0)
    
    def create_summary_plot_tab(self, results: List[Dict[str, Any]]):
        """Render researcher-quality reliability summary into self.reliability_widget."""
        if not self.reliability_widget:
            return
        summary_widget = self.reliability_widget

        try:
            fig = summary_widget.figure
            fig.clear()
            fig.patch.set_facecolor('#1a1a1a')

            file_label = Path(self.current_analysis_file_path).name if self.current_analysis_file_path else (
                results[0].get('Source File', 'selected file') if results else 'selected file'
            )
            n_tests = len(results)
            fig.suptitle(
                f'Analysis Reliability Summary  —  {file_label}  ({n_tests} included tests)',
                fontsize=12, fontweight='bold', y=0.99, color='#e0e0e0'
            )

            hardness_values = [r.get('Hardness (GPa)', 0) for r in results if r.get('Hardness (GPa)')]
            modulus_values  = [r.get('Oliver-Pharr Modulus (GPa)', 0) for r in results if r.get('Oliver-Pharr Modulus (GPa)')]
            loading_points = [
                (idx + 1, str(r.get('Test', idx + 1)), r.get('Loading R²', 0))
                for idx, r in enumerate(results)
                if r.get('Loading R²')
            ]
            unloading_points = [
                (idx + 1, str(r.get('Test', idx + 1)), r.get('Unloading Fit R²', 0))
                for idx, r in enumerate(results)
                if r.get('Unloading Fit R²')
            ]
            loading_r2 = [point[2] for point in loading_points]
            unloading_r2 = [point[2] for point in unloading_points]

            ax1 = fig.add_subplot(2, 2, 1)
            ax2 = fig.add_subplot(2, 2, 2)
            ax3 = fig.add_subplot(2, 2, 3)
            ax4 = fig.add_subplot(2, 2, 4)
            for _ax in (ax1, ax2, ax3, ax4):
                _ax.set_facecolor('#0f0f0f')
                for spine in _ax.spines.values():
                    spine.set_edgecolor('#2a2a2a')
                _ax.tick_params(colors='#aaaaaa', labelsize=8)
                _ax.xaxis.label.set_color('#cccccc')
                _ax.yaxis.label.set_color('#cccccc')
                _ax.title.set_color('#e0e0e0')

            # ── Panel 1: R² per test (fit reliability) ────────────────────────
            if loading_r2 or unloading_r2:
                xs = np.arange(1, len(results) + 1)
                tick_labels = [str(r.get('Test', idx + 1)) for idx, r in enumerate(results)]
                if loading_r2:
                    loading_xs = [point[0] for point in loading_points]
                    ax1.plot(loading_xs, loading_r2, 'o-', linewidth=1.8,
                             markersize=6, color='#2980b9', label='Loading R²', zorder=3)
                if unloading_r2:
                    unloading_xs = [point[0] for point in unloading_points]
                    ax1.plot(unloading_xs, unloading_r2, 's-', linewidth=1.8,
                             markersize=6, color='#e74c3c', label='Unloading R²', zorder=3)
                ax1.axhline(0.99, color='#e67e22', linestyle='--', linewidth=1.4,
                            label='ISO threshold  R²=0.99', alpha=0.9)
                ax1.fill_between(xs, 0.99, 1.002, alpha=0.10, color='#27ae60')
                ymin_r2 = max(0.90, min((loading_r2 or [1]) + (unloading_r2 or [1])) - 0.015)
                ax1.set_ylim(ymin_r2, 1.005)
                if len(xs) <= 20:
                    ax1.set_xticks(xs)
                    ax1.set_xticklabels(tick_labels, rotation=45, ha='right')
                ax1.set_xlabel('Included test', fontsize=10)
                ax1.set_ylabel('R²', fontsize=10)
                ax1.set_title('Curve Fit Quality per Test', fontweight='bold', fontsize=11)
                ax1.legend(fontsize=8, loc='lower left', framealpha=0.9,
                           facecolor='#1a1a1a', edgecolor='#3a3a3a', labelcolor='#e0e0e0')
                ax1.grid(True, alpha=0.15, linestyle=':', color='#ffffff')
            else:
                ax1.text(0.5, 0.5, 'No R² data', ha='center', va='center',
                         transform=ax1.transAxes, color='#888888')
                ax1.set_title('Curve Fit Quality', fontweight='bold')

            # ── Panel 2: Hardness distribution ────────────────────────────────
            _stat_box = dict(boxstyle='round,pad=0.5', facecolor='#0f0f0f',
                             edgecolor='#00a8cc', linewidth=1.2, alpha=0.95)
            if hardness_values:
                mu_h, sd_h = np.mean(hardness_values), np.std(hardness_values)
                n_bins = min(15, max(4, len(hardness_values) // 2))
                ax2.hist(hardness_values, bins=n_bins, color='#00a8cc', alpha=0.75,
                         edgecolor='#0f0f0f', linewidth=0.8)
                ax2.axvline(mu_h, color='#ff6b6b', linewidth=2, linestyle='--',
                            label=f'Mean {mu_h:.3f} GPa')
                ax2.axvspan(mu_h - sd_h, mu_h + sd_h, alpha=0.08, color='#ff6b6b')
                cv_h = sd_h / mu_h * 100 if mu_h else 0
                ax2.set_xlabel('Hardness  H  (GPa)', fontsize=10)
                ax2.set_ylabel('Count', fontsize=10)
                ax2.set_title('Hardness Distribution', fontweight='bold', fontsize=11)
                ax2.grid(True, alpha=0.15, axis='y', linestyle=':', color='#ffffff')
            else:
                ax2.text(0.5, 0.5, 'No hardness data', ha='center', va='center',
                         transform=ax2.transAxes, color='#888888')
                ax2.set_title('Hardness Distribution', fontweight='bold')

            # ── Panel 3: Reduced modulus distribution ─────────────────────────
            if modulus_values:
                mu_e, sd_e = np.mean(modulus_values), np.std(modulus_values)
                n_bins = min(15, max(4, len(modulus_values) // 2))
                ax3.hist(modulus_values, bins=n_bins, color='#2ecc71', alpha=0.75,
                         edgecolor='#0f0f0f', linewidth=0.8)
                ax3.axvline(mu_e, color='#ff6b6b', linewidth=2, linestyle='--',
                            label=f'Mean {mu_e:.2f} GPa')
                ax3.axvspan(mu_e - sd_e, mu_e + sd_e, alpha=0.08, color='#ff6b6b')
                cv_e = sd_e / mu_e * 100 if mu_e else 0
                ax3.set_xlabel('Reduced Modulus  Er  (GPa)', fontsize=10)
                ax3.set_ylabel('Count', fontsize=10)
                ax3.set_title('Reduced Modulus Distribution', fontweight='bold', fontsize=11)
                ax3.grid(True, alpha=0.15, axis='y', linestyle=':', color='#ffffff')
            else:
                ax3.text(0.5, 0.5, 'No modulus data', ha='center', va='center',
                         transform=ax3.transAxes, color='#888888')
                ax3.set_title('Reduced Modulus Distribution', fontweight='bold')

            # ── Panel 4: Summary statistics ────────────────────────────────────
            ax4.axis('off')
            ax4.set_facecolor('#0f0f0f')
            pass_loading   = sum(1 for r in loading_r2   if r >= 0.99)
            pass_unloading = sum(1 for r in unloading_r2 if r >= 0.99)

            summary_stats = []
            if hardness_values:
                mu_h, sd_h = np.mean(hardness_values), np.std(hardness_values)
                cv_h = sd_h / mu_h * 100 if mu_h else 0
                summary_stats += [
                    "Hardness (GPa):",
                    f"  n    : {len(hardness_values)}",
                    f"  Mean : {mu_h:.3f}",
                    f"  SD   : {sd_h:.3f}",
                    f"  CV   : {cv_h:.1f} %",
                    f"  Range: {np.min(hardness_values):.3f} – {np.max(hardness_values):.3f}", ""]
            if modulus_values:
                mu_e, sd_e = np.mean(modulus_values), np.std(modulus_values)
                cv_e = sd_e / mu_e * 100 if mu_e else 0
                summary_stats += [
                    "Reduced Modulus (GPa):",
                    f"  n    : {len(modulus_values)}",
                    f"  Mean : {mu_e:.2f}",
                    f"  SD   : {sd_e:.2f}",
                    f"  CV   : {cv_e:.1f} %",
                    f"  Range: {np.min(modulus_values):.2f} – {np.max(modulus_values):.2f}", ""]
            summary_stats += [
                "Fit Quality  (ISO 14577-1, R²≥0.99):",
                f"  Loading  pass: {pass_loading}/{len(loading_r2)}",
                f"  Unloading pass: {pass_unloading}/{len(unloading_r2)}",
                f"  Total tests  : {n_tests}"]

            ax4.text(0.05, 0.95, "\n".join(summary_stats), transform=ax4.transAxes,
                     fontfamily='monospace', fontsize=9, color='#e0e0e0',
                     verticalalignment='top',
                     bbox=dict(boxstyle='round,pad=0.9', facecolor='#0f0f0f',
                               edgecolor='#00a8cc', linewidth=1.5, alpha=0.95))
            ax4.set_title('Summary Statistics', fontweight='bold', fontsize=11, color='#e0e0e0')

            fig.text(
                0.5, 0.005,
                "ISO 14577-1:2015 — R² ≥ 0.99 required  |  CV > 10% may indicate surface effects",
                ha='center', fontsize=7.5, color='#666666', style='italic'
            )

            fig.tight_layout(rect=[0, 0.025, 1, 0.96])
            summary_widget.canvas.draw()

        except Exception as e:
            summary_widget.figure.clear()
            ax_err = summary_widget.figure.add_subplot(111)
            ax_err.set_facecolor('#0f0f0f')
            ax_err.text(0.5, 0.5, f'Error creating summary:\n{str(e)}',
                        transform=ax_err.transAxes, ha='center', va='center', color='#e0e0e0',
                        bbox=dict(boxstyle='round,pad=0.8', facecolor='#3a0000', alpha=0.9), fontsize=9)
            ax_err.axis('off')
            summary_widget.canvas.draw()
    
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
            raw_loading_disp, raw_loading_load, raw_unloading_disp, raw_unloading_load, plot_load_cap, unloading_plot_shift = (
                self._prepare_peak_matched_plot_data(
                    raw_loading_disp,
                    raw_loading_load,
                    raw_unloading_disp,
                    raw_unloading_load
                )
            )

            loading_fit_disp = []
            loading_fit_load = []
            loading_r2_value = curve.get('r_squared', 0.0)
            loading_offset_h0 = None
            loading_power_C = None
            loading_power_n = None
            if raw_loading_disp and raw_loading_load and len(raw_loading_disp) >= 4:
                h_all = np.asarray(raw_loading_disp, dtype=float)
                p_all = np.asarray(raw_loading_load, dtype=float)
                valid_mask = np.isfinite(h_all) & np.isfinite(p_all) & (h_all > 0) & (p_all > 0)
                h_valid = h_all[valid_mask]
                p_valid = p_all[valid_mask]
                if h_valid.size >= 4:
                    def loading_power_offset_model(h, C_fit, n_fit, h0_fit):
                        return C_fit * np.power(np.maximum(h - h0_fit, 1e-12), n_fit)

                    min_h = float(np.min(h_valid))
                    max_h = float(np.max(h_valid))
                    h_span = max(max_h - min_h, 1e-9)
                    h0_guess = min_h - 0.02 * h_span
                    shifted_h = np.maximum(h_valid - h0_guess, 1e-12)
                    try:
                        log_h = np.log(shifted_h)
                        log_p = np.log(p_valid)
                        n_guess, log_C_guess = np.polyfit(log_h, log_p, 1)
                        C_guess = float(np.exp(log_C_guess))
                        n_guess = float(np.clip(n_guess, 0.1, 10.0))
                    except Exception:
                        n_guess = 2.0
                        C_guess = float(np.max(p_valid) / max((max_h - h0_guess) ** n_guess, 1e-12))

                    h0_lower = min_h - 2.0 * h_span
                    h0_upper = min_h - 1e-9
                    try:
                        popt, _pcov = curve_fit(
                            loading_power_offset_model,
                            h_valid,
                            p_valid,
                            p0=[max(C_guess, 1e-12), n_guess, h0_guess],
                            bounds=([1e-12, 0.1, h0_lower], [np.inf, 10.0, h0_upper]),
                            maxfev=10000
                        )
                        C_exp, n_exp, h0_fit = [float(v) for v in popt]
                    except Exception:
                        def loading_power_fixed_offset_model(h, C_fit, n_fit):
                            return loading_power_offset_model(h, C_fit, n_fit, h0_guess)

                        popt, _pcov = curve_fit(
                            loading_power_fixed_offset_model,
                            h_valid,
                            p_valid,
                            p0=[max(C_guess, 1e-12), n_guess],
                            bounds=([1e-12, 0.1], [np.inf, 10.0]),
                            maxfev=10000
                        )
                        C_exp, n_exp = [float(v) for v in popt]
                        h0_fit = h0_guess

                    h_fit_start = h0_fit
                    h_fit_loading = np.linspace(h_fit_start, max_h, 200)
                    p_fit_loading = loading_power_offset_model(h_fit_loading, C_exp, n_exp, h0_fit)
                    p_fit_loading[0] = 0.0
                    loading_fit_disp = h_fit_loading.tolist()
                    loading_fit_load = p_fit_loading.tolist()
                    p_pred = loading_power_offset_model(h_valid, C_exp, n_exp, h0_fit)
                    ss_res = float(np.sum((p_valid - p_pred) ** 2))
                    ss_tot = float(np.sum((p_valid - np.mean(p_valid)) ** 2))
                    loading_r2_value = (1.0 - ss_res / ss_tot) if ss_tot > 0 else 0.0
                    loading_offset_h0 = h0_fit
                    loading_power_C = C_exp
                    loading_power_n = n_exp

            params = curve.get('parameters', {}) if isinstance(curve.get('parameters', {}), dict) else {}
            h_f_nm = params.get('h_f', None)
            if h_f_nm is not None:
                h_f_nm = float(h_f_nm)

            unloading_fit_disp = []
            unloading_fit_load = []
            if raw_unloading_disp:
                h_unloading_display = np.asarray(raw_unloading_disp, dtype=float)
                h_unloading = h_unloading_display - unloading_plot_shift
                # Prefer explicit fit arrays from the curve_fitting result
                h_fit_seg = np.asarray(curve.get('fit_displacement', []), dtype=float)
                p_fit_seg = np.asarray(curve.get('fit_curve', []), dtype=float)
                p_fit_full = np.asarray(curve.get('fitted_curve', []), dtype=float)
                if h_fit_seg.size == p_fit_seg.size and h_fit_seg.size > 0:
                    unloading_fit_disp = h_fit_seg.tolist()
                    unloading_fit_load = np.maximum(p_fit_seg, 0.0).tolist()
                elif p_fit_full.size == h_unloading.size and p_fit_full.size > 0:
                    unloading_fit_disp = h_unloading.tolist()
                    unloading_fit_load = np.maximum(p_fit_full, 0.0).tolist()

                # Build Oliver-Pharr model curve from parameters when no pre-computed fit exists
                if not unloading_fit_disp and h_f_nm is not None:
                    h_max_u = float(np.max(h_unloading))
                    h_sweep = np.linspace(h_max_u, h_f_nm, 200)
                    method_used = curve.get('method_used') or curve.get('method') or ''
                    if method_used == 'oliver_pharr' and all(k in params for k in ('A', 'm')):
                        p_model = float(params['A']) * np.maximum(h_sweep - h_f_nm, 0.0) ** float(params['m'])
                    elif all(k in params for k in ('P_max', 'm')) and max_disp_nm > 0:
                        denom = max(float(max_disp_nm) - h_f_nm, 1e-12)
                        p_model = float(params['P_max']) * np.power(
                            np.maximum((h_sweep - h_f_nm) / denom, 0.0), float(params['m']))
                    else:
                        p_model = None
                    if p_model is not None:
                        unloading_fit_disp = h_sweep.tolist()
                        unloading_fit_load = np.maximum(p_model, 0.0).tolist()

                # Ensure the fit curve ends exactly at hf (P=0)
                if unloading_fit_disp and h_f_nm is not None:
                    if abs(float(unloading_fit_disp[-1]) - h_f_nm) > 0.5:
                        unloading_fit_disp.append(h_f_nm)
                        unloading_fit_load.append(0.0)

                if unloading_fit_disp and unloading_fit_load and plot_load_cap is not None:
                    h_fit_trim, p_fit_trim = self._finite_xy(unloading_fit_disp, unloading_fit_load)
                    h_fit_trim, p_fit_trim = self._trim_curve_to_load_cap(h_fit_trim, p_fit_trim, plot_load_cap)
                    h_fit_trim = h_fit_trim + unloading_plot_shift
                    unloading_fit_disp = h_fit_trim.tolist()
                    unloading_fit_load = p_fit_trim.tolist()

            # Stiffness tangent line at peak load.
            # Tangent: P(h) = Pmax + S*(h - hmax).  Crosses P=0 at h = hmax - Pmax/S.
            tangent_disp = []
            tangent_load = []
            if 'tangent_displacement' in curve and 'tangent_load' in curve:
                h_t = np.asarray(curve['tangent_displacement'], dtype=float)
                p_t = np.asarray(curve['tangent_load'], dtype=float)
                if h_t.size == p_t.size and h_t.size > 0:
                    if plot_load_cap is not None:
                        h_t, p_t = self._trim_curve_to_load_cap(h_t, np.maximum(p_t, 0.0), plot_load_cap)
                    tangent_disp = (h_t + unloading_plot_shift).tolist()
                    tangent_load = np.maximum(p_t, 0.0).tolist()
            if not tangent_disp and stiffness_n_m > 0 and max_disp_nm > 0 and max_load_mn > 0:
                # Compute tangent from S, hmax, Pmax (units: mN/nm)
                S_mN_nm = stiffness_n_m / 1e6
                h_zero = max_disp_nm - max_load_mn / S_mN_nm  # where tangent hits P=0
                h_zero = max(0.0, h_zero)
                h_t = np.asarray([h_zero, float(max_disp_nm)], dtype=float)
                p_t = np.asarray([0.0, float(max_load_mn)], dtype=float)
                if plot_load_cap is not None:
                    h_t, p_t = self._trim_curve_to_load_cap(h_t, p_t, plot_load_cap)
                tangent_disp = (h_t + unloading_plot_shift).tolist()
                tangent_load = p_t.tolist()

            normalized.append({
                'Test': test_name,
                'Source File': Path(results.get('file_path', '')).name if results.get('file_path') else '',
                'Hardness (GPa)': hardness.get('hardness_gpa', 0.0),
                'Oliver-Pharr Modulus (GPa)': sample_mod.get('sample_modulus_gpa', 0.0),
                'Loading R²': loading_r2_value,
                'Loading Power C': loading_power_C,
                'Loading Power n': loading_power_n,
                'Loading Offset h0 (nm)': loading_offset_h0,
                'Plot Peak Load Cap (mN)': plot_load_cap,
                'Unloading Plot Shift (nm)': unloading_plot_shift,
                'Unloading Fit R²': curve.get('r_squared', 0.0),
                'Max Load (mN)': max_load_mn,
                'Max Displacement (nm)': max_disp_nm,
                'S (N/m)': stiffness_n_m,
                'Hc (m)': contact_depth_nm * 1e-9 if contact_depth_nm else 0.0,
                'hf (nm)': h_f_nm,
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

    @staticmethod
    def _finite_xy(displacement_values, load_values):
        """Return finite displacement/load arrays while preserving order."""
        h = np.asarray(displacement_values, dtype=float)
        p = np.asarray(load_values, dtype=float)
        if h.size != p.size or h.size == 0:
            return np.asarray([], dtype=float), np.asarray([], dtype=float)
        mask = np.isfinite(h) & np.isfinite(p)
        return h[mask], p[mask]

    @staticmethod
    def _remove_high_load_points(h: np.ndarray, p: np.ndarray, fraction: float = 0.03):
        """Remove the highest-load fraction from a curve for peak-end plotting."""
        if h.size != p.size or h.size < 10:
            return h, p
        n_remove = max(1, int(np.ceil(h.size * fraction)))
        if n_remove >= h.size - 3:
            return h, p

        peak_idx = int(np.argmax(p))
        if peak_idx <= h.size * 0.25:
            return h[n_remove:], p[n_remove:]
        if peak_idx >= h.size * 0.75:
            return h[:-n_remove], p[:-n_remove]

        remove_indices = np.argsort(p)[-n_remove:]
        keep_mask = np.ones(h.size, dtype=bool)
        keep_mask[remove_indices] = False
        return h[keep_mask], p[keep_mask]

    @staticmethod
    def _trim_curve_to_load_cap(h: np.ndarray, p: np.ndarray, load_cap: float):
        """Trim the high-load end of a curve and include an interpolated cap point."""
        if h.size != p.size or h.size < 2 or not np.isfinite(load_cap):
            return h, p
        if np.max(p) <= load_cap:
            return h, p

        max_idx = int(np.argmax(p))
        high_load_at_tail = max_idx >= (h.size / 2)

        if high_load_at_tail:
            search_range = range(h.size - 2, -1, -1)
        else:
            search_range = range(0, h.size - 1)

        for idx in search_range:
            p0, p1 = p[idx], p[idx + 1]
            if (p0 - load_cap) * (p1 - load_cap) <= 0 and p0 != p1:
                t = (load_cap - p0) / (p1 - p0)
                h_cross = h[idx] + t * (h[idx + 1] - h[idx])
                if high_load_at_tail:
                    return (
                        np.concatenate([h[:idx + 1], [h_cross]]),
                        np.concatenate([p[:idx + 1], [load_cap]])
                    )
                return (
                    np.concatenate([[h_cross], h[idx + 1:]]),
                    np.concatenate([[load_cap], p[idx + 1:]])
                )

        keep_mask = p <= load_cap
        return h[keep_mask], p[keep_mask]

    @staticmethod
    def _matched_endpoint_displacement(h: np.ndarray, p: np.ndarray, load_cap: float) -> Optional[float]:
        """Return the displacement at the matched high-load endpoint."""
        if h.size != p.size or h.size == 0 or not np.isfinite(load_cap):
            return None
        cap_indices = np.where(np.isclose(p, load_cap, rtol=1e-6, atol=1e-9))[0]
        if cap_indices.size > 0:
            return float(h[int(cap_indices[-1])])
        return float(h[int(np.argmax(p))])

    def _prepare_peak_matched_plot_data(self, loading_disp, loading_load, unloading_disp, unloading_load):
        """Trim peak-end plot data and align loading/unloading high-load endpoints."""
        h_load, p_load = self._finite_xy(loading_disp, loading_load)
        h_unload, p_unload = self._finite_xy(unloading_disp, unloading_load)

        h_load, p_load = self._remove_high_load_points(h_load, p_load)
        h_unload, p_unload = self._remove_high_load_points(h_unload, p_unload)

        load_cap = None
        unloading_shift = 0.0
        if h_load.size > 0 and h_unload.size > 0:
            load_cap = float(min(np.max(p_load), np.max(p_unload)))
            h_load, p_load = self._trim_curve_to_load_cap(h_load, p_load, load_cap)
            h_unload, p_unload = self._trim_curve_to_load_cap(h_unload, p_unload, load_cap)
            loading_endpoint = self._matched_endpoint_displacement(h_load, p_load, load_cap)
            unloading_endpoint = self._matched_endpoint_displacement(h_unload, p_unload, load_cap)
            if loading_endpoint is not None and unloading_endpoint is not None:
                unloading_shift = loading_endpoint - unloading_endpoint
                h_unload = h_unload + unloading_shift

        return h_load.tolist(), p_load.tolist(), h_unload.tolist(), p_unload.tolist(), load_cap, unloading_shift
    
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
        self.excluded_test_indices.clear()
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
            
            self.log_final_calculation_summary(normalized_results)
            
            if normalized_results:
                self.create_plot_tabs(normalized_results)
                # Switch right panel to Reliability tab after analysis
                if self.results_panel_tabs:
                    for i in range(self.results_panel_tabs.count()):
                        if self.results_panel_tabs.tabText(i) == 'Reliability':
                            self.results_panel_tabs.setCurrentIndex(i)
                            break
        
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
        included_results = self.get_included_results()
        if not included_results:
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
                df = pd.DataFrame(included_results)
                df.to_excel(file_path, index=False, engine='openpyxl')
                self.log_widget.append(f"📊 Results exported to: {file_path}")
                QMessageBox.information(self, "Export Successful", f"Results exported to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export to Excel:\n{str(e)}")
    
    def export_to_csv(self):
        """Export results to CSV file"""
        included_results = self.get_included_results()
        if not included_results:
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
                df = pd.DataFrame(included_results)
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
