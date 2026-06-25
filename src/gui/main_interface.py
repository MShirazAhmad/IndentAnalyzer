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
import re
import shutil
import pickle
import subprocess
from pathlib import Path
import traceback
from typing import Optional, Dict, Any, List, Set, Tuple
import webbrowser
import logging
import time
import importlib.util
from datetime import datetime
from tempfile import gettempdir

# PyQt5 imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog,
    QProgressBar, QTabWidget, QTableWidget, QTableWidgetItem, QCheckBox,
    QGroupBox, QSplitter, QMessageBox, QScrollArea, QSpinBox, QDoubleSpinBox,
    QComboBox, QFrame, QSizePolicy, QHeaderView, QAbstractItemView, QAction,
    QDialog, QDialogButtonBox, QTabBar, QFormLayout
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer, QSize, QUrl
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPalette, QColor, QPainter, QTextCursor

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    QT_WEBENGINE_AVAILABLE = True
except ImportError:
    QWebEngineView = None
    QT_WEBENGINE_AVAILABLE = False

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

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    go = None
    PLOTLY_AVAILABLE = False

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
CSMAnalyzer = None

try:
    from ..analysis.main_analyzer import NanoindentationAnalyzer, analyze_nanoindentation_file
    from ..core.standards import ISO14577Constants, AnalysisConfig
    from ..analysis.mechanical_calculator import MechanicalPropertiesCalculator
    from ..calibration.nist_methods import NISTCalibrationMethods
    from ..analysis.csm_analyzer import CSMAnalyzer
    # Keep the old analyzer for backward compatibility
    from ..analysis.enhanced_analyzer import FixedIndentXLSAnalyzer
except ImportError as e:
    # Fallback to absolute imports
    try:
        from analysis.main_analyzer import NanoindentationAnalyzer, analyze_nanoindentation_file
        from core.standards import ISO14577Constants, AnalysisConfig
        from analysis.mechanical_calculator import MechanicalPropertiesCalculator
        from calibration.nist_methods import NISTCalibrationMethods
        from analysis.csm_analyzer import CSMAnalyzer
        from analysis.enhanced_analyzer import FixedIndentXLSAnalyzer
    except ImportError as e2:
        # Final fallback - import enhanced analyzer directly by adding to path
        try:
            import os
            analysis_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'analysis')
            sys.path.insert(0, analysis_dir)
            from enhanced_analyzer import FixedIndentXLSAnalyzer
        except ImportError as e3:
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
    handlers = [logging.FileHandler(log_file, encoding='utf-8')]
    if os.environ.get("INDENT_ANALYZER_VERBOSE", "").strip() in {"1", "true", "TRUE", "yes", "YES"}:
        handlers.append(logging.StreamHandler(sys.stdout))
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | %(levelname)8s | %(name)20s | %(funcName)20s:%(lineno)4d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=handlers
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


