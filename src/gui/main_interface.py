#!/usr/bin/env python3
"""
Nanoindentation Analysis GUI
A comprehensive PyQt5 interface for the FixedIndentXLSAnalyzer
ISO 14577-4:2016 compliant nanoindentation analysis with advanced tip calibration
"""

import sys
import os
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

try:
    from ..analysis.main_analyzer import NanoindentationAnalyzer, analyze_nanoindentation_file
    from ..core.standards import ISO14577Constants, AnalysisConfig
    from ..analysis.mechanical_calculator import MechanicalPropertiesCalculator
    # Keep the old analyzer for backward compatibility
    from ..analysis.enhanced_analyzer import FixedIndentXLSAnalyzer
except ImportError as e:
    print(f"Warning: Could not import new modular components: {e}")
    # Fallback to absolute imports
    try:
        from analysis.main_analyzer import NanoindentationAnalyzer, analyze_nanoindentation_file
        from core.standards import ISO14577Constants, AnalysisConfig
        from analysis.mechanical_calculator import MechanicalPropertiesCalculator
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
    
    def __init__(self, analyzer=None, file_path=None, use_new_analyzer=True):
        super().__init__()
        self.analyzer = analyzer
        self.file_path = file_path
        self.use_new_analyzer = use_new_analyzer
        self.is_cancelled = False
        self.logger = logging.getLogger('AnalysisWorker')
        
        # Debug log initialization
        self.logger.debug(f"AnalysisWorker initialized:")
        self.logger.debug(f"  - file_path: {file_path}")
        self.logger.debug(f"  - use_new_analyzer: {use_new_analyzer}")
        self.logger.debug(f"  - analyzer type: {type(analyzer).__name__ if analyzer else 'None'}")
    
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
        new_analyzer = NanoindentationAnalyzer()
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
        results = new_analyzer.analyze_file(self.file_path)
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
            
            # Try to get actual curve data from the analyzer
            test_number = test_data.get('Test', 'N/A')
            has_curve_data = False
            
            # If analyzer has curve data, plot it
            if hasattr(analyzer, 'curve_data') and analyzer.curve_data:
                for test_id, curve_info in analyzer.curve_data.items():
                    if str(test_id) == str(test_number):
                        # Plot loading and unloading curves
                        if 'loading_displacement' in curve_info and 'loading_load' in curve_info:
                            ax.plot(curve_info['loading_displacement'], curve_info['loading_load'], 
                                   'b-', linewidth=2, label='Loading', alpha=0.8)
                        
                        if 'unloading_displacement' in curve_info and 'unloading_load' in curve_info:
                            ax.plot(curve_info['unloading_displacement'], curve_info['unloading_load'], 
                                   'r-', linewidth=2, label='Unloading', alpha=0.8)
                        
                        # Plot fits if available
                        if 'loading_fit_displacement' in curve_info and 'loading_fit_load' in curve_info:
                            ax.plot(curve_info['loading_fit_displacement'], curve_info['loading_fit_load'], 
                                   'b--', linewidth=1, label='Loading Fit', alpha=0.6)
                        
                        if 'unloading_fit_displacement' in curve_info and 'unloading_fit_load' in curve_info:
                            ax.plot(curve_info['unloading_fit_displacement'], curve_info['unloading_fit_load'], 
                                   'r--', linewidth=1, label='Unloading Fit', alpha=0.6)
                        
                        ax.legend()
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
                ax.legend()
                ax.text(0.5, 0.5, 'Simulated Curve\n(Raw data not available)', 
                       transform=ax.transAxes, ha='center', va='center',
                       bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7))
            
            # Add results text box
            result_text = f"""Test: {test_data.get('Test', 'N/A')}
Hardness: {test_data.get('Hardness (GPa)', 0):.3f} GPa
Modulus: {test_data.get('Oliver-Pharr Modulus (GPa)', 0):.1f} GPa
Max Load: {test_data.get('Max Load (mN)', 0):.2f} mN
Max Disp: {test_data.get('Max Displacement (nm)', 0):.1f} nm
Contact Area: {test_data.get('A (m^2)', 0)*1e18:.0f} nm²
Stiffness: {test_data.get('S (N/m)', 0)/1e6:.2f} mN/nm
Loading R²: {test_data.get('Loading R²', 0):.4f}
Unloading R²: {test_data.get('Unloading Fit R²', 0):.4f}"""
            
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
        
        # Get all unique keys from results
        all_keys = set()
        for result in results:
            all_keys.update(result.keys())
        
        # Define key columns to display first
        priority_keys = [
            'Test', 'Hardness (GPa)', 'Oliver-Pharr Hardness (GPa)', 
            'Oliver-Pharr Modulus (GPa)', 'CSM Hardness (GPa)',
            'Loading R²', 'Unloading Fit R²', 'S (N/m)', 'A (m^2)',
            'Hc (m)', 'Pmax (N)', 'Calibration Factor'
        ]
        
        # Order columns: priority first, then others alphabetically
        other_keys = sorted([k for k in all_keys if k not in priority_keys])
        ordered_keys = [k for k in priority_keys if k in all_keys] + other_keys
        
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
    
    def __init__(self):
        super().__init__()
        
        # Initialize attributes
        self.analyzer: Optional[FixedIndentXLSAnalyzer] = None
        self.analysis_worker: Optional[AnalysisWorker] = None
        self.current_results: List[Dict[str, Any]] = []
        self.plots_tab_widget: Optional[QTabWidget] = None
        
        # Set up the GUI
        self.init_ui()
        self.setStyleSheet(self.get_stylesheet())
        
        # Center the window
        self.center_window()
    
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
        
        # File selection group
        file_group = QGroupBox("📁 File Selection")
        file_layout = QVBoxLayout(file_group)
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select Excel file containing nanoindentation data...")
        self.file_path_edit.setReadOnly(True)
        file_layout.addWidget(self.file_path_edit)
        
        file_button_layout = QHBoxLayout()
        self.browse_button = QPushButton("📁 Browse")
        self.browse_button.clicked.connect(self.browse_file)
        file_button_layout.addWidget(self.browse_button)
        
        self.reload_button = QPushButton("🔄 Reload")
        self.reload_button.clicked.connect(self.reload_file)
        self.reload_button.setEnabled(False)
        file_button_layout.addWidget(self.reload_button)
        
        file_layout.addLayout(file_button_layout)
        layout.addWidget(file_group)
        
        # Analysis settings group
        settings_group = QGroupBox("⚙️ Analysis Settings")
        settings_layout = QGridLayout(settings_group)
        
        # Plot settings
        self.generate_plots_cb = QCheckBox("Generate Plots")
        self.generate_plots_cb.setChecked(True)
        settings_layout.addWidget(self.generate_plots_cb, 0, 0)
        
        self.export_plots_cb = QCheckBox("Export Plots")
        self.export_plots_cb.setChecked(True)
        settings_layout.addWidget(self.export_plots_cb, 0, 1)
        
        # ISO compliance settings
        settings_layout.addWidget(QLabel("Min R² for fits:"), 1, 0)
        self.min_r2_spinbox = QDoubleSpinBox()
        self.min_r2_spinbox.setRange(0.90, 0.999)
        self.min_r2_spinbox.setValue(0.98)
        self.min_r2_spinbox.setDecimals(3)
        self.min_r2_spinbox.setSingleStep(0.001)
        settings_layout.addWidget(self.min_r2_spinbox, 1, 1)
        
        layout.addWidget(settings_group)
        
        # Analysis buttons
        button_group = QGroupBox("🚀 Analysis Control")
        button_layout = QVBoxLayout(button_group)
        
        self.analyze_button = QPushButton("🔬 Start Analysis")
        self.analyze_button.clicked.connect(self.start_analysis)
        self.analyze_button.setEnabled(False)
        self.analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        button_layout.addWidget(self.analyze_button)
        
        self.cancel_button = QPushButton("❌ Cancel Analysis")
        self.cancel_button.clicked.connect(self.cancel_analysis)
        self.cancel_button.setEnabled(False)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        button_layout.addWidget(self.cancel_button)
        
        layout.addWidget(button_group)
        
        # Results export group
        export_group = QGroupBox("💾 Export Results")
        export_layout = QVBoxLayout(export_group)
        
        self.export_excel_button = QPushButton("📊 Export to Excel")
        self.export_excel_button.clicked.connect(self.export_to_excel)
        self.export_excel_button.setEnabled(False)
        export_layout.addWidget(self.export_excel_button)
        
        self.export_csv_button = QPushButton("📄 Export to CSV")
        self.export_csv_button.clicked.connect(self.export_to_csv)
        self.export_csv_button.setEnabled(False)
        export_layout.addWidget(self.export_csv_button)
        
        layout.addWidget(export_group)
        
        # Info group
        info_group = QGroupBox("ℹ️ Information")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel("""
• ISO 14577-4:2016 compliant analysis
• Advanced tip area function calibration
• Oliver-Pharr method implementation
• Power law and polynomial curve fitting
• Automatic horizontal segment detection
• Quality validation and compliance scoring
        """.strip())
        info_text.setWordWrap(True)
        info_text.setStyleSheet("font-size: 10px; color: #7f8c8d;")
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        return panel
    
    def create_results_panel(self):
        """Create the results panel with tabs"""
        tab_widget = QTabWidget()
        
        # Results table tab
        self.results_table = ResultsTableWidget()
        tab_widget.addTab(self.results_table, "📊 Results Table")
        
        # Plot tabs container - this will hold subtabs for each test
        self.plots_tab_widget = QTabWidget()
        tab_widget.addTab(self.plots_tab_widget, "📈 Plots")
        
        # Log tab
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        # Use system monospace font with fallbacks
        log_font = QFont()
        log_font.setFamily("Monaco")  # macOS monospace
        log_font.setStyleHint(QFont.Monospace)  # Fallback to system monospace
        log_font.setPointSize(9)
        self.log_widget.setFont(log_font)
        tab_widget.addTab(self.log_widget, "📝 Analysis Log")
        
        return tab_widget
    
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
    
    def create_plot_tabs(self, results: List[Dict[str, Any]]):
        """Create individual plot tabs for each test result"""
        self.clear_plot_tabs()
        
        if not results:
            # Add a placeholder tab if no results
            placeholder = QLabel("No plots available")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("color: #888888; font-size: 14px;")
            self.plots_tab_widget.addTab(placeholder, "No Data")
            return
        
        # Create summary tab first
        self.create_summary_plot_tab(results)
        
        # Create a tab for each result (since each result represents a test)
        for i, result in enumerate(results):
            # Create matplotlib widget for this test
            plot_widget = MatplotlibWidget()
            
            # Plot the test data
            try:
                plot_widget.plot_nanoindentation_curve(self.analyzer, result)
            except Exception as e:
                self.log_widget.append(f"⚠️ Error plotting result {i+1}: {str(e)}")
            
            # Create tab name - use test number if available, otherwise use index
            test_id = result.get('Test', f'#{i+1}')
            tab_name = f"Test {test_id}"
            
            # If there are multiple results with same test ID, add index
            existing_tabs = [self.plots_tab_widget.tabText(j) for j in range(self.plots_tab_widget.count())]
            if tab_name in existing_tabs:
                tab_name = f"Test {test_id}-{i+1}"
            
            self.plots_tab_widget.addTab(plot_widget, tab_name)
        
        self.log_widget.append(f"📊 Created {len(results)} plot tabs + summary")
    
    def create_summary_plot_tab(self, results: List[Dict[str, Any]]):
        """Create a summary plot showing statistics for all tests"""
        summary_widget = MatplotlibWidget()
        
        try:
            summary_widget.figure.clear()
            
            # Create subplots for different statistics
            fig = summary_widget.figure
            fig.suptitle('Nanoindentation Analysis Summary', fontsize=16, fontweight='bold')
            
            # Extract data for plotting
            hardness_values = [r.get('Hardness (GPa)', 0) for r in results if r.get('Hardness (GPa)')]
            modulus_values = [r.get('Oliver-Pharr Modulus (GPa)', 0) for r in results if r.get('Oliver-Pharr Modulus (GPa)')]
            loading_r2 = [r.get('Loading R²', 0) for r in results if r.get('Loading R²')]
            unloading_r2 = [r.get('Unloading Fit R²', 0) for r in results if r.get('Unloading Fit R²')]
            
            # Create 2x2 subplot layout
            ax1 = fig.add_subplot(2, 2, 1)
            ax2 = fig.add_subplot(2, 2, 2)
            ax3 = fig.add_subplot(2, 2, 3)
            ax4 = fig.add_subplot(2, 2, 4)
            
            # Hardness histogram
            if hardness_values:
                ax1.hist(hardness_values, bins=min(10, len(hardness_values)), alpha=0.7, color='blue', edgecolor='black')
                ax1.set_xlabel('Hardness (GPa)')
                ax1.set_ylabel('Frequency')
                ax1.set_title(f'Hardness Distribution\n(μ={np.mean(hardness_values):.2f}±{np.std(hardness_values):.2f} GPa)')
                ax1.grid(True, alpha=0.3)
            
            # Modulus histogram
            if modulus_values:
                ax2.hist(modulus_values, bins=min(10, len(modulus_values)), alpha=0.7, color='green', edgecolor='black')
                ax2.set_xlabel('Modulus (GPa)')
                ax2.set_ylabel('Frequency')
                ax2.set_title(f'Modulus Distribution\n(μ={np.mean(modulus_values):.1f}±{np.std(modulus_values):.1f} GPa)')
                ax2.grid(True, alpha=0.3)
            
            # Loading R² values
            if loading_r2:
                test_indices = list(range(1, len(loading_r2) + 1))
                ax3.plot(test_indices, loading_r2, 'bo-', markersize=4, linewidth=1)
                ax3.set_xlabel('Test Number')
                ax3.set_ylabel('Loading R²')
                ax3.set_title(f'Loading Fit Quality\n(μ={np.mean(loading_r2):.4f})')
                ax3.grid(True, alpha=0.3)
                ax3.set_ylim(0.98, 1.002)
            
            # Unloading R² values
            if unloading_r2:
                test_indices = list(range(1, len(unloading_r2) + 1))
                ax4.plot(test_indices, unloading_r2, 'ro-', markersize=4, linewidth=1)
                ax4.set_xlabel('Test Number')
                ax4.set_ylabel('Unloading R²')
                ax4.set_title(f'Unloading Fit Quality\n(μ={np.mean(unloading_r2):.4f})')
                ax4.grid(True, alpha=0.3)
                ax4.set_ylim(0.98, 1.002)
            
            # Adjust layout
            fig.tight_layout()
            summary_widget.canvas.draw()
            
        except Exception as e:
            # Error handling for summary plot
            summary_widget.figure.clear()
            ax = summary_widget.figure.add_subplot(111)
            ax.text(0.5, 0.5, f'Error creating summary plot:\n{str(e)}', 
                   transform=ax.transAxes, ha='center', va='center',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='red', alpha=0.7))
            ax.set_title("Summary Plot Error")
            summary_widget.canvas.draw()
        
        # Add summary tab first
        self.plots_tab_widget.addTab(summary_widget, "📊 Summary")
    
    def browse_file(self):
        """Open file dialog to select Excel file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Nanoindentation Data File",
            str(Path.home()),
            "Excel Files (*.xls *.xlsx);;All Files (*)"
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
            self.reload_button.setEnabled(True)
            self.analyze_button.setEnabled(True)
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
            # Create analyzer instance
            self.analyzer = FixedIndentXLSAnalyzer(filename=file_path)
            
            # Apply settings
            self.analyzer.generatePlot = self.generate_plots_cb.isChecked()
            self.analyzer.hidePlot = True  # Always hide plots in GUI mode
            self.analyzer.export = self.export_plots_cb.isChecked()
            
            # Update ISO compliance settings
            self.analyzer.ISO_MIN_R_SQUARED = self.min_r2_spinbox.value()
            
            # Clear previous results
            self.current_results.clear()
            self.results_table.setRowCount(0)
            self.clear_plot_tabs()
            self.log_widget.clear()
            
            # Setup UI for analysis
            self.analyze_button.setEnabled(False)
            self.cancel_button.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            self.log_widget.append("🔬 Starting nanoindentation analysis...")
            self.log_widget.append(f"📁 File: {file_path}")
            self.log_widget.append(f"⚙️ Settings: Plots={self.generate_plots_cb.isChecked()}, Export={self.export_plots_cb.isChecked()}, Min R²={self.min_r2_spinbox.value()}")
            self.log_widget.append("=" * 60)
            
            # Create and start worker thread
            self.analysis_worker = AnalysisWorker(self.analyzer)
            self.analysis_worker.progress_update.connect(self.update_progress)
            self.analysis_worker.status_update.connect(self.update_status)
            self.analysis_worker.result_ready.connect(self.handle_results)
            self.analysis_worker.error_occurred.connect(self.handle_error)
            self.analysis_worker.finished.connect(self.analysis_finished)
            
            self.analysis_worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start analysis:\n{str(e)}")
            self.analysis_finished()
    
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
    
    def handle_results(self, results: List[Dict[str, Any]]):
        """Handle analysis results"""
        self.current_results = results
        
        if results:
            # Load results into table
            self.results_table.load_results(results)
            
            # Enable export buttons
            self.export_excel_button.setEnabled(True)
            self.export_csv_button.setEnabled(True)
            
            # Log summary
            self.log_widget.append("=" * 60)
            self.log_widget.append(f"✅ Analysis completed successfully!")
            self.log_widget.append(f"📊 {len(results)} tests analyzed")
            
            # Calculate summary statistics
            hardness_values = [r.get('Hardness (GPa)', 0) for r in results if r.get('Hardness (GPa)')]
            if hardness_values:
                mean_hardness = np.mean(hardness_values)
                std_hardness = np.std(hardness_values)
                self.log_widget.append(f"📈 Average Hardness: {mean_hardness:.2f} ± {std_hardness:.2f} GPa")
            
            modulus_values = [r.get('Oliver-Pharr Modulus (GPa)', 0) for r in results if r.get('Oliver-Pharr Modulus (GPa)')]
            if modulus_values:
                mean_modulus = np.mean(modulus_values)
                std_modulus = np.std(modulus_values)
                self.log_widget.append(f"📈 Average Modulus: {mean_modulus:.2f} ± {std_modulus:.2f} GPa")
            
            # Plot first test as example
            if results:
                self.create_plot_tabs(results)
        
        else:
            self.log_widget.append("⚠️ No valid results obtained from analysis")
    
    def handle_error(self, error_message: str):
        """Handle analysis errors"""
        self.log_widget.append(f"❌ Error: {error_message}")
        QMessageBox.critical(self, "Analysis Error", error_message)
    
    def analysis_finished(self):
        """Clean up after analysis finishes"""
        self.analyze_button.setEnabled(True)
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
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results to CSV",
            "nanoindentation_results.csv",
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