def app_resource_root() -> Path:
    """Return the repo root in development or the PyInstaller data root when frozen."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


def app_user_data_dir() -> Path:
    """Writable per-user storage for config and bundled sample files."""
    if sys.platform == "darwin":
        data_dir = Path.home() / "Library" / "Application Support" / "IndentAnalyzer"
    else:
        data_dir = Path.home() / ".indentanalyzer"
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    except OSError:
        fallback_dir = Path(gettempdir()) / "IndentAnalyzer"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        return fallback_dir


def resolve_app_icon_path() -> Optional[Path]:
    """Return the first available icon path from repo root, assets, then gui dir."""
    project_root = app_resource_root()
    # Prefer specific branding/icon files (project logo first), then common names.
    icon_candidates = (
        project_root / "src" / "logo" / "NanoInd.png",
        project_root / "src" / "logo" / "NanoInd.jpeg",
        project_root / "src" / "logo" / "NanoInd.jpg",
        project_root / "AppIcon.png",
        project_root / "AppIcon.jpeg",
        project_root / "AppIcon.jpg",
        project_root / "src" / "logo" / "AppIcon.png",
        project_root / "src" / "logo" / "AppIcon.jpeg",
        project_root / "src" / "logo" / "AppIcon.jpg",
        project_root / "icon.png",
        project_root / "assets" / "AppIcon.png",
        project_root / "assets" / "AppIcon.jpeg",
        project_root / "assets" / "AppIcon.jpg",
        project_root / "assets" / "icon.png",
        Path(__file__).resolve().parent / "NanoInd.png",
        Path(__file__).resolve().parent / "NanoInd.jpeg",
        Path(__file__).resolve().parent / "NanoInd.jpg",
        Path(__file__).resolve().parent / "AppIcon.png",
        Path(__file__).resolve().parent / "AppIcon.jpeg",
        Path(__file__).resolve().parent / "AppIcon.jpg",
        Path(__file__).resolve().parent / "icon.png",
    )
    for icon_path in icon_candidates:
        if icon_path.is_file():
            return icon_path
    return None


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
                 min_r_squared=0.98, fit_percent=25.0,
                 file_loader_name='AgilentG200'):
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
        self.file_loader_name = file_loader_name or 'AgilentG200'
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
        self.logger.debug(f"  - file_loader_name: {self.file_loader_name}")
    
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
        if hasattr(new_analyzer, 'data_loader') and hasattr(new_analyzer.data_loader, 'set_loader'):
            new_analyzer.data_loader.set_loader(self.file_loader_name)
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
        self.plot_axis_limits: Dict[str, Optional[float]] = {
            "xmin": None,
            "xmax": None,
            "ymin": None,
            "ymax": None,
        }
        self.plot_subplot_limits: Dict[int, Dict[str, Optional[float]]] = {}
        self.plot_figure_size: Optional[Tuple[float, float]] = None
        self.plot_subplot_layout: Optional[str] = None
        self._applying_plot_settings = False
        self._plot_editor_process: Optional[subprocess.Popen] = None
        self._plot_editor_output_path: Optional[str] = None
        self._plot_editor_stderr: str = ""
        self._last_plot_editor_transfer: Dict[str, Any] = {}
        
        # Create matplotlib figure and canvas with a light background
        self.figure = Figure(figsize=(12, 8), dpi=100, facecolor='#ffffff')
        self.canvas = FigureCanvas(self.figure)
        self._canvas_draw = self.canvas.draw
        self.canvas.draw = self._draw_with_plot_settings
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.plot_editor_action = self._add_plot_editor_button()
        self._apply_light_toolbar_style()
        
        self.canvas.setStyleSheet("background-color: #ffffff;")
        
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.logger.debug("MatplotlibWidget initialized successfully")

    def _draw_with_plot_settings(self, *args, **kwargs):
        self.apply_plot_settings()
        return self._canvas_draw(*args, **kwargs)

    def _add_plot_editor_button(self) -> QAction:
        """Add the large colorful plot-editor launcher to the Matplotlib toolbar."""
        button = QPushButton("Edit Plot")
        button.setToolTip("Open this plot in the external plot editor.")
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumWidth(168)
        button.setMinimumHeight(34)
        button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #00a8cc, stop:0.55 #23c552, stop:1 #ffbe0b);
                color: #ffffff;
                border: 1px solid #0794af;
                border-radius: 8px;
                font-weight: 800;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #05bfdc, stop:0.55 #31d969, stop:1 #ffd166);
            }
            QPushButton:pressed {
                background: #0089a6;
            }
            QPushButton:disabled {
                background: #cfd8dd;
                color: #74828a;
                border-color: #b7c2c8;
            }
        """)
        button.clicked.connect(self.open_in_plot_editor)
        self.toolbar.addSeparator()
        return self.toolbar.addWidget(button)

    def apply_plot_settings(self):
        """Apply persistent user plot settings to all current axes before drawing."""
        if self._applying_plot_settings:
            return
        axes = list(self.figure.axes)
        if not axes:
            return
        self._applying_plot_settings = True
        try:
            if self.plot_figure_size is not None:
                width, height = self.plot_figure_size
                if width > 0 and height > 0:
                    self.figure.set_size_inches(width, height, forward=False)

            if self.plot_subplot_layout:
                self._apply_subplot_layout(axes)

            for ax_index, ax in enumerate(axes):
                limits = dict(self.plot_axis_limits)
                subplot_limits = self.plot_subplot_limits.get(ax_index, {})
                for key, value in subplot_limits.items():
                    if value is not None:
                        limits[key] = value
                x_has_override = limits.get("xmin") is not None or limits.get("xmax") is not None
                y_has_override = limits.get("ymin") is not None or limits.get("ymax") is not None
                if x_has_override:
                    current_xmin, current_xmax = ax.get_xlim()
                    xmin = limits["xmin"] if limits["xmin"] is not None else current_xmin
                    xmax = limits["xmax"] if limits["xmax"] is not None else current_xmax
                    if np.isfinite(xmin) and np.isfinite(xmax) and float(xmax) > float(xmin):
                        ax.set_xlim(float(xmin), float(xmax))
                if y_has_override:
                    current_ymin, current_ymax = ax.get_ylim()
                    ymin = limits["ymin"] if limits["ymin"] is not None else current_ymin
                    ymax = limits["ymax"] if limits["ymax"] is not None else current_ymax
                    if np.isfinite(ymin) and np.isfinite(ymax) and float(ymax) > float(ymin):
                        ax.set_ylim(float(ymin), float(ymax))
        finally:
            self._applying_plot_settings = False

    def reset_plot_settings(self):
        """Clear all manual display settings for this plot widget."""
        self.plot_axis_limits = {"xmin": None, "xmax": None, "ymin": None, "ymax": None}
        self.plot_subplot_limits.clear()
        self.plot_figure_size = None
        self.plot_subplot_layout = None

    def _apply_subplot_layout(self, axes: List[Any]):
        """Stack all visible subplots vertically or horizontally."""
        visible_axes = [ax for ax in axes if ax.get_visible()]
        n_axes = len(visible_axes)
        if n_axes < 2:
            return
        left, right = 0.11, 0.96
        bottom, top = 0.11, 0.92
        gap = 0.075
        if self.plot_subplot_layout == "vertical":
            height = max((top - bottom - gap * (n_axes - 1)) / n_axes, 0.05)
            for idx, ax in enumerate(visible_axes):
                y0 = top - (idx + 1) * height - idx * gap
                ax.set_position([left, y0, right - left, height])
        elif self.plot_subplot_layout == "horizontal":
            width = max((right - left - gap * (n_axes - 1)) / n_axes, 0.05)
            for idx, ax in enumerate(visible_axes):
                x0 = left + idx * (width + gap)
                ax.set_position([x0, bottom, width, top - bottom])

    def open_plot_settings_dialog(self):
        """Open per-plot controls for limits and aspect ratio."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Configure Plot")
        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        axes = list(self.figure.axes)
        if axes:
            xlim = axes[0].get_xlim()
            ylim = axes[0].get_ylim()
        else:
            xlim = (0.0, 1.0)
            ylim = (0.0, 1.0)
        fig_w, fig_h = self.plot_figure_size or tuple(float(v) for v in self.figure.get_size_inches())

        target_combo = QComboBox()
        target_combo.addItem("All subplots", None)
        for idx, ax in enumerate(axes):
            title = ax.get_title().strip()
            label = f"Subplot {idx + 1}"
            if title:
                label += f" - {title[:32]}"
            target_combo.addItem(label, idx)
        target_combo.setToolTip("For CSM plots, set shared X limits on All subplots and Y limits per subplot.")
        form.addRow("Apply limits to:", target_combo)

        limit_widgets: Dict[str, Tuple[QCheckBox, QDoubleSpinBox]] = {}

        def add_limit_row(key: str, label: str, current_value: float):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(6)
            checkbox = QCheckBox("manual")
            checkbox.setChecked(self.plot_axis_limits.get(key) is not None)
            spin = QDoubleSpinBox()
            spin.setRange(-1e12, 1e12)
            spin.setDecimals(6)
            spin.setSingleStep(1.0)
            spin.setValue(float(self.plot_axis_limits.get(key) if self.plot_axis_limits.get(key) is not None else current_value))
            spin.setEnabled(checkbox.isChecked())
            checkbox.toggled.connect(spin.setEnabled)
            row_layout.addWidget(checkbox)
            row_layout.addWidget(spin, 1)
            form.addRow(label, row)
            limit_widgets[key] = (checkbox, spin)

        def selected_axis_index() -> Optional[int]:
            value = target_combo.currentData()
            return int(value) if value is not None else None

        def current_target_limits() -> Dict[str, Optional[float]]:
            axis_index = selected_axis_index()
            if axis_index is None:
                return self.plot_axis_limits
            return self.plot_subplot_limits.get(
                axis_index,
                {"xmin": None, "xmax": None, "ymin": None, "ymax": None},
            )

        def current_target_axis_limits() -> Tuple[Tuple[float, float], Tuple[float, float]]:
            axis_index = selected_axis_index()
            if axis_index is not None and 0 <= axis_index < len(axes):
                return axes[axis_index].get_xlim(), axes[axis_index].get_ylim()
            if axes:
                return axes[0].get_xlim(), axes[0].get_ylim()
            return (0.0, 1.0), (0.0, 1.0)

        def load_limit_widgets():
            target_limits = current_target_limits()
            target_xlim, target_ylim = current_target_axis_limits()
            defaults = {
                "xmin": target_xlim[0],
                "xmax": target_xlim[1],
                "ymin": target_ylim[0],
                "ymax": target_ylim[1],
            }
            for key, (checkbox, spin) in limit_widgets.items():
                value = target_limits.get(key)
                checkbox.setChecked(value is not None)
                spin.setValue(float(value if value is not None else defaults[key]))
                spin.setEnabled(value is not None)

        add_limit_row("xmin", "X min:", xlim[0])
        add_limit_row("xmax", "X max:", xlim[1])
        add_limit_row("ymin", "Y min:", ylim[0])
        add_limit_row("ymax", "Y max:", ylim[1])
        target_combo.currentIndexChanged.connect(load_limit_widgets)

        size_row = QWidget()
        size_layout = QHBoxLayout(size_row)
        size_layout.setContentsMargins(0, 0, 0, 0)
        size_layout.setSpacing(6)
        size_check = QCheckBox("manual")
        size_check.setChecked(self.plot_figure_size is not None)
        width_spin = QDoubleSpinBox()
        width_spin.setRange(1.0, 80.0)
        width_spin.setDecimals(2)
        width_spin.setSingleStep(0.5)
        width_spin.setSuffix(" in")
        width_spin.setValue(float(fig_w))
        height_spin = QDoubleSpinBox()
        height_spin.setRange(1.0, 80.0)
        height_spin.setDecimals(2)
        height_spin.setSingleStep(0.5)
        height_spin.setSuffix(" in")
        height_spin.setValue(float(fig_h))
        width_spin.setEnabled(size_check.isChecked())
        height_spin.setEnabled(size_check.isChecked())
        size_check.toggled.connect(width_spin.setEnabled)
        size_check.toggled.connect(height_spin.setEnabled)
        size_layout.addWidget(size_check)
        size_layout.addWidget(QLabel("W"))
        size_layout.addWidget(width_spin)
        size_layout.addWidget(QLabel("H"))
        size_layout.addWidget(height_spin)
        form.addRow("Image aspect ratio:", size_row)

        subplot_layout_combo = QComboBox()
        subplot_layout_combo.addItems(["Original", "Vertical", "Horizontal"])
        if self.plot_subplot_layout == "vertical":
            subplot_layout_combo.setCurrentText("Vertical")
        elif self.plot_subplot_layout == "horizontal":
            subplot_layout_combo.setCurrentText("Horizontal")
        else:
            subplot_layout_combo.setCurrentText("Original")
        subplot_layout_combo.setToolTip("Re-stack subplots in this result view as rows or columns.")
        form.addRow("Subplot stack:", subplot_layout_combo)

        layout.addLayout(form)
        note = QLabel(
            "For CSM plots, use All subplots for shared X limits, then choose each subplot "
            "to set separate hardness/modulus Y limits. Settings persist when the plot redraws."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color:#5e6a72;")
        layout.addWidget(note)

        buttons = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Reset | QDialogButtonBox.Close)
        layout.addWidget(buttons)

        def apply_settings():
            axis_index = selected_axis_index()
            target_limits = {
                key: float(spin.value()) if checkbox.isChecked() else None
                for key, (checkbox, spin) in limit_widgets.items()
            }
            if axis_index is None:
                self.plot_axis_limits = target_limits
            else:
                self.plot_subplot_limits[axis_index] = target_limits
            if size_check.isChecked():
                self.plot_figure_size = (float(width_spin.value()), float(height_spin.value()))
            else:
                self.plot_figure_size = None
            layout_choice = subplot_layout_combo.currentText()
            if layout_choice == "Vertical":
                self.plot_subplot_layout = "vertical"
            elif layout_choice == "Horizontal":
                self.plot_subplot_layout = "horizontal"
            else:
                self.plot_subplot_layout = None
            self.canvas.draw()

        def reset_settings():
            self.reset_plot_settings()
            for key, (checkbox, spin) in limit_widgets.items():
                checkbox.setChecked(False)
            size_check.setChecked(False)
            subplot_layout_combo.setCurrentText("Original")
            load_limit_widgets()
            self.canvas.draw()

        buttons.button(QDialogButtonBox.Apply).clicked.connect(apply_settings)
        buttons.button(QDialogButtonBox.Reset).clicked.connect(reset_settings)
        buttons.rejected.connect(dialog.reject)
        buttons.button(QDialogButtonBox.Close).clicked.connect(dialog.accept)
        dialog.exec_()

    def _find_plot_editor_python(self) -> Optional[str]:
        candidates: List[str] = []
        local_venv_python = app_resource_root() / ".figureforge-venv" / "bin" / "python"
        if local_venv_python.exists():
            candidates.append(str(local_venv_python))
        for name in ("python3.13", "python3.12", "python3.11", "python3", "python"):
            path = shutil.which(name)
            if path and path not in candidates:
                candidates.append(path)
        if sys.executable and sys.executable not in candidates:
            candidates.append(sys.executable)

        for python_exe in candidates:
            try:
                result = subprocess.run(
                    [python_exe, "-c", "import FigureForge"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=4,
                    check=False,
                )
            except Exception:
                continue
            if result.returncode == 0:
                return python_exe
        return None

    def _ensure_plot_editor_plugins(self, python_exe: str):
        """Install lightweight IndentAnalyzer helpers into the local plot-editor plugin folder."""
        try:
            plugin_path_text = subprocess.check_output(
                [
                    python_exe,
                    "-c",
                    (
                        "import pathlib, FigureForge; "
                        "print(pathlib.Path(FigureForge.__file__).resolve().parent / "
                        "'plugins' / 'indent_subplot_layout.py')"
                    ),
                ],
                text=True,
                timeout=5,
            ).strip()
            if not plugin_path_text:
                return
            plugin_path = Path(plugin_path_text)
            plugin_path.parent.mkdir(parents=True, exist_ok=True)
            plugin_code = '''from matplotlib.figure import Figure
from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QVBoxLayout


class IndentSubplotLayout:
    name = "Subplot Layout"
    tooltip = "Stack all subplots vertically or horizontally."
    submenu = "IndentAnalyzer"

    def run(self, obj):
        fig = obj if isinstance(obj, Figure) else getattr(obj, "figure", None)
        if fig is None or len(fig.axes) < 2:
            return

        dialog = QDialog()
        dialog.setWindowTitle("Subplot Layout")
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        mode_combo = QComboBox()
        mode_combo.addItems(["Vertical", "Horizontal"])
        form.addRow("Stack:", mode_combo)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec() != QDialog.Accepted:
            return

        visible_axes = [ax for ax in fig.axes if ax.get_visible()]
        if len(visible_axes) < 2:
            return
        left, right = 0.11, 0.96
        bottom, top = 0.11, 0.92
        gap = 0.075
        mode = mode_combo.currentText()
        if mode == "Vertical":
            height = max((top - bottom - gap * (len(visible_axes) - 1)) / len(visible_axes), 0.05)
            for idx, ax in enumerate(visible_axes):
                y0 = top - (idx + 1) * height - idx * gap
                ax.set_position([left, y0, right - left, height])
        else:
            width = max((right - left - gap * (len(visible_axes) - 1)) / len(visible_axes), 0.05)
            for idx, ax in enumerate(visible_axes):
                x0 = left + idx * (width + gap)
                ax.set_position([x0, bottom, width, top - bottom])
'''
            if not plugin_path.exists() or plugin_path.read_text(encoding="utf-8") != plugin_code:
                plugin_path.write_text(plugin_code, encoding="utf-8")
        except Exception as exc:
            self.logger.warning("Could not install plot-editor IndentAnalyzer plugin: %s", exc)

    def _figure_transfer_summary(self, figure: Figure) -> Dict[str, Any]:
        """Summarize the Matplotlib artists that are expected to round-trip through the plot editor."""
        axes_summary = []
        for ax in figure.axes:
            axes_summary.append({
                "title": ax.get_title(),
                "xlabel": ax.get_xlabel(),
                "ylabel": ax.get_ylabel(),
                "xlim": tuple(float(v) for v in ax.get_xlim()),
                "ylim": tuple(float(v) for v in ax.get_ylim()),
                "lines": len(ax.lines),
                "collections": len(ax.collections),
                "images": len(ax.images),
                "patches": len(ax.patches),
                "texts": len(ax.texts),
                "tables": len(ax.tables),
                "legend": ax.get_legend() is not None,
            })
        return {
            "axes": len(figure.axes),
            "size_inches": tuple(float(v) for v in figure.get_size_inches()),
            "dpi": float(figure.dpi),
            "figure_texts": len(figure.texts),
            "axes_detail": axes_summary,
        }

    def _prepare_figure_for_plot_editor(self) -> Dict[str, Any]:
        """Apply pending display settings and capture the exact figure state sent to the editor."""
        self.apply_plot_settings()
        try:
            self._canvas_draw()
        except Exception as exc:
            self.logger.debug("Could not pre-draw plot before editor export: %s", exc)
        summary = self._figure_transfer_summary(self.figure)
        self._last_plot_editor_transfer = {"sent": summary}
        self.logger.info(
            "Plot editor export: axes=%s, figure_texts=%s, size=%s, dpi=%s",
            summary["axes"],
            summary["figure_texts"],
            summary["size_inches"],
            summary["dpi"],
        )
        return summary

    def open_in_plot_editor(self):
        """Open this figure in the external plot editor and import edits when it closes."""
        if self._plot_editor_process and self._plot_editor_process.poll() is None:
            QMessageBox.information(self, "Plot Editor Running", "The plot editor is already open for this plot.")
            return
        python_exe = self._find_plot_editor_python()
        if not python_exe:
            QMessageBox.warning(
                self,
                "Plot Editor Not Available",
                "The external plot editor is not installed in a compatible Python environment.\n\n"
                "Use the bundled optional editor environment or install the editor dependency "
                "in a Python 3.11-3.13 environment."
            )
            return
        self._ensure_plot_editor_plugins(python_exe)
        self._prepare_figure_for_plot_editor()

        timestamp = int(time.time() * 1000)
        input_path = os.path.join(gettempdir(), f"indent_analyzer_plot_editor_{timestamp}_input.pkl")
        output_path = os.path.join(gettempdir(), f"indent_analyzer_plot_editor_{timestamp}_output.pkl")
        try:
            with open(input_path, "wb") as handle:
                pickle.dump(self.figure, handle, protocol=4)
        except Exception as exc:
            QMessageBox.warning(self, "Plot Editor Export Error", f"Could not prepare the current figure:\n{exc}")
            return

        runner = (
            "import pickle, sys\n"
            "from types import MethodType\n"
            "from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QPushButton\n"
            "from PySide6.QtCore import QTimer\n"
            "from PySide6.QtGui import QIcon\n"
            "from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas\n"
            "from FigureForge.preferences import Preferences\n"
            "from FigureForge.gui import MainWindow\n"
            "class _SilentSplash:\n"
            "    def showMessage(self, *args, **kwargs):\n"
            "        pass\n"
            "    def finish(self, *args, **kwargs):\n"
            "        pass\n"
            "prefs = Preferences()\n"
            "prefs.set('show_welcome', False)\n"
            "prefs.set('check_for_updates', False)\n"
            "app = QApplication.instance() or QApplication(sys.argv)\n"
            "splash = _SilentSplash()\n"
            "window = MainWindow(splash, None)\n"
            "window.setWindowIcon(QIcon())\n"
            "window.setWindowTitle('Plot Editor')\n"
            "def _current_canvas_container():\n"
            "    current = window.tab_widget.currentWidget()\n"
            "    layout = current.layout() if hasattr(current, 'layout') else None\n"
            "    return current, layout\n"
            "def _replace_editor_canvas(old_canvas, new_canvas):\n"
            "    current, layout = _current_canvas_container()\n"
            "    if layout is not None:\n"
            "        replaced = False\n"
            "        for idx in range(layout.count()):\n"
            "            if layout.itemAt(idx).widget() is old_canvas:\n"
            "                layout.replaceWidget(old_canvas, new_canvas)\n"
            "                replaced = True\n"
            "                break\n"
            "        if not replaced:\n"
            "            layout.addWidget(new_canvas)\n"
            "    else:\n"
            "        tab_idx = window.tab_widget.currentIndex()\n"
            "        title = window.tab_widget.tabText(tab_idx)\n"
            "        window.tab_widget.removeTab(tab_idx)\n"
            "        window.tab_widget.insertTab(tab_idx, new_canvas, title)\n"
            "        window.tab_widget.setCurrentIndex(tab_idx)\n"
            "    if old_canvas is not None:\n"
            "        old_canvas.setParent(None)\n"
            "        old_canvas.deleteLater()\n"
            "def _hard_load_figure(fm, file_name):\n"
            "    if not file_name:\n"
            "        return\n"
            "    with open(file_name, 'rb') as f:\n"
            "        loaded_figure = pickle.load(f)\n"
            "    old_canvas = getattr(fm, 'canvas', None)\n"
            "    fm.figure = loaded_figure\n"
            "    fm.canvas = FigureCanvas(fm.figure)\n"
            "    fm.figure.set_canvas(fm.canvas)\n"
            "    _replace_editor_canvas(old_canvas, fm.canvas)\n"
            "    fm.file_name = file_name\n"
            "    fm.unsaved_changes = False\n"
            "    fm.updateLabel.emit(file_name.split('/')[-1])\n"
            "    fm.fe.build_tree(fm.figure)\n"
            "    fm.pi.clear_properties()\n"
            "    fm.canvas.draw_idle()\n"
            "def _patched_load_figure(self, file_name):\n"
            "    _hard_load_figure(self, file_name)\n"
            "def _stack_axes(mode):\n"
            "    fig = window.fm.figure\n"
            "    axes = [ax for ax in fig.axes if ax.get_visible()]\n"
            "    if len(axes) < 2:\n"
            "        return\n"
            "    left, right = 0.10, 0.96\n"
            "    bottom, top = 0.12, 0.90\n"
            "    gap = 0.075\n"
            "    if mode == 'vertical':\n"
            "        height = max((top - bottom - gap * (len(axes) - 1)) / len(axes), 0.05)\n"
            "        for idx, ax in enumerate(axes):\n"
            "            y0 = top - (idx + 1) * height - idx * gap\n"
            "            ax.set_position([left, y0, right - left, height])\n"
            "    else:\n"
            "        width = max((right - left - gap * (len(axes) - 1)) / len(axes), 0.05)\n"
            "        for idx, ax in enumerate(axes):\n"
            "            x0 = left + idx * (width + gap)\n"
            "            ax.set_position([x0, bottom, width, top - bottom])\n"
            "    window.fm.unsaved_changes = True\n"
            "    window.fm.fe.build_tree(fig)\n"
            "    window.fm.canvas.draw_idle()\n"
            "def _install_stack_controls():\n"
            "    current, layout = _current_canvas_container()\n"
            "    if layout is None or getattr(window, '_indent_stack_controls', None) is not None:\n"
            "        return\n"
            "    controls = QWidget()\n"
            "    row = QHBoxLayout(controls)\n"
            "    row.setContentsMargins(6, 4, 6, 4)\n"
            "    row.setSpacing(6)\n"
            "    vertical_btn = QPushButton('Stack Vertical')\n"
            "    horizontal_btn = QPushButton('Stack Horizontal')\n"
            "    vertical_btn.setToolTip('Arrange visible subplots from top to bottom.')\n"
            "    horizontal_btn.setToolTip('Arrange visible subplots from left to right.')\n"
            "    vertical_btn.clicked.connect(lambda: _stack_axes('vertical'))\n"
            "    horizontal_btn.clicked.connect(lambda: _stack_axes('horizontal'))\n"
            "    row.addStretch()\n"
            "    row.addWidget(vertical_btn)\n"
            "    row.addWidget(horizontal_btn)\n"
            "    layout.insertWidget(0, controls)\n"
            "    window._indent_stack_controls = controls\n"
            "window.fm.load_figure = MethodType(_patched_load_figure, window.fm)\n"
            "window.fm.file_name = sys.argv[1]\n"
            "_hard_load_figure(window.fm, sys.argv[1])\n"
            "_install_stack_controls()\n"
            "window.setWindowTitle('Plot Editor')\n"
            "menubar = window.menuBar()\n"
            "for action in list(menubar.actions()):\n"
            "    menu = action.menu()\n"
            "    title = action.text().replace('&', '')\n"
            "    if title == 'Help':\n"
            "        menubar.removeAction(action)\n"
            "    elif title == 'Plugins' and menu is not None:\n"
            "        for plugin_action in list(menu.actions()):\n"
            "            text = plugin_action.text().replace('&', '')\n"
            "            if text in {'Plugins Documentation', 'New Plugin', 'Open Plugins Folder...'}:\n"
            "                menu.removeAction(plugin_action)\n"
            "window.show()\n"
            "window.setWindowTitle('Plot Editor')\n"
            "splash.finish(window)\n"
            "def select_initial_item():\n"
            "    root = window.fm.fe.tree.topLevelItem(0)\n"
            "    if root is not None:\n"
            "        window.fm.fe.tree.setCurrentItem(root)\n"
            "        window.fm.on_item_selected(root.reference)\n"
            "QTimer.singleShot(0, select_initial_item)\n"
            "app.exec()\n"
            "with open(sys.argv[2], 'wb') as f:\n"
            "    pickle.dump(window.fm.figure, f, protocol=4)\n"
        )
        try:
            self._plot_editor_process = subprocess.Popen(
                [python_exe, "-c", runner, input_path, output_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except Exception as exc:
            QMessageBox.warning(self, "Plot Editor Launch Error", f"Could not start the plot editor:\n{exc}")
            return

        self._plot_editor_output_path = output_path
        self._plot_editor_stderr = ""
        self.plot_editor_action.setEnabled(False)
        QTimer.singleShot(500, self._poll_plot_editor_process)

    def _poll_plot_editor_process(self):
        process = self._plot_editor_process
        if process is None:
            self.plot_editor_action.setEnabled(True)
            return
        if process.poll() is None:
            QTimer.singleShot(500, self._poll_plot_editor_process)
            return

        stdout, stderr = process.communicate()
        self._plot_editor_stderr = stderr or ""
        self._plot_editor_process = None
        self.plot_editor_action.setEnabled(True)
        if process.returncode != 0:
            message = self._plot_editor_stderr.strip() or stdout.strip() or "The plot editor exited with an error."
            QMessageBox.warning(self, "Plot Editor Error", message[:4000])
            return

        output_path = self._plot_editor_output_path
        if not output_path or not os.path.exists(output_path):
            QMessageBox.information(self, "Plot Editor Closed", "The plot editor closed without returning an edited figure.")
            return
        try:
            with open(output_path, "rb") as handle:
                edited_figure = pickle.load(handle)
            if not isinstance(edited_figure, Figure):
                raise TypeError(f"Expected a Matplotlib Figure, got {type(edited_figure).__name__}")
            returned_summary = self._figure_transfer_summary(edited_figure)
            self._last_plot_editor_transfer["returned"] = returned_summary
            self.logger.info(
                "Plot editor import: axes=%s, figure_texts=%s, size=%s, dpi=%s",
                returned_summary["axes"],
                returned_summary["figure_texts"],
                returned_summary["size_inches"],
                returned_summary["dpi"],
            )
            self._replace_canvas_figure(edited_figure)
        except Exception as exc:
            QMessageBox.warning(self, "Plot Editor Import Error", f"Could not load the edited figure:\n{exc}")

    def _replace_canvas_figure(self, figure: Figure):
        """Replace the embedded Matplotlib canvas so edited figures do not merge with old axes."""
        layout = self.layout()
        old_toolbar = self.toolbar
        old_canvas = self.canvas

        self.figure = figure
        self.canvas = FigureCanvas(self.figure)
        self.figure.set_canvas(self.canvas)
        self._canvas_draw = self.canvas.draw
        self.canvas.draw = self._draw_with_plot_settings
        self.canvas.setStyleSheet("background-color: #ffffff;")

        self.toolbar = NavigationToolbar(self.canvas, self)
        self.plot_editor_action = self._add_plot_editor_button()
        self._apply_light_toolbar_style()

        if layout is not None:
            layout.replaceWidget(old_toolbar, self.toolbar)
            layout.replaceWidget(old_canvas, self.canvas)
        old_toolbar.deleteLater()
        old_canvas.deleteLater()

        self.reset_plot_settings()
        self.canvas.draw()

    def _apply_light_toolbar_style(self):
        """Keep Matplotlib toolbar controls readable on the light application theme."""
        self.toolbar.setStyleSheet("""
            QToolBar {
                background-color: #ffffff;
                border: 1px solid #d6dbe0;
                spacing: 2px;
                padding: 2px;
            }
            QToolButton {
                background-color: #f5f7f9;
                border: 1px solid #d6dbe0;
                border-radius: 4px;
                padding: 3px;
                margin: 0;
            }
            QToolButton:hover {
                background-color: #e7f7fb;
                border-color: #00a8cc;
            }
            QToolButton:pressed {
                background-color: #cceff7;
            }
        """)

        for action in self.toolbar.actions():
            icon = action.icon()
            if icon.isNull():
                continue
            pixmap = icon.pixmap(QSize(24, 24))
            if pixmap.isNull():
                continue
            tinted = QPixmap(pixmap.size())
            tinted.fill(Qt.transparent)
            painter = QPainter(tinted)
            painter.drawPixmap(0, 0, pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(tinted.rect(), QColor("#24313a"))
            painter.end()
            action.setIcon(QIcon(tinted))
    
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
                background-color: #ffffff;
                color: #24313a;
                border: 1px solid #d6dbe0;
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
        fig.patch.set_facecolor('#ffffff')
        
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
                      facecolor='#ffffff', edgecolor='#c7d0d8', labelcolor='#24313a')
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
<hr style="border: 1px solid #d6dbe0;">

<h4 style="color: #00d9ff;">MECHANICAL PROPERTIES</h4>
<table style="width: 100%; color: #24313a;">
  <tr><td>Hardness (H):</td><td style="text-align: right; color: #00a8cc;"><b>{self.test_data.get('Hardness (GPa)', 'N/A')} GPa</b></td></tr>
  <tr><td>Oliver-Pharr Modulus (E*):</td><td style="text-align: right; color: #00a8cc;"><b>{self.test_data.get('Oliver-Pharr Modulus (GPa)', 'N/A')} GPa</b></td></tr>
  <tr><td>CSM Hardness:</td><td style="text-align: right;">{self.test_data.get('CSM Hardness (GPa)', 'N/A')} GPa</td></tr>
</table>

<h4 style="color: #00d9ff;">MECHANICAL PARAMETERS</h4>
<table style="width: 100%; color: #24313a;">
  <tr><td>Maximum Load (P<sub>max</sub>):</td><td style="text-align: right;">{self.test_data.get('Max Load (mN)', 'N/A')} mN</td></tr>
  <tr><td>Maximum Displacement (h<sub>max</sub>):</td><td style="text-align: right;">{self.test_data.get('Max Displacement (nm)', 'N/A')} nm</td></tr>
  <tr><td>Contact Area (A<sub>c</sub>):</td><td style="text-align: right;">{self.test_data.get('A (m^2)', 'N/A')} m²</td></tr>
  <tr><td>Contact Depth (h<sub>c</sub>):</td><td style="text-align: right;">{self.test_data.get('Hc (m)', 'N/A')} m</td></tr>
  <tr><td>Stiffness (S):</td><td style="text-align: right;">{self.test_data.get('S (N/m)', 'N/A')} N/m</td></tr>
</table>

<h4 style="color: #00d9ff;">CURVE FIT QUALITY (ISO 14577-1)</h4>
<table style="width: 100%; color: #24313a;">
  <tr><td>Loading R²:</td><td style="text-align: right;"><b>{self.test_data.get('Loading R²', 'N/A')}</b></td></tr>
  <tr><td>Unloading R²:</td><td style="text-align: right;"><b>{self.test_data.get('Unloading Fit R²', 'N/A')}</b></td></tr>
</table>
<p style="color: #888; font-size: 9pt;">ISO threshold: R² ≥ 0.99</p>

<h4 style="color: #00d9ff;">CALIBRATION</h4>
<table style="width: 100%; color: #24313a;">
  <tr><td>Calibration Factor:</td><td style="text-align: right;">{self.test_data.get('Calibration Factor', 'N/A')}</td></tr>
  <tr><td>Source File:</td><td style="text-align: right; font-size: 9pt;">{self.test_data.get('Source File', 'N/A')}</td></tr>
</table>

<h4 style="color: #00d9ff;">ANALYSIS STATUS</h4>
<table style="width: 100%; color: #24313a;">
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
        font.setFamily("Menlo")
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
        self._apply_app_icon()
        
        # Initialize attributes
        self.analyzer: Optional[FixedIndentXLSAnalyzer] = None
        self.analysis_worker: Optional[AnalysisWorker] = None
        self.current_results: List[Dict[str, Any]] = []
        self.plots_tab_widget: Optional[QTabWidget] = None  # unused; kept for safety
        self.results_panel_tabs: Optional[QTabWidget] = None
        self.results_view_buttons: Dict[str, QPushButton] = {}
        self.results_summary_label: Optional[QLabel] = None
        self.results_view_help_label: Optional[QLabel] = None
        self.reliability_widget: Optional[MatplotlibWidget] = None
        self.op_overlay_widget: Optional[MatplotlibWidget] = None
        self.summary_statistics_text: Optional[QTextEdit] = None
        self.single_test_plot: Optional[MatplotlibWidget] = None
        self.current_test_index: int = 0
        self.test_nav_label: Optional[QLabel] = None
        self.test_nav_prev: Optional[QPushButton] = None
        self.test_nav_next: Optional[QPushButton] = None
        self.test_include_checkbox: Optional[QCheckBox] = None
        self.excluded_test_indices = set()
        self.excluded_test_numbers: Set[int] = set()
        self.workflow_tabs: Optional[QTabWidget] = None
        self.workflow_top_tabs: Optional[QTabBar] = None
        self.step4_plot_buttons_layout: Optional[QGridLayout] = None
        self.step4_plot_buttons_note: Optional[QLabel] = None
        self.step4_plot_buttons_group: Optional[QGroupBox] = None
        self.step4_plot_buttons: Dict[int, QPushButton] = {}
        self.generate_curves_button: Optional[QPushButton] = None
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
        self.op_overlay_hold_combo: Optional[QComboBox] = None
        self.op_overlay_cutoff_label: Optional[QLabel] = None
        self.op_overlay_cutoff_spin: Optional[QDoubleSpinBox] = None
        self.op_overlay_cutoff_user_set: bool = False
        self.op_overlay_cutoff_syncing: bool = False
        self.op_overlay_refresh_timer: Optional[QTimer] = QTimer(self)
        self.op_overlay_refresh_timer.setSingleShot(True)
        self.op_overlay_refresh_timer.timeout.connect(self._refresh_op_overlay_options_now)
        self.overlay_curve_cache: Dict[Tuple[str, int], Tuple[List[float], List[float], List[float], List[float]]] = {}
        self.overlay_sheet_names_cache: Dict[str, List[str]] = {}
        self.file_loader_combo: Optional[QComboBox] = None
        self.file_loader_menu = None
        self.file_loader_actions: Dict[str, QAction] = {}
        self.header_file_label: Optional[QLabel] = None
        self.available_file_loaders: Dict[str, Any] = {}
        self.selected_file_loader_name: str = "AgilentG200"
        self.fit_curve_percent_spinbox: Optional[QDoubleSpinBox] = None
        self.readiness_text: Optional[QTextEdit] = None
        self.config_values: Dict[str, Any] = self.load_analysis_config()
        self.available_file_loaders = self.discover_file_loaders()
        configured_loader = str(self.config_values.get("default_file_loader", "")).strip()
        if configured_loader in self.available_file_loaders:
            self.selected_file_loader_name = configured_loader
        elif "AgilentG200" in self.available_file_loaders:
            self.selected_file_loader_name = "AgilentG200"
        elif self.available_file_loaders:
            self.selected_file_loader_name = next(iter(self.available_file_loaders))
        self.current_analysis_file_path: Optional[str] = None
        self.pending_analysis_context: Optional[str] = None
        self.calibration_plot_widget: Optional[MatplotlibWidget] = None
        self.calibration_metrics_text: Optional[QTextEdit] = None
        self.csm_file_path: Optional[str] = None
        self.csm_offsets: Dict[int, float] = {}
        self.file_load_offsets: Dict[int, float] = {}
        self.csm_selected_test_numbers: List[int] = []
        self._last_csm_selection_log_signature: Optional[tuple] = None
        self.csm_results: Optional[Dict[str, Any]] = None
        self.csm_table: Optional[QTableWidget] = None
        self.csm_depth_plot_widget: Optional[MatplotlibWidget] = None
        self.csm_offset_plot_widget: Optional[MatplotlibWidget] = None
        self.csm_plot_mode_combo: Optional[QComboBox] = None
        self.csm_reset_plot_settings_button: Optional[QPushButton] = None
        self.workflow_log_widget: Optional[QTextEdit] = None
        self.workflow_log_last_length: int = 0
        self.last_run_context: str = "analysis"
        self.live_plot_data: Optional[pd.DataFrame] = None
        self.live_plot_units: Dict[str, str] = {}
        self.live_plot_file_path: Optional[str] = None
        self.live_plot_test_sheets: List[str] = []
        self.live_plot_range_signature: Optional[tuple] = None
        self.live_plot_has_rendered: bool = False
        self.live_plot_html_path: Optional[Path] = None
        self.live_plot_sheet_combo: Optional[QComboBox] = None
        self.live_plot_x_combo: Optional[QComboBox] = None
        self.live_plot_y_combo: Optional[QComboBox] = None
        self.live_plot_refresh_button: Optional[QPushButton] = None
        self.live_plot_show_button: Optional[QPushButton] = None
        self.live_plot_status_label: Optional[QLabel] = None
        self.live_plot_widget: Optional[Any] = None
        self.live_plot_use_ranges_cb: Optional[QCheckBox] = None
        self.live_plot_xmin_spin: Optional[QDoubleSpinBox] = None
        self.live_plot_xmax_spin: Optional[QDoubleSpinBox] = None
        self.live_plot_ymin_spin: Optional[QDoubleSpinBox] = None
        self.live_plot_ymax_spin: Optional[QDoubleSpinBox] = None
        self.live_plot_lsq_fit_cb: Optional[QCheckBox] = None
        self.live_plot_lsq_degree_spin: Optional[QSpinBox] = None
        self.live_plot_lsq_status_label: Optional[QLabel] = None
        self.expert_offsets_table: Optional[QTableWidget] = None
        self.expert_offsets_status_label: Optional[QLabel] = None
        self.expert_offsets_reset_button: Optional[QPushButton] = None
        self.expert_offsets_syncing: bool = False
        self.csm_target_x_start_spin: Optional[QDoubleSpinBox] = None
        self.csm_target_x_end_spin: Optional[QDoubleSpinBox] = None
        self.csm_target_x_step_spin: Optional[QDoubleSpinBox] = None
        self.configure_responsive_metrics()
        self.apply_responsive_app_font()
        
        # Set up the GUI
        self.init_ui()
        self.setStyleSheet(self.get_stylesheet())
        self.setup_matplotlib_style()
        
        # Center the window
        self.center_window()

    def _apply_app_icon(self):
        """Apply icon to both this window and QApplication if an icon file exists."""
        icon_path = resolve_app_icon_path()
        if not icon_path:
            return
        icon = QIcon(str(icon_path))
        if icon.isNull():
            return
        self.setWindowIcon(icon)
        app = QApplication.instance()
        if app:
            app.setWindowIcon(icon)

    def configure_responsive_metrics(self):
        """Calculate UI dimensions from the current screen instead of fixed pixels."""
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            screen_width = geometry.width()
            screen_height = geometry.height()
        else:
            screen_width, screen_height = 1440, 900

        base_scale = min(screen_width / 1440.0, screen_height / 900.0)
        self.ui_scale = max(0.78, min(1.18, base_scale))
        self.font_scale = max(0.88, min(1.14, base_scale))

        target_width = int(screen_width * (0.96 if screen_width < 1300 else 0.92))
        target_height = int(screen_height * (0.94 if screen_height < 850 else 0.88))
        self.window_target_size = QSize(
            max(760, min(target_width, 1800)),
            max(560, min(target_height, 1120))
        )

        self.window_min_size = QSize(
            min(max(740, self.sp(980)), max(640, screen_width - self.sp(80))),
            min(max(540, self.sp(660)), max(500, screen_height - self.sp(80)))
        )
        self.control_panel_width = max(self.sp(330), min(self.sp(500), int(self.window_target_size.width() * 0.34)))
        self.results_panel_width = max(self.sp(560), self.window_target_size.width() - self.control_panel_width)
        self.app_font_point_size = max(9, min(12, int(round(10 * self.font_scale))))

    def sp(self, value: float) -> int:
        """Scale spacing and fixed dimensions."""
        return max(1, int(round(value * getattr(self, "ui_scale", 1.0))))

    def fp(self, value: float) -> int:
        """Scale CSS pixel font sizes conservatively."""
        return max(8, int(round(value * getattr(self, "font_scale", 1.0))))

    def apply_responsive_app_font(self):
        app = QApplication.instance()
        if not app:
            return
        font = app.font()
        font.setPointSize(getattr(self, "app_font_point_size", 10))
        app.setFont(font)

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
            "default_fitting_method": "oliver_pharr",
            "default_file_loader": "AgilentG200",
        }
        config_path = self.analysis_config_path()
        if not config_path.exists():
            return defaults

        parser = configparser.ConfigParser()
        parser.read(config_path)
        if parser.has_section("analysis"):
            defaults["min_r_squared"] = parser.getfloat("analysis", "min_r_squared", fallback=defaults["min_r_squared"])
            defaults["fit_curve_percent"] = parser.getfloat("analysis", "fit_curve_percent", fallback=defaults["fit_curve_percent"])
        if parser.has_section("calibration"):
            defaults["sample_poisson"] = parser.getfloat("calibration", "reference_poisson", fallback=defaults["sample_poisson"])
        if parser.has_section("loader"):
            defaults["default_file_loader"] = parser.get(
                "loader", "default_file_loader", fallback=defaults["default_file_loader"]
            )
        return defaults

    def analysis_config_path(self) -> Path:
        user_config_path = app_user_data_dir() / "config" / "analysis_settings.ini"
        if not user_config_path.exists():
            bundled_config_path = app_resource_root() / "config" / "analysis_settings.ini"
            if bundled_config_path.exists():
                user_config_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(bundled_config_path, user_config_path)
        return user_config_path

    def samples_dir(self) -> Path:
        user_samples_dir = app_user_data_dir() / "samples"
        if not user_samples_dir.exists():
            bundled_samples_dir = app_resource_root() / "samples"
            if bundled_samples_dir.exists():
                shutil.copytree(bundled_samples_dir, user_samples_dir)
            else:
                user_samples_dir.mkdir(parents=True, exist_ok=True)
        return user_samples_dir

    def setup_menu_bar(self):
        """Create the application menu bar."""
        menu_bar = self.menuBar()
        settings_menu = menu_bar.addMenu("Settings")
        help_menu = menu_bar.addMenu("Help")

        self.file_loader_menu = settings_menu.addMenu("File Loader")
        self._rebuild_file_loader_menu()
        settings_menu.addSeparator()

        edit_config_action = QAction("Edit Analysis Config...", self)
        edit_config_action.setStatusTip("Open and update config/analysis_settings.ini variables.")
        edit_config_action.triggered.connect(self.open_analysis_config_editor)
        settings_menu.addAction(edit_config_action)

        about_action = QAction("About", self)
        about_action.setStatusTip("Show project and author details.")
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def _rebuild_file_loader_menu(self):
        if self.file_loader_menu is None:
            return
        self.file_loader_menu.clear()
        self.file_loader_actions = {}
        loader_names = list(self.available_file_loaders.keys()) or [self.selected_file_loader_name or "AgilentG200"]
        for loader_name in loader_names:
            action = QAction(loader_name, self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked=False, name=loader_name: self.on_file_loader_changed(name))
            self.file_loader_menu.addAction(action)
            self.file_loader_actions[loader_name] = action
        self._sync_file_loader_menu_checks()

    def _sync_file_loader_menu_checks(self):
        for name, action in self.file_loader_actions.items():
            action.setChecked(name == self.selected_file_loader_name)

    def show_about_dialog(self):
        """Show project and author information."""
        about = QMessageBox(self)
        about.setWindowTitle("About IndentAnalyzer")
        about.setTextFormat(Qt.RichText)
        about.setIcon(QMessageBox.Information)
        about.setText(
            "<b>IndentAnalyzer</b><br>"
            "Nanoindentation Analysis Suite for ISO 14577-4:2016 workflows."
        )
        about.setInformativeText(
            "Author: M Shiraz Ahmad<br>"
            "Repository: "
            "<a href='https://github.com/MShirazAhmad/IndentAnalyzer.git'>"
            "https://github.com/MShirazAhmad/IndentAnalyzer.git</a><br><br>"
            "Includes guided calibration, loading-curve review, Oliver-Pharr analysis, "
            "CSM support, Expert Mode plotting, and configurable analysis defaults."
        )
        about.exec_()

    def open_analysis_config_editor(self):
        """Open a small editor for config/analysis_settings.ini."""
        config_path = self.analysis_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        if not config_path.exists():
            config_path.write_text(
                "# Nanoindentation Analysis Configuration\n"
                "# Used by the GUI researcher workflow as editable defaults.\n"
                "# Units are listed beside each setting. Dimensionless values are noted explicitly.\n"
                "# Keep section names and key names unchanged; the GUI reads these names directly.\n\n"
                "[analysis]\n"
                "# Minimum number of numeric points required in the loading segment [count].\n"
                "min_data_points_loading = 50\n"
                "# Minimum number of numeric points required in the unloading segment [count].\n"
                "min_data_points_unloading = 30\n"
                "# Minimum accepted coefficient of determination for curve fits [dimensionless R^2].\n"
                "min_r_squared = 0.98\n"
                "# Fit window used for loading/unloading curve fitting [% of curve segment].\n"
                "fit_curve_percent = 25.0\n"
                "# Relative noise threshold used by quality checks [dimensionless fraction].\n"
                "noise_threshold = 0.15\n"
                "# Default unloading fit model. Valid examples: oliver_pharr, power_law, auto.\n"
                "default_fitting_method = oliver_pharr\n\n"
                "[calibration]\n"
                "# Reference material name used for calibration/self-check workflows [text].\n"
                "reference_material = fused_silica\n"
                "# Reference reduced/elastic modulus for fused silica [Pa].\n"
                "reference_modulus = 72e9\n"
                "# Reference Poisson's ratio for fused silica [dimensionless].\n"
                "reference_poisson = 0.17\n"
                "# Reference hardness for fused silica [GPa].\n"
                "reference_hardness = 9.0\n"
                "# Default indenter material. Valid examples: diamond, sapphire.\n"
                "default_indenter = diamond\n\n"
                "[loader]\n"
                "# Default file-loader module name from src/fileloader [text].\n"
                "default_file_loader = AgilentG200\n\n"
                "[validation]\n"
                "# Maximum plausible hardness accepted by validation [GPa].\n"
                "max_hardness = 100.0\n"
                "# Minimum plausible hardness accepted by validation [GPa].\n"
                "min_hardness = 0.1\n"
                "# Maximum plausible modulus accepted by validation [Pa].\n"
                "max_modulus = 1000e9\n"
                "# Minimum plausible modulus accepted by validation [Pa].\n"
                "min_modulus = 1e9\n",
                encoding="utf-8"
            )

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit analysis_settings.ini")
        dialog.resize(self.sp(720), self.sp(560))

        layout = QVBoxLayout(dialog)
        intro = QLabel(
            f"Editing: {config_path}\n"
            "Update values, then Save. The file is validated as INI before it is written."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        editor = QTextEdit()
        editor.setPlainText(config_path.read_text(encoding="utf-8"))
        editor.setLineWrapMode(QTextEdit.NoWrap)
        font = QFont()
        font.setFamily("Menlo")
        font.setPointSize(max(9, self.app_font_point_size))
        editor.setFont(font)
        layout.addWidget(editor)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)

        def save_config():
            text = editor.toPlainText()
            parser = configparser.ConfigParser()
            try:
                parser.read_string(text)
            except configparser.Error as exc:
                QMessageBox.warning(dialog, "Invalid INI", f"Please fix the config format:\n{exc}")
                return

            config_path.write_text(text, encoding="utf-8")
            self.config_values = self.load_analysis_config()
            self.apply_config_values_to_controls()
            self.update_readiness_summary()
            if getattr(self, "log_widget", None):
                self.log_widget.append(f"⚙️ Analysis config updated: {config_path}")
            self.status_bar.showMessage("Analysis settings updated.")
            dialog.accept()

        buttons.accepted.connect(save_config)
        buttons.rejected.connect(dialog.reject)
        dialog.exec_()

    def apply_config_values_to_controls(self):
        """Refresh visible controls from the current analysis config values."""
        if getattr(self, "min_r2_spinbox", None):
            self.min_r2_spinbox.setValue(float(self.config_values.get("min_r_squared", 0.98)))
        if getattr(self, "fit_curve_percent_spinbox", None):
            self.fit_curve_percent_spinbox.setValue(float(self.config_values.get("fit_curve_percent", 25.0)))
        if getattr(self, "sample_poisson_spinbox", None):
            self.sample_poisson_spinbox.setValue(float(self.config_values.get("sample_poisson", 0.30)))
        if getattr(self, "indenter_combo", None):
            indenter = str(self.config_values.get("default_indenter", "diamond")).lower()
            self.indenter_combo.setCurrentText(indenter if indenter in ["diamond", "sapphire"] else "diamond")
        if getattr(self, "fitting_method_combo", None):
            method = str(self.config_values.get("default_fitting_method", "oliver_pharr")).lower()
            self.fitting_method_combo.setCurrentText(
                method if method in ["oliver_pharr", "power_law", "auto"] else "oliver_pharr"
            )
        configured_loader = str(self.config_values.get("default_file_loader", "")).strip()
        if configured_loader in self.available_file_loaders:
            self.selected_file_loader_name = configured_loader
            self._sync_file_loader_menu_checks()
            self.refresh_live_plot_source()

    def fileloader_dir(self) -> Path:
        return app_resource_root() / "src" / "fileloader"

    def discover_file_loaders(self) -> Dict[str, Any]:
        loaders: Dict[str, Any] = {}
        loader_dir = self.fileloader_dir()
        if not loader_dir.exists():
            return loaders
        for path in sorted(loader_dir.glob("*.py")):
            if path.name.startswith("_"):
                continue
            name = path.stem
            try:
                module = self._load_file_loader_module(name)
                loaders[name] = module
            except Exception as exc:
                logging.getLogger('NanoindentationGUI').warning(
                    "Could not load file loader %s: %s", name, exc
                )
        return loaders

    def _load_file_loader_module(self, loader_name: Optional[str] = None):
        loader_name = loader_name or self.selected_file_loader_name or "AgilentG200"
        loader_path = self.fileloader_dir() / f"{loader_name}.py"
        if not loader_path.exists():
            raise FileNotFoundError(f"File loader not found: {loader_path}")
        spec = importlib.util.spec_from_file_location(f"indent_fileloader_{loader_name}", loader_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not import file loader: {loader_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def selected_file_loader(self):
        loader_name = self.selected_file_loader_name
        return self.available_file_loaders.get(loader_name) or self._load_file_loader_module(loader_name)

    def selected_loader_extensions(self) -> List[str]:
        try:
            loader = self.selected_file_loader()
            extensions = getattr(loader, "ALLOWED_EXTENSIONS", [".xls", ".xlsx"])
            return [str(ext).lower() for ext in extensions]
        except Exception:
            return [".xls", ".xlsx"]

    def file_dialog_filter_for_loader(self) -> str:
        extensions = self.selected_loader_extensions()
        patterns = " ".join(f"*{ext}" for ext in extensions)
        label = self.selected_file_loader_name or "Selected Loader"
        return f"{label} Files ({patterns});;All Files (*)"

    def on_file_loader_changed(self, loader_name: str):
        if not loader_name:
            return
        if loader_name not in self.available_file_loaders:
            return
        self.selected_file_loader_name = loader_name
        self._sync_file_loader_menu_checks()
        self._persist_file_loader_choice()
        if getattr(self, "log_widget", None):
            self.log_widget.append(f"📦 File loader selected: {loader_name}")
        self.refresh_live_plot_source()

    def _persist_file_loader_choice(self):
        config_path = self.analysis_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        parser = configparser.ConfigParser()
        if config_path.exists():
            parser.read(config_path)
        if not parser.has_section("loader"):
            parser.add_section("loader")
        parser.set("loader", "default_file_loader", self.selected_file_loader_name)
        with config_path.open("w", encoding="utf-8") as fh:
            parser.write(fh)

    def create_guided_text(self, title: str, body: str) -> QLabel:
        """Create consistent self-guided workflow copy for each step."""
        label = QLabel(f"<b>{title}</b><br>{body}")
        label.setWordWrap(True)
        label.setTextFormat(Qt.RichText)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        label.setMaximumHeight(self.sp(82))
        label.setMinimumHeight(self.sp(64))
        label.setStyleSheet("""
            QLabel {
                background-color: #f8fbfc;
                color: #24313a;
                border: 1px solid #c8e8ef;
                border-left: 4px solid #00a8cc;
                border-radius: 6px;
                padding: 10px 12px;
                line-height: 1.35;
            }
        """)
        return label

    def update_readiness_summary(self):
        if not self.readiness_text:
            return

        analysis_type = self.get_selected_analysis_type()
        selected_step4_tests = self._selected_step4_test_numbers()
        checks = [
            ("Calibration selected", self.calibration_source is not None),
            ("Experiment file selected", bool(self.file_path_edit and self.file_path_edit.text())),
            ("Sample name entered", bool(self.sample_name_edit and self.sample_name_edit.text().strip())),
            ("Analysis type selected", bool(analysis_type)),
        ]
        if analysis_type == "Oliver-Pharr":
            checks.extend([
                ("Poisson ratio set", self.sample_poisson_spinbox is not None),
                ("Fitting method selected", self.fitting_method_combo is not None)
            ])
        else:
            plot_average = self._selected_csm_plot_mode() == "average"
            use_error_bars = (
                plot_average
                and getattr(self, "csm_sd_display_combo", None) is not None
                and self.csm_sd_display_combo.currentText() == "SD error bars"
            )
            has_valid_csm_target_range = (
                self.csm_target_x_start_spin is not None
                and self.csm_target_x_end_spin is not None
                and self.csm_target_x_step_spin is not None
                and self.csm_target_x_step_spin.value() > 0
                and self.csm_target_x_end_spin.value() >= self.csm_target_x_start_spin.value()
            )
            checks.extend([
                ("CSM tests selected in Open Test Plot", bool(selected_step4_tests)),
                ("CSM depth window set", getattr(self, "csm_depth_min_spin", None) is not None and getattr(self, "csm_depth_max_spin", None) is not None),
            ])
            if use_error_bars:
                checks.append(("CSM error-bar placement set", has_valid_csm_target_range))
        lines = ["Before running analysis, confirm these items:"]
        for label, ok in checks:
            lines.append(f"{'✅' if ok else '⬜'} {label}")

        lines.append(f"\nAnalysis: {analysis_type}")
        if self.sample_name_edit:
            lines.append(f"\nSample: {self.sample_name_edit.text().strip() or 'not provided'}")
        if self.research_goal_combo:
            lines.append(f"Goal: {self.research_goal_combo.currentText()}")
        if analysis_type == "Oliver-Pharr" and self.sample_poisson_spinbox:
            lines.append(f"Poisson ratio: {self.sample_poisson_spinbox.value():.3f}")
        if analysis_type == "Oliver-Pharr" and self.indenter_combo:
            lines.append(f"Indenter: {self.indenter_combo.currentText()}")
        if analysis_type == "Oliver-Pharr" and self.fitting_method_combo:
            lines.append(f"Fitting method: {self.fitting_method_combo.currentText()}")
        if analysis_type == "Oliver-Pharr" and self.fit_curve_percent_spinbox:
            lines.append(f"Fit curve percentage used (loading/unloading): {self.fit_curve_percent_spinbox.value():.1f}%")
        if analysis_type == "Oliver-Pharr" and getattr(self, "op_overlay_hold_combo", None):
            lines.append(f"Load Overlay hold segment: {self.op_overlay_hold_combo.currentText()}")
            if self._op_overlay_remove_hold_segment() and getattr(self, "op_overlay_cutoff_spin", None):
                lines.append(f"Load Overlay cutoff: {self.op_overlay_cutoff_spin.value():.3f} mN")
        if analysis_type == "CSM":
            if selected_step4_tests:
                lines.append(f"CSM selected tests: {self._format_test_range(selected_step4_tests)}")
            else:
                lines.append("CSM selected tests: none")
            lines.append(f"CSM source: {self.csm_source_combo.currentText()}")
            if getattr(self, "csm_plot_mode_combo", None):
                lines.append(f"CSM plot layout: {self.csm_plot_mode_combo.currentText()}")
            plot_average = self._selected_csm_plot_mode() == "average"
            use_error_bars = (
                plot_average
                and getattr(self, "csm_sd_display_combo", None) is not None
                and self.csm_sd_display_combo.currentText() == "SD error bars"
            )
            if plot_average and getattr(self, "csm_sd_display_combo", None):
                lines.append(f"CSM spread display: {self.csm_sd_display_combo.currentText()}")
            lines.append(
                f"CSM depth window: {self.csm_depth_min_spin.value():.1f}–"
                f"{self.csm_depth_max_spin.value():.1f} nm"
            )
            if (
                use_error_bars
                and self.csm_target_x_start_spin
                and self.csm_target_x_end_spin
                and self.csm_target_x_step_spin
            ):
                lines.append(
                    f"CSM error-bar placement: ({self.csm_target_x_start_spin.value():.1f}, "
                    f"{self.csm_target_x_end_spin.value():.1f}, "
                    f"{self.csm_target_x_step_spin.value():.1f}) "
                )
            lines.append("CSM offsets: from Curve Viewer loading h0 values")

        self.readiness_text.setPlainText("\n".join(lines))

    def get_selected_analysis_type(self) -> str:
        if getattr(self, "proceed_op_combo", None):
            return self.proceed_op_combo.currentText()
        if getattr(self, "analysis_type_combo", None):
            return "CSM" if self.analysis_type_combo.currentIndex() == 1 else "Oliver-Pharr"
        return "Oliver-Pharr"

    def update_analysis_type_options(self):
        """Show only the settings relevant to the selected shared workflow mode."""
        analysis_type = self.get_selected_analysis_type()
        is_csm = analysis_type == "CSM"
        if getattr(self, "oliver_settings_group", None):
            self.oliver_settings_group.setVisible(not is_csm)
        if getattr(self, "csm_settings_group", None):
            self.csm_settings_group.setVisible(is_csm)
        if getattr(self, "analyze_button", None):
            self.analyze_button.setText("Regenerate CSM Profiles" if is_csm else "Regenerate Oliver-Pharr Results")
        if getattr(self, "step4_plot_buttons_note", None):
            self.step4_plot_buttons_note.setText("Browse a file, then click Generate Test Curves to populate review buttons.")
        # Keep Open Test Plot visible in both modes because CSM now uses this selection.
        if getattr(self, "step4_plot_buttons_group", None):
            self.step4_plot_buttons_group.setVisible(True)
        self._configure_results_panel_visibility()
        self.update_readiness_summary()

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
        fig.patch.set_facecolor('#ffffff')

        fname = Path(self.calibration_file_path).name if self.calibration_file_path else 'manual / default'
        fig.suptitle(
            f'Calibration Reliability  —  {self.calibration_source}  |  {fname}',
            fontsize=11, fontweight='bold', y=0.98
        )

        # ── Area Function ─────────────────────────────────────────────────
        gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 0.9])
        ax1a = fig.add_subplot(gs[0, 0])
        ax1a.plot(hc, A_ideal / 1e6, 'k--', linewidth=1.5, alpha=0.55,
                  label='Ideal Berkovich')
        ax1a.plot(hc, A_loaded / 1e6, color='#00a8cc', linewidth=2.2,
                  label='Loaded calibration')
        ax1a.set_xlabel('Contact Depth hc (nm)', fontsize=9)
        ax1a.set_ylabel('Projected Area A (µm²)', fontsize=9)
        ax1a.set_title('Tip Area Function  A(hc)', fontweight='bold', fontsize=10)
        ax1a.legend(fontsize=8, loc='upper left')
        ax1a.grid(True, alpha=0.3)

        # ── Deviation Analysis ────────────────────────────────────────────
        ax1b = fig.add_subplot(gs[0, 1])
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

        # ── Coefficients ──────────────────────────────────────────────────
        ax2a = fig.add_subplot(gs[1, :])
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

        self._set_calibration_metrics_text(quality_text, verdict_color)

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
            self._sync_workflow_top_tabs()

    def _workflow_tab_index(self, title: str) -> int:
        if not self.workflow_tabs:
            return -1
        for i in range(self.workflow_tabs.count()):
            if self.workflow_tabs.tabText(i) == title:
                return i
        return -1

    def unlock_workflow_tab(self, title: str, move_to_tab: bool = False):
        idx = self._workflow_tab_index(title)
        if idx >= 0:
            self.unlock_workflow_step(idx, move_to_step=move_to_tab)

    def _results_tab_index(self, title: str) -> int:
        if self.results_panel_tabs is None:
            return -1
        for i in range(self.results_panel_tabs.count()):
            if self.results_panel_tabs.tabText(i) == title:
                return i
        return -1

    def _set_results_tab_visible(self, title: str, visible: bool):
        if self.results_panel_tabs is None:
            return
        idx = self._results_tab_index(title)
        if idx < 0:
            return
        tab_bar = self.results_panel_tabs.tabBar()
        if hasattr(tab_bar, "setTabVisible"):
            tab_bar.setTabVisible(idx, visible)
        else:
            self.results_panel_tabs.setTabEnabled(idx, visible)
        self._refresh_results_view_buttons()

    def _configure_results_panel_visibility(self):
        if self.results_panel_tabs is None:
            return
        step = self.workflow_tabs.currentIndex() if self.workflow_tabs else 0
        workflow_title = self.workflow_tabs.tabText(step) if self.workflow_tabs and step >= 0 else ""
        mode = self.get_selected_analysis_type()
        has_loading_results = bool(self.current_results)

        if workflow_title.startswith("1. Calibration"):
            visible_titles = {"Calibration", "Calibration Metrics"}
        elif workflow_title in ("2. Load File", "3. Settings"):
            visible_titles = {"Reliability", "Summary Statistics", "Curve Viewer"} if has_loading_results else set()
        elif workflow_title == "Expert Mode":
            visible_titles = {"Expert Plot"}
        elif workflow_title == "Log":
            visible_titles = set()
        else:
            visible_titles = (
                {"CSM Depth Profiles", "CSM Averaged Data"}
                if mode == "CSM"
                else {"Reliability", "Load Overlay", "Summary Statistics", "Curve Viewer", "Results Table"}
            )

        all_titles = [
            "Calibration",
            "Calibration Metrics",
            "Results Table",
            "Reliability",
            "Load Overlay",
            "Summary Statistics",
            "Curve Viewer",
            "Log",
            "CSM Depth Profiles",
            "CSM Averaged Data",
            "Expert Plot",
        ]
        for title in all_titles:
            self._set_results_tab_visible(title, title in visible_titles)

        if workflow_title.startswith("1. Calibration"):
            idx = self._results_tab_index("Calibration")
            if idx >= 0:
                self.results_panel_tabs.setCurrentIndex(idx)
            return

        for preferred in ("Calibration", "Calibration Metrics", "Expert Plot", "CSM Depth Profiles", "Reliability", "Load Overlay", "Summary Statistics", "Curve Viewer", "CSM Averaged Data", "Results Table"):
            if preferred not in visible_titles:
                continue
            idx = self._results_tab_index(preferred)
            if idx >= 0:
                self.results_panel_tabs.setCurrentIndex(idx)
                break
        self._refresh_results_view_buttons()

    def _show_workflow_results(self, preferred_results_tab: str):
        """Move the workflow to Results and focus a populated right-side results tab."""
        current_title = ""
        if self.workflow_tabs:
            current_idx = self.workflow_tabs.currentIndex()
            current_title = self.workflow_tabs.tabText(current_idx) if current_idx >= 0 else ""
        if current_title == "3. Settings":
            self.unlock_workflow_step(3, move_to_step=True)
        elif current_title != "4. Results":
            return
        self._configure_results_panel_visibility()
        if self.results_panel_tabs:
            idx = self._results_tab_index(preferred_results_tab)
            if idx >= 0:
                self.results_panel_tabs.setCurrentIndex(idx)
        self._refresh_results_view_buttons()

    def _on_workflow_step_changed(self, _index: int):
        self._sync_workflow_top_tabs()
        if self.workflow_tabs and self.workflow_tabs.tabText(_index) == "Expert Mode":
            self.refresh_live_plot_source()
            self._show_expert_plot_tab_only()
        self._configure_results_panel_visibility()

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
        samples_dir = str(self.samples_dir())
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
        samples_dir = str(self.samples_dir())
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
        samples_dir = str(self.samples_dir())
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
            self.unlock_workflow_step(1, move_to_step=False)
            self.status_bar.showMessage(
                "Calibration generated. Select an unknown-sample experiment file in Step 2."
            )
        except Exception as e:
            QMessageBox.critical(self, "Calibration Error", f"Failed to generate calibration:\n{str(e)}")
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Nanoindentation Analysis - ISO 14577-4:2016 Compliant")
        self.setMinimumSize(self.window_min_size)
        self.resize(self.window_target_size)
        self.setup_menu_bar()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(self.sp(4), self.sp(4), self.sp(4), self.sp(4))
        main_layout.setSpacing(self.sp(4))
        
        # Create header
        header_layout = self.create_header()
        main_layout.addLayout(header_layout)
        
        # Left panel - Controls
        left_panel = self.create_control_panel()
        workflow_nav = self.create_workflow_top_tab_bar()
        main_layout.addWidget(workflow_nav)

        # Create splitter for main content
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setChildrenCollapsible(False)
        main_layout.addWidget(main_splitter)
        main_layout.setStretch(0, 0)
        main_layout.setStretch(1, 0)
        main_layout.setStretch(2, 1)

        main_splitter.addWidget(left_panel)
        
        # Right panel - Results and plots
        right_panel = self.create_results_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([self.control_panel_width, self.results_panel_width])
        self._configure_results_panel_visibility()
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready - Select an Excel file to begin analysis")
        
        # Progress bar in status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        self.refresh_live_plot_source()
    
    def create_header(self):
        """Create the header section"""
        bar = QFrame()
        bar.setStyleSheet("""
            QFrame {
                background-color: #f7fafc;
                border: 1px solid #d6dbe0;
                border-radius: 8px;
            }
        """)
        row = QHBoxLayout(bar)
        row.setContentsMargins(self.sp(10), self.sp(6), self.sp(10), self.sp(6))
        row.setSpacing(self.sp(10))

        title_label = QLabel("🔬 Nanoindentation Analysis Suite")
        title_label.setStyleSheet(f"font-size:{self.fp(18)}px; font-weight:600; color:#24313a;")
        row.addWidget(title_label)

        iso_badge = QLabel("ISO 14577-4:2016")
        iso_badge.setStyleSheet("""
            QLabel {
                background:#eef7fb;
                color:#24586a;
                border:1px solid #cfe7ef;
                border-radius:10px;
                padding:2px 8px;
                font-weight:600;
            }
        """)
        row.addWidget(iso_badge)

        self.header_file_label = QLabel("No experiment file selected")
        self.header_file_label.setStyleSheet(f"font-size:{self.fp(11)}px; color:#5e6a72;")
        self.header_file_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row.addWidget(self.header_file_label, 1)

        wrapper = QVBoxLayout()
        wrapper.setSpacing(self.sp(2))
        wrapper.addWidget(bar)
        return wrapper

    def update_header_experiment_file(self, file_path: Optional[str] = None):
        """Show only the selected unknown-sample experiment file in the app header."""
        if not self.header_file_label:
            return
        if file_path:
            self.header_file_label.setText(Path(file_path).name)
            self.header_file_label.setToolTip(str(Path(file_path).resolve()))
        else:
            self.header_file_label.setText("No experiment file selected")
            self.header_file_label.setToolTip("")

    def create_workflow_top_tab_bar(self) -> QTabBar:
        """Create a full-width workflow tab bar that controls the left workflow pages."""
        top_tabs = QTabBar()
        top_tabs.setExpanding(True)
        top_tabs.setElideMode(Qt.ElideRight)
        top_tabs.setUsesScrollButtons(True)
        top_tabs.setDocumentMode(True)
        top_tabs.setMinimumHeight(self.sp(42))
        top_tabs.setStyleSheet("""
            QTabBar {
                background: #ffffff;
            }
            QTabBar::tab {
                font-weight: 700;
                padding: 8px 18px;
                min-height: 26px;
            }
        """)
        self.workflow_top_tabs = top_tabs

        if self.workflow_tabs:
            self.workflow_tabs.tabBar().hide()
            for idx in range(self.workflow_tabs.count()):
                top_tabs.addTab(self.workflow_tabs.tabText(idx))
            self._sync_workflow_top_tabs()

        top_tabs.currentChanged.connect(self._top_workflow_tab_changed)
        return top_tabs

    def _top_workflow_tab_changed(self, index: int):
        if not self.workflow_tabs or not self.workflow_top_tabs:
            return
        if index < 0 or index >= self.workflow_tabs.count():
            return
        if not self.workflow_tabs.isTabEnabled(index):
            self._sync_workflow_top_tabs()
            return
        if self.workflow_tabs.currentIndex() != index:
            self.workflow_tabs.setCurrentIndex(index)

    def _sync_workflow_top_tabs(self):
        if not self.workflow_tabs or not self.workflow_top_tabs:
            return
        self.workflow_top_tabs.blockSignals(True)
        try:
            while self.workflow_top_tabs.count() < self.workflow_tabs.count():
                idx = self.workflow_top_tabs.count()
                self.workflow_top_tabs.addTab(self.workflow_tabs.tabText(idx))
            while self.workflow_top_tabs.count() > self.workflow_tabs.count():
                self.workflow_top_tabs.removeTab(self.workflow_top_tabs.count() - 1)
            for idx in range(self.workflow_tabs.count()):
                self.workflow_top_tabs.setTabText(idx, self.workflow_tabs.tabText(idx))
                self.workflow_top_tabs.setTabEnabled(idx, self.workflow_tabs.isTabEnabled(idx))
            self.workflow_top_tabs.setCurrentIndex(self.workflow_tabs.currentIndex())
        finally:
            self.workflow_top_tabs.blockSignals(False)

    def create_custom_plot_panel(self):
        """Create the Expert Mode custom X/Y plot controls."""
        live_plot_group = QGroupBox("Custom plot from selected file")
        live_plot_layout = QVBoxLayout(live_plot_group)
        live_plot_layout.setSpacing(self.sp(8))

        section1_group = QGroupBox("1. Select source and variables")
        section1_layout = QGridLayout(section1_group)
        section1_layout.setVerticalSpacing(self.sp(7))
        section1_layout.setHorizontalSpacing(self.sp(8))
        section1_layout.setColumnStretch(1, 1)
        section1_layout.setColumnStretch(3, 1)

        section1_layout.addWidget(QLabel("Sheet / source:"), 0, 0)
        self.live_plot_sheet_combo = QComboBox()
        self._configure_expert_combo(self.live_plot_sheet_combo)
        self.live_plot_sheet_combo.currentTextChanged.connect(self._live_plot_sheet_changed)
        section1_layout.addWidget(self.live_plot_sheet_combo, 0, 1, 1, 3)
        section1_layout.addWidget(QLabel("X variable:"), 1, 0)
        self.live_plot_x_combo = QComboBox()
        self._configure_expert_combo(self.live_plot_x_combo)
        self.live_plot_x_combo.currentTextChanged.connect(self._expert_plot_controls_changed)
        section1_layout.addWidget(self.live_plot_x_combo, 1, 1, 1, 3)
        section1_layout.addWidget(QLabel("Y variable:"), 2, 0)
        self.live_plot_y_combo = QComboBox()
        self._configure_expert_combo(self.live_plot_y_combo)
        self.live_plot_y_combo.currentTextChanged.connect(self._expert_plot_controls_changed)
        section1_layout.addWidget(self.live_plot_y_combo, 2, 1, 1, 3)

        self.live_plot_use_ranges_cb = QCheckBox("Use custom axis ranges")
        self.live_plot_use_ranges_cb.toggled.connect(self._toggle_live_plot_ranges)
        section1_layout.addWidget(self.live_plot_use_ranges_cb, 3, 0, 1, 4)

        self.live_plot_xmin_spin = self._create_axis_range_spinbox()
        self.live_plot_xmax_spin = self._create_axis_range_spinbox()
        self.live_plot_ymin_spin = self._create_axis_range_spinbox()
        self.live_plot_ymax_spin = self._create_axis_range_spinbox()
        for spin in (
            self.live_plot_xmin_spin,
            self.live_plot_xmax_spin,
            self.live_plot_ymin_spin,
            self.live_plot_ymax_spin,
        ):
            spin.valueChanged.connect(self._expert_plot_controls_changed)

        section1_layout.addWidget(QLabel("X min:"), 4, 0)
        section1_layout.addWidget(self.live_plot_xmin_spin, 4, 1)
        section1_layout.addWidget(QLabel("X max:"), 4, 2)
        section1_layout.addWidget(self.live_plot_xmax_spin, 4, 3)
        section1_layout.addWidget(QLabel("Y min:"), 5, 0)
        section1_layout.addWidget(self.live_plot_ymin_spin, 5, 1)
        section1_layout.addWidget(QLabel("Y max:"), 5, 2)
        section1_layout.addWidget(self.live_plot_ymax_spin, 5, 3)

        section2_group = QGroupBox("2. LSQ polynomial fit")
        section2_layout = QGridLayout(section2_group)
        section2_layout.setHorizontalSpacing(self.sp(8))
        section2_layout.setVerticalSpacing(self.sp(6))

        self.live_plot_lsq_fit_cb = QCheckBox("Show LSQ polynomial fit")
        self.live_plot_lsq_fit_cb.setToolTip("Fit Y as a least-squares polynomial of X for the selected sheet.")
        self.live_plot_lsq_fit_cb.toggled.connect(self._expert_lsq_controls_changed)
        section2_layout.addWidget(self.live_plot_lsq_fit_cb, 0, 0, 1, 2)

        section2_layout.addWidget(QLabel("Polynomial degree:"), 1, 0)
        self.live_plot_lsq_degree_spin = QSpinBox()
        self.live_plot_lsq_degree_spin.setRange(1, 8)
        self.live_plot_lsq_degree_spin.setValue(1)
        self.live_plot_lsq_degree_spin.setToolTip("Least-squares polynomial degree.")
        self.live_plot_lsq_degree_spin.valueChanged.connect(self._expert_lsq_controls_changed)
        section2_layout.addWidget(self.live_plot_lsq_degree_spin, 1, 1)

        self.live_plot_lsq_status_label = QLabel("Select a single sheet to enable LSQ fit.")
        self.live_plot_lsq_status_label.setWordWrap(True)
        self.live_plot_lsq_status_label.setStyleSheet(f"color:#5e6a72; font-size:{self.fp(10)}px;")
        section2_layout.addWidget(self.live_plot_lsq_status_label, 2, 0, 1, 2)

        section3_group = QGroupBox("3. Refresh and generate plot")
        section3_layout = QGridLayout(section3_group)
        section3_layout.setHorizontalSpacing(self.sp(8))
        section3_layout.setVerticalSpacing(self.sp(6))

        self.live_plot_refresh_button = QPushButton("Refresh from Step 2 File")
        self.live_plot_refresh_button.clicked.connect(self.refresh_live_plot_source)
        section3_layout.addWidget(self.live_plot_refresh_button, 0, 0)

        self.live_plot_show_button = QPushButton("Show Plot on Right")
        self.live_plot_show_button.clicked.connect(self.show_expert_plot_tab)
        section3_layout.addWidget(self.live_plot_show_button, 0, 1)

        self.live_plot_status_label = QLabel("Select an experiment file to load available variables.")
        self.live_plot_status_label.setWordWrap(True)
        section3_layout.addWidget(self.live_plot_status_label, 1, 0, 1, 2)

        live_plot_layout.addWidget(section1_group)
        live_plot_layout.addWidget(section2_group)
        live_plot_layout.addWidget(section3_group)
        self._sync_lsq_fit_controls()
        self._toggle_live_plot_ranges(False)
        return live_plot_group

    def create_expert_offsets_panel(self):
        """Create the Expert Mode editable global offset table."""
        offsets_group = QGroupBox("Global variables / loading h0 offsets")
        offsets_layout = QVBoxLayout(offsets_group)
        offsets_layout.setContentsMargins(self.sp(8), self.sp(8), self.sp(8), self.sp(8))
        offsets_layout.setSpacing(self.sp(6))

        self.expert_offsets_table = QTableWidget()
        self.expert_offsets_table.setColumnCount(4)
        self.expert_offsets_table.setHorizontalHeaderLabels(["Use", "Test", "Sheet", "Loading h0 (nm)"])
        self.expert_offsets_table.setAlternatingRowColors(True)
        self.expert_offsets_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.expert_offsets_table.setMinimumHeight(self.sp(150))
        self.expert_offsets_table.setMaximumHeight(self.sp(260))
        self.expert_offsets_table.verticalHeader().setVisible(False)
        self.expert_offsets_table.itemChanged.connect(self._expert_offset_item_changed)

        header = self.expert_offsets_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        offsets_layout.addWidget(self.expert_offsets_table)

        self.expert_offsets_status_label = QLabel("h0 offsets: no generated file-load defaults yet.")
        self.expert_offsets_status_label.setWordWrap(True)
        self.expert_offsets_status_label.setStyleSheet(f"color:#5e6a72; font-size:{self.fp(10)}px;")
        offsets_layout.addWidget(self.expert_offsets_status_label)

        self.expert_offsets_reset_button = QPushButton("Reset to File-Load h0 Offsets")
        self.expert_offsets_reset_button.setToolTip(
            "Restore the loading h0 offsets generated when the file was first loaded."
        )
        self.expert_offsets_reset_button.clicked.connect(self.reset_expert_offsets_to_file_load_defaults)
        offsets_layout.addWidget(self.expert_offsets_reset_button)
        self._sync_expert_offsets_table()
        return offsets_group
    
    def create_control_panel(self):
        """Create the control panel"""
        panel = QWidget()
        panel.setMinimumWidth(self.sp(300))
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self.sp(4))
        self.workflow_tabs = QTabWidget()
        self.workflow_tabs.tabBar().setExpanding(False)
        self.workflow_tabs.tabBar().setElideMode(Qt.ElideRight)
        self.workflow_tabs.tabBar().setUsesScrollButtons(True)

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
        step1_layout.setSpacing(self.sp(7))
        step1_layout.setContentsMargins(self.sp(6), self.sp(6), self.sp(6), self.sp(6))

        step1_intro = self.create_guided_text(
            "Step 1 of 5 — Tip Area Function Calibration",
            "Start by defining the indenter tip area function. Use a saved calibration "
            "when one already exists, generate one from fused silica for a fresh reference "
            "check, or enter coefficients from your lab protocol. The calibration profile "
            "on the right updates after you apply a choice."
        )
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
            label.setFixedWidth(self.sp(28))
            spin = QDoubleSpinBox()
            spin.setDecimals(6)
            spin.setRange(-1e6, 1e6)
            spin.setSingleStep(0.1 if idx == 0 else 0.001)
            spin.setValue(self.calibration_coefficients.get(key, 0.0))
            spin.setMinimumWidth(self.sp(96))
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
        step2_layout.setSpacing(self.sp(6))
        step2_layout.setContentsMargins(self.sp(6), self.sp(6), self.sp(6), self.sp(6))
        step2_layout.addWidget(self.create_guided_text(
            "Step 2 of 5 — Research Context and File",
            "Name the sample, choose the goal that best matches this run, then browse for "
            "the exported XLS/XLSX file. Click Generate Test Curves when you are ready so you "
            "can inspect each test and decide what belongs in the final calculation. For "
            "free-form X/Y inspection, use the Expert Mode tab."
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
        self.browse_button.setProperty("secondary", True)
        self.browse_button.clicked.connect(self.browse_file)
        file_button_layout.addWidget(self.browse_button)
        self.reload_button = QPushButton("Reload")
        self.reload_button.setProperty("secondary", True)
        self.reload_button.clicked.connect(self.reload_file)
        self.reload_button.setEnabled(False)
        file_button_layout.addWidget(self.reload_button)
        self.generate_curves_button = QPushButton("Generate Test Curves")
        self.generate_curves_button.setProperty("primary", True)
        self.generate_curves_button.setEnabled(False)
        self.generate_curves_button.setToolTip(
            "Generate loading/unloading curves and h0 offsets for test selection."
        )
        self.generate_curves_button.clicked.connect(self.generate_loading_curves_for_selection)
        file_button_layout.addWidget(self.generate_curves_button)
        step2_layout.addLayout(file_button_layout)

        self.workflow_tabs.addTab(step2, "2. Load File")

        # STEP 3: Settings
        step3 = QWidget()
        step3_layout = QVBoxLayout(step3)
        step3_layout.setAlignment(Qt.AlignTop)
        step3_layout.setSpacing(self.sp(8))
        step3_layout.setContentsMargins(self.sp(6), self.sp(6), self.sp(6), self.sp(6))
        step3_layout.addWidget(self.create_guided_text(
            "Step 3 of 5 — Analysis Settings",
            "Choose Oliver-Pharr or CSM, then adjust only the settings needed for that "
            "workflow before moving on to results."
        ))
        settings_group = QGroupBox("Analysis Settings")
        self.oliver_settings_group = settings_group
        settings_layout = QGridLayout(settings_group)
        self.generate_plots_cb = QCheckBox("Generate Plots")
        self.generate_plots_cb.setChecked(True)
        settings_layout.addWidget(self.generate_plots_cb, 0, 0)
        self.export_plots_cb = QCheckBox("Export Plot Images")
        self.export_plots_cb.setChecked(True)
        settings_layout.addWidget(self.export_plots_cb, 0, 1)
        settings_layout.addWidget(QLabel("Minimum fit R²:"), 1, 0)
        self.min_r2_spinbox = QDoubleSpinBox()
        self.min_r2_spinbox.setRange(0.90, 0.999)
        self.min_r2_spinbox.setValue(float(self.config_values.get("min_r_squared", 0.98)))
        self.min_r2_spinbox.setDecimals(3)
        self.min_r2_spinbox.setSingleStep(0.001)
        settings_layout.addWidget(self.min_r2_spinbox, 1, 1)
        settings_layout.addWidget(QLabel("Fit window (% unloading curve):"), 2, 0)
        self.fit_curve_percent_spinbox = QDoubleSpinBox()
        self.fit_curve_percent_spinbox.setRange(5.0, 100.0)
        self.fit_curve_percent_spinbox.setDecimals(1)
        self.fit_curve_percent_spinbox.setSingleStep(1.0)
        self.fit_curve_percent_spinbox.setValue(float(self.config_values.get("fit_curve_percent", 25.0)))
        self.fit_curve_percent_spinbox.valueChanged.connect(self.update_readiness_summary)
        settings_layout.addWidget(self.fit_curve_percent_spinbox, 2, 1)
        settings_layout.addWidget(QLabel("Sample Poisson’s ratio, ν:"), 3, 0)
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
        settings_layout.addWidget(QLabel("Unloading fit model:"), 5, 0)
        self.fitting_method_combo = QComboBox()
        self.fitting_method_combo.addItems(["oliver_pharr", "power_law", "auto"])
        default_method = str(self.config_values.get("default_fitting_method", "oliver_pharr")).lower()
        self.fitting_method_combo.setCurrentText(default_method if default_method in ["oliver_pharr", "power_law", "auto"] else "oliver_pharr")
        self.fitting_method_combo.currentIndexChanged.connect(self.update_readiness_summary)
        settings_layout.addWidget(self.fitting_method_combo, 5, 1)
        settings_layout.addWidget(QLabel("Load Overlay hold segment:"), 6, 0)
        self.op_overlay_hold_combo = QComboBox()
        self.op_overlay_hold_combo.addItems([
            "Remove hold segment",
            "Keep hold segment",
        ])
        self.op_overlay_hold_combo.setToolTip(
            "Choose whether peak hold-time shelves are hidden or retained in the Oliver-Pharr Load Overlay tab."
        )
        self.op_overlay_hold_combo.currentIndexChanged.connect(self._sync_op_overlay_hold_controls)
        settings_layout.addWidget(self.op_overlay_hold_combo, 6, 1)
        self.op_overlay_cutoff_label = QLabel("Load cutoff value (mN):")
        self.op_overlay_cutoff_label.setToolTip(
            "Used when removing the hold segment. Defaults to the lowest peak load among included overlay curves."
        )
        settings_layout.addWidget(self.op_overlay_cutoff_label, 7, 0)
        self.op_overlay_cutoff_spin = QDoubleSpinBox()
        self.op_overlay_cutoff_spin.setRange(0.0, 1e9)
        self.op_overlay_cutoff_spin.setDecimals(3)
        self.op_overlay_cutoff_spin.setSingleStep(1.0)
        self.op_overlay_cutoff_spin.setToolTip(
            "Curves in Load Overlay are trimmed at this load when hold segments are removed."
        )
        self.op_overlay_cutoff_spin.valueChanged.connect(self._op_overlay_cutoff_changed)
        self.op_overlay_cutoff_spin.editingFinished.connect(self._op_overlay_cutoff_changed)
        settings_layout.addWidget(self.op_overlay_cutoff_spin, 7, 1)
        step3_layout.addWidget(settings_group)

        self.csm_settings_group = QGroupBox("CSM Settings")
        csm_settings_layout = QGridLayout(self.csm_settings_group)
        csm_settings_layout.setVerticalSpacing(8)
        csm_settings_layout.setHorizontalSpacing(10)
        csm_settings_layout.setColumnStretch(1, 1)
        csm_settings_layout.addWidget(QLabel("CSM values:"), 1, 0)
        self.csm_source_combo = QComboBox()
        self.csm_source_combo.addItems([
            "Use exported H/Er",
            "Recalculate H/Er"
        ])
        self.csm_source_combo.setToolTip(
            "Use H/Er values already exported by the instrument, or recalculate them "
            "from CSM stiffness using the active tip calibration."
        )
        self.csm_source_combo.currentIndexChanged.connect(self.update_readiness_summary)
        csm_settings_layout.addWidget(self.csm_source_combo, 1, 1)

        self.csm_sd_display_label = QLabel("Spread display:")
        csm_settings_layout.addWidget(self.csm_sd_display_label, 2, 0)
        self.csm_sd_display_combo = QComboBox()
        self.csm_sd_display_combo.addItems([
            "SD band",
            "SD error bars",
        ])
        self.csm_sd_display_combo.setToolTip(
            "Controls how standard deviation is drawn for the averaged CSM profile."
        )
        self.csm_sd_display_combo.currentIndexChanged.connect(self._sync_csm_settings_visibility)
        csm_settings_layout.addWidget(self.csm_sd_display_combo, 2, 1)

        csm_settings_layout.addWidget(QLabel("Plot content:"), 3, 0)
        self.csm_plot_mode_combo = QComboBox()
        self.csm_plot_mode_combo.addItems([
            "Average profile",
            "Individual profiles",
        ])
        self.csm_plot_mode_combo.setToolTip(
            "Choose whether the CSM Depth Profiles tab shows the averaged profile "
            "or overlays every selected test profile with mean and SD annotations."
        )
        self.csm_plot_mode_combo.currentIndexChanged.connect(self._sync_csm_settings_visibility)
        csm_settings_layout.addWidget(self.csm_plot_mode_combo, 3, 1)

        self.csm_plot_mode_help_label = QLabel(
            "Average profile summarizes selected tests; Individual profiles overlays each selected test."
        )
        self.csm_plot_mode_help_label.setWordWrap(True)
        self.csm_plot_mode_help_label.setStyleSheet(f"color:#5e6a72; font-size:{self.fp(10)}px;")
        csm_settings_layout.addWidget(self.csm_plot_mode_help_label, 4, 0, 1, 2)

        depth_min_label = QLabel("Plot/result depth min (nm):")
        depth_min_label.setToolTip("Lower bound of corrected depth values kept in the CSM averaged result and depth-profile plot.")
        csm_settings_layout.addWidget(depth_min_label, 5, 0)
        self.csm_depth_min_spin = QDoubleSpinBox()
        self.csm_depth_min_spin.setRange(-100000, 100000)
        self.csm_depth_min_spin.setValue(100.0)
        self.csm_depth_min_spin.setToolTip("Rows shallower than this corrected depth are excluded from the final CSM average/plot.")
        csm_settings_layout.addWidget(self.csm_depth_min_spin, 5, 1)

        depth_max_label = QLabel("Plot/result depth max (nm):")
        depth_max_label.setToolTip("Upper bound of corrected depth values kept in the CSM averaged result and depth-profile plot.")
        csm_settings_layout.addWidget(depth_max_label, 6, 0)
        self.csm_depth_max_spin = QDoubleSpinBox()
        self.csm_depth_max_spin.setRange(-100000, 100000)
        self.csm_depth_max_spin.setValue(2000.0)
        self.csm_depth_max_spin.setToolTip("Rows deeper than this corrected depth are excluded from the final CSM average/plot.")
        csm_settings_layout.addWidget(self.csm_depth_max_spin, 6, 1)

        self.csm_target_x_label = QLabel("Error-bar depths (start,end,step nm):")
        self.csm_target_x_label.setToolTip(
            "Used only for discrete SD error-bar placement.\n"
            "Example (100, 200, 50) places bars at 100, 150, 200 nm."
        )
        csm_settings_layout.addWidget(self.csm_target_x_label, 7, 0)
        self.csm_target_x_container = QWidget()
        target_x_layout = QHBoxLayout(self.csm_target_x_container)
        target_x_layout.setContentsMargins(0, 0, 0, 0)
        target_x_layout.setSpacing(6)
        self.csm_target_x_start_spin = QDoubleSpinBox()
        self.csm_target_x_start_spin.setRange(-100000, 100000)
        self.csm_target_x_start_spin.setDecimals(1)
        self.csm_target_x_start_spin.setValue(100.0)
        self.csm_target_x_start_spin.setToolTip("Discrete error-bar start depth in nm.")
        self.csm_target_x_start_spin.valueChanged.connect(self.update_readiness_summary)
        target_x_layout.addWidget(self.csm_target_x_start_spin)
        self.csm_target_x_end_spin = QDoubleSpinBox()
        self.csm_target_x_end_spin.setRange(-100000, 100000)
        self.csm_target_x_end_spin.setDecimals(1)
        self.csm_target_x_end_spin.setValue(200.0)
        self.csm_target_x_end_spin.setToolTip("Discrete error-bar end depth in nm.")
        self.csm_target_x_end_spin.valueChanged.connect(self.update_readiness_summary)
        target_x_layout.addWidget(self.csm_target_x_end_spin)
        self.csm_target_x_step_spin = QDoubleSpinBox()
        self.csm_target_x_step_spin.setRange(0.1, 100000)
        self.csm_target_x_step_spin.setDecimals(1)
        self.csm_target_x_step_spin.setValue(50.0)
        self.csm_target_x_step_spin.setToolTip("Discrete error-bar interval (nm).")
        self.csm_target_x_step_spin.valueChanged.connect(self.update_readiness_summary)
        target_x_layout.addWidget(self.csm_target_x_step_spin)
        csm_settings_layout.addWidget(self.csm_target_x_container, 7, 1)

        self.csm_apply_offsets_cb = QCheckBox("Apply Expert Mode h0 offsets")
        self.csm_apply_offsets_cb.setToolTip(
            "Use the current h0 offsets shown in Expert Mode, including any edited values."
        )
        self.csm_apply_offsets_cb.setChecked(True)
        csm_settings_layout.addWidget(self.csm_apply_offsets_cb, 8, 0, 1, 2)

        self.csm_compute_offsets_button = QPushButton("Sync Current h0 Offsets")
        self.csm_compute_offsets_button.setToolTip(
            "Synchronize offsets from the current result records without discarding Expert Mode edits."
        )
        self.csm_compute_offsets_button.clicked.connect(self.compute_csm_offsets)
        csm_settings_layout.addWidget(self.csm_compute_offsets_button, 9, 0, 1, 2)

        self.csm_reset_plot_settings_button = QPushButton("Reset CSM Plot Settings && Redraw")
        self.csm_reset_plot_settings_button.setToolTip(
            "Clear manual CSM axis limits, subplot stacking, and image aspect settings, then redraw the CSM plot."
        )
        self.csm_reset_plot_settings_button.clicked.connect(self.reset_csm_plot_settings_and_redraw)
        csm_settings_layout.addWidget(self.csm_reset_plot_settings_button, 10, 0, 1, 2)

        self.csm_status_text = QTextEdit()
        self.csm_status_text.setReadOnly(True)
        self.csm_status_text.setFixedHeight(self.sp(92))
        csm_settings_layout.addWidget(self.csm_status_text, 11, 0, 1, 2)
        step3_layout.addWidget(self.csm_settings_group)

        # ── Proceed options after settings ────────────────────────────────
        proceed_group = QGroupBox("Run analysis")
        proceed_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        proceed_layout = QHBoxLayout(proceed_group)
        proceed_layout.setContentsMargins(self.sp(12), self.sp(12), self.sp(12), self.sp(12))
        proceed_layout.setSpacing(self.sp(10))
        self.proceed_op_combo = QComboBox()
        self.proceed_op_combo.addItems(["Oliver-Pharr", "CSM"])
        self.proceed_op_combo.setToolTip("Choose analysis workflow to run for the selected tests")
        self.proceed_op_combo.currentIndexChanged.connect(self.update_analysis_type_options)
        proceed_layout.addWidget(self.proceed_op_combo)

        self.proceed_button = QPushButton("Run Analysis")
        self.proceed_button.setProperty("primary", True)
        self.proceed_button.setEnabled(False)
        self.proceed_button.clicked.connect(self._proceed_with_selected_tests)
        proceed_layout.addWidget(self.proceed_button)
        step3_layout.addWidget(proceed_group)
        step3_layout.addStretch(1)
        plot_buttons_group = QGroupBox("Select Tests / Review Curves")
        self.step4_plot_buttons_group = plot_buttons_group
        plot_buttons_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        plot_buttons_group.setMinimumHeight(self.sp(180))
        plot_buttons_group_layout = QVBoxLayout(plot_buttons_group)
        plot_buttons_group_layout.setContentsMargins(self.sp(8), self.sp(8), self.sp(8), self.sp(8))
        plot_buttons_group_layout.setSpacing(self.sp(6))
        self.step4_plot_buttons_note = QLabel("Generate test curves in Step 2 to populate review buttons.")
        self.step4_plot_buttons_note.setWordWrap(True)
        self.step4_plot_buttons_note.setStyleSheet(f"color:#5e6a72; font-size:{self.fp(10)}px;")
        plot_buttons_group_layout.addWidget(self.step4_plot_buttons_note)

        plot_buttons_scroll = QScrollArea()
        plot_buttons_scroll.setWidgetResizable(True)
        plot_buttons_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        plot_buttons_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        plot_buttons_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        plot_buttons_container = QWidget()
        self.step4_plot_buttons_layout = QGridLayout(plot_buttons_container)
        self.step4_plot_buttons_layout.setAlignment(Qt.AlignTop)
        self.step4_plot_buttons_layout.setHorizontalSpacing(8)
        self.step4_plot_buttons_layout.setVerticalSpacing(6)
        self.step4_plot_buttons_layout.setColumnStretch(0, 1)
        self.step4_plot_buttons_layout.setColumnStretch(1, 1)
        self.step4_plot_buttons_layout.setColumnStretch(2, 1)
        plot_buttons_scroll.setWidget(plot_buttons_container)
        plot_buttons_group_layout.addWidget(plot_buttons_scroll, 1)
        step2_layout.addWidget(plot_buttons_group, 1)

        self.step2_next_button = QPushButton("Continue to Settings ▶")
        self.step2_next_button.setProperty("primary", True)
        self.step2_next_button.setEnabled(False)
        self.step2_next_button.clicked.connect(lambda: self.unlock_workflow_step(2, move_to_step=True))
        step2_layout.addWidget(self.step2_next_button)

        self.workflow_tabs.addTab(step3, "3. Settings")

        # STEP 4: Results
        step4 = QWidget()
        step4_layout = QVBoxLayout(step4)
        step4_layout.addWidget(self.create_guided_text(
            "Step 4 of 5 — Results Review",
            "Run the selected analysis, then review the reliability plot and individual "
            "curves. Keep the checkbox enabled for tests you trust; clear it for tests "
            "that should be excluded from the final averages and exports."
        ))
        self.readiness_text = QTextEdit()
        self.readiness_text.setReadOnly(True)
        self.readiness_text.setMinimumHeight(140)
        step4_layout.addWidget(self.readiness_text)
        self.analyze_button = QPushButton("Run Analysis")
        self.analyze_button.setProperty("primary", True)
        self.analyze_button.clicked.connect(lambda _checked=False: self.start_analysis(False))
        self.analyze_button.setEnabled(False)
        step4_layout.addWidget(self.analyze_button)
        self.cancel_button = QPushButton("Cancel Analysis")
        self.cancel_button.setProperty("secondary", True)
        self.cancel_button.clicked.connect(self.cancel_analysis)
        self.cancel_button.setEnabled(False)
        step4_layout.addWidget(self.cancel_button)
        self.step4_next_button = QPushButton("Continue to Export Results ▶")
        self.step4_next_button.setProperty("primary", True)
        self.step4_next_button.setEnabled(False)
        self.step4_next_button.clicked.connect(
            lambda: (
                self.unlock_workflow_step(4, move_to_step=True),
                self.unlock_workflow_tab("Expert Mode", move_to_tab=False),
                self.unlock_workflow_tab("Log", move_to_tab=False),
            )
        )
        step4_layout.addWidget(self.step4_next_button)

        self.workflow_tabs.addTab(step4, "4. Results")

        # STEP 5: Export
        step5 = QWidget()
        step5_layout = QVBoxLayout(step5)
        step5_layout.addWidget(self.create_guided_text(
            "Step 5 of 5 — Export",
            "Export only after the included-test set reflects your review. The Excel and "
            "CSV files use the current final calculations, so any exclusions made in Curve "
            "Viewer are carried into the saved output."
        ))
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

        # Expert Mode: Custom plotting
        expert_mode = QScrollArea()
        expert_mode.setWidgetResizable(True)
        expert_mode.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        expert_mode.setFrameShape(QFrame.NoFrame)
        expert_inner = QWidget()
        expert_layout = QVBoxLayout(expert_inner)
        expert_layout.setContentsMargins(self.sp(6), self.sp(6), self.sp(6), self.sp(6))
        expert_layout.setSpacing(self.sp(8))
        expert_layout.addWidget(self.create_guided_text(
            "Expert Mode — Custom Plot",
            "Choose any numeric X/Y variables from the loaded file and optionally set "
            "manual axis ranges. This tab is separate from the guided analysis flow so "
            "advanced inspection does not interrupt the standard workflow."
        ))
        expert_layout.addWidget(self.create_custom_plot_panel())
        expert_layout.addWidget(self.create_expert_offsets_panel())
        expert_mode.setWidget(expert_inner)
        self.workflow_tabs.addTab(expert_mode, "Expert Mode")

        # Log
        step6 = QWidget()
        step6_layout = QVBoxLayout(step6)
        step6_layout.addWidget(self.create_guided_text(
            "Session Log",
            "Use this as an audit trail for file loading, calibration decisions, analysis "
            "runs, exclusions, and exports during the current session."
        ))
        self.workflow_log_widget = QTextEdit()
        self.workflow_log_widget.setReadOnly(True)
        log_font = QFont()
        log_font.setFamily("Menlo")
        log_font.setPointSize(9)
        self.workflow_log_widget.setFont(log_font)
        step6_layout.addWidget(self.workflow_log_widget)
        self.workflow_tabs.addTab(step6, "Log")

        # lock workflow to strict sequential progression
        for idx in range(1, self.workflow_tabs.count()):
            self.workflow_tabs.setTabEnabled(idx, False)
        self.workflow_tabs.setCurrentIndex(0)
        self.workflow_tabs.currentChanged.connect(self._on_workflow_step_changed)
        self.update_analysis_type_options()
        self._sync_op_overlay_hold_controls()
        self._sync_csm_settings_visibility()
        self.update_readiness_summary()

        layout.addWidget(self.workflow_tabs)
        return panel

    def create_results_panel(self):
        """Create right panel with compact secondary view controls."""
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(self.sp(4))

        tab_widget = QTabWidget()
        tab_widget.setMinimumWidth(self.sp(520))
        tab_widget.tabBar().setExpanding(False)
        tab_widget.tabBar().setElideMode(Qt.ElideRight)
        tab_widget.tabBar().setUsesScrollButtons(True)
        tab_widget.tabBar().hide()
        self.results_panel_tabs = tab_widget

        # ── Tab 0: Calibration profile ────────────────────────────────────
        self.calibration_plot_widget = MatplotlibWidget()
        tab_widget.addTab(self.calibration_plot_widget, "Calibration")
        self._draw_calibration_placeholder()

        self.calibration_metrics_text = QTextEdit()
        self.calibration_metrics_text.setReadOnly(True)
        metrics_font = QFont()
        metrics_font.setFamily("Menlo")
        metrics_font.setPointSize(11)
        self.calibration_metrics_text.setFont(metrics_font)
        self.calibration_metrics_text.setPlainText(
            "Calibration quality metrics will appear after you load, generate, or apply a calibration."
        )
        self._set_calibration_metrics_text_style("#00a8cc")
        tab_widget.addTab(self.calibration_metrics_text, "Calibration Metrics")

        # ── Tab 1: Results table ──────────────────────────────────────────
        self.results_table = ResultsTableWidget()
        tab_widget.addTab(self.results_table, "Results Table")

        # ── Tab 2: Reliability summary (populated after analysis) ─────────
        self.reliability_widget = MatplotlibWidget()
        tab_widget.addTab(self.reliability_widget, "Reliability")

        self.op_overlay_widget = MatplotlibWidget()
        tab_widget.addTab(self.op_overlay_widget, "Load Overlay")

        self.summary_statistics_text = QTextEdit()
        self.summary_statistics_text.setReadOnly(True)
        summary_font = QFont()
        summary_font.setFamily("Menlo")
        summary_font.setPointSize(11)
        self.summary_statistics_text.setFont(summary_font)
        self.summary_statistics_text.setPlainText("Summary statistics will appear after analysis.")
        self.summary_statistics_text.setStyleSheet(f"""
            QTextEdit {{
                background:#f8fbfc;
                color:#24313a;
                border:1px solid #d6dbe0;
                border-left:5px solid #00a8cc;
                border-radius:{self.sp(6)}px;
                padding:{self.sp(14)}px;
                selection-background-color:#c8e8ef;
            }}
        """)
        tab_widget.addTab(self.summary_statistics_text, "Summary Statistics")

        # ── Tab 3: Single test plot with prev/next navigation ─────────────
        test_plot_container = QWidget()
        vbox = QVBoxLayout(test_plot_container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        nav_bar = QWidget()
        nav_bar.setFixedHeight(self.sp(38))
        nav_bar.setStyleSheet("background:#ffffff; border-bottom:1px solid #d6dbe0;")
        nav_h = QHBoxLayout(nav_bar)
        nav_h.setContentsMargins(self.sp(8), 0, self.sp(8), 0)
        nav_h.setSpacing(self.sp(6))

        self.test_nav_prev = QPushButton("◀  Prev")
        self.test_nav_prev.setFixedWidth(self.sp(82))
        self.test_nav_prev.setEnabled(False)
        self.test_nav_prev.setToolTip("Open the previous included/loaded test curve in Curve Viewer.")
        self.test_nav_prev.clicked.connect(self._prev_test)

        self.test_nav_label = QLabel("No tests loaded")
        self.test_nav_label.setAlignment(Qt.AlignCenter)
        self.test_nav_label.setStyleSheet(f"color:#5e6a72; font-size:{self.fp(11)}px;")
        self.test_nav_label.setWordWrap(False)

        self.test_nav_next = QPushButton("Next  ▶")
        self.test_nav_next.setFixedWidth(self.sp(82))
        self.test_nav_next.setEnabled(False)
        self.test_nav_next.setToolTip("Open the next included/loaded test curve in Curve Viewer.")
        self.test_nav_next.clicked.connect(self._next_test)

        self.test_include_checkbox = QCheckBox("Use in final calculations")
        self.test_include_checkbox.setChecked(True)
        self.test_include_checkbox.setEnabled(False)
        self.test_include_checkbox.setToolTip(
            "Checked tests are used in averages, uncertainty summaries, CSM selections, and exports. "
            "Uncheck a questionable curve to exclude it."
        )
        self.test_include_checkbox.setStyleSheet(f"color:#24313a; font-size:{self.fp(11)}px;")
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
        tab_widget.addTab(test_plot_container, "Curve Viewer")

        # ── Tab 4: Analysis log ───────────────────────────────────────────
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        log_font = QFont()
        log_font.setFamily("Menlo")
        log_font.setPointSize(9)
        self.log_widget.setFont(log_font)
        self.log_widget.textChanged.connect(self._sync_workflow_log_tab)
        tab_widget.addTab(self.log_widget, "Log")
        self._sync_workflow_log_tab()

        # ── CSM tabs ──────────────────────────────────────────────────────
        self.csm_depth_plot_widget = MatplotlibWidget()
        tab_widget.addTab(self.csm_depth_plot_widget, "CSM Depth Profiles")

        self.csm_table = QTableWidget()
        self.csm_table.setAlternatingRowColors(True)
        self.csm_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        tab_widget.addTab(self.csm_table, "CSM Averaged Data")

        # ── Expert Mode custom plot ───────────────────────────────────────
        if PLOTLY_AVAILABLE and QT_WEBENGINE_AVAILABLE:
            self.live_plot_widget = QWebEngineView()
        else:
            self.live_plot_widget = QTextEdit()
            self.live_plot_widget.setReadOnly(True)
        tab_widget.addTab(self.live_plot_widget, "Expert Plot")
        self._draw_expert_plot_placeholder()
        tab_widget.currentChanged.connect(lambda _idx: self._refresh_results_view_buttons())

        self.results_summary_label = QLabel("Load a file, generate test curves, then run analysis.")
        self.results_summary_label.setWordWrap(True)
        self.results_summary_label.setStyleSheet(f"""
            QLabel {{
                background:#f8fbfc;
                color:#24313a;
                border:1px solid #c8e8ef;
                border-left:4px solid #00a8cc;
                border-radius:{self.sp(6)}px;
                padding:{self.sp(7)}px {self.sp(9)}px;
                font-size:{self.fp(10)}px;
            }}
        """)

        controls = QFrame()
        controls.setStyleSheet("QFrame { background:#ffffff; border:1px solid #d6dbe0; border-radius:6px; }")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(self.sp(6), self.sp(4), self.sp(6), self.sp(4))
        controls_layout.setSpacing(self.sp(6))
        view_tooltips = {
            "Reliability": "Overview of fit quality and property distributions across all included tests.",
            "Load Overlay": "Overlay of included Oliver-Pharr loading and unloading curves with mean values.",
            "Curve Viewer": "Inspect one load-displacement curve at a time, then include or exclude tests.",
            "Results Table": "Tabular accepted-test results currently used for final calculations.",
            "CSM Depth Profiles": "Averaged CSM hardness/modulus profiles versus corrected depth.",
            "CSM Averaged Data": "Numeric CSM averaged profile rows for export and review.",
            "Expert Plot": "Custom X/Y plotting from the selected file and included tests.",
            "Log": "Timestamped session audit trail.",
            "Calibration": "Tip area function and calibration reliability view.",
            "Calibration Metrics": "Numeric calibration quality assessment and overall verdict.",
            "Summary Statistics": "Numeric final statistics for included tests.",
        }
        for title in ("Calibration", "Calibration Metrics", "Reliability", "Load Overlay", "Summary Statistics", "Curve Viewer", "Results Table", "CSM Depth Profiles", "CSM Averaged Data", "Expert Plot", "Log"):
            btn = QPushButton(title)
            btn.setCheckable(True)
            btn.setProperty("viewSwitch", True)
            btn.setMinimumHeight(self.sp(26))
            btn.setToolTip(view_tooltips.get(title, title))
            btn.clicked.connect(lambda _checked=False, name=title: self._switch_results_view(name))
            controls_layout.addWidget(btn)
            self.results_view_buttons[title] = btn
        controls_layout.addStretch()

        self.results_view_help_label = QLabel("")
        self.results_view_help_label.setWordWrap(True)
        self.results_view_help_label.setStyleSheet(f"""
            QLabel {{
                background:#ffffff;
                color:#5e6a72;
                border:1px solid #e1e7eb;
                border-radius:{self.sp(5)}px;
                padding:{self.sp(6)}px {self.sp(8)}px;
                font-size:{self.fp(10)}px;
            }}
        """)

        panel_layout.addWidget(self.results_summary_label)
        panel_layout.addWidget(controls)
        panel_layout.addWidget(self.results_view_help_label)
        panel_layout.addWidget(tab_widget, 1)
        self._refresh_results_view_buttons()
        return panel

    def _switch_results_view(self, title: str):
        idx = self._results_tab_index(title)
        if idx >= 0 and self.results_panel_tabs:
            self.results_panel_tabs.setCurrentIndex(idx)
        self._refresh_results_view_buttons()

    def _refresh_results_view_buttons(self):
        if not self.results_panel_tabs or not self.results_view_buttons:
            return
        current_title = self.results_panel_tabs.tabText(self.results_panel_tabs.currentIndex())
        help_text = {
            "Reliability": (
                "Reliability shows the whole batch: fit quality, accepted-test distributions, "
                "and whether any tests look inconsistent before final averages are trusted."
            ),
            "Load Overlay": (
                "Load Overlay draws all included Oliver-Pharr load-displacement curves together "
                "and annotates the mean hardness and modulus."
            ),
            "Curve Viewer": (
                "Curve Viewer is for test-by-test review. Use Prev/Next or the test buttons on the left, "
                "inspect the load-displacement curve and fit markers, then uncheck questionable tests."
            ),
            "Results Table": "Results Table lists the numeric values for the currently included tests.",
            "CSM Depth Profiles": "CSM Depth Profiles show averaged hardness/modulus versus corrected depth.",
            "CSM Averaged Data": "CSM Averaged Data is the numeric profile table used for export.",
            "Expert Plot": "Expert Plot lets you choose custom X/Y variables and optional LSQ fitting.",
            "Log": "Log records file choices, settings, exclusions, final values, and exports.",
            "Calibration": "Calibration shows the active tip area function and calibration reliability.",
            "Calibration Metrics": "Calibration Metrics shows the numeric quality assessment separately from the plots.",
            "Summary Statistics": "Summary Statistics lists final hardness, modulus, and fit-quality statistics for included tests.",
        }
        if self.results_view_help_label is not None:
            self.results_view_help_label.setText(help_text.get(current_title, ""))
        for title, button in self.results_view_buttons.items():
            idx = self._results_tab_index(title)
            if idx < 0:
                button.setVisible(False)
                continue
            tab_bar = self.results_panel_tabs.tabBar()
            visible = tab_bar.isTabVisible(idx) if hasattr(tab_bar, "isTabVisible") else self.results_panel_tabs.isTabEnabled(idx)
            button.setVisible(visible)
            button.setChecked(visible and title == current_title)

    def _set_calibration_metrics_text_style(self, accent_color: str):
        if not self.calibration_metrics_text:
            return
        self.calibration_metrics_text.setStyleSheet(f"""
            QTextEdit {{
                background:#f8fbfc;
                color:#24313a;
                border:1px solid #d6dbe0;
                border-left:5px solid {accent_color};
                border-radius:{self.sp(6)}px;
                padding:{self.sp(14)}px;
                selection-background-color:#c8e8ef;
            }}
        """)

    def _set_calibration_metrics_text(self, text: str, accent_color: str = "#00a8cc"):
        if not self.calibration_metrics_text:
            return
        self.calibration_metrics_text.setPlainText(text.strip())
        self._set_calibration_metrics_text_style(accent_color)

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

    def _draw_expert_plot_placeholder(self):
        """Show an instructional placeholder in the Expert Plot tab."""
        if self.live_plot_widget is None:
            return
        self._set_expert_plot_html(
            """
            <div class="placeholder">
              <h1>Expert Plot</h1>
              <p>Load a file in Step 2, then use Expert Mode on the left to choose tests and X/Y variables.</p>
              <p>Click <b>Show Plot on Right</b> to generate the Plotly chart.</p>
            </div>
            """
        )

    def _expert_plot_html_shell(self, body: str) -> str:
        return f"""
        <html>
        <head>
        <style>
          html, body {{
            margin: 0;
            height: 100%;
            background: #ffffff;
            color: #24313a;
            font-family: Arial, Helvetica, sans-serif;
          }}
          .placeholder {{
            height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
          }}
          h1 {{
            margin: 0 0 12px;
            font-size: {self.fp(24)}px;
          }}
          p {{
            margin: 4px 0;
            color: #5e6a72;
            font-size: {self.fp(14)}px;
          }}
        </style>
        </head>
        <body>{body}</body>
        </html>
        """

    def _set_expert_plot_html(self, body_or_html: str, already_full_html: bool = False):
        html = body_or_html if already_full_html else self._expert_plot_html_shell(body_or_html)
        html = html.replace(":focus-visible", ":focus")
        if self.live_plot_widget is None:
            return
        if hasattr(self.live_plot_widget, "load"):
            render_id = int(time.time() * 1000)
            tmp_path = Path(gettempdir()) / f"indentanalyzer_expert_plot_{render_id}.html"
            tmp_path.write_text(html, encoding="utf-8")
            self.live_plot_html_path = tmp_path
            url = QUrl.fromLocalFile(str(tmp_path))
            url.setQuery(f"v={render_id}")
            self.live_plot_widget.load(url)
        elif hasattr(self.live_plot_widget, "setContent"):
            self.live_plot_widget.setContent(
                html.encode("utf-8"),
                "text/html;charset=UTF-8",
                QUrl("about:blank")
            )
        elif hasattr(self.live_plot_widget, "setHtml"):
            self.live_plot_widget.setHtml(html)
        elif hasattr(self.live_plot_widget, "setPlainText"):
            self.live_plot_widget.setPlainText("Plotly/WebEngine is not available. Install plotly and PyQtWebEngine.")

    def _sync_workflow_log_tab(self):
        if not self.workflow_log_widget or not self.log_widget:
            return
        source_text = self.log_widget.toPlainText()
        if self.workflow_log_last_length > len(source_text):
            self.workflow_log_widget.append("\n--- log continued ---\n")
            self.workflow_log_last_length = 0
        new_text = source_text[self.workflow_log_last_length:]
        if new_text:
            self.workflow_log_widget.moveCursor(QTextCursor.End)
            self.workflow_log_widget.insertPlainText(new_text)
            self.workflow_log_last_length = len(source_text)
        self.workflow_log_widget.verticalScrollBar().setValue(
            self.workflow_log_widget.verticalScrollBar().maximum()
        )

    def _make_csm_analyzer(self):
        if CSMAnalyzer is None:
            raise RuntimeError("CSM analyzer module is not available.")
        return CSMAnalyzer(
            area_function_coefficients=self.calibration_coefficients.copy(),
            file_loader_name=self.selected_file_loader_name,
        )

    @staticmethod
    def _format_test_range(test_numbers: List[int]) -> str:
        if not test_numbers:
            return ""
        ranges = []
        start = prev = None
        for value in sorted(set(test_numbers)):
            if start is None:
                start = prev = value
            elif value == prev + 1:
                prev = value
            else:
                ranges.append(str(start) if start == prev else f"{start}-{prev}")
                start = prev = value
        if start is not None:
            ranges.append(str(start) if start == prev else f"{start}-{prev}")
        return ",".join(ranges)

    @staticmethod
    def _log_timestamp() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def append_research_log(self, message: str = "", category: str = ""):
        if not self.log_widget:
            return
        if not message:
            self.log_widget.append("")
            return
        prefix = f"[{self._log_timestamp()}]"
        if category:
            prefix = f"{prefix} {category}"
        self.log_widget.append(f"{prefix} {message}")

    def append_csm_status_log(self, message: str = "", category: str = ""):
        if self.csm_status_text:
            if message:
                prefix = f"[{self._log_timestamp()}]"
                if category:
                    prefix = f"{prefix} {category}"
                self.csm_status_text.append(f"{prefix} {message}")
            else:
                self.csm_status_text.append("")
        self.append_research_log(message, category)

    def _selected_step4_test_numbers(self) -> List[int]:
        if not self.current_results:
            return []
        selected_tests = []
        for idx, result in enumerate(self.current_results):
            if idx in self.excluded_test_indices:
                continue
            test_number = self._test_number_from_result(result, idx)
            if test_number in self.excluded_test_numbers:
                continue
            selected_tests.append(test_number)
        return sorted(set(selected_tests))

    def _sync_csm_test_range_from_selection(self):
        selected_tests = self._selected_step4_test_numbers()
        self.csm_selected_test_numbers = selected_tests.copy()
        self._sync_expert_offsets_table()
        self.update_readiness_summary()

    def _csm_test_numbers(self) -> List[int]:
        selected_tests = self._selected_step4_test_numbers()
        if selected_tests:
            self.csm_selected_test_numbers = selected_tests.copy()
            return selected_tests
        if self.csm_selected_test_numbers:
            return self.csm_selected_test_numbers.copy()
        raise ValueError("No tests selected for CSM. Select included tests in Open Test Plot first.")

    def _curve_viewer_offsets_for_tests(self, test_numbers: List[int]) -> Dict[int, float]:
        offsets: Dict[int, float] = {}
        requested = set(test_numbers)
        for test_number in requested:
            if test_number in self.csm_offsets:
                value = self.csm_offsets.get(test_number)
                try:
                    value_float = float(value)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(value_float) and abs(value_float) < 10000:
                    offsets[test_number] = value_float

        if not self.current_results:
            return offsets

        for idx, result in enumerate(self.current_results):
            if idx in self.excluded_test_indices:
                continue
            test_number = self._test_number_from_result(result, idx)
            if test_number not in requested or test_number in offsets:
                continue
            h0_value = result.get("Loading Offset h0 (nm)")
            try:
                h0_float = float(h0_value)
            except (TypeError, ValueError):
                continue
            if np.isfinite(h0_float) and abs(h0_float) < 10000:
                offsets[test_number] = h0_float
        return offsets

    @staticmethod
    def _finite_float_or_none(value: Any) -> Optional[float]:
        try:
            value_float = float(value)
        except (TypeError, ValueError):
            return None
        return value_float if np.isfinite(value_float) and abs(value_float) < 10000 else None

    def _snapshot_file_load_offsets(self, results: List[Dict[str, Any]]):
        """Remember the automatically generated loading h0 offsets from file load."""
        offsets: Dict[int, float] = {}
        for idx, result in enumerate(results):
            test_number = self._test_number_from_result(result, idx)
            if test_number is None:
                test_number = idx + 1
            offset = self._finite_float_or_none(result.get("Loading Offset h0 (nm)"))
            if offset is not None:
                offsets[int(test_number)] = offset
        self.file_load_offsets = offsets
        self.update_expert_offsets_status()

    def _set_result_loading_offset(self, test_number: int, value: float):
        for idx, result in enumerate(self.current_results):
            if self._test_number_from_result(result, idx) == test_number:
                result["Loading Offset h0 (nm)"] = value
                break

    def _apply_expert_offsets_to_current_results(self) -> int:
        """Apply edited Expert Mode h0 offsets to the active result records."""
        if not self.current_results or not self.csm_offsets:
            return 0
        applied = 0
        for idx, result in enumerate(self.current_results):
            test_number = self._test_number_from_result(result, idx)
            if test_number is None:
                continue
            offset = self._finite_float_or_none(self.csm_offsets.get(test_number))
            if offset is None:
                continue
            result["Loading Offset h0 (nm)"] = offset
            applied += 1
        return applied

    def _refresh_outputs_after_offset_change(self, test_number: int):
        """Refresh views that display loading h0 corrected data."""
        if self.results_table and self.current_results:
            self.results_table.load_results(self.get_included_results())

        for idx, result in enumerate(self.current_results):
            if self._test_number_from_result(result, idx) != test_number:
                continue
            if idx == self.current_test_index and self.single_test_plot is not None:
                self._render_test_plot(self.single_test_plot, result)
                self._update_test_nav_label()
            break

        included_results = self.get_included_results() if self.current_results else []
        if included_results and self.op_overlay_widget is not None:
            self.create_load_overlay_plot_tab(included_results)

        self.update_results_summary_strip()

    def reset_expert_offsets_to_file_load_defaults(self):
        """Restore editable Expert Mode offsets to the file-load generated baseline."""
        if not self.file_load_offsets:
            QMessageBox.information(
                self,
                "No File-Load Offsets",
                "No generated loading h0 offsets are available to restore yet."
            )
            return

        restored = 0
        for test_number, value in self.file_load_offsets.items():
            self.csm_offsets[int(test_number)] = float(value)
            self._set_result_loading_offset(int(test_number), float(value))
            restored += 1

        self._sync_expert_offsets_table()
        self.update_expert_offsets_status()
        current_test_number = None
        if self.current_results and 0 <= self.current_test_index < len(self.current_results):
            current_test_number = self._test_number_from_result(
                self.current_results[self.current_test_index],
                self.current_test_index
            )
        if current_test_number is not None:
            self._refresh_outputs_after_offset_change(current_test_number)
        self.update_readiness_summary()
        if self._selected_live_plot_source() == "__all_tests__":
            self.update_live_variable_plot()
        if self.log_widget:
            self.log_widget.append(f"Reset Expert Mode offsets to file-load defaults for {restored} tests.")
        self.status_bar.showMessage("Expert Mode offsets reset to file-load defaults.")

    def _offsets_match_file_load_defaults(self) -> bool:
        if not self.file_load_offsets:
            return False
        for test_number, default_value in self.file_load_offsets.items():
            current = self._finite_float_or_none(self.csm_offsets.get(test_number))
            if current is None or abs(current - float(default_value)) > 1e-6:
                return False
        return True

    def update_expert_offsets_status(self):
        if self.expert_offsets_status_label is None:
            return
        if not self.file_load_offsets:
            text = "h0 offsets: no generated file-load defaults yet."
        elif self._offsets_match_file_load_defaults():
            text = f"h0 offsets: generated from file load ({len(self.file_load_offsets)} defaults)."
        else:
            text = "h0 offsets: edited from file-load defaults. Use reset to restore generated values."
        self.expert_offsets_status_label.setText(text)

    def _expert_offset_item_changed(self, item: QTableWidgetItem):
        if self.expert_offsets_syncing:
            return
        test_number = item.data(Qt.UserRole)
        if test_number is None:
            return
        if item.column() == 0:
            included = item.checkState() == Qt.Checked
            self._set_test_included_for_expert_table(int(test_number), included)
            if self.current_results:
                self.refresh_final_calculations()
            else:
                self._sync_expert_offsets_table()
            if self._selected_live_plot_source() == "__all_tests__":
                self.update_live_variable_plot()
            state_text = "included" if included else "excluded"
            self.status_bar.showMessage(f"Test {int(test_number):03d} {state_text} in Expert Mode.")
            return
        if item.column() != 3:
            return
        value = self._finite_float_or_none(item.text())
        if value is None:
            item.setBackground(QColor("#fff0f0"))
            self.status_bar.showMessage("Expert offset must be a numeric value.")
            return

        test_number = int(test_number)
        self.csm_offsets[test_number] = value
        self._set_result_loading_offset(test_number, value)
        self.update_expert_offsets_status()
        self._refresh_outputs_after_offset_change(test_number)
        self.update_readiness_summary()

        if self._selected_live_plot_source() == "__all_tests__":
            self.update_live_variable_plot()

        self.expert_offsets_syncing = True
        if self.expert_offsets_table is not None:
            self.expert_offsets_table.blockSignals(True)
        item.setText(f"{value:.2f}")
        item.setBackground(QColor("#ffffff"))
        if self.expert_offsets_table is not None:
            self.expert_offsets_table.blockSignals(False)
        self.expert_offsets_syncing = False
        self.status_bar.showMessage(f"Updated loading h0 offset for Test {test_number:03d}.")

    def _set_test_included_for_expert_table(self, test_number: int, included: bool):
        if included:
            self.excluded_test_numbers.discard(test_number)
        else:
            self.excluded_test_numbers.add(test_number)

        for idx, result in enumerate(self.current_results):
            if self._test_number_from_result(result, idx) != test_number:
                continue
            if included:
                self.excluded_test_indices.discard(idx)
            else:
                self.excluded_test_indices.add(idx)

    def _sync_expert_offsets_table(self):
        """Mirror Load-tab test inclusion and expose editable loading h0 offsets."""
        if self.expert_offsets_table is None:
            return

        self.expert_offsets_syncing = True
        table = self.expert_offsets_table
        table.blockSignals(True)
        try:
            if self.current_results:
                rows = []
                for idx, result in enumerate(self.current_results):
                    test_number = self._test_number_from_result(result, idx)
                    if test_number is None:
                        test_number = idx + 1
                    sheet_name = f"Test {test_number:03d}"
                    included = self._is_result_included(idx, result)
                    auto_offset = self._finite_float_or_none(result.get("Loading Offset h0 (nm)"))
                    if auto_offset is not None and test_number not in self.csm_offsets:
                        self.csm_offsets[test_number] = auto_offset
                    offset_value = self.csm_offsets.get(test_number, auto_offset)
                    rows.append((test_number, sheet_name, included, offset_value))
            else:
                rows = []
                for idx, sheet_name in enumerate(self.live_plot_test_sheets):
                    test_number = self._test_number_from_sheet_name(sheet_name) or idx + 1
                    included = test_number not in self.excluded_test_numbers
                    rows.append((test_number, sheet_name, included, self.csm_offsets.get(test_number)))

            table.setRowCount(len(rows))
            if self.expert_offsets_reset_button is not None:
                self.expert_offsets_reset_button.setEnabled(bool(self.file_load_offsets))
            for row, (test_number, sheet_name, included, offset_value) in enumerate(rows):
                status_item = QTableWidgetItem("")
                test_item = QTableWidgetItem(f"{test_number:03d}")
                sheet_item = QTableWidgetItem(str(sheet_name))
                offset_text = "" if offset_value is None else f"{float(offset_value):.2f}"
                offset_item = QTableWidgetItem(offset_text)

                for item in (status_item, test_item, sheet_item, offset_item):
                    item.setData(Qt.UserRole, int(test_number))
                    item.setForeground(QColor("#24313a" if included else "#8a949b"))
                    item.setBackground(QColor("#ffffff" if included else "#f1f4f6"))

                default_offset = self.file_load_offsets.get(int(test_number))
                offset_is_edited = (
                    default_offset is not None
                    and offset_value is not None
                    and abs(float(offset_value) - float(default_offset)) > 1e-6
                )
                if offset_is_edited and included:
                    offset_item.setBackground(QColor("#fff8dc"))
                    offset_item.setToolTip(
                        f"Edited from file-load default: {float(default_offset):.2f} nm"
                    )
                elif default_offset is not None:
                    offset_item.setToolTip("Generated at file load.")

                read_only = Qt.ItemIsSelectable | Qt.ItemIsEnabled
                status_item.setFlags(read_only | Qt.ItemIsUserCheckable)
                status_item.setCheckState(Qt.Checked if included else Qt.Unchecked)
                test_item.setFlags(read_only)
                sheet_item.setFlags(read_only)
                offset_item.setFlags(
                    (Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                    if included else read_only
                )

                table.setItem(row, 0, status_item)
                table.setItem(row, 1, test_item)
                table.setItem(row, 2, sheet_item)
                table.setItem(row, 3, offset_item)

            table.resizeColumnsToContents()
        finally:
            table.blockSignals(False)
            self.expert_offsets_syncing = False
            self.update_expert_offsets_status()

    def compute_csm_offsets(self):
        try:
            tests = self._csm_test_numbers()
            offsets = self._curve_viewer_offsets_for_tests(tests)
            if not offsets:
                QMessageBox.warning(
                    self,
                    "No h0 Offsets",
                    "No loading h0 offsets found for the currently selected tests.\n"
                    "Keep tests that have Loading Offset h0 values, edit them in Expert Mode, "
                    "or disable offset application."
                )
                return
            self.csm_offsets.update(offsets)
            for test_number, value in offsets.items():
                self._set_result_loading_offset(test_number, value)

            self._sync_expert_offsets_table()
            self.update_expert_offsets_status()
            current_test_number = None
            if self.current_results and 0 <= self.current_test_index < len(self.current_results):
                current_test_number = self._test_number_from_result(
                    self.current_results[self.current_test_index],
                    self.current_test_index
                )
            if current_test_number is not None and current_test_number in offsets:
                self._refresh_outputs_after_offset_change(current_test_number)

            missing = sorted(set(tests) - set(offsets.keys()))
            self.append_csm_status_log(
                f"Synced current Expert Mode loading h0 offsets for {len(offsets)} selected tests.",
                "CSM"
            )
            if missing:
                self.append_csm_status_log(
                    f"Missing loading h0 offsets for tests: {self._format_test_range(missing)}",
                    "CSM"
                )
            self.status_bar.showMessage("CSM offsets synced from current Expert Mode values.")
            if self._selected_live_plot_source() == "__all_tests__":
                self.update_live_variable_plot()
        except Exception as e:
            QMessageBox.critical(self, "CSM Offset Error", f"Failed to sync CSM offsets:\n{str(e)}")

    def _summarize_csm_publication_values(
        self,
        raw: pd.DataFrame,
        test_numbers: List[int],
        depth_window: Tuple[float, float],
    ) -> Dict[str, Any]:
        start_nm, end_nm = [float(v) for v in depth_window]
        summary: Dict[str, Any] = {
            "depth_start_nm": start_nm,
            "depth_end_nm": end_nm,
            "test_numbers": list(test_numbers),
            "properties": {},
        }
        if raw is None or raw.empty or "Depth (nm)" not in raw or "Test" not in raw:
            return summary

        working = raw.copy()
        working["Depth (nm)"] = pd.to_numeric(working["Depth (nm)"], errors="coerce")
        working["Test"] = pd.to_numeric(working["Test"], errors="coerce")
        windowed = working[
            working["Depth (nm)"].between(start_nm, end_nm, inclusive="both")
            & working["Test"].isin(test_numbers)
        ].copy()

        property_columns = [
            ("Hardness", "Hardness (GPa)", "GPa"),
            ("Modulus", "Modulus (GPa)", "GPa"),
        ]
        for label, column, unit in property_columns:
            if column not in windowed:
                continue
            per_test: List[Dict[str, Any]] = []
            for test_number in test_numbers:
                values = pd.to_numeric(
                    windowed.loc[windowed["Test"] == test_number, column],
                    errors="coerce",
                ).replace([np.inf, -np.inf], np.nan).dropna()
                n_points = int(values.count())
                if n_points == 0:
                    per_test.append({
                        "test": int(test_number),
                        "n": 0,
                        "mean": np.nan,
                        "sd": np.nan,
                        "uncertainty": np.nan,
                    })
                    continue
                mean_value = float(values.mean())
                sd_value = float(values.std(ddof=1)) if n_points > 1 else 0.0
                uncertainty = float(sd_value / np.sqrt(n_points)) if n_points > 1 else 0.0
                per_test.append({
                    "test": int(test_number),
                    "n": n_points,
                    "mean": mean_value,
                    "sd": sd_value,
                    "uncertainty": uncertainty,
                })

            valid_rows = [row for row in per_test if np.isfinite(row["mean"])]
            if valid_rows:
                means = np.asarray([row["mean"] for row in valid_rows], dtype=float)
                uncertainties = np.asarray([
                    row["uncertainty"] if np.isfinite(row["uncertainty"]) else 0.0
                    for row in valid_rows
                ], dtype=float)
                n_tests = int(means.size)
                overall_mean = float(np.mean(means))
                propagated_uncertainty = float(np.sqrt(np.sum(np.square(uncertainties))) / n_tests)
                between_test_uncertainty = (
                    float(np.std(means, ddof=1) / np.sqrt(n_tests)) if n_tests > 1 else 0.0
                )
                quoted_uncertainty = propagated_uncertainty
            else:
                n_tests = 0
                overall_mean = np.nan
                propagated_uncertainty = np.nan
                between_test_uncertainty = np.nan
                quoted_uncertainty = np.nan

            summary["properties"][label] = {
                "column": column,
                "unit": unit,
                "per_test": per_test,
                "n_tests": n_tests,
                "overall_mean": overall_mean,
                "propagated_uncertainty": propagated_uncertainty,
                "between_test_uncertainty": between_test_uncertainty,
                "quoted_uncertainty": quoted_uncertainty,
            }
        return summary

    @staticmethod
    def _format_publication_number(value: Any) -> str:
        try:
            value = float(value)
        except (TypeError, ValueError):
            return "n/a"
        if not np.isfinite(value):
            return "n/a"
        return f"{value:.6g}"

    def _log_csm_publication_summary(self, summary: Dict[str, Any]):
        if not summary:
            return
        start_nm = summary.get("depth_start_nm", np.nan)
        end_nm = summary.get("depth_end_nm", np.nan)
        test_numbers = summary.get("test_numbers", [])
        properties = summary.get("properties", {})
        selected_tests = self._format_test_range(test_numbers) if test_numbers else "none"

        timestamp = self._log_timestamp()
        lines = [
            "",
            f"[{timestamp}] CSM Publication Summary",
            f"  Selected tests for final calculations: {selected_tests}",
            "  All selected tests use the same averaging window: "
            f"{self._format_publication_number(start_nm)} to "
            f"{self._format_publication_number(end_nm)} nm.",
            "  Uncertainty method: per-test mean uncertainty is SD/sqrt(n); "
            "single quoted uncertainty is propagated from the selected per-test uncertainties.",
        ]
        if not properties:
            lines.append("  No hardness or modulus columns were available in the selected CSM window.")

        for property_name, result in properties.items():
            unit = result.get("unit", "")
            lines.append(f"  {property_name} per-test averages:")
            for row in result.get("per_test", []):
                test_label = f"{int(row['test']):03d}" if "test" in row else "???"
                if int(row.get("n", 0)) <= 0:
                    lines.append(f"    Test {test_label}: no points in window")
                    continue
                lines.append(
                    f"    Test {test_label}: mean={self._format_publication_number(row.get('mean'))} {unit}, "
                    f"u={self._format_publication_number(row.get('uncertainty'))} {unit}, "
                    f"n={int(row.get('n', 0))}"
                )
            lines.append(
                f"  {property_name} all-tests average: "
                f"{self._format_publication_number(result.get('overall_mean'))} +/- "
                f"{self._format_publication_number(result.get('quoted_uncertainty'))} {unit} "
                f"(N={int(result.get('n_tests', 0))} tests; propagated="
                f"{self._format_publication_number(result.get('propagated_uncertainty'))}, "
                f"between-test SEM={self._format_publication_number(result.get('between_test_uncertainty'))})"
            )

        message = "\n".join(lines)
        self.log_widget.append(message)
        if self.csm_status_text:
            self.csm_status_text.append(message)

    def _csm_publication_summary_table(self, summary: Dict[str, Any]) -> pd.DataFrame:
        rows: List[Dict[str, Any]] = []
        if not summary:
            return pd.DataFrame(rows)
        start_nm = summary.get("depth_start_nm", np.nan)
        end_nm = summary.get("depth_end_nm", np.nan)
        for property_name, result in summary.get("properties", {}).items():
            unit = result.get("unit", "")
            for row in result.get("per_test", []):
                rows.append({
                    "Property": property_name,
                    "Scope": "Per test",
                    "Test": row.get("test"),
                    "Depth Start (nm)": start_nm,
                    "Depth End (nm)": end_nm,
                    "Mean": row.get("mean"),
                    "Quoted Uncertainty": row.get("uncertainty"),
                    "Unit": unit,
                    "N Points": row.get("n"),
                    "N Tests": "",
                    "Propagated Uncertainty": "",
                    "Between-Test SEM": "",
                })
            rows.append({
                "Property": property_name,
                "Scope": "All tests",
                "Test": "",
                "Depth Start (nm)": start_nm,
                "Depth End (nm)": end_nm,
                "Mean": result.get("overall_mean"),
                "Quoted Uncertainty": result.get("quoted_uncertainty"),
                "Unit": unit,
                "N Points": "",
                "N Tests": result.get("n_tests"),
                "Propagated Uncertainty": result.get("propagated_uncertainty"),
                "Between-Test SEM": result.get("between_test_uncertainty"),
            })
        return pd.DataFrame(rows)

    def run_csm_analysis(self):
        file_path = self.file_path_edit.text() if self.file_path_edit else ""
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "No CSM File", "Select a CSM XLS/XLSX file in Step 2 first.")
            return
        try:
            self.last_run_context = "csm"
            test_numbers = self._csm_test_numbers()
            depth_range = (
                float(self.csm_depth_min_spin.value()),
                float(self.csm_depth_max_spin.value()),
            )
            if depth_range[1] < depth_range[0]:
                QMessageBox.warning(
                    self,
                    "Invalid CSM Depth Window",
                    "Set Plot/result depth max greater than or equal to Plot/result depth min."
                )
                return
            error_bar_range = (
                float(self.csm_target_x_start_spin.value()),
                float(self.csm_target_x_end_spin.value()),
                float(self.csm_target_x_step_spin.value()),
            )
            if error_bar_range[2] <= 0 or error_bar_range[1] < error_bar_range[0]:
                QMessageBox.warning(
                    self,
                    "Invalid CSM Error-Bar Range",
                    "Set Error-bar placement (start, end, step) with end >= start and step > 0."
                )
                return
            offsets = None
            if self.csm_apply_offsets_cb.isChecked():
                offsets = self._curve_viewer_offsets_for_tests(test_numbers)
                if len(offsets) != len(test_numbers):
                    missing = sorted(set(test_numbers) - set(offsets.keys()))
                    missing_text = self._format_test_range(missing)
                    QMessageBox.warning(
                        self,
                        "Missing h0 Offsets",
                        "Some selected tests do not have current h0 offsets.\n"
                        f"Missing tests: {missing_text}\n"
                        "Keep tests that have Loading Offset h0 values, edit them in Expert Mode, "
                        "or disable offset application."
                    )
                    return
                self.csm_offsets = offsets

            self.current_analysis_file_path = str(Path(file_path).resolve())
            # Keep existing Curve Viewer plots and include/exclude selections intact.
            # CSM analysis should augment results with CSM tabs, not reset Step 4 state.
            self.analyze_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            self.step4_next_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(10)
            run_stamp = self._log_timestamp()
            self.log_widget.append(f"\n=== [{run_stamp}] CSM Run ===")
            self.append_research_log(
                "Starting continuous stiffness measurement analysis for the currently included tests.",
                "CSM"
            )
            self.append_research_log(f"Experiment file: {file_path}", "CSM")
            self.append_research_log(f"Tip area calibration source: {self.calibration_source}", "CSM")
            self.append_research_log(
                "CSM profile and publication averaging window: "
                f"{depth_range[0]:g} to {depth_range[1]:g} nm. "
                "Discrete error bars are placed independently at "
                f"{error_bar_range[0]:g} to {error_bar_range[1]:g} nm "
                f"every {error_bar_range[2]:g} nm.",
                "CSM"
            )
            self.append_research_log(
                f"Selected tests for this CSM run: {self._format_test_range(test_numbers)} "
                f"({len(test_numbers)} tests).",
                "CSM"
            )
            recalculate = self.csm_source_combo.currentIndex() == 1
            if recalculate and self.calibration_source == "Default Berkovich":
                reply = QMessageBox.question(
                    self,
                    "Use Default Calibration?",
                    "CSM recalculation needs a tip area calibration. Continue with default Berkovich coefficients?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
                    return
            analyzer = self._make_csm_analyzer()
            results = analyzer.analyze_file(
                file_path,
                test_numbers,
                depth_range=depth_range,
                target_x_range=None,
                offsets_nm=offsets,
                recalculate=recalculate,
            )
            results["error_bar_range"] = error_bar_range
            results["depth_range"] = depth_range
            self.progress_bar.setValue(80)
            averaged = results["averaged"]
            if averaged.empty:
                QMessageBox.warning(self, "No CSM Results", "No valid CSM profile rows were produced.")
                return
            publication_summary = self._summarize_csm_publication_values(
                results["raw"],
                results["test_numbers"],
                depth_range,
            )
            results["publication_summary"] = publication_summary
            self.csm_results = results
            self._load_csm_table(averaged)
            self._reset_csm_plot_settings()
            self._plot_csm_depth_profiles(averaged, results["source"])
            self.export_csv_button.setEnabled(True)
            self.export_excel_button.setEnabled(True)
            self.step4_next_button.setEnabled(True)
            if self.step2_next_button:
                self.step2_next_button.setEnabled(True)
            self.unlock_workflow_step(3)
            self.unlock_workflow_step(4)
            self.unlock_workflow_tab("Expert Mode")
            self.unlock_workflow_tab("Log")
            self.append_csm_status_log(
                f"CSM analysis complete: {len(averaged)} shared-depth profile points generated "
                f"from {len(results['test_numbers'])} selected tests using {results['source']} data.",
                "CSM"
            )
            self._log_csm_publication_summary(publication_summary)
            self._show_workflow_results("CSM Depth Profiles")
            self._configure_results_panel_visibility()
            self.update_results_summary_strip()
            self.progress_bar.setValue(100)
            self.status_bar.showMessage("CSM analysis completed.")
        except Exception as e:
            QMessageBox.critical(self, "CSM Analysis Error", f"Failed to run CSM analysis:\n{str(e)}")
        finally:
            self.analyze_button.setEnabled(bool(self.file_path_edit.text()))
            self.progress_bar.setVisible(False)

    def _reset_csm_plot_settings(self):
        for widget in (
            getattr(self, "csm_depth_plot_widget", None),
            getattr(self, "csm_offset_plot_widget", None),
        ):
            if widget is not None and hasattr(widget, "reset_plot_settings"):
                widget.reset_plot_settings()

    def reset_csm_plot_settings_and_redraw(self):
        self._reset_csm_plot_settings()
        if self.csm_results:
            averaged = self.csm_results.get("averaged")
            source = self.csm_results.get("source", "instrument_exported")
            if isinstance(averaged, pd.DataFrame) and not averaged.empty:
                self._plot_csm_depth_profiles(averaged, str(source))
                self._show_workflow_results("CSM Depth Profiles")
                self.status_bar.showMessage("CSM plot settings reset and plot redrawn.")
                self.append_csm_status_log("Reset CSM plot settings and redrew fresh CSM plots.", "CSM")
                return
        if self.csm_depth_plot_widget:
            self.csm_depth_plot_widget.canvas.draw()
        self.status_bar.showMessage("CSM plot settings reset.")

    def _load_csm_table(self, df: pd.DataFrame):
        if not self.csm_table:
            return
        self.csm_table.clear()
        self.csm_table.setRowCount(len(df))
        self.csm_table.setColumnCount(len(df.columns))
        self.csm_table.setHorizontalHeaderLabels([str(c) for c in df.columns])
        for row_idx, (_, row) in enumerate(df.iterrows()):
            for col_idx, value in enumerate(row):
                if isinstance(value, (float, np.floating)):
                    text = "" if not np.isfinite(value) else f"{value:.6g}"
                else:
                    text = str(value)
                self.csm_table.setItem(row_idx, col_idx, QTableWidgetItem(text))
        self.csm_table.resizeColumnsToContents()

    def _refresh_csm_plot_mode(self, *_args):
        self.update_readiness_summary()
        if not self.csm_results:
            return
        averaged = self.csm_results.get("averaged")
        source = self.csm_results.get("source", "instrument_exported")
        if isinstance(averaged, pd.DataFrame) and not averaged.empty:
            self._plot_csm_depth_profiles(averaged, str(source))

    def _selected_csm_plot_mode(self) -> str:
        if getattr(self, "csm_plot_mode_combo", None) is None:
            return "average"
        return "separate" if self.csm_plot_mode_combo.currentIndex() == 1 else "average"

    def _sync_csm_settings_visibility(self, *_args):
        plot_average = self._selected_csm_plot_mode() == "average"
        discrete_error_bars = (
            getattr(self, "csm_sd_display_combo", None) is not None
            and self.csm_sd_display_combo.currentText() == "SD error bars"
        )
        show_error_bar_depths = plot_average and discrete_error_bars

        for widget in (
            getattr(self, "csm_sd_display_label", None),
            getattr(self, "csm_sd_display_combo", None),
        ):
            if widget is not None:
                widget.setVisible(plot_average)

        for widget in (
            getattr(self, "csm_target_x_label", None),
            getattr(self, "csm_target_x_container", None),
        ):
            if widget is not None:
                widget.setVisible(show_error_bar_depths)

        if getattr(self, "csm_plot_mode_help_label", None) is not None:
            if plot_average:
                self.csm_plot_mode_help_label.setText(
                    "Average profile summarizes selected tests; choose SD band or SD error bars for spread."
                )
            else:
                self.csm_plot_mode_help_label.setText(
                    "Individual profiles overlays each selected test; spread controls are hidden."
                )

        self._refresh_csm_plot_mode()

    def _plot_csm_depth_profiles(self, averaged: pd.DataFrame, source: str):
        if not self.csm_depth_plot_widget:
            return
        fig = self.csm_depth_plot_widget.figure
        fig.clear()
        if self._selected_csm_plot_mode() == "separate":
            self._plot_csm_individual_depth_profiles(fig, source)
            self.csm_depth_plot_widget.canvas.draw()
            return

        ax_h = fig.add_subplot(2, 1, 1)
        ax_m = fig.add_subplot(2, 1, 2, sharex=ax_h)
        x = averaged["Depth (nm)"]
        use_error_bars = (
            getattr(self, "csm_sd_display_combo", None) is not None
            and self.csm_sd_display_combo.currentText() == "SD error bars"
        )
        err_start = float(self.csm_target_x_start_spin.value()) if self.csm_target_x_start_spin else float(np.nanmin(x))
        err_end = float(self.csm_target_x_end_spin.value()) if self.csm_target_x_end_spin else float(np.nanmax(x))
        err_step = float(self.csm_target_x_step_spin.value()) if self.csm_target_x_step_spin else 1.0

        def _plot_discrete_error_bars(ax, x_series, y_series, e_series, color: str):
            if err_step <= 0 or err_end < err_start:
                return
            x_vals = pd.to_numeric(x_series, errors="coerce").to_numpy(dtype=float)
            y_vals = pd.to_numeric(y_series, errors="coerce").to_numpy(dtype=float)
            e_vals = pd.to_numeric(e_series, errors="coerce").to_numpy(dtype=float)
            valid = np.isfinite(x_vals) & np.isfinite(y_vals) & np.isfinite(e_vals)
            if np.count_nonzero(valid) < 2:
                return
            xv = x_vals[valid]
            yv = y_vals[valid]
            ev = e_vals[valid]
            order = np.argsort(xv)
            xv = xv[order]
            yv = yv[order]
            ev = ev[order]
            unique_x, unique_idx = np.unique(xv, return_index=True)
            if unique_x.size < 2:
                return
            y_unique = yv[unique_idx]
            e_unique = ev[unique_idx]
            anchors = np.arange(err_start, err_end + 0.5 * err_step, err_step, dtype=float)
            anchors = anchors[(anchors >= unique_x.min()) & (anchors <= unique_x.max())]
            if anchors.size == 0:
                return
            y_anchor = np.interp(anchors, unique_x, y_unique)
            e_anchor = np.interp(anchors, unique_x, e_unique)
            ax.errorbar(
                anchors, y_anchor, yerr=e_anchor,
                fmt="none", ecolor=color,
                elinewidth=1.0, alpha=0.65, capsize=2,
                label=f"SD (error bars every {err_step:g} nm)",
            )
        if "Hardness Mean (GPa)" in averaged:
            ax_h.plot(x, averaged["Hardness Mean (GPa)"], color="#00d9ff", label="Hardness mean")
            if "Hardness SD (GPa)" in averaged:
                y = averaged["Hardness Mean (GPa)"]
                e = averaged["Hardness SD (GPa)"].fillna(0)
                if use_error_bars:
                    _plot_discrete_error_bars(ax_h, x, y, e, "#00d9ff")
                else:
                    ax_h.fill_between(x, y - e, y + e, color="#00d9ff", alpha=0.18, label="SD (band)")
        if "Modulus Mean (GPa)" in averaged:
            ax_m.plot(x, averaged["Modulus Mean (GPa)"], color="#ffbe0b", label="Modulus mean")
            if "Modulus SD (GPa)" in averaged:
                y = averaged["Modulus Mean (GPa)"]
                e = averaged["Modulus SD (GPa)"].fillna(0)
                if use_error_bars:
                    _plot_discrete_error_bars(ax_m, x, y, e, "#ffbe0b")
                else:
                    ax_m.fill_between(x, y - e, y + e, color="#ffbe0b", alpha=0.18, label="SD (band)")
        ax_h.set_ylabel("Hardness (GPa)")
        ax_m.set_ylabel("Modulus (GPa)")
        ax_m.set_xlabel("Corrected depth (nm)")
        ax_h.set_title(f"CSM Depth Profiles ({source.replace('_', ' ')})")
        for ax in (ax_h, ax_m):
            ax.grid(True, alpha=0.2)
            ax.legend(loc="best")
        fig.tight_layout()
        self.csm_depth_plot_widget.canvas.draw()

    def _plot_csm_individual_depth_profiles(self, fig: Figure, source: str):
        results = self.csm_results or {}
        raw = results.get("raw")
        if not isinstance(raw, pd.DataFrame) or raw.empty:
            ax = fig.add_subplot(111)
            ax.axis("off")
            ax.text(
                0.5, 0.5,
                "No per-test CSM data available.",
                ha="center", va="center", transform=ax.transAxes,
                color="#24313a", fontsize=12,
            )
            return

        required = {"Test", "Depth (nm)"}
        if not required.issubset(raw.columns):
            ax = fig.add_subplot(111)
            ax.axis("off")
            ax.text(
                0.5, 0.5,
                "Per-test CSM plot needs Test and Depth columns.",
                ha="center", va="center", transform=ax.transAxes,
                color="#24313a", fontsize=12,
            )
            return

        depth_range = results.get("depth_range")
        depth_min = depth_max = None
        if isinstance(depth_range, (tuple, list)) and len(depth_range) == 2:
            depth_min, depth_max = float(depth_range[0]), float(depth_range[1])

        working = raw.copy()
        working["Test"] = pd.to_numeric(working["Test"], errors="coerce")
        working["Depth (nm)"] = pd.to_numeric(working["Depth (nm)"], errors="coerce")
        if depth_min is not None and depth_max is not None:
            working = working[working["Depth (nm)"].between(depth_min, depth_max, inclusive="both")]
        working = working.replace([np.inf, -np.inf], np.nan)

        requested_tests = results.get("test_numbers") or []
        if requested_tests:
            test_numbers = [int(test) for test in requested_tests if pd.notna(test)]
        else:
            test_numbers = sorted(
                int(test) for test in working["Test"].dropna().unique()
            )
        test_numbers = [
            test for test in test_numbers
            if not working[working["Test"] == test].dropna(how="all").empty
        ]
        if not test_numbers:
            ax = fig.add_subplot(111)
            ax.axis("off")
            ax.text(
                0.5, 0.5,
                "No CSM rows remain in the selected depth window.",
                ha="center", va="center", transform=ax.transAxes,
                color="#24313a", fontsize=12,
            )
            return

        ax_h = fig.add_subplot(2, 1, 1)
        ax_m = fig.add_subplot(2, 1, 2, sharex=ax_h)
        fig.suptitle(
            f"CSM Individual Test Profiles ({source.replace('_', ' ')})",
            fontsize=12, fontweight="bold", color="#24313a",
        )

        colors = plt.rcParams["axes.prop_cycle"].by_key().get("color", [])
        if not colors:
            colors = ["#00a8cc", "#ffbe0b", "#2ecc71", "#e74c3c", "#9b59b6"]

        for ax in (ax_h, ax_m):
            ax.set_facecolor("#ffffff")
            for spine in ax.spines.values():
                spine.set_edgecolor("#d6dbe0")
            ax.tick_params(colors="#5e6a72", labelsize=8)
            ax.grid(True, alpha=0.25, linestyle=":", color="#d6dbe0")

        hardness_means = []
        modulus_means = []

        for plot_idx, test_number in enumerate(test_numbers):
            test_df = working[working["Test"] == test_number].sort_values("Depth (nm)")
            x = pd.to_numeric(test_df["Depth (nm)"], errors="coerce")
            color = colors[plot_idx % len(colors)]

            if "Hardness (GPa)" in test_df:
                hardness = pd.to_numeric(test_df["Hardness (GPa)"], errors="coerce")
                valid = x.notna() & hardness.notna()
                if valid.any():
                    ax_h.plot(
                        x[valid], hardness[valid],
                        linewidth=1.0, alpha=0.82, color=color,
                        label=f"Test {test_number:03d}",
                    )
                    hardness_means.append(float(hardness[valid].mean()))

            if "Modulus (GPa)" in test_df:
                modulus = pd.to_numeric(test_df["Modulus (GPa)"], errors="coerce")
                valid = x.notna() & modulus.notna()
                if valid.any():
                    ax_m.plot(
                        x[valid], modulus[valid],
                        linewidth=1.0, alpha=0.82, color=color,
                        label=f"Test {test_number:03d}",
                    )
                    modulus_means.append(float(modulus[valid].mean()))

        def _stats_text(label: str, values: List[float], unit: str) -> str:
            finite = np.asarray(values, dtype=float)
            finite = finite[np.isfinite(finite)]
            if finite.size == 0:
                return f"Mean {label} = n/a\nStd. Dev. = n/a"
            mean_value = float(np.mean(finite))
            sd_value = float(np.std(finite, ddof=1)) if finite.size > 1 else 0.0
            return f"Mean {label} = {mean_value:.3g} {unit}\nStd. Dev. = {sd_value:.3g} {unit}"

        ax_h.text(
            0.02, 0.95,
            _stats_text("Hardness", hardness_means, "GPa"),
            transform=ax_h.transAxes, ha="left", va="top",
            fontsize=9, color="#24313a",
            bbox=dict(facecolor="#ffffff", edgecolor="none", alpha=0.72, pad=3),
        )
        ax_m.text(
            0.02, 0.95,
            _stats_text("Modulus", modulus_means, "GPa"),
            transform=ax_m.transAxes, ha="left", va="top",
            fontsize=9, color="#24313a",
            bbox=dict(facecolor="#ffffff", edgecolor="none", alpha=0.72, pad=3),
        )

        ax_h.set_ylabel("Hardness (GPa)")
        ax_m.set_ylabel("Modulus (GPa)")
        ax_m.set_xlabel("Displacement into Surface (nm)")
        ax_h.set_title("Hardness profiles", fontsize=10, fontweight="bold", color="#24313a")
        ax_m.set_title("Modulus profiles", fontsize=10, fontweight="bold", color="#24313a")

        if len(test_numbers) <= 12:
            ax_h.legend(loc="best", fontsize=7, framealpha=0.85)
        fig.tight_layout(rect=[0, 0, 1, 0.94])

    def export_csm_csv(self):
        if not self.csm_results or self.csm_results["averaged"].empty:
            QMessageBox.warning(self, "No Data", "No CSM results to export.")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSM Averaged Data to CSV",
            "csm_averaged_results.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        if not file_path:
            return
        self.csm_results["averaged"].to_csv(file_path, index=False)
        self.append_csm_status_log(f"Exported CSM averaged profile CSV: {file_path}", "Export")

    def export_csm_excel(self):
        if not self.csm_results or self.csm_results["averaged"].empty:
            QMessageBox.warning(self, "No Data", "No CSM results to export.")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSM Results to Excel",
            "csm_results.xlsx",
            "Excel Files (*.xlsx);;All Files (*)"
        )
        if not file_path:
            return
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            self.csm_results["averaged"].to_excel(writer, sheet_name="Averaged", index=False)
            self.csm_results["raw"].to_excel(writer, sheet_name="Per Test", index=False)
            publication_summary = self.csm_results.get("publication_summary")
            if publication_summary:
                publication_table = self._csm_publication_summary_table(publication_summary)
                if not publication_table.empty:
                    publication_table.to_excel(writer, sheet_name="Publication Summary", index=False)
        self.append_csm_status_log(
            f"Exported CSM Excel workbook with averaged profiles, per-test data, and publication summary: {file_path}",
            "Export"
        )
    
    def get_stylesheet(self):
        """Return the application stylesheet - Modern Light Theme"""
        base_stylesheet = """
            /* ===== MODERN LIGHT THEME (2024) ===== */
            
            /* Main Window */
            QMainWindow {
                background-color: #ffffff;
                color: #24313a;
            }
            
            /* Central Widget */
            QWidget {
                background-color: #ffffff;
                color: #24313a;
            }
            
            /* Group Boxes - Modern flat design */
            QGroupBox {
                font-weight: 600;
                border: 1px solid #d6dbe0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: #ffffff;
                color: #24313a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #006f86;
                font-weight: 700;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #f7fafc;
                color: #24313a;
                border: 1px solid #cfd8df;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #eef6f8;
                border-color: #9ec9d4;
                color: #1f343d;
            }
            QPushButton:pressed {
                background-color: #dcecf1;
            }
            QPushButton:disabled {
                background-color: #e1e5e8;
                color: #8a949b;
                border-color: #d6dbe0;
            }
            QPushButton[primary="true"] {
                background-color: #00a8cc;
                color: #ffffff;
                border: 1px solid #00a8cc;
            }
            QPushButton[primary="true"]:hover {
                background-color: #0097b8;
                color: #ffffff;
                border-color: #0097b8;
            }
            QPushButton[primary="true"]:pressed {
                background-color: #007f9c;
            }
            QPushButton[secondary="true"] {
                background-color: #ffffff;
                color: #24313a;
                border: 1px solid #cfd8df;
            }
            QPushButton[viewSwitch="true"] {
                background-color: #ffffff;
                color: #4b5b65;
                border: 1px solid #cfd8df;
                padding: 7px 12px;
                border-radius: 5px;
            }
            QPushButton[viewSwitch="true"]:checked {
                background-color: #e8f7fb;
                color: #006f86;
                border-color: #00a8cc;
            }
            
            /* Input Fields - Cleaner look */
            QLineEdit {
                border: 1px solid #d6dbe0;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 11px;
                background-color: #ffffff;
                color: #24313a;
                selection-background-color: #00a8cc;
            }
            QLineEdit:focus {
                border: 2px solid #00d9ff;
                background-color: #f8fbfc;
            }
            
            /* Spin Boxes */
            QSpinBox, QDoubleSpinBox {
                border: 1px solid #d6dbe0;
                border-radius: 6px;
                padding: 8px;
                background-color: #ffffff;
                color: #24313a;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #00d9ff;
                background-color: #f8fbfc;
            }
            
            /* Combo Boxes */
            QComboBox {
                border: 1px solid #d6dbe0;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #ffffff;
                color: #24313a;
            }
            QComboBox:focus {
                border: 2px solid #00d9ff;
                background-color: #f8fbfc;
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
                background-color: #ffffff;
                color: #24313a;
                selection-background-color: #00a8cc;
                border: 1px solid #d6dbe0;
                border-radius: 4px;
            }
            
            /* Tab Widget - Modern styling */
            QTabWidget::pane {
                border: 1px solid #d6dbe0;
                border-radius: 6px;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #ffffff;
                color: #5e6a72;
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border: 1px solid #d6dbe0;
                font-weight: 500;
            }
            QTabBar::tab:hover {
                background-color: #eef6f8;
                color: #3c4a53;
            }
            QTabBar::tab:selected {
                background-color: #e8f7fb;
                color: #006f86;
                border-bottom: 3px solid #00d9ff;
                font-weight: 600;
            }
            QTabBar::tab:first {
                margin-left: 4px;
            }
            
            /* Text Areas */
            QTextEdit {
                border: 1px solid #d6dbe0;
                border-radius: 6px;
                background-color: #ffffff;
                color: #24313a;
                font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
                font-size: 10px;
                padding: 8px;
            }
            QTextEdit:focus {
                border: 2px solid #00d9ff;
            }
            
            /* Tables - Modern alternating rows */
            QTableWidget {
                border: 1px solid #d6dbe0;
                background-color: #ffffff;
                alternate-background-color: #f8fafc;
                color: #24313a;
                gridline-color: #d6dbe0;
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
                background-color: #f5f7f9;
                color: #006f86;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #9ec9d4;
                font-weight: 600;
            }
            
            /* Progress Bar */
            QProgressBar {
                border: 1px solid #d6dbe0;
                border-radius: 6px;
                background-color: #ffffff;
                color: #24313a;
                text-align: center;
                height: 24px;
            }
            QProgressBar::chunk {
                background-color: #00a8cc;
                border-radius: 4px;
            }
            
            /* Check Boxes */
            QCheckBox {
                color: #24313a;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #d6dbe0;
                border-radius: 4px;
                background-color: #ffffff;
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
                color: #24313a;
            }
            
            /* Scrollbars - Sleek design */
            QScrollBar:vertical {
                background-color: #ffffff;
                width: 14px;
                border-radius: 7px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #c7d0d8;
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
                background-color: #ffffff;
                height: 14px;
                border-radius: 7px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background-color: #c7d0d8;
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
                background-color: #f5f7f9;
                color: #5e6a72;
                border-top: 1px solid #d6dbe0;
            }
            
            /* Splitter - Thin dividers */
            QSplitter::handle {
                background-color: #d6dbe0;
            }
            QSplitter::handle:horizontal {
                width: 1px;
            }
            QSplitter::handle:vertical {
                height: 1px;
            }
            QSplitter::handle:hover {
                background-color: #9ec9d4;
            }
            
            /* Matplotlib Canvas */
            QWidget[objectName="qt_scrollarea_viewport"] {
                background-color: #ffffff;
            }
            
            /* Toolbar */
            QToolBar {
                background-color: #ffffff;
                border: 1px solid #d6dbe0;
                color: #24313a;
                spacing: 2px;
                padding: 2px;
            }
            QToolBar QToolButton {
                background-color: transparent;
                color: #24313a;
                border: none;
                padding: 3px 5px;
                border-radius: 4px;
            }
            QToolBar QToolButton:hover {
                background-color: #eef6f8;
                color: #006f86;
            }
            QToolBar QToolButton:pressed {
                background-color: #dcecf1;
                color: #24313a;
            }
            
            /* Dialogs */
            QDialog {
                background-color: #ffffff;
                color: #24313a;
            }
            
            /* Frame */
            QFrame {
                background-color: #ffffff;
                color: #24313a;
            }
        """
        responsive_stylesheet = f"""
            QPushButton {{
                padding: {self.sp(8)}px {self.sp(14)}px;
                border-radius: {self.sp(6)}px;
                font-size: {self.fp(11)}px;
                min-height: {self.sp(18)}px;
            }}
            QLineEdit {{
                padding: {self.sp(8)}px {self.sp(10)}px;
                border-radius: {self.sp(6)}px;
                font-size: {self.fp(11)}px;
                min-height: {self.sp(18)}px;
            }}
            QSpinBox, QDoubleSpinBox {{
                padding: {self.sp(6)}px;
                border-radius: {self.sp(6)}px;
                font-size: {self.fp(10)}px;
                min-height: {self.sp(18)}px;
            }}
            QComboBox {{
                padding: {self.sp(7)}px {self.sp(10)}px;
                border-radius: {self.sp(6)}px;
                font-size: {self.fp(11)}px;
                min-height: {self.sp(18)}px;
            }}
            QComboBox::drop-down {{
                width: {self.sp(24)}px;
            }}
            QGroupBox {{
                border-radius: {self.sp(8)}px;
                margin-top: {self.sp(11)}px;
                padding-top: {self.sp(11)}px;
                font-size: {self.fp(11)}px;
            }}
            QGroupBox::title {{
                left: {self.sp(12)}px;
                padding: 0 {self.sp(7)}px;
            }}
            QTabBar::tab {{
                padding: {self.sp(9)}px {self.sp(14)}px;
                margin-right: {self.sp(3)}px;
                border-top-left-radius: {self.sp(6)}px;
                border-top-right-radius: {self.sp(6)}px;
                font-size: {self.fp(11)}px;
                min-width: {self.sp(64)}px;
            }}
            QTextEdit {{
                font-size: {self.fp(10)}px;
                padding: {self.sp(7)}px;
                border-radius: {self.sp(6)}px;
            }}
            QTableWidget::item {{
                padding: {self.sp(5)}px;
            }}
            QHeaderView::section {{
                padding: {self.sp(7)}px;
                font-size: {self.fp(10)}px;
            }}
            QCheckBox {{
                spacing: {self.sp(7)}px;
                font-size: {self.fp(11)}px;
            }}
            QCheckBox::indicator {{
                width: {self.sp(17)}px;
                height: {self.sp(17)}px;
                border-radius: {self.sp(4)}px;
            }}
            QLabel {{
                font-size: {self.fp(11)}px;
            }}
            QScrollBar:vertical {{
                width: {self.sp(12)}px;
                border-radius: {self.sp(6)}px;
            }}
            QScrollBar:horizontal {{
                height: {self.sp(12)}px;
                border-radius: {self.sp(6)}px;
            }}
            QToolBar {{
                spacing: {self.sp(2)}px;
                padding: {self.sp(2)}px;
            }}
            QToolBar QToolButton {{
                padding: {self.sp(3)}px {self.sp(5)}px;
                border-radius: {self.sp(4)}px;
            }}
        """
        return base_stylesheet + responsive_stylesheet
    
    def setup_matplotlib_style(self):
        """Configure matplotlib for modern light mode theme"""
        import matplotlib.pyplot as plt
        
        # Set matplotlib style parameters
        plt.rcParams.update({
            # Figure
            'figure.facecolor': '#ffffff',
            'figure.edgecolor': '#d6dbe0',
            'figure.figsize': (12, 8),
            'figure.dpi': 100,
            'savefig.facecolor': '#ffffff',
            
            # Axes
            'axes.facecolor': '#ffffff',
            'axes.edgecolor': '#d6dbe0',
            'axes.labelcolor': '#24313a',
            'axes.prop_cycle': plt.cycler('color', [
                '#00d9ff', '#ff006e', '#ffbe0b', '#8338ec',
                '#3a86ff', '#fb5607', '#06ffa5', '#ff006e'
            ]),
            
            # Grid
            'grid.color': '#d6dbe0',
            'grid.alpha': 0.2,
            'grid.linestyle': ':',
            'grid.linewidth': 0.8,
            
            # Lines
            'lines.linewidth': 2.0,
            'lines.markersize': 6,
            'lines.color': '#24313a',
            
            # Ticks
            'xtick.color': '#24313a',
            'ytick.color': '#24313a',
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            
            # Legend
            'legend.facecolor': '#ffffff',
            'legend.edgecolor': '#d6dbe0',
            'legend.labelcolor': '#24313a',
            'legend.framealpha': 0.95,
            
            # Text
            'text.color': '#24313a',
            'font.size': 10,
            'font.family': 'sans-serif',
            'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
            
            # Axes titles
            'axes.titlesize': 12,
            'axes.labelsize': 11,
        })
    
    def center_window(self):
        """Center the window on the screen"""
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry() if screen else QApplication.desktop().screenGeometry()
        size = self.frameGeometry()
        self.move(
            available.x() + (available.width() - size.width()) // 2,
            available.y() + (available.height() - size.height()) // 2
        )
    
    def clear_plot_tabs(self, clear_exclusions: bool = True):
        """Clear the reliability summary and test plot widgets."""
        if self.reliability_widget:
            self.reliability_widget.figure.clear()
            self.reliability_widget.canvas.draw()
        if self.summary_statistics_text:
            self.summary_statistics_text.setPlainText("Summary statistics will appear after analysis.")
        if self.single_test_plot:
            self.single_test_plot.figure.clear()
            self.single_test_plot.canvas.draw()
        self.current_test_index = 0
        if clear_exclusions:
            self.excluded_test_indices.clear()
            self.excluded_test_numbers.clear()
        self._update_test_nav_label()

    def get_included_results(self) -> List[Dict[str, Any]]:
        """Return test results currently included in final calculations."""
        return [
            result
            for idx, result in enumerate(self.current_results)
            if self._is_result_included(idx, result)
        ]

    def _test_log_label(self, result: Dict[str, Any], fallback_index: int) -> str:
        """Return a readable test label without duplicating the word Test."""
        test_name = str(result.get('Test', fallback_index + 1)).strip()
        if test_name.lower().startswith('test '):
            return test_name
        return f"Test {test_name}"

    @staticmethod
    def _test_number_from_sheet_name(sheet_name: str) -> Optional[int]:
        match = re.search(r"\btest\s*0*(\d+)\b", str(sheet_name), flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def _test_number_from_result(self, result: Dict[str, Any], fallback_index: int) -> Optional[int]:
        raw_test = result.get("Test")
        try:
            return int(raw_test)
        except (TypeError, ValueError):
            pass
        match = re.search(r"\d+", str(raw_test))
        if match:
            try:
                return int(match.group(0))
            except ValueError:
                pass
        return fallback_index + 1

    def _is_result_included(self, result_index: int, result: Dict[str, Any]) -> bool:
        test_number = self._test_number_from_result(result, result_index)
        return (
            result_index not in self.excluded_test_indices
            and (test_number is None or test_number not in self.excluded_test_numbers)
        )

    @staticmethod
    def _finite_result_values(results: List[Dict[str, Any]], key: str) -> np.ndarray:
        values = []
        for result in results:
            try:
                value = float(result.get(key, np.nan))
            except (TypeError, ValueError):
                continue
            if np.isfinite(value):
                values.append(value)
        return np.asarray(values, dtype=float)

    def _log_op_publication_uncertainty(self, label: str, values: np.ndarray, unit: str):
        n = int(values.size)
        if n == 0:
            self.append_research_log(f"{label}: no finite values available for uncertainty calculation.", "Summary")
            return
        mean_value = float(np.mean(values))
        sd_value = float(np.std(values, ddof=1)) if n > 1 else 0.0
        uncertainty = float(sd_value / np.sqrt(n)) if n > 1 else 0.0
        cv_percent = float((sd_value / abs(mean_value)) * 100.0) if mean_value else np.nan
        self.append_research_log(
            f"{label}: mean={mean_value:.4g} {unit}, SD={sd_value:.4g} {unit}, "
            f"n={n}, propagated standard uncertainty u=SD/sqrt(n)={uncertainty:.4g} {unit}.",
            "Summary"
        )
        cv_text = f", CV={cv_percent:.2f}%" if np.isfinite(cv_percent) else ""
        self.append_research_log(
            f"Publication value: {label} = {mean_value:.4g} +/- {uncertainty:.3g} {unit} "
            f"(k=1 standard uncertainty{cv_text}).",
            "Summary"
        )

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
            self.append_research_log(f"Final calculation summary recalculated because: {reason}", "Summary")
        else:
            self.append_research_log(
                "Final calculation summary for the currently included tests.",
                "Summary"
            )
        self.append_research_log(
            f"Included tests: {included_count}/{total_count}. Excluded tests are not used in averages.",
            "Summary"
        )
        if excluded_labels:
            self.append_research_log(f"Excluded tests: {', '.join(excluded_labels)}", "Summary")

        if not included_results:
            self.append_research_log("No tests selected for final calculations.", "Summary")
            return

        self.append_research_log(
            "Oliver-Pharr uncertainty method: each accepted test contributes one value; "
            "the quoted uncertainty is the propagated standard uncertainty of the mean, u = SD/sqrt(n).",
            "Summary"
        )
        hardness_values = self._finite_result_values(included_results, 'Hardness (GPa)')
        self._log_op_publication_uncertainty("Hardness", hardness_values, "GPa")

        modulus_values = self._finite_result_values(included_results, 'Oliver-Pharr Modulus (GPa)')
        self._log_op_publication_uncertainty("Oliver-Pharr modulus", modulus_values, "GPa")

    def update_results_summary_strip(self):
        """Update the compact right-panel summary."""
        if not self.results_summary_label:
            return

        if self.get_selected_analysis_type() == "CSM" and self.csm_results:
            averaged = self.csm_results.get("averaged")
            rows = len(averaged) if isinstance(averaged, pd.DataFrame) else 0
            tests = self.csm_results.get("test_numbers", [])
            self.results_summary_label.setText(
                f"CSM results: {len(tests)} tests selected | {rows} averaged depth rows | "
                f"File: {Path(self.current_analysis_file_path or '').name}"
            )
            return

        if not self.current_results:
            file_name = Path(self.file_path_edit.text()).name if getattr(self, "file_path_edit", None) and self.file_path_edit.text() else "no file selected"
            self.results_summary_label.setText(
                f"Workflow state: {file_name} | Generate test curves, select tests, then run analysis."
            )
            return

        included_results = self.get_included_results()
        total_count = len(self.current_results)
        included_count = len(included_results)
        file_name = Path(self.current_analysis_file_path).name if self.current_analysis_file_path else "selected file"

        hardness_values = [
            float(r.get('Hardness (GPa)', 0))
            for r in included_results
            if r.get('Hardness (GPa)')
        ]
        modulus_values = [
            float(r.get('Oliver-Pharr Modulus (GPa)', 0))
            for r in included_results
            if r.get('Oliver-Pharr Modulus (GPa)')
        ]
        hardness_text = f"H {np.mean(hardness_values):.2f} GPa" if hardness_values else "H n/a"
        modulus_text = f"E {np.mean(modulus_values):.2f} GPa" if modulus_values else "E n/a"
        self.results_summary_label.setText(
            f"{file_name} | Included {included_count}/{total_count} tests | {hardness_text} | {modulus_text}"
        )

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
            current_included = (
                n > 0
                and self._is_result_included(
                    self.current_test_index,
                    self.current_results[self.current_test_index]
                )
            )
            self.test_include_checkbox.blockSignals(True)
            self.test_include_checkbox.setEnabled(n > 0)
            self.test_include_checkbox.setChecked(current_included)
            self.test_include_checkbox.blockSignals(False)

    def _current_test_inclusion_changed(self, checked: bool):
        """Include/exclude the current test from final table, summary, and exports."""
        if not self.current_results:
            return

        test_label = self._test_log_label(
            self.current_results[self.current_test_index],
            self.current_test_index
        )
        parsed_test_number = self._test_number_from_result(
            self.current_results[self.current_test_index],
            self.current_test_index
        )
        if checked:
            self.excluded_test_indices.discard(self.current_test_index)
            if parsed_test_number is not None:
                self.excluded_test_numbers.discard(parsed_test_number)
            action = "included"
        else:
            self.excluded_test_indices.add(self.current_test_index)
            if parsed_test_number is not None:
                self.excluded_test_numbers.add(parsed_test_number)
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
            self.create_load_overlay_plot_tab(included_results)
        elif self.reliability_widget:
            self.reliability_widget.figure.clear()
            ax = self.reliability_widget.figure.add_subplot(111)
            ax.axis('off')
            ax.text(
                0.5, 0.5,
                "No tests selected for final calculations.",
                ha='center', va='center', fontsize=12, color='#24313a',
                transform=ax.transAxes
            )
            self.reliability_widget.canvas.draw()
            if self.op_overlay_widget:
                self.op_overlay_widget.figure.clear()
                ax_overlay = self.op_overlay_widget.figure.add_subplot(111)
                ax_overlay.axis('off')
                ax_overlay.text(
                    0.5, 0.5,
                    "No tests selected for final calculations.",
                    ha='center', va='center', fontsize=12, color='#24313a',
                    transform=ax_overlay.transAxes
                )
                self.op_overlay_widget.canvas.draw()
            if self.summary_statistics_text:
                self.summary_statistics_text.setPlainText("No tests selected for final calculations.")

        if self.step4_plot_buttons_note:
            self.step4_plot_buttons_note.setText(
                f"Select a test below to open it in Curve Viewer. Use Reliability for the batch overview, "
                f"then inspect questionable tests here. {included_count}/{total_count} tests included."
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
        self._sync_csm_test_range_from_selection()
        self._sync_expert_offsets_table()
        self.update_results_summary_strip()
        self.update_readiness_summary()

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
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: #e8f7fb;
                    color: #006f86;
                    border: 1px solid #00a8cc;
                    padding: {self.sp(6)}px {self.sp(8)}px;
                    border-radius: {self.sp(5)}px;
                    font-weight: 600;
                    font-size: {self.fp(10)}px;
                }}
                QPushButton:hover {{
                    background-color: #d5f1f8;
                    color: #004c5d;
                }}
                QPushButton:pressed {{
                    background-color: #bfe8f2;
                }}
            """)
        else:
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: #eef3f5;
                    color: #5e6a72;
                    border: 1px solid #c7d0d8;
                    padding: {self.sp(6)}px {self.sp(8)}px;
                    border-radius: {self.sp(5)}px;
                    font-weight: 600;
                    font-size: {self.fp(10)}px;
                }}
                QPushButton:hover {{
                    background-color: #e7f7fb;
                    color: #24313a;
                }}
                QPushButton:pressed {{
                    background-color: #d7edf4;
                }}
            """)

    def update_step4_plot_button_styles(self):
        """Refresh Step 4 plot button colors for included/excluded tests."""
        for idx, button in self.step4_plot_buttons.items():
            included = True
            if 0 <= idx < len(self.current_results):
                included = self._is_result_included(idx, self.current_results[idx])
            else:
                included = idx not in self.excluded_test_indices
            self.set_step4_plot_button_style(button, included)

    def populate_step4_plot_buttons(self, results: List[Dict[str, Any]]):
        """Populate Step 4 with one button per test result."""
        self.clear_step4_plot_buttons()
        if self.step4_plot_buttons_layout is None:
            return

        if self.step4_plot_buttons_note:
            self.step4_plot_buttons_note.setText(
                f"Select a test below to open it in Curve Viewer. Use Reliability for the batch overview, "
                f"then inspect questionable tests here. {len(results)}/{len(results)} tests included."
            )

        available_width = self.step4_plot_buttons_group.width() if self.step4_plot_buttons_group else self.control_panel_width
        button_width = max(self.sp(138), 120)
        buttons_per_row = max(1, min(3, int(max(available_width - self.sp(48), button_width) / button_width)))
        for idx, result in enumerate(results):
            test_name = str(result.get('Test', f'Test {idx + 1}'))
            test_number = self._test_number_from_result(result, idx)
            button_label = test_name.replace("Test ", "T", 1) if test_name.startswith("Test ") else test_name
            if len(button_label) > 13:
                button_label = button_label[:10].rstrip() + "..."
            button = QPushButton(button_label)
            button.setToolTip(test_name)
            if test_number is not None:
                button.setProperty("test_number", int(test_number))
            button.setMinimumHeight(self.sp(30))
            button.setMinimumWidth(self.sp(96))
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.step4_plot_buttons[idx] = button
            self.set_step4_plot_button_style(button, self._is_result_included(idx, result))
            button.clicked.connect(lambda _checked=False, result_index=idx: self.open_test_plot_from_step4(result_index))
            row = idx // buttons_per_row
            col = idx % buttons_per_row
            self.step4_plot_buttons_layout.addWidget(button, row, col)
        # Enable the proceed button once tests are listed
        if getattr(self, 'proceed_button', None):
            self.proceed_button.setEnabled(True)

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

        # Switch to Curve Viewer tab
        if self.results_panel_tabs:
            for i in range(self.results_panel_tabs.count()):
                if self.results_panel_tabs.tabText(i) == "Curve Viewer":
                    self.results_panel_tabs.setCurrentIndex(i)
                    break

    def _proceed_with_selected_tests(self):
        """Handle the Proceed action: branch to Oliver-Pharr or CSM workflows."""
        choice = self.proceed_op_combo.currentText() if getattr(self, 'proceed_op_combo', None) else 'Oliver-Pharr'

        selected_tests = self._selected_step4_test_numbers()

        if not selected_tests:
            QMessageBox.warning(self, "No Tests Selected", "Please select at least one test to proceed.")
            return

        self._sync_csm_test_range_from_selection()
        self._sync_expert_offsets_table()

        if choice == 'Oliver-Pharr':
            # Run the existing Oliver-Pharr flow (uses start_analysis)
            self.append_research_log(
                f"Proceeding with Oliver-Pharr analysis for {len(selected_tests)} included test(s): "
                f"{self._format_test_range(selected_tests)}.",
                "Workflow"
            )
            # Ensure correct analysis type is set (UI summary)
            self.unlock_workflow_step(3, move_to_step=True)
            # Trigger analysis (this will run the existing flow)
            self.start_analysis()
            return

        # Else: CSM selected -> present CSM settings and let user configure then run CSM analysis
        if choice == 'CSM':
            signature = ("CSM", tuple(selected_tests))
            should_log_selection = signature != self._last_csm_selection_log_signature
            if should_log_selection:
                self.append_research_log(
                    "CSM workflow selected. The included tests from Open Test Plot are now linked "
                    "to the CSM Settings tab for profile averaging and publication summary calculations.",
                    "Workflow"
                )
            # Make sure CSM settings are visible and Oliver settings hidden
            if getattr(self, 'csm_settings_group', None):
                self.csm_settings_group.setVisible(True)
            if getattr(self, 'oliver_settings_group', None):
                self.oliver_settings_group.setVisible(False)
            if selected_tests and should_log_selection:
                self.append_research_log(
                    f"Selected CSM tests: {self._format_test_range(selected_tests)} "
                    f"({len(selected_tests)} tests). These are the tests used unless you change "
                    "the include/exclude selection.",
                    "Workflow"
                )
            self._last_csm_selection_log_signature = signature
            # If the user is already on CSM Settings, run the CSM calculation now.
            self.unlock_workflow_step(2, move_to_step=False)
            # Enable compute offsets button so user can run CSM-specific computations
            if getattr(self, 'csm_compute_offsets_button', None):
                self.csm_compute_offsets_button.setEnabled(True)
            if getattr(self, 'analyze_button', None):
                self.analyze_button.setEnabled(True)
            if self.workflow_tabs and self.workflow_tabs.currentIndex() >= 2:
                self.run_csm_analysis()
            else:
                self.unlock_workflow_step(2, move_to_step=True)
            return

    def _render_test_plot(self, widget: MatplotlibWidget, test_data: dict):
        """Render a researcher-quality Oliver-Pharr load-displacement plot into widget."""
        fig = widget.figure
        fig.clear()
        fig.patch.set_facecolor('#ffffff')

        ax = fig.add_subplot(111)
        ax.set_facecolor('#ffffff')

        test_id = test_data.get('Test', 'Unknown')

        fallback_index = self.current_test_index
        file_curves, raw_unloading_needs_plot_shift = self._overlay_curve_data(test_data, fallback_index)
        if file_curves is not None:
            loading_disp_raw, loading_load_raw, unloading_disp_raw, unloading_load_raw = file_curves
        else:
            loading_disp_raw = test_data.get('Full Raw Loading Displacement (nm)', [])
            loading_load_raw = test_data.get('Full Raw Loading Load (mN)', [])
            unloading_disp_raw = test_data.get('Full Raw Unloading Displacement (nm)', [])
            unloading_load_raw = test_data.get('Full Raw Unloading Load (mN)', [])
            raw_unloading_needs_plot_shift = bool(loading_disp_raw or unloading_disp_raw)
            if not loading_disp_raw or not loading_load_raw or not unloading_disp_raw or not unloading_load_raw:
                loading_disp_raw  = test_data.get('Raw Loading Displacement (nm)', [])
                loading_load_raw  = test_data.get('Raw Loading Load (mN)', [])
                unloading_disp_raw = test_data.get('Raw Unloading Displacement (nm)', [])
                unloading_load_raw = test_data.get('Raw Unloading Load (mN)', [])
                raw_unloading_needs_plot_shift = False
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
        loading_h0 = self._current_overlay_h0_offset(test_data, fallback_index)
        unloading_plot_shift = test_data.get('Unloading Plot Shift (nm)', 0.0) or 0.0

        displacement_offset = 0.0
        if loading_h0 is not None:
            try:
                candidate_offset = float(loading_h0)
                if np.isfinite(candidate_offset):
                    displacement_offset = candidate_offset
            except (TypeError, ValueError):
                displacement_offset = 0.0

        def shifted_displacement(values, x_shift: float = 0.0):
            if values is None or len(values) == 0:
                return values
            return (np.asarray(values, dtype=float) + float(x_shift) - displacement_offset).tolist()

        loading_disp_raw = shifted_displacement(loading_disp_raw)
        unloading_disp_raw = shifted_displacement(
            unloading_disp_raw,
            unloading_plot_shift if raw_unloading_needs_plot_shift else 0.0,
        )
        loading_fit_disp = shifted_displacement(loading_fit_disp)
        unloading_fit_disp = shifted_displacement(unloading_fit_disp)
        tangent_disp = shifted_displacement(tangent_disp)

        remove_hold_segment = self._op_overlay_remove_hold_segment()
        if remove_hold_segment and not self.op_overlay_cutoff_user_set:
            self._set_op_overlay_cutoff_default(self.get_included_results() if self.current_results else [test_data])
        cutoff_load = self._op_overlay_cutoff_value() if remove_hold_segment else None
        def trim_pair_to_cutoff(x_values, y_values):
            try:
                x_arr, y_arr = self._finite_xy(x_values, y_values)
            except (TypeError, ValueError):
                return [], []
            if remove_hold_segment and cutoff_load is not None:
                x_arr, y_arr = self._trim_overlay_curve_to_load_cutoff(x_arr, y_arr, cutoff_load)
            return x_arr.tolist(), y_arr.tolist()

        loading_disp_raw, loading_load_raw = trim_pair_to_cutoff(loading_disp_raw, loading_load_raw)
        unloading_disp_raw, unloading_load_raw = trim_pair_to_cutoff(unloading_disp_raw, unloading_load_raw)
        loading_fit_disp, loading_fit_load = trim_pair_to_cutoff(loading_fit_disp, loading_fit_load)
        unloading_fit_disp, unloading_fit_load = trim_pair_to_cutoff(unloading_fit_disp, unloading_fit_load)
        tangent_disp, tangent_load = trim_pair_to_cutoff(tangent_disp, tangent_load)

        unloading_alignment_shift = 0.0
        anchor_x = None
        anchor_y = None
        try:
            h_load_for_align = np.asarray(loading_disp_raw, dtype=float)
            p_load_for_align = np.asarray(loading_load_raw, dtype=float)
            h_unload_for_align = np.asarray(unloading_disp_raw, dtype=float)
            p_unload_for_align = np.asarray(unloading_load_raw, dtype=float)
            shift_info = self._unloading_overlay_alignment_shift(
                h_load_for_align, p_load_for_align, h_unload_for_align, p_unload_for_align
            )
            if shift_info is not None:
                unloading_alignment_shift, anchor_x, anchor_y, _unload_start_idx = shift_info
                aligned_unload_x = h_unload_for_align + unloading_alignment_shift
                unloading_disp_raw = np.concatenate(([anchor_x], aligned_unload_x)).tolist()
                unloading_load_raw = np.concatenate(([anchor_y], p_unload_for_align)).tolist()
        except (TypeError, ValueError):
            unloading_alignment_shift = 0.0

        def shift_unloading_display(values):
            if values is None or len(values) == 0 or not unloading_alignment_shift:
                return values
            return (np.asarray(values, dtype=float) + unloading_alignment_shift).tolist()

        unloading_fit_disp = shift_unloading_display(unloading_fit_disp)
        tangent_disp = shift_unloading_display(tangent_disp)

        def anchor_unloading_line_to_peak(x_values, y_values):
            if anchor_x is None or anchor_y is None or x_values is None or y_values is None:
                return x_values, y_values
            try:
                x_arr, y_arr = self._finite_xy(x_values, y_values)
            except (TypeError, ValueError):
                return x_values, y_values
            if x_arr.size == 0 or y_arr.size == 0:
                return x_values, y_values
            peak_idx = int(np.nanargmax(y_arr))
            x_arr = x_arr.copy()
            y_arr = y_arr.copy()
            x_arr[peak_idx] = float(anchor_x)
            y_arr[peak_idx] = float(anchor_y)
            return x_arr.tolist(), y_arr.tolist()

        unloading_fit_disp, unloading_fit_load = anchor_unloading_line_to_peak(
            unloading_fit_disp, unloading_fit_load
        )
        tangent_disp, tangent_load = anchor_unloading_line_to_peak(tangent_disp, tangent_load)
        h_max_plot = h_max - displacement_offset
        h_c_plot = h_c + unloading_plot_shift - displacement_offset + unloading_alignment_shift
        h_f_plot = (h_f + unloading_plot_shift - displacement_offset + unloading_alignment_shift) if h_f is not None else None
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

        loading_plot_x, loading_plot_y = self._thin_curve_for_plot(
            np.asarray(loading_disp_raw, dtype=float),
            np.asarray(loading_load_raw, dtype=float),
        )
        unloading_plot_x, unloading_plot_y = self._thin_curve_for_plot(
            np.asarray(unloading_disp_raw, dtype=float),
            np.asarray(unloading_load_raw, dtype=float),
        )

        # ── Raw data scatter ──────────────────────────────────────────────
        if loading_plot_x.size and loading_plot_y.size:
            ax.scatter(loading_plot_x, loading_plot_y, s=6, alpha=0.5,
                       color='#00a8cc', zorder=2, label='Loading data')
        if unloading_plot_x.size and unloading_plot_y.size:
            ax.scatter(unloading_plot_x, unloading_plot_y, s=6, alpha=0.5,
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
            ax.text(h_max_plot * 1.01, p_max_plot * 0.5, 'hmax',
                    fontsize=8, color='#5e6a72', va='center')

        if h_c_plot > 0:
            ax.axvline(h_c_plot, color='#a29bfe', linestyle=':', linewidth=1.4, alpha=0.8)
            ax.text(h_c_plot, 0, ' hc', fontsize=8, color='#a29bfe', va='bottom')

        if h_f_plot is not None and h_f_plot > 0:
            ax.axvline(h_f_plot, color='#fdcb6e', linestyle=':', linewidth=1.4, alpha=0.8)
            ax.text(h_f_plot, 0, ' hf', fontsize=8, color='#fdcb6e', va='bottom')

        # ── Axes styling for light theme ───────────────────────────────────
        for spine in ax.spines.values():
            spine.set_edgecolor('#d6dbe0')
        ax.tick_params(colors='#24313a', labelsize=9)
        ax.xaxis.label.set_color('#24313a')
        ax.yaxis.label.set_color('#24313a')
        ax.title.set_color('#24313a')

        ax.set_xlabel('Corrected displacement  h - h0  (nm)', fontsize=11, fontweight='bold', labelpad=6)
        ax.set_ylabel('Load on Sample  P  (mN)', fontsize=11, fontweight='bold', labelpad=6)
        test_label = str(test_id).strip()
        if not test_label.lower().startswith("test"):
            test_label = f"Test {test_label}"
        ax.set_title(f'{test_label}  —  Load-Displacement Curve  [ISO 14577-1]',
                     fontsize=12, fontweight='bold', pad=10)
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        ax.grid(True, alpha=0.45, linestyle=':', color='#d6dbe0')
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
                fontsize=8.0, fontfamily='monospace', color='#24313a',
                verticalalignment='top', horizontalalignment='left',
                bbox=dict(boxstyle='round,pad=0.45', facecolor='#ffffff',
                          edgecolor='#9ec9d4', linewidth=1.0, alpha=0.90))

        fig.tight_layout(pad=1.4)
        widget.canvas.draw()
    
    def create_plot_tabs(self, results: List[Dict[str, Any]]):
        """Render reliability summary and auto-open first test plot."""
        self.clear_plot_tabs(clear_exclusions=False)

        if not results:
            self.clear_step4_plot_buttons()
            if self.step4_plot_buttons_note:
                self.step4_plot_buttons_note.setText("No analysis results available yet.")
            return

        included_results = self.get_included_results() if self.current_results else results
        if included_results:
            self.create_summary_plot_tab(included_results)
            self.create_load_overlay_plot_tab(included_results)
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
            fig.patch.set_facecolor('#ffffff')

            file_label = Path(self.current_analysis_file_path).name if self.current_analysis_file_path else (
                results[0].get('Source File', 'selected file') if results else 'selected file'
            )
            n_tests = len(results)
            fig.suptitle(
                f'Analysis Reliability Summary  —  {file_label}  ({n_tests} included tests)',
                fontsize=12, fontweight='bold', y=0.99, color='#24313a'
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

            gs = fig.add_gridspec(2, 2, height_ratios=[1.15, 1.0])
            ax1 = fig.add_subplot(gs[0, :])
            ax2 = fig.add_subplot(gs[1, 0])
            ax3 = fig.add_subplot(gs[1, 1])
            for _ax in (ax1, ax2, ax3):
                _ax.set_facecolor('#ffffff')
                for spine in _ax.spines.values():
                    spine.set_edgecolor('#d6dbe0')
                _ax.tick_params(colors='#5e6a72', labelsize=8)
                _ax.xaxis.label.set_color('#24313a')
                _ax.yaxis.label.set_color('#24313a')
                _ax.title.set_color('#24313a')

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
                           facecolor='#ffffff', edgecolor='#c7d0d8', labelcolor='#24313a')
                ax1.grid(True, alpha=0.45, linestyle=':', color='#d6dbe0')
            else:
                ax1.text(0.5, 0.5, 'No R² data', ha='center', va='center',
                         transform=ax1.transAxes, color='#888888')
                ax1.set_title('Curve Fit Quality', fontweight='bold')

            # ── Panel 2: Hardness distribution ────────────────────────────────
            if hardness_values:
                mu_h, sd_h = np.mean(hardness_values), np.std(hardness_values)
                n_bins = min(15, max(4, len(hardness_values) // 2))
                ax2.hist(hardness_values, bins=n_bins, color='#00a8cc', alpha=0.75,
                         edgecolor='#ffffff', linewidth=0.8)
                ax2.axvline(mu_h, color='#ff6b6b', linewidth=2, linestyle='--',
                            label=f'Mean {mu_h:.3f} GPa')
                ax2.axvspan(mu_h - sd_h, mu_h + sd_h, alpha=0.08, color='#ff6b6b')
                cv_h = sd_h / mu_h * 100 if mu_h else 0
                ax2.set_xlabel('Hardness  H  (GPa)', fontsize=10)
                ax2.set_ylabel('Count', fontsize=10)
                ax2.set_title('Hardness Distribution', fontweight='bold', fontsize=11)
                ax2.grid(True, alpha=0.45, axis='y', linestyle=':', color='#d6dbe0')
            else:
                ax2.text(0.5, 0.5, 'No hardness data', ha='center', va='center',
                         transform=ax2.transAxes, color='#888888')
                ax2.set_title('Hardness Distribution', fontweight='bold')

            # ── Panel 3: Reduced modulus distribution ─────────────────────────
            if modulus_values:
                mu_e, sd_e = np.mean(modulus_values), np.std(modulus_values)
                n_bins = min(15, max(4, len(modulus_values) // 2))
                ax3.hist(modulus_values, bins=n_bins, color='#2ecc71', alpha=0.75,
                         edgecolor='#ffffff', linewidth=0.8)
                ax3.axvline(mu_e, color='#ff6b6b', linewidth=2, linestyle='--',
                            label=f'Mean {mu_e:.2f} GPa')
                ax3.axvspan(mu_e - sd_e, mu_e + sd_e, alpha=0.08, color='#ff6b6b')
                cv_e = sd_e / mu_e * 100 if mu_e else 0
                ax3.set_xlabel('Reduced Modulus  Er  (GPa)', fontsize=10)
                ax3.set_ylabel('Count', fontsize=10)
                ax3.set_title('Reduced Modulus Distribution', fontweight='bold', fontsize=11)
                ax3.grid(True, alpha=0.45, axis='y', linestyle=':', color='#d6dbe0')
            else:
                ax3.text(0.5, 0.5, 'No modulus data', ha='center', va='center',
                         transform=ax3.transAxes, color='#888888')
                ax3.set_title('Reduced Modulus Distribution', fontweight='bold')

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

            if self.summary_statistics_text:
                self.summary_statistics_text.setPlainText("\n".join(summary_stats))

            fig.text(
                0.5, 0.005,
                "ISO 14577-1:2015 — R² ≥ 0.99 required  |  CV > 10% may indicate surface effects",
                ha='center', fontsize=7.5, color='#8a949b', style='italic'
            )

            fig.tight_layout(rect=[0, 0.025, 1, 0.96])
            summary_widget.canvas.draw()

        except Exception as e:
            summary_widget.figure.clear()
            ax_err = summary_widget.figure.add_subplot(111)
            ax_err.set_facecolor('#ffffff')
            ax_err.text(0.5, 0.5, f'Error creating summary:\n{str(e)}',
                        transform=ax_err.transAxes, ha='center', va='center', color='#24313a',
                        bbox=dict(boxstyle='round,pad=0.8', facecolor='#fff0f0', edgecolor='#e74c3c', alpha=0.95), fontsize=9)
            ax_err.axis('off')
            summary_widget.canvas.draw()

    def create_load_overlay_plot_tab(self, results: List[Dict[str, Any]]):
        """Render an Oliver-Pharr batch load-displacement overlay plot."""
        if not self.op_overlay_widget:
            return

        widget = self.op_overlay_widget
        fig = widget.figure
        fig.clear()
        fig.patch.set_facecolor('#ffffff')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#ffffff')

        plotted_any = False
        colors = plt.rcParams["axes.prop_cycle"].by_key().get("color", [])
        if not colors:
            colors = ["#00a8cc", "#ffbe0b", "#2ecc71", "#e74c3c", "#9b59b6"]

        remove_hold_segment = self._op_overlay_remove_hold_segment()
        if remove_hold_segment and not self.op_overlay_cutoff_user_set:
            self._set_op_overlay_cutoff_default(results)
        cutoff_load = self._op_overlay_cutoff_value()
        max_x = 0.0
        max_y = 0.0
        for idx, result in enumerate(results):
            color = colors[idx % len(colors)]
            curve_data, unloading_needs_plot_shift = self._overlay_curve_data(result, idx)
            if curve_data is None:
                continue
            loading_disp, loading_load, unloading_disp, unloading_load = curve_data

            offset = self._current_overlay_h0_offset(result, idx)
            displacement_offset = offset if offset is not None else 0.0
            unloading_plot_shift = result.get('Unloading Plot Shift (nm)', 0.0) or 0.0

            def _finite_xy(x_values, y_values, x_shift: float = 0.0):
                if x_values is None or y_values is None:
                    return np.asarray([]), np.asarray([])
                try:
                    x = np.asarray(x_values, dtype=float) + float(x_shift) - displacement_offset
                    y = np.asarray(y_values, dtype=float)
                except (TypeError, ValueError):
                    return np.asarray([]), np.asarray([])
                valid = np.isfinite(x) & np.isfinite(y)
                valid &= (np.abs(x) < 1e12) & (np.abs(y) < 1e12)
                x = x[valid]
                y = y[valid]
                return x, y

            x_load, y_load = _finite_xy(loading_disp, loading_load)
            x_unload, y_unload = _finite_xy(
                unloading_disp,
                unloading_load,
                unloading_plot_shift if unloading_needs_plot_shift else 0.0,
            )
            if remove_hold_segment:
                x_load, y_load = self._trim_overlay_curve_to_load_cutoff(x_load, y_load, cutoff_load)
                x_unload, y_unload = self._trim_overlay_curve_to_load_cutoff(x_unload, y_unload, cutoff_load)
            x_unload, y_unload = self._align_unloading_overlay_to_loading(
                x_load, y_load, x_unload, y_unload
            )

            test_label = self._test_log_label(result, idx)
            if x_load.size > 1 and y_load.size > 1:
                x_load_plot, y_load_plot = self._thin_curve_for_plot(x_load, y_load, max_points=1200)
                ax.plot(x_load_plot, y_load_plot, color=color, linewidth=1.2, alpha=0.82, label=test_label)
                plotted_any = True
                max_x = max(max_x, float(np.nanmax(x_load)))
                max_y = max(max_y, float(np.nanmax(y_load)))
            if x_unload.size > 1 and y_unload.size > 1:
                x_unload_plot, y_unload_plot = self._thin_curve_for_plot(x_unload, y_unload, max_points=1200)
                ax.plot(x_unload_plot, y_unload_plot, color=color, linewidth=1.2, alpha=0.82)
                plotted_any = True
                max_x = max(max_x, float(np.nanmax(x_unload)))
                max_y = max(max_y, float(np.nanmax(y_unload)))

        if not plotted_any:
            ax.axis('off')
            ax.text(
                0.5, 0.5,
                "No load-displacement curve data available for included tests.",
                ha='center', va='center', fontsize=12, color='#24313a',
                transform=ax.transAxes
            )
            widget.canvas.draw()
            return

        hardness_values = self._finite_result_values(results, 'Hardness (GPa)')
        modulus_values = self._finite_result_values(results, 'Oliver-Pharr Modulus (GPa)')
        hardness_text = (
            f"Mean Hardness = {float(np.mean(hardness_values)):.3g} GPa"
            if hardness_values.size else "Mean Hardness = n/a"
        )
        modulus_text = (
            f"Mean Modulus = {float(np.mean(modulus_values)):.3g} GPa"
            if modulus_values.size else "Mean Modulus = n/a"
        )
        ax.text(
            0.03, 0.95,
            f"{hardness_text}\n{modulus_text}",
            transform=ax.transAxes, ha='left', va='top',
            fontsize=10, color='#24313a',
            bbox=dict(facecolor='#ffffff', edgecolor='none', alpha=0.70, pad=3),
        )

        if max_x > 0 and max_y > 0:
            ax.annotate(
                "Loading",
                xy=(0.48 * max_x, 0.62 * max_y),
                xytext=(0.30 * max_x, 0.45 * max_y),
                arrowprops=dict(arrowstyle='->', lw=1.1, color='#24313a'),
                color='#24313a', fontsize=9,
            )
            ax.annotate(
                "Unloading",
                xy=(0.70 * max_x, 0.28 * max_y),
                xytext=(0.78 * max_x, 0.47 * max_y),
                arrowprops=dict(arrowstyle='->', lw=1.1, color='#24313a'),
                color='#24313a', fontsize=9,
            )

        for spine in ax.spines.values():
            spine.set_edgecolor('#d6dbe0')
        ax.tick_params(colors='#24313a', labelsize=9)
        ax.xaxis.label.set_color('#24313a')
        ax.yaxis.label.set_color('#24313a')
        ax.title.set_color('#24313a')
        ax.grid(True, alpha=0.35, linestyle=':', color='#d6dbe0')
        ax.set_xlabel('Corrected displacement  h - h0  (nm)', fontsize=11)
        ax.set_ylabel('Load On Sample (mN)', fontsize=11)
        ax.set_title('Oliver-Pharr Load-Displacement Overlay', fontsize=12, fontweight='bold', pad=10)
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        if len(results) <= 12:
            ax.legend(loc='lower right', fontsize=7, framealpha=0.86, facecolor='#ffffff', edgecolor='#c7d0d8')
        fig.tight_layout()
        widget.canvas.draw()

    def _current_overlay_h0_offset(self, result: Dict[str, Any], fallback_index: int) -> Optional[float]:
        test_number = self._test_number_from_result(result, fallback_index)
        if test_number is not None:
            edited_offset = self._finite_float_or_none(self.csm_offsets.get(int(test_number)))
            if edited_offset is not None:
                return edited_offset
        return self._finite_float_or_none(result.get('Loading Offset h0 (nm)'))

    @staticmethod
    def _curve_tuple_has_data(curves: Tuple[List[float], List[float], List[float], List[float]]) -> bool:
        return all(values is not None and len(values) > 0 for values in curves)

    @staticmethod
    def _thin_curve_for_plot(
        x: np.ndarray,
        y: np.ndarray,
        max_points: int = 1600,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Reduce dense display curves while preserving endpoints and the load peak."""
        if x.size != y.size or x.size <= max_points or max_points < 4:
            return x, y
        valid = np.isfinite(x) & np.isfinite(y)
        if np.count_nonzero(valid) <= max_points:
            return x[valid], y[valid]
        valid_indices = np.where(valid)[0]
        peak_idx = valid_indices[int(np.nanargmax(y[valid]))]
        base = np.linspace(0, x.size - 1, max_points - 3, dtype=int)
        indices = np.unique(np.concatenate((base, [0, peak_idx, x.size - 1])))
        indices = indices[np.isfinite(x[indices]) & np.isfinite(y[indices])]
        return x[indices], y[indices]

    def _overlay_curve_data(
        self,
        result: Dict[str, Any],
        fallback_index: int,
    ) -> Tuple[Optional[Tuple[List[float], List[float], List[float], List[float]]], bool]:
        """Return curve arrays and whether unloading still needs the analysis plot shift."""
        full_curves = (
            result.get('Full Raw Loading Displacement (nm)', []),
            result.get('Full Raw Loading Load (mN)', []),
            result.get('Full Raw Unloading Displacement (nm)', []),
            result.get('Full Raw Unloading Load (mN)', []),
        )
        if self._curve_tuple_has_data(full_curves):
            return full_curves, True

        raw_curves = (
            result.get('Raw Loading Displacement (nm)', []),
            result.get('Raw Loading Load (mN)', []),
            result.get('Raw Unloading Displacement (nm)', []),
            result.get('Raw Unloading Load (mN)', []),
        )
        if self._curve_tuple_has_data(raw_curves):
            return raw_curves, False

        file_curves = self._load_full_overlay_curves_from_file(result, fallback_index)
        if file_curves is not None:
            return file_curves, True
        return None, False

    def _load_full_overlay_curves_from_file(
        self,
        result: Dict[str, Any],
        fallback_index: int,
    ) -> Optional[Tuple[List[float], List[float], List[float], List[float]]]:
        file_path = self.current_analysis_file_path
        if not file_path and getattr(self, "file_path_edit", None):
            file_path = self.file_path_edit.text()
        if not file_path or not os.path.exists(file_path):
            return None

        test_number = self._test_number_from_result(result, fallback_index)
        if test_number is None:
            return None
        cache_key = (str(Path(file_path).resolve()), int(test_number))
        cached = self.overlay_curve_cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            loader = self.selected_file_loader()
            sheet_name = f"Test {int(test_number):03d}"
            if hasattr(loader, "get_sheet_names"):
                resolved_path = str(Path(file_path).resolve())
                sheet_names = self.overlay_sheet_names_cache.get(resolved_path)
                if sheet_names is None:
                    sheet_names = loader.get_sheet_names(file_path)
                    self.overlay_sheet_names_cache[resolved_path] = list(sheet_names)
                matching = [
                    name for name in sheet_names
                    if self._test_number_from_sheet_name(str(name)) == int(test_number)
                ]
                if matching:
                    sheet_name = matching[0]

            if not hasattr(loader, "load_sheet"):
                return None
            raw_df, _units = loader.load_sheet(file_path, sheet_name)
            if raw_df is None or raw_df.empty:
                return None

            if hasattr(loader, "normalize_sheet"):
                df = loader.normalize_sheet(raw_df)
            else:
                df = raw_df.copy()
            if df is None or df.empty or not {"Load (mN)", "Displacement (nm)"}.issubset(df.columns):
                return None

            full_df = df[["Displacement (nm)", "Load (mN)"]].copy()
            full_df["Displacement (nm)"] = pd.to_numeric(full_df["Displacement (nm)"], errors="coerce")
            full_df["Load (mN)"] = pd.to_numeric(full_df["Load (mN)"], errors="coerce")
            full_df = full_df.replace([np.inf, -np.inf], np.nan).dropna()
            if full_df.empty:
                return None

            peak_pos = int(np.argmax(full_df["Load (mN)"].to_numpy(dtype=float)))
            loading_df = full_df.iloc[:peak_pos + 1]
            unloading_df = full_df.iloc[peak_pos:]
            curves = (
                loading_df["Displacement (nm)"].tolist(),
                loading_df["Load (mN)"].tolist(),
                unloading_df["Displacement (nm)"].tolist(),
                unloading_df["Load (mN)"].tolist(),
            )
            self.overlay_curve_cache[cache_key] = curves
            return curves
        except Exception:
            return None

    def _op_overlay_remove_hold_segment(self) -> bool:
        if getattr(self, "op_overlay_hold_combo", None) is None:
            return True
        return self.op_overlay_hold_combo.currentIndex() == 0

    def _op_overlay_cutoff_value(self) -> Optional[float]:
        if getattr(self, "op_overlay_cutoff_spin", None) is None:
            return None
        self.op_overlay_cutoff_spin.interpretText()
        value = float(self.op_overlay_cutoff_spin.value())
        return value if np.isfinite(value) and value > 0 else None

    def _sync_op_overlay_hold_controls(self, *_args):
        remove_hold = self._op_overlay_remove_hold_segment()
        for widget in (
            getattr(self, "op_overlay_cutoff_label", None),
            getattr(self, "op_overlay_cutoff_spin", None),
        ):
            if widget is not None:
                widget.setVisible(remove_hold)
        if remove_hold and not self.op_overlay_cutoff_user_set:
            self._set_op_overlay_cutoff_default(self.get_included_results() if self.current_results else [])
        self._refresh_op_overlay_options()

    def _op_overlay_cutoff_changed(self, *_args):
        if self.op_overlay_cutoff_syncing:
            return
        if getattr(self, "op_overlay_cutoff_spin", None) is not None:
            self.op_overlay_cutoff_spin.interpretText()
        self.op_overlay_cutoff_user_set = True
        self._refresh_op_overlay_options()

    def _refresh_op_overlay_options(self, *_args):
        self.update_readiness_summary()
        if getattr(self, "op_overlay_refresh_timer", None) is not None:
            self.op_overlay_refresh_timer.start(120)
            return
        self._refresh_op_overlay_options_now()

    def _refresh_op_overlay_options_now(self):
        included_results = self.get_included_results() if self.current_results else []
        if included_results:
            self.create_load_overlay_plot_tab(included_results)

    def _set_op_overlay_cutoff_default(self, results: List[Dict[str, Any]]):
        if getattr(self, "op_overlay_cutoff_spin", None) is None or not results:
            return
        cutoff = self._default_op_overlay_cutoff(results)
        if cutoff is None:
            return
        self.op_overlay_cutoff_syncing = True
        self.op_overlay_cutoff_spin.blockSignals(True)
        self.op_overlay_cutoff_spin.setValue(float(cutoff))
        self.op_overlay_cutoff_spin.blockSignals(False)
        self.op_overlay_cutoff_syncing = False

    def _default_op_overlay_cutoff(self, results: List[Dict[str, Any]]) -> Optional[float]:
        peak_loads: List[float] = []
        for idx, result in enumerate(results):
            curve_data, _unloading_needs_plot_shift = self._overlay_curve_data(result, idx)
            if curve_data is None:
                continue
            _loading_disp, loading_load, _unloading_disp, unloading_load = curve_data
            try:
                loads = np.asarray(list(loading_load) + list(unloading_load), dtype=float)
            except (TypeError, ValueError):
                continue
            loads = loads[np.isfinite(loads)]
            if loads.size:
                peak_loads.append(float(np.nanmax(loads)))
        if not peak_loads:
            return None
        return float(np.nanmin(np.asarray(peak_loads, dtype=float)))

    @staticmethod
    def _trim_overlay_curve_to_load_cutoff(
        x: np.ndarray,
        y: np.ndarray,
        cutoff: Optional[float],
    ) -> Tuple[np.ndarray, np.ndarray]:
        if cutoff is None or not np.isfinite(cutoff) or cutoff <= 0:
            return x, y
        if x.size != y.size or x.size < 2:
            return x, y

        valid = np.isfinite(x) & np.isfinite(y)
        x = x[valid]
        y = y[valid]
        if x.size < 2:
            return x, y

        cutoff = float(cutoff)
        cutoff_tol = max(1e-6, abs(cutoff) * 1e-7)
        below_cutoff = y < (cutoff - cutoff_tol)
        at_or_above_cutoff = ~below_cutoff

        def interpolate_cutoff(idx_a: int, idx_b: int) -> Tuple[float, float]:
            x_a, y_a = float(x[idx_a]), float(y[idx_a])
            x_b, y_b = float(x[idx_b]), float(y[idx_b])
            denom = y_b - y_a
            if abs(denom) < 1e-12:
                return x_b, cutoff
            frac = (cutoff - y_a) / denom
            frac = float(np.clip(frac, 0.0, 1.0))
            return x_a + frac * (x_b - x_a), cutoff

        starts_above_cutoff = at_or_above_cutoff[0]
        if starts_above_cutoff:
            below_indices = np.where(below_cutoff)[0]
            if below_indices.size == 0:
                return np.asarray([float(x[0])], dtype=float), np.asarray([cutoff], dtype=float)
            first_below = int(below_indices[0])
            if first_below == 0:
                return x, y
            x_cut, y_cut = interpolate_cutoff(first_below - 1, first_below)
            return (
                np.concatenate(([x_cut], x[first_below:])),
                np.concatenate(([y_cut], y[first_below:])),
            )

        at_or_above_indices = np.where(at_or_above_cutoff)[0]
        if at_or_above_indices.size == 0:
            return x, y
        first_above = int(at_or_above_indices[0])
        if first_above == 0:
            return np.asarray([float(x[0])], dtype=float), np.asarray([cutoff], dtype=float)
        x_cut, y_cut = interpolate_cutoff(first_above - 1, first_above)
        return (
            np.concatenate((x[:first_above], [x_cut])),
            np.concatenate((y[:first_above], [y_cut])),
        )

    @staticmethod
    def _align_unloading_overlay_to_loading(
        x_load: np.ndarray,
        y_load: np.ndarray,
        x_unload: np.ndarray,
        y_unload: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Shift unloading x values and anchor it to the loading peak."""
        shift_info = NanoindentationGUI._unloading_overlay_alignment_shift(
            x_load, y_load, x_unload, y_unload
        )
        if shift_info is None:
            return x_unload, y_unload
        shift, anchor_x, anchor_y, unload_start_idx = shift_info
        shifted_x = x_unload + shift
        if shifted_x.size == 0:
            return shifted_x, y_unload

        already_anchored = (
            np.isfinite(shifted_x[unload_start_idx])
            and np.isfinite(y_unload[unload_start_idx])
            and abs(float(shifted_x[unload_start_idx]) - anchor_x) < 1e-6
            and abs(float(y_unload[unload_start_idx]) - anchor_y) < 1e-6
        )
        if already_anchored:
            return shifted_x, y_unload

        anchored_x = np.concatenate(([anchor_x], shifted_x))
        anchored_y = np.concatenate(([anchor_y], y_unload))
        return anchored_x, anchored_y

    @staticmethod
    def _unloading_overlay_alignment_shift(
        x_load: np.ndarray,
        y_load: np.ndarray,
        x_unload: np.ndarray,
        y_unload: np.ndarray,
    ) -> Optional[Tuple[float, float, float, int]]:
        """Return the x-shift needed to put unloading start at the loading peak."""
        load_valid = np.isfinite(x_load) & np.isfinite(y_load)
        unload_valid = np.isfinite(x_unload) & np.isfinite(y_unload)
        if np.count_nonzero(load_valid) == 0 or np.count_nonzero(unload_valid) == 0:
            return None

        load_indices = np.where(load_valid)[0]
        unload_indices = np.where(unload_valid)[0]
        peak_local_idx = int(np.nanargmax(y_load[load_valid]))
        load_peak_idx = int(load_indices[peak_local_idx])
        unload_start_idx = int(unload_indices[0])

        anchor_x = float(x_load[load_peak_idx])
        anchor_y = float(y_load[load_peak_idx])
        shift = float(anchor_x - x_unload[unload_start_idx])
        if not np.isfinite(shift):
            return None
        return shift, anchor_x, anchor_y, int(unload_start_idx)

    @staticmethod
    def _remove_high_load_horizontal_overlay_segments(x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Break peak-hold shelves in overlay curves while preserving the experimental ramp."""
        if x.size != y.size or x.size < 4:
            return x, y
        y_max = float(np.nanmax(y))
        if not np.isfinite(y_max) or y_max <= 0:
            return x, y

        dx = np.diff(x)
        dy = np.diff(y)
        high_load = (y[:-1] >= 0.90 * y_max) & (y[1:] >= 0.90 * y_max)
        slope = np.divide(
            np.abs(dy),
            np.maximum(np.abs(dx), 1e-9),
            out=np.full_like(dy, np.inf, dtype=float),
            where=np.abs(dx) > 1e-9,
        )
        horizontal = slope <= 0.08
        moving_in_x = np.abs(dx) >= 0.1
        plateau_segment = high_load & horizontal & moving_in_x
        if not np.any(plateau_segment):
            return x, y

        cleaned_x: List[float] = []
        cleaned_y: List[float] = []
        in_gap = False
        for idx in range(x.size - 1):
            if not in_gap:
                cleaned_x.append(float(x[idx]))
                cleaned_y.append(float(y[idx]))
            if plateau_segment[idx]:
                if not in_gap:
                    cleaned_x.append(np.nan)
                    cleaned_y.append(np.nan)
                    in_gap = True
            else:
                if in_gap:
                    cleaned_x.append(float(x[idx + 1]))
                    cleaned_y.append(float(y[idx + 1]))
                    in_gap = False

        if not in_gap:
            cleaned_x.append(float(x[-1]))
            cleaned_y.append(float(y[-1]))
        if len(cleaned_x) < 2:
            return x, y
        return np.asarray(cleaned_x, dtype=float), np.asarray(cleaned_y, dtype=float)

    def _create_axis_range_spinbox(self) -> QDoubleSpinBox:
        spinbox = QDoubleSpinBox()
        spinbox.setRange(-1e12, 1e12)
        spinbox.setDecimals(6)
        spinbox.setSingleStep(1.0)
        spinbox.setEnabled(True)
        return spinbox

    def _configure_expert_combo(self, combo: QComboBox):
        combo.setMinimumWidth(self.sp(170))
        combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        combo.setMinimumContentsLength(18 if self.control_panel_width < self.sp(390) else 24)
        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: #ffffff;
                color: #24313a;
                border: 1px solid #d6dbe0;
                border-radius: {self.sp(6)}px;
                padding: {self.sp(7)}px {self.sp(10)}px;
                font-size: {self.fp(11)}px;
            }}
            QComboBox:focus {{
                border: 2px solid #00d9ff;
                background-color: #f8fbfc;
            }}
            QComboBox QAbstractItemView {{
                background-color: #ffffff;
                color: #24313a;
                selection-background-color: #00a8cc;
                selection-color: #ffffff;
            }}
        """)

    def _toggle_live_plot_ranges(self, enabled: bool):
        for spinbox in (
            self.live_plot_xmin_spin,
            self.live_plot_xmax_spin,
            self.live_plot_ymin_spin,
            self.live_plot_ymax_spin,
        ):
            if spinbox is not None:
                spinbox.setEnabled(True)
                spinbox.setToolTip(
                    "Editable axis range value. Check 'Use custom axis ranges' "
                    "to apply these limits to the Expert Plot."
                )
        self._expert_plot_controls_changed()

    def _show_expert_plot_tab_only(self):
        if self.results_panel_tabs is None:
            return
        idx = self._results_tab_index("Expert Plot")
        if idx >= 0:
            self._set_results_tab_visible("Expert Plot", True)
            self.results_panel_tabs.setCurrentIndex(idx)

    def show_expert_plot_tab(self):
        try:
            if self.live_plot_data is None:
                self.refresh_live_plot_source()
            self._show_expert_plot_tab_only()
            self.update_live_variable_plot()
        except Exception as exc:
            self._set_expert_plot_html(
                "<div class='placeholder'><h1>Expert plot error</h1>"
                f"<p>{str(exc)}</p></div>"
            )
            if self.live_plot_status_label is not None:
                self.live_plot_status_label.setText(f"Could not render Expert plot: {str(exc)}")

    def _expert_plot_controls_changed(self, *_args):
        if self.live_plot_status_label is not None and self.live_plot_has_rendered:
            self.live_plot_status_label.setText(
                "Expert plot settings changed. Click 'Show Plot on Right' to regenerate."
            )

    def _expert_lsq_controls_changed(self, *_args):
        self._sync_lsq_fit_controls()
        self._expert_plot_controls_changed()

    def _sync_lsq_fit_controls(self):
        source = self._selected_live_plot_source()
        single_sheet = bool(source and source != "__all_tests__")
        fit_enabled = bool(single_sheet and self.live_plot_lsq_fit_cb and self.live_plot_lsq_fit_cb.isChecked())

        if self.live_plot_lsq_fit_cb is not None:
            self.live_plot_lsq_fit_cb.setEnabled(single_sheet)
            if not single_sheet:
                self.live_plot_lsq_fit_cb.blockSignals(True)
                self.live_plot_lsq_fit_cb.setChecked(False)
                self.live_plot_lsq_fit_cb.blockSignals(False)
        if self.live_plot_lsq_degree_spin is not None:
            self.live_plot_lsq_degree_spin.setEnabled(fit_enabled)
        if self.live_plot_lsq_status_label is not None:
            if not single_sheet:
                self.live_plot_lsq_status_label.setText("Select a single sheet to enable LSQ fit.")
            elif fit_enabled:
                degree = self.live_plot_lsq_degree_spin.value() if self.live_plot_lsq_degree_spin else 1
                self.live_plot_lsq_status_label.setText(f"LSQ polynomial degree {degree}; click Show Plot on Right.")
            else:
                self.live_plot_lsq_status_label.setText("Enable LSQ fit to calculate the y=0 x-intercept.")

    def _lsq_polynomial_fit(self, x_values, y_values, degree: int):
        x = np.asarray(x_values, dtype=float)
        y = np.asarray(y_values, dtype=float)
        mask = np.isfinite(x) & np.isfinite(y) & (np.abs(x) < 1e12) & (np.abs(y) < 1e12)
        x = x[mask]
        y = y[mask]
        if x.size < 2:
            return None, "Not enough points for LSQ fit."

        degree = int(max(1, min(degree, x.size - 1)))
        unique_x = np.unique(x)
        if unique_x.size <= degree:
            degree = max(1, unique_x.size - 1)
        if degree < 1:
            return None, "Not enough unique X values for LSQ fit."

        x_min = float(np.nanmin(x))
        x_max = float(np.nanmax(x))
        x_center = 0.5 * (x_min + x_max)
        x_span = 0.5 * (x_max - x_min)
        if not np.isfinite(x_span) or x_span <= 0:
            return None, "X range is not wide enough for LSQ fit."
        x_scaled = (x - x_center) / x_span

        try:
            coeffs = np.polyfit(x_scaled, y, degree)
        except Exception as exc:
            return None, f"LSQ fit failed: {exc}"
        coeffs = np.asarray(coeffs, dtype=float)
        if coeffs.size == 0 or not np.isfinite(coeffs).all():
            return None, "LSQ fit failed: polynomial coefficients were not finite."
        if not np.isfinite(coeffs[0]) or abs(coeffs[0]) < np.finfo(float).eps:
            return None, "LSQ fit failed: polynomial leading coefficient was zero."

        x_fit = np.linspace(x_min, x_max, 400)
        y_fit = np.polyval(coeffs, (x_fit - x_center) / x_span)
        finite_fit = np.isfinite(x_fit) & np.isfinite(y_fit) & (np.abs(y_fit) < 1e12)
        x_fit = x_fit[finite_fit]
        y_fit = y_fit[finite_fit]
        if x_fit.size < 2:
            return None, "LSQ fit failed: fitted values were not finite."

        roots = []
        root_warning = ""
        try:
            raw_roots = np.roots(coeffs)
        except Exception as exc:
            raw_roots = []
            root_warning = f"Root calculation failed: {exc}"
        for root in raw_roots:
            if not np.isfinite(np.real(root)) or not np.isfinite(np.imag(root)):
                continue
            if abs(np.imag(root)) > 1e-7:
                continue
            root_real = x_center + float(np.real(root)) * x_span
            if np.isfinite(root_real) and x_min <= root_real <= x_max:
                roots.append(root_real)
        roots = sorted(set(round(root, 9) for root in roots))

        return {
            "degree": degree,
            "coeffs": coeffs,
            "x_fit": x_fit,
            "y_fit": y_fit,
            "roots": roots,
            "x_range": (x_min, x_max),
        }, root_warning

    @staticmethod
    def _points_inside_ranges(x_values, y_values, xmin, xmax, ymin, ymax) -> int:
        x = np.asarray(x_values, dtype=float)
        y = np.asarray(y_values, dtype=float)
        if x.size != y.size or x.size == 0:
            return 0
        mask = (
            np.isfinite(x)
            & np.isfinite(y)
            & (x >= float(xmin))
            & (x <= float(xmax))
            & (y >= float(ymin))
            & (y <= float(ymax))
        )
        return int(np.count_nonzero(mask))

    def selected_expert_test_sheets(self) -> List[str]:
        selected = []
        for sheet_name in self.live_plot_test_sheets:
            test_number = self._test_number_from_sheet_name(sheet_name)
            if test_number is not None:
                if test_number in self.excluded_test_numbers:
                    continue
            selected.append(sheet_name)
        return selected

    @staticmethod
    def _is_test_sheet_name(sheet_name: str) -> bool:
        parts = str(sheet_name).split()
        return (
            len(parts) >= 2
            and parts[0].lower() == "test"
            and parts[1].isdigit()
        )

    def _load_live_plot_sheet(self, file_path: str, sheet_name=0) -> tuple[pd.DataFrame, Dict[str, str]]:
        try:
            loader = self.selected_file_loader()
            if hasattr(loader, "load_sheet"):
                return loader.load_sheet(file_path, sheet_name)
        except Exception:
            if str(file_path).lower().endswith(".csv"):
                return pd.read_csv(file_path), {}

        raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        if raw.empty:
            return pd.DataFrame(), {}

        header_row = 0
        headers = [str(value).strip() if pd.notna(value) else f"Column {idx + 1}" for idx, value in enumerate(raw.iloc[header_row])]
        units = {}
        data_start = header_row + 1
        if len(raw) > header_row + 1:
            unit_row = raw.iloc[header_row + 1]
            non_empty_units = 0
            for header, unit_value in zip(headers, unit_row):
                if pd.notna(unit_value):
                    unit_text = str(unit_value).strip()
                    if unit_text and not unit_text.replace(".", "", 1).isdigit():
                        units[header] = unit_text
                        non_empty_units += 1
            if non_empty_units:
                data_start = header_row + 2

        df = raw.iloc[data_start:].copy()
        df.columns = headers
        df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")
        return df.reset_index(drop=True), units

    def _live_plot_label(self, column: str) -> str:
        unit = self.live_plot_units.get(column, "")
        return f"{column} ({unit})" if unit else column

    def _expert_display_range(self, values, column_name: str) -> tuple[float, float]:
        arr = np.asarray(values, dtype=float)
        arr = arr[np.isfinite(arr)]
        if arr.size == 0:
            return 0.0, 1.0

        lname = str(column_name).lower()
        mostly_positive = np.count_nonzero(arr >= 0) >= max(2, int(arr.size * 0.80))
        positive_physical = any(
            token in lname
            for token in ["displacement", "depth", "load", "hardness", "modulus", "stiffness", "time"]
        )
        if positive_physical and mostly_positive:
            non_negative = arr[arr >= 0]
            if non_negative.size >= 2:
                arr = non_negative

        lo = float(np.nanpercentile(arr, 1.0))
        hi = float(np.nanpercentile(arr, 99.5))
        if positive_physical and mostly_positive:
            lo = max(0.0, lo)
        if not np.isfinite(lo) or not np.isfinite(hi) or lo == hi:
            lo = float(np.nanmin(arr))
            hi = float(np.nanmax(arr))
        if lo == hi:
            pad = abs(lo) * 0.05 or 1.0
            return lo - pad, hi + pad

        pad = (hi - lo) * 0.02
        lo = max(0.0, lo - pad) if positive_physical and mostly_positive else lo - pad
        hi = hi + pad
        if not np.isfinite(lo) or not np.isfinite(hi):
            return 0.0, 1.0
        return float(lo), float(hi)

    def _set_expert_range_fields(self, x_values, y_values, x_col: str, y_col: str, signature: tuple):
        if self.live_plot_range_signature == signature:
            return
        self.live_plot_range_signature = signature
        xmin, xmax = self._expert_display_range(x_values, x_col)
        ymin, ymax = self._expert_display_range(y_values, y_col)
        for spinbox, value in (
            (self.live_plot_xmin_spin, xmin),
            (self.live_plot_xmax_spin, xmax),
            (self.live_plot_ymin_spin, ymin),
            (self.live_plot_ymax_spin, ymax),
        ):
            if spinbox is not None:
                spinbox.blockSignals(True)
                spinbox.setValue(float(value))
                spinbox.blockSignals(False)

    def _set_live_plot_axis_choices(self, columns: List[str]):
        numeric_columns = []
        if self.live_plot_data is not None and not self.live_plot_data.empty:
            for column in columns:
                numeric_values = pd.to_numeric(self.live_plot_data[column], errors="coerce")
                if numeric_values.notna().sum() >= 2:
                    numeric_columns.append(column)
        else:
            numeric_columns = columns

        if self.live_plot_x_combo is not None:
            self.live_plot_x_combo.blockSignals(True)
            self.live_plot_x_combo.clear()
            for column in numeric_columns:
                self.live_plot_x_combo.addItem(self._live_plot_label(column), column)
            if numeric_columns:
                self.live_plot_x_combo.setCurrentIndex(0)
                self.live_plot_x_combo.setCurrentText(self._live_plot_label(numeric_columns[0]))
            self.live_plot_x_combo.blockSignals(False)
        if self.live_plot_y_combo is not None:
            self.live_plot_y_combo.blockSignals(True)
            self.live_plot_y_combo.clear()
            for column in numeric_columns:
                self.live_plot_y_combo.addItem(self._live_plot_label(column), column)
            if numeric_columns:
                self.live_plot_y_combo.setCurrentIndex(0)
                self.live_plot_y_combo.setCurrentText(self._live_plot_label(numeric_columns[0]))
            self.live_plot_y_combo.blockSignals(False)

        x_default = 0
        y_default = 1 if len(numeric_columns) > 1 else 0
        for idx, name in enumerate(numeric_columns):
            lname = name.lower()
            if any(tag in lname for tag in ["depth", "displacement", "time", "x"]):
                x_default = idx
                break
        for idx, name in enumerate(numeric_columns):
            lname = name.lower()
            if any(tag in lname for tag in ["load", "hardness", "modulus", "stiffness", "force", "y"]):
                y_default = idx
                break

        if self.live_plot_x_combo is not None and numeric_columns:
            self.live_plot_x_combo.setCurrentIndex(x_default)
            self.live_plot_x_combo.setCurrentText(self._live_plot_label(numeric_columns[x_default]))
        if self.live_plot_y_combo is not None and numeric_columns:
            self.live_plot_y_combo.setCurrentIndex(y_default)
            self.live_plot_y_combo.setCurrentText(self._live_plot_label(numeric_columns[y_default]))

    def _live_plot_sheet_changed(self, *_args):
        if not self.live_plot_file_path or self.live_plot_sheet_combo is None:
            return

        source = self.live_plot_sheet_combo.currentData()
        if source == "__all_tests__":
            self._sync_lsq_fit_controls()
            if not self.live_plot_test_sheets:
                return
            first_df, units = self._load_live_plot_sheet(self.live_plot_file_path, self.live_plot_test_sheets[0])
            self.live_plot_data = pd.DataFrame()
            self.live_plot_units = units
            columns = [col for col in first_df.columns if str(col).lower() != "segment"]
            self._set_live_plot_axis_choices(columns)
            if self.live_plot_status_label is not None:
                self.live_plot_status_label.setText(
                    f"Loaded {len(columns)} variables from {len(self.live_plot_test_sheets)} Test sheets. "
                    "Choose X and Y, then click 'Show Plot on Right'."
                )
            return

        try:
            df, units = self._load_live_plot_sheet(self.live_plot_file_path, source)
        except Exception as e:
            self.live_plot_data = None
            self.live_plot_units = {}
            if self.live_plot_status_label is not None:
                self.live_plot_status_label.setText(f"Could not load sheet: {str(e)}")
            return

        self.live_plot_data = df
        self.live_plot_units = units
        self.live_plot_range_signature = None
        self._sync_lsq_fit_controls()
        columns = [col for col in df.columns if str(col).lower() != "segment"]
        self._set_live_plot_axis_choices(columns)
        if self.live_plot_status_label is not None:
            self.live_plot_status_label.setText(
                f"Loaded {len(columns)} variables from sheet '{self.live_plot_sheet_combo.currentText()}'."
                " Click 'Show Plot on Right' to render."
            )

    def refresh_live_plot_source(self):
        """Load selected file columns into custom live-plot selectors."""
        file_path = self.file_path_edit.text().strip() if self.file_path_edit else ""
        if not file_path or not os.path.exists(file_path):
            self.live_plot_data = None
            self.live_plot_units = {}
            self.live_plot_file_path = None
            self.live_plot_test_sheets = []
            self.live_plot_range_signature = None
            if self.live_plot_sheet_combo is not None:
                self.live_plot_sheet_combo.clear()
            if self.live_plot_x_combo is not None:
                self.live_plot_x_combo.clear()
            if self.live_plot_y_combo is not None:
                self.live_plot_y_combo.clear()
            if self.live_plot_status_label is not None:
                self.live_plot_status_label.setText("Select an experiment file to load available variables.")
            self.live_plot_has_rendered = False
            self._sync_expert_offsets_table()
            self._draw_expert_plot_placeholder()
            return

        try:
            self.live_plot_file_path = file_path
            suffix = Path(file_path).suffix.lower()
            loader = self.selected_file_loader()
            if hasattr(loader, "get_sheet_names"):
                sheet_names = loader.get_sheet_names(file_path)
                df, units = self._load_live_plot_sheet(file_path, sheet_names[0] if sheet_names else 0)
            elif suffix == ".csv":
                df, units = self._load_live_plot_sheet(file_path)
                sheet_names = ["CSV"]
            else:
                excel_file = pd.ExcelFile(file_path)
                sheet_names = excel_file.sheet_names
                df, units = self._load_live_plot_sheet(file_path, sheet_names[0])
            if not isinstance(df, pd.DataFrame) or df.empty:
                raise ValueError("No tabular rows found in file.")
        except Exception as e:
            self.live_plot_data = None
            self.live_plot_units = {}
            self.live_plot_file_path = None
            self.live_plot_test_sheets = []
            self.live_plot_range_signature = None
            if self.live_plot_sheet_combo is not None:
                self.live_plot_sheet_combo.clear()
            if self.live_plot_x_combo is not None:
                self.live_plot_x_combo.clear()
            if self.live_plot_y_combo is not None:
                self.live_plot_y_combo.clear()
            if self.live_plot_status_label is not None:
                self.live_plot_status_label.setText(f"Could not load file variables: {str(e)}")
            self.live_plot_has_rendered = False
            self._sync_expert_offsets_table()
            self._draw_expert_plot_placeholder()
            return

        self.live_plot_data = df
        self.live_plot_units = units
        self.live_plot_range_signature = None
        self.live_plot_test_sheets = [name for name in sheet_names if self._is_test_sheet_name(name)]
        self._sync_expert_offsets_table()
        if self.live_plot_sheet_combo is not None:
            self.live_plot_sheet_combo.blockSignals(True)
            self.live_plot_sheet_combo.clear()
            if self.live_plot_test_sheets:
                self.live_plot_sheet_combo.addItem(
                    f"All Test Sheets ({len(self.live_plot_test_sheets)} overlays)",
                    "__all_tests__"
                )
            for sheet_name in sheet_names:
                self.live_plot_sheet_combo.addItem(sheet_name, sheet_name)
            if self.live_plot_sheet_combo.count() > 0:
                self.live_plot_sheet_combo.setCurrentIndex(0)
                self.live_plot_sheet_combo.setCurrentText(self.live_plot_sheet_combo.itemText(0))
            self.live_plot_sheet_combo.blockSignals(False)

        if self.live_plot_test_sheets and self.live_plot_sheet_combo is not None:
            self._live_plot_sheet_changed()
            return

        columns = [str(col) for col in df.columns if str(col).lower() != "segment"]
        self._set_live_plot_axis_choices(columns)
        if self.live_plot_status_label is not None:
            self.live_plot_status_label.setText(
                f"Loaded {len(columns)} variables from {Path(file_path).name}. Choose X and Y, then click 'Show Plot on Right'."
            )

    @staticmethod
    def _current_combo_data(combo: Optional[QComboBox]) -> str:
        if combo is None:
            return ""
        data = combo.currentData()
        return str(data if data is not None else combo.currentText()).strip()

    def _resolve_live_plot_column(self, selection: str) -> str:
        if not selection:
            return ""
        if self.live_plot_data is None:
            return selection
        columns = [str(col) for col in self.live_plot_data.columns]
        if selection in columns:
            return selection
        for column in columns:
            if selection == self._live_plot_label(column):
                return column
        return selection

    def _selected_live_plot_source(self) -> str:
        source = self._current_combo_data(self.live_plot_sheet_combo)
        if source:
            return source
        if self.live_plot_sheet_combo is not None:
            text = (self.live_plot_sheet_combo.currentText() or "").strip()
            if text.startswith("All Test Sheets"):
                return "__all_tests__"
            return text
        return ""

    def _selected_live_plot_columns(self) -> tuple[str, str]:
        x_raw = self._current_combo_data(self.live_plot_x_combo)
        y_raw = self._current_combo_data(self.live_plot_y_combo)
        if not x_raw and self.live_plot_x_combo is not None:
            x_raw = (self.live_plot_x_combo.currentText() or "").strip()
        if not y_raw and self.live_plot_y_combo is not None:
            y_raw = (self.live_plot_y_combo.currentText() or "").strip()
        return (
            self._resolve_live_plot_column(x_raw),
            self._resolve_live_plot_column(y_raw),
        )
    def _expert_corrected_xy_for_sheet(
        self,
        sheet_name: str,
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
    ) -> tuple[np.ndarray, np.ndarray, str]:
        """Return Expert Mode X/Y values, applying h-h0 correction for displacement-like X columns."""
        x_values = pd.to_numeric(df[x_col], errors="coerce").replace([np.inf, -np.inf], np.nan)
        y_values = pd.to_numeric(df[y_col], errors="coerce").replace([np.inf, -np.inf], np.nan)

        x_label = self._live_plot_label(x_col)
        x_col_lower = str(x_col).lower()

        test_number = self._test_number_from_sheet_name(sheet_name)
        offset = 0.0

        is_displacement_x = (
            "displacement into surface" in x_col_lower
            or "displacement" in x_col_lower
            or x_col_lower.strip() in {"h", "depth"}
        )

        if is_displacement_x and test_number is not None:
            offset_candidate = self.csm_offsets.get(test_number)

            if offset_candidate is None and self.current_results:
                for idx, result in enumerate(self.current_results):
                    if self._test_number_from_result(result, idx) == test_number:
                        offset_candidate = result.get("Loading Offset h0 (nm)")
                        break

            try:
                offset_float = float(offset_candidate)
                if np.isfinite(offset_float):
                    offset = offset_float
            except (TypeError, ValueError):
                offset = 0.0

            x_values = x_values - offset
            x_label = "Corrected displacement h - h0 (nm)"

        valid = np.isfinite(x_values.to_numpy(dtype=float)) & np.isfinite(y_values.to_numpy(dtype=float))
        x = x_values[valid].to_numpy(dtype=float)
        y = y_values[valid].to_numpy(dtype=float)
        if x.size and y.size:
            magnitude_ok = (np.abs(x) < 1e12) & (np.abs(y) < 1e12)
            x = x[magnitude_ok]
            y = y[magnitude_ok]

        return x, y, x_label
    def update_live_variable_plot(self):
        """Render the Expert Mode Plotly chart only when the user clicks the plot button."""
        if self.live_plot_widget is None:
            return

        self.live_plot_has_rendered = True
        if not PLOTLY_AVAILABLE or go is None:
            self._set_expert_plot_html(
                "<div class='placeholder'><h1>Plotly unavailable</h1>"
                "<p>Install plotly to render Expert Mode plots.</p></div>"
            )
            return

        source = self._selected_live_plot_source()
        x_col, y_col = self._selected_live_plot_columns()

        if source == "__all_tests__":
            try:
                self._plot_all_test_sheets(x_col, y_col)
            except Exception as exc:
                self._set_expert_plot_html(
                    "<div class='placeholder'><h1>Expert plot error</h1>"
                    f"<p>{str(exc)}</p></div>"
                )
                if self.live_plot_status_label is not None:
                    self.live_plot_status_label.setText(f"Could not render Expert plot: {str(exc)}")
            return

        if self.live_plot_data is None or self.live_plot_data.empty:
            self._set_expert_plot_html(
                "<div class='placeholder'><h1>No file variables loaded</h1>"
                "<p>Load a file in Step 2 and refresh Expert Mode.</p></div>"
            )
            return

        if not x_col or not y_col or x_col not in self.live_plot_data.columns or y_col not in self.live_plot_data.columns:
            self._set_expert_plot_html(
                "<div class='placeholder'><h1>Choose both X and Y variables</h1></div>"
            )
            return

        try:
            sheet_name = self.live_plot_sheet_combo.currentText() if self.live_plot_sheet_combo else ""
            x, y, x_axis_label = self._expert_corrected_xy_for_sheet(
                sheet_name,
                self.live_plot_data,
                x_col,
                y_col,
            )
        except Exception as exc:
            self._set_expert_plot_html(
                "<div class='placeholder'><h1>Expert plot error</h1>"
                f"<p>{str(exc)}</p></div>"
            )
            if self.live_plot_status_label is not None:
                self.live_plot_status_label.setText(f"Could not render Expert plot: {str(exc)}")
            return

        if x.size < 2 or y.size < 2:
            self._set_expert_plot_html(
                "<div class='placeholder'><h1>Not enough numeric points</h1>"
                "<p>Selected columns do not have enough numeric values.</p></div>"
            )
            if self.live_plot_status_label is not None:
                self.live_plot_status_label.setText(
                    f"Cannot plot '{x_col}' vs '{y_col}': not enough numeric rows."
                )
            return

        use_custom_ranges = bool(
            self.live_plot_use_ranges_cb
            and self.live_plot_use_ranges_cb.isChecked()
        )
        signature = (source, x_col, y_col)
        self._set_expert_range_fields(x, y, x_col, y_col, signature)
        if use_custom_ranges:
            xmin = self.live_plot_xmin_spin.value() if self.live_plot_xmin_spin else None
            xmax = self.live_plot_xmax_spin.value() if self.live_plot_xmax_spin else None
            ymin = self.live_plot_ymin_spin.value() if self.live_plot_ymin_spin else None
            ymax = self.live_plot_ymax_spin.value() if self.live_plot_ymax_spin else None
            if not np.isfinite([xmin, xmax, ymin, ymax]).all():
                self._set_expert_plot_html(
                    "<div class='placeholder'><h1>Invalid axis range</h1>"
                    "<p>Axis limits must be finite numeric values.</p></div>"
                )
                if self.live_plot_status_label is not None:
                    self.live_plot_status_label.setText("Invalid axis range: limits must be finite numeric values.")
                return
            if xmin is not None and xmax is not None and xmin >= xmax:
                self._set_expert_plot_html(
                    "<div class='placeholder'><h1>Invalid X range</h1>"
                    "<p>X-axis minimum must be less than maximum.</p></div>"
                )
                if self.live_plot_status_label is not None:
                    self.live_plot_status_label.setText("Invalid X range: minimum must be less than maximum.")
                return
            if ymin is not None and ymax is not None and ymin >= ymax:
                self._set_expert_plot_html(
                    "<div class='placeholder'><h1>Invalid Y range</h1>"
                    "<p>Y-axis minimum must be less than maximum.</p></div>"
                )
                if self.live_plot_status_label is not None:
                    self.live_plot_status_label.setText("Invalid Y range: minimum must be less than maximum.")
                return
            if self._points_inside_ranges(x, y, xmin, xmax, ymin, ymax) == 0:
                self._set_expert_plot_html(
                    "<div class='placeholder'><h1>No data in custom range</h1>"
                    "<p>Adjust X/Y limits or clear 'Use custom axis ranges'.</p></div>"
                )
                if self.live_plot_status_label is not None:
                    self.live_plot_status_label.setText(
                        "Custom axis ranges hide all plotted points. Adjust the limits and show the plot again."
                    )
                return

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode="lines",
            name=self.live_plot_sheet_combo.currentText() if self.live_plot_sheet_combo else "Selected sheet",
            line=dict(color="#0b3d91", width=3.4, dash="solid", shape="linear"),
            hovertemplate=(
                f"{x_axis_label}: %{{x:.6g}}<br>"
                f"{self._live_plot_label(y_col)}: %{{y:.6g}}"
                "<extra>%{fullData.name}</extra>"
            ),
        ))

        lsq_status = ""
        lsq_fit = None
        if (
            self.live_plot_lsq_fit_cb is not None
            and self.live_plot_lsq_fit_cb.isChecked()
            and source != "__all_tests__"
        ):
            degree = self.live_plot_lsq_degree_spin.value() if self.live_plot_lsq_degree_spin else 1
            lsq_fit, lsq_error = self._lsq_polynomial_fit(x, y, degree)
            if lsq_fit is None:
                lsq_status = lsq_error
            else:
                fit_name = f"LSQ polynomial degree {lsq_fit['degree']}"
                fig.add_trace(go.Scatter(
                    x=lsq_fit["x_fit"],
                    y=lsq_fit["y_fit"],
                    mode="lines",
                    name=fit_name,
                    line=dict(color="#b00020", width=3.0, dash="solid", shape="linear"),
                    hovertemplate=(
                        f"{x_axis_label}: %{{x:.6g}}<br>"
                        f"LSQ fit {self._live_plot_label(y_col)}: %{{y:.6g}}"
                        f"<extra>{fit_name}</extra>"
                    ),
                ))
                if lsq_fit["roots"]:
                    root_text = ", ".join(f"{root:.6g}" for root in lsq_fit["roots"])
                    lsq_status = f"LSQ y=0 x-intercept: {root_text}"
                    y_marker_min = float(ymin) if use_custom_ranges else float(np.nanmin(y))
                    y_marker_max = float(ymax) if use_custom_ranges else float(np.nanmax(y))
                    if not np.isfinite(y_marker_min) or not np.isfinite(y_marker_max) or y_marker_min == y_marker_max:
                        y_marker_min, y_marker_max = -1.0, 1.0
                    for root in lsq_fit["roots"]:
                        if not np.isfinite(root):
                            continue
                        fig.add_trace(go.Scatter(
                            x=[root, root],
                            y=[y_marker_min, y_marker_max],
                            mode="lines",
                            name=f"y=0 x={root:.4g}",
                            line=dict(color="#b00020", width=1.4, dash="solid"),
                            hoverinfo="skip",
                            showlegend=False,
                        ))
                else:
                    lo, hi = lsq_fit["x_range"]
                    lsq_status = f"LSQ fit has no y=0 crossing between x={lo:.6g} and x={hi:.6g}."
                if lsq_error:
                    lsq_status = f"{lsq_status} {lsq_error}"

        title = f"Custom Plot: {self._live_plot_label(y_col)} vs {x_axis_label}"
        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
            title=title,
            xaxis_title=x_axis_label,
            yaxis_title=self._live_plot_label(y_col),
            margin=dict(l=64, r=32, t=56, b=56),
            legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#d6dbe0", borderwidth=1),
        )
        if use_custom_ranges:
            fig.update_xaxes(range=[xmin, xmax])
            fig.update_yaxes(range=[ymin, ymax])
        if lsq_fit is not None:
            zero_visible = not use_custom_ranges or (ymin <= 0 <= ymax)
            if zero_visible:
                x0, x1 = lsq_fit["x_range"]
                if np.isfinite(x0) and np.isfinite(x1) and x0 != x1:
                    fig.add_trace(go.Scatter(
                        x=[x0, x1],
                        y=[0, 0],
                        mode="lines",
                        name="y=0",
                        line=dict(color="#8a949b", width=1.2, dash="solid"),
                        hoverinfo="skip",
                        showlegend=False,
                    ))
        self._set_expert_plot_html(fig.to_html(full_html=True, include_plotlyjs=True, config={"responsive": True}), already_full_html=True)

        if self.live_plot_status_label is not None:
            range_note = " with custom ranges" if use_custom_ranges else ""
            status = f"Plotting {len(x)} numeric rows: {self._live_plot_label(y_col)} vs {x_axis_label}{range_note}."
            if lsq_status:
                status += f" {lsq_status}"
            self.live_plot_status_label.setText(status)
        if self.live_plot_lsq_status_label is not None and lsq_status:
            self.live_plot_lsq_status_label.setText(lsq_status)

    def _plot_all_test_sheets(self, x_col: str, y_col: str):
        selected_sheets = self.selected_expert_test_sheets()
        if not self.live_plot_file_path or not self.live_plot_test_sheets:
            self._set_expert_plot_html(
                "<div class='placeholder'><h1>No Test sheets found</h1>"
                "<p>The selected file does not contain Test ### sheets.</p></div>"
            )
            return
        if not selected_sheets:
            self._set_expert_plot_html(
                "<div class='placeholder'><h1>No Expert Mode tests selected</h1>"
                "<p>Use the Load tab / Curve Viewer selection to include tests.</p></div>"
            )
            if self.live_plot_status_label is not None:
                self.live_plot_status_label.setText(
                    "No Expert Mode tests selected. Include tests from the Load tab / Curve Viewer."
                )
            return

        if not x_col or not y_col:
            self._set_expert_plot_html(
                "<div class='placeholder'><h1>Choose both X and Y variables</h1></div>"
            )
            return

        use_custom_ranges = bool(
            self.live_plot_use_ranges_cb
            and self.live_plot_use_ranges_cb.isChecked()
        )
        xmin = self.live_plot_xmin_spin.value() if self.live_plot_xmin_spin else None
        xmax = self.live_plot_xmax_spin.value() if self.live_plot_xmax_spin else None
        ymin = self.live_plot_ymin_spin.value() if self.live_plot_ymin_spin else None
        ymax = self.live_plot_ymax_spin.value() if self.live_plot_ymax_spin else None
        if use_custom_ranges:
            if not np.isfinite([xmin, xmax, ymin, ymax]).all():
                self._set_expert_plot_html(
                    "<div class='placeholder'><h1>Invalid axis range</h1>"
                    "<p>Axis limits must be finite numeric values.</p></div>"
                )
                if self.live_plot_status_label is not None:
                    self.live_plot_status_label.setText("Invalid axis range: limits must be finite numeric values.")
                return
            if xmin is not None and xmax is not None and xmin >= xmax:
                self._set_expert_plot_html(
                    "<div class='placeholder'><h1>Invalid X range</h1>"
                    "<p>X-axis minimum must be less than maximum.</p></div>"
                )
                if self.live_plot_status_label is not None:
                    self.live_plot_status_label.setText("Invalid X range: minimum must be less than maximum.")
                return
            if ymin is not None and ymax is not None and ymin >= ymax:
                self._set_expert_plot_html(
                    "<div class='placeholder'><h1>Invalid Y range</h1>"
                    "<p>Y-axis minimum must be less than maximum.</p></div>"
                )
                if self.live_plot_status_label is not None:
                    self.live_plot_status_label.setText("Invalid Y range: minimum must be less than maximum.")
                return

        plotted = 0
        all_x = []
        all_y = []
        fig = go.Figure()
        color_cycle = [
            "#0b3d91",
            "#b00020",
            "#006d3b",
            "#6f2dbd",
            "#c45a00",
            "#007c89",
            "#3d4756",
            "#111827",
        ]
        x_axis_label = self._live_plot_label(x_col)
        for sheet_name in selected_sheets:
            try:
                df, _units = self._load_live_plot_sheet(self.live_plot_file_path, sheet_name)
            except Exception:
                continue
            if x_col not in df.columns or y_col not in df.columns:
                continue
            x, y, x_axis_label = self._expert_corrected_xy_for_sheet(
                sheet_name,
                df,
                x_col,
                y_col,
            )
            if x.size < 2 or y.size < 2:
                continue
            label = sheet_name.replace("Test ", "")
            fig.add_trace(go.Scatter(
                x=x,
                y=y,
                mode="lines",
                name=label,
                line=dict(width=2.8, color=color_cycle[plotted % len(color_cycle)], dash="solid", shape="linear"),
                opacity=1,
                hovertemplate=(
                    f"{x_axis_label}: %{{x:.6g}}<br>"
                    f"{self._live_plot_label(y_col)}: %{{y:.6g}}"
                    "<extra>Test %{fullData.name}</extra>"
                ),
            ))
            all_x.extend(x.tolist())
            all_y.extend(y.tolist())
            plotted += 1

        if plotted == 0:
            self._set_expert_plot_html(
                f"<div class='placeholder'><h1>No numeric data found</h1>"
                f"<p>No numeric data found for {y_col} vs {x_col}.</p></div>"
            )
            if self.live_plot_status_label is not None:
                self.live_plot_status_label.setText("No valid numeric data found for the selected variables.")
            return

        if use_custom_ranges and self._points_inside_ranges(all_x, all_y, xmin, xmax, ymin, ymax) == 0:
            self._set_expert_plot_html(
                "<div class='placeholder'><h1>No data in custom range</h1>"
                "<p>Adjust X/Y limits or clear 'Use custom axis ranges'.</p></div>"
            )
            if self.live_plot_status_label is not None:
                self.live_plot_status_label.setText(
                    "Custom axis ranges hide all plotted points. Adjust the limits and show the plot again."
                )
            return

        signature = ("__all_tests__", x_col, y_col)
        self._set_expert_range_fields(all_x, all_y, x_col, y_col, signature)
        fig.update_layout(
            template="plotly_white",
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
            title=f"Selected Expert Tests: {self._live_plot_label(y_col)} vs {x_axis_label}",
            xaxis_title=x_axis_label,
            yaxis_title=self._live_plot_label(y_col),
            margin=dict(l=64, r=32, t=56, b=56),
            legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#d6dbe0", borderwidth=1),
        )
        if use_custom_ranges:
            fig.update_xaxes(range=[xmin, xmax])
            fig.update_yaxes(range=[ymin, ymax])
        self._set_expert_plot_html(fig.to_html(full_html=True, include_plotlyjs=True, config={"responsive": True}), already_full_html=True)

        if self.live_plot_status_label is not None:
            range_note = " with custom ranges" if use_custom_ranges else ""
            self.live_plot_status_label.setText(
                f"Overlaying {plotted}/{len(self.live_plot_test_sheets)} selected Expert tests: "
                f"{self._live_plot_label(y_col)} vs {x_axis_label}{range_note}."
            )
    
    def browse_file(self):
        """Open file dialog to select Excel file"""
        samples_dir = str(self.samples_dir())
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Nanoindentation Data File",
            samples_dir,
            self.file_dialog_filter_for_loader()
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
            self.update_header_experiment_file(file_path)
            self.csm_file_path = file_path
            self.reload_button.setEnabled(True)
            if self.generate_curves_button:
                self.generate_curves_button.setEnabled(True)
            self.analyze_button.setEnabled(False)
            self.step2_next_button.setEnabled(False)
            self.current_results.clear()
            self.csm_results = None
            self.csm_offsets.clear()
            self.file_load_offsets.clear()
            self.overlay_curve_cache.clear()
            self.overlay_sheet_names_cache.clear()
            self.op_overlay_cutoff_user_set = False
            self.clear_step4_plot_buttons()
            self.results_table.setRowCount(0)
            self.update_expert_offsets_status()
            if self.workflow_tabs:
                for idx in range(2, min(5, self.workflow_tabs.count())):
                    self.workflow_tabs.setTabEnabled(idx, False)
                self._sync_workflow_top_tabs()
            self.unlock_workflow_tab("Expert Mode")
            self.update_readiness_summary()
            self.refresh_live_plot_source()
            self.append_research_log(f"Selected experiment file: {file_path}", "File")
            self.append_research_log(
                "File selected. Click Generate Test Curves to create loading/unloading review plots "
                "and file-load h0 offsets for Expert Mode.",
                "Workflow"
            )
            self.status_bar.showMessage(f"File selected: {Path(file_path).name}. Click Generate Test Curves to start.")
            self.update_results_summary_strip()
    
    def reload_file(self):
        """Reload the current file"""
        if self.file_path_edit.text():
            self.append_research_log(
                f"Reloading selected file and regenerating loading curves: {self.file_path_edit.text()}",
                "File"
            )
            self.refresh_live_plot_source()
            self.status_bar.showMessage("Reloading file and regenerating plots...")
            self.generate_loading_curves_for_selection()

    def generate_loading_curves_for_selection(self):
        """Always run loading-curve generation for test selection, regardless of mode."""
        self.start_analysis(force_loading_curves=True)

    def start_analysis(self, force_loading_curves: bool = False):
        """Start the nanoindentation analysis"""
        file_path = self.file_path_edit.text()
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Error", "Please select a valid Excel file.")
            return
        if self.get_selected_analysis_type() == "CSM" and not force_loading_curves:
            self.run_csm_analysis()
            return
        
        try:
            self.current_analysis_file_path = str(Path(file_path).resolve())
            self.overlay_curve_cache.clear()
            self.overlay_sheet_names_cache.clear()
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
            if force_loading_curves:
                self.csm_offsets.clear()
                self.file_load_offsets.clear()
            self._sync_expert_offsets_table()
            self.results_table.setRowCount(0)
            self.clear_plot_tabs(clear_exclusions=force_loading_curves)
            self.update_results_summary_strip()
            self.update_expert_offsets_status()
            self.last_run_context = "loading_curves" if force_loading_curves else "oliver_pharr"
            
            # Setup UI for analysis
            self.analyze_button.setEnabled(False)
            if self.generate_curves_button:
                self.generate_curves_button.setEnabled(False)
            self.cancel_button.setEnabled(True)
            self.step4_next_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            if force_loading_curves:
                run_stamp = self._log_timestamp()
                self.log_widget.append(f"\n=== [{run_stamp}] Loading Curves / h0 Offset Run ===")
                self.append_research_log(
                    "Starting loading-curve generation. Purpose: inspect all tests, calculate loading h0 offsets, "
                    "and choose which tests are included in final calculations.",
                    "Run"
                )
            else:
                run_stamp = self._log_timestamp()
                self.log_widget.append(f"\n=== [{run_stamp}] Oliver-Pharr Run ===")
                self.append_research_log(
                    "Starting Oliver-Pharr analysis for the currently included tests.",
                    "Run"
                )
            self.append_research_log(f"Experiment file: {file_path}", "Run")
            if self.sample_name_edit and self.sample_name_edit.text().strip():
                self.append_research_log(f"Sample label: {self.sample_name_edit.text().strip()}", "Run")
            if self.research_goal_combo:
                self.append_research_log(f"Research goal: {self.research_goal_combo.currentText()}", "Run")
            self.append_research_log(f"Tip area calibration source: {self.calibration_source}", "Run")
            if self.pending_analysis_context:
                self.append_research_log(f"Context: {self.pending_analysis_context}", "Run")
                self.pending_analysis_context = None
            self.append_research_log(
                f"Analysis settings: generate plots={self.generate_plots_cb.isChecked()}, "
                f"export plots={self.export_plots_cb.isChecked()}, minimum accepted fit R²={self.min_r2_spinbox.value()}, "
                f"Fit segment={self.fit_curve_percent_spinbox.value() if self.fit_curve_percent_spinbox else 25.0}%, "
                f"file loader={self.selected_file_loader_name}.",
                "Run"
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
                fit_percent=self.fit_curve_percent_spinbox.value() if self.fit_curve_percent_spinbox else 25.0,
                file_loader_name=self.selected_file_loader_name
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
            original_df = test_data.get('data_processing', {}).get('original_data', pd.DataFrame())
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
            full_raw_loading_disp = list(raw_loading_disp)
            full_raw_loading_load = list(raw_loading_load)
            full_raw_unloading_disp = list(raw_unloading_disp)
            full_raw_unloading_load = list(raw_unloading_load)
            if isinstance(original_df, pd.DataFrame) and {"Load (mN)", "Displacement (nm)"}.issubset(original_df.columns):
                full_df = original_df[["Displacement (nm)", "Load (mN)"]].copy()
                full_df["Displacement (nm)"] = pd.to_numeric(full_df["Displacement (nm)"], errors="coerce")
                full_df["Load (mN)"] = pd.to_numeric(full_df["Load (mN)"], errors="coerce")
                full_df = full_df.replace([np.inf, -np.inf], np.nan).dropna()
                if not full_df.empty:
                    peak_pos = int(np.argmax(full_df["Load (mN)"].to_numpy(dtype=float)))
                    full_loading_df = full_df.iloc[:peak_pos + 1]
                    full_unloading_df = full_df.iloc[peak_pos:]
                    full_raw_loading_disp = full_loading_df["Displacement (nm)"].tolist()
                    full_raw_loading_load = full_loading_df["Load (mN)"].tolist()
                    full_raw_unloading_disp = full_unloading_df["Displacement (nm)"].tolist()
                    full_raw_unloading_load = full_unloading_df["Load (mN)"].tolist()
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
                'Full Raw Loading Displacement (nm)': full_raw_loading_disp,
                'Full Raw Loading Load (mN)': full_raw_loading_load,
                'Full Raw Unloading Displacement (nm)': full_raw_unloading_disp,
                'Full Raw Unloading Load (mN)': full_raw_unloading_load,
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
        self.append_research_log(message, "Status")
        # Auto-scroll to bottom
        self.log_widget.verticalScrollBar().setValue(
            self.log_widget.verticalScrollBar().maximum()
        )
    
    def handle_results(self, results: Any):
        """Handle analysis results"""
        total_tests = len(results.get('tests', {})) if isinstance(results, dict) else None
        previous_excluded_numbers = set(self.excluded_test_numbers)
        previous_excluded_indices = set(self.excluded_test_indices)
        preserve_user_exclusions = self.last_run_context != "loading_curves"
        use_index_fallback = preserve_user_exclusions and not previous_excluded_numbers
        normalized_results = self.normalize_results_for_gui(results)
        if self.last_run_context == "loading_curves":
            self._snapshot_file_load_offsets(normalized_results)
            self.csm_offsets.clear()
        self.excluded_test_indices.clear()
        self.excluded_test_numbers.clear()
        self.current_results = normalized_results
        if preserve_user_exclusions:
            for idx, result in enumerate(self.current_results):
                test_number = self._test_number_from_result(result, idx)
                if (
                    (test_number is not None and test_number in previous_excluded_numbers)
                    or (use_index_fallback and idx in previous_excluded_indices)
                ):
                    self.excluded_test_indices.add(idx)
                    if test_number is not None:
                        self.excluded_test_numbers.add(test_number)
        applied_expert_offsets = 0
        if self.last_run_context != "loading_curves":
            applied_expert_offsets = self._apply_expert_offsets_to_current_results()
        self._sync_expert_offsets_table()
        
        if normalized_results:
            included_results = self.get_included_results()
            # Load results into table
            self.results_table.load_results(included_results)
            
            loading_curve_preview = self.last_run_context == "loading_curves"
            self.export_excel_button.setEnabled(not loading_curve_preview)
            self.export_csv_button.setEnabled(not loading_curve_preview)
            self.unlock_workflow_step(2)
            self.unlock_workflow_step(3)
            if not loading_curve_preview:
                self.unlock_workflow_step(4)
            self.unlock_workflow_tab("Expert Mode")
            self.unlock_workflow_tab("Log")
            if self.step2_next_button:
                self.step2_next_button.setEnabled(True)
            self.step4_next_button.setEnabled(not loading_curve_preview)
            
            # Log summary
            self.log_widget.append("=" * 60)
            if self.last_run_context == "loading_curves":
                self.append_research_log(
                    "Loading curves and file-load h0 offsets generated successfully.",
                    "Result"
                )
            elif self.last_run_context == "csm":
                self.append_research_log("CSM analysis completed successfully.", "Result")
            else:
                self.append_research_log("Oliver-Pharr analysis completed successfully.", "Result")
            self.append_research_log(
                f"Analyzed tests accepted for review: {len(normalized_results)}; "
                f"{len(included_results)} currently included after user exclusions.",
                "Result"
            )
            if applied_expert_offsets:
                self.append_research_log(
                    f"Applied edited Expert Mode h0 offsets to {applied_expert_offsets} result record(s). "
                    "These offsets are now used for corrected displacement plots, CSM offset correction, "
                    "and exported result values.",
                    "Result"
                )
            if total_tests is not None and self.min_r2_spinbox:
                excluded = max(total_tests - len(normalized_results), 0)
                self.append_research_log(
                    f"Fit quality filter: minimum R²={self.min_r2_spinbox.value():.3f}; "
                    f"{len(normalized_results)} tests accepted and {excluded} excluded.",
                    "Result"
                )
            
            self.log_final_calculation_summary(included_results)
            self.update_results_summary_strip()
            
            if normalized_results:
                self.create_plot_tabs(normalized_results)
                if not loading_curve_preview:
                    self._show_workflow_results("Reliability")
        
        else:
            self.log_widget.append("⚠️ No valid results obtained from analysis")
            self.update_results_summary_strip()
        self._configure_results_panel_visibility()
    
    def handle_error(self, error_message: str):
        """Handle analysis errors"""
        self.log_widget.append(f"❌ Error: {error_message}")
        QMessageBox.critical(self, "Analysis Error", error_message)
    
    def analysis_finished(self):
        """Clean up after analysis finishes"""
        self.analyze_button.setEnabled(bool(self.file_path_edit.text()))
        if self.generate_curves_button:
            self.generate_curves_button.setEnabled(bool(self.file_path_edit.text()))
        self.cancel_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        if self.analysis_worker:
            self.analysis_worker.deleteLater()
            self.analysis_worker = None
    
    def export_to_excel(self):
        """Export results to Excel file"""
        if self.get_selected_analysis_type() == "CSM":
            self.export_csm_excel()
            return
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
        if self.get_selected_analysis_type() == "CSM":
            self.export_csm_csv()
            return
        included_results = self.get_included_results()
        if not included_results:
            QMessageBox.warning(self, "No Data", "No analysis results to export.")
            return
        
        samples_dir = str(self.samples_dir())
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
