# 🔬 Nanoindentation Analysis GUI

A comprehensive PyQt5 graphical user interface for the sophisticated nanoindentation analysis system. This GUI provides an intuitive interface for your advanced `FixedIndentXLSAnalyzer` with full ISO 14577-4:2016 compliance.

## 🚀 Features

### Analysis Capabilities
- **ISO 14577-4:2016 Compliant**: Full compliance with international nanoindentation standards
- **Advanced Tip Calibration**: Sophisticated area function calibration using multiple reference measurements
- **Oliver-Pharr Method**: Industry-standard analysis with calibrated contact area calculations
- **Power Law & Polynomial Fitting**: Advanced curve fitting with quality validation
- **Horizontal Segment Detection**: Automatic detection and correction of instrument drift
- **Quality Validation**: Comprehensive R² analysis and compliance scoring

### GUI Features
- **Intuitive Interface**: User-friendly design with organized control panels
- **Real-time Progress**: Live progress tracking during analysis
- **Multi-threaded**: Non-blocking analysis using worker threads
- **Interactive Plots**: Matplotlib integration with zoom and pan capabilities
- **Results Table**: Sortable, searchable results with detailed measurements
- **Export Options**: Excel and CSV export functionality
- **Analysis Logging**: Detailed log of analysis progress and results

## 📋 Requirements

- Python 3.8+
- PyQt5
- matplotlib
- pandas
- numpy
- scipy
- openpyxl (for Excel export)

## 🛠️ Installation

### Automatic Installation
The launcher script will automatically check and install dependencies:

```bash
./launch_gui.sh
```

### Manual Installation
If you prefer to install dependencies manually:

```bash
pip install PyQt5 matplotlib pandas numpy scipy openpyxl
```

## 🎯 Usage

### Quick Start

1. **Launch the GUI**:
   ```bash
   ./launch_gui.sh
   ```
   or
   ```bash
   python nanoindentation_gui.py
   ```

2. **Select Data File**:
   - Click "📁 Browse" to select your Excel file
   - The file should contain nanoindentation data with multiple test sheets

3. **Configure Settings**:
   - **Generate Plots**: Enable/disable plot generation
   - **Export Plots**: Save plots as PNG files
   - **Min R² for fits**: Set minimum R-squared threshold (default: 0.98)

4. **Start Analysis**:
   - Click "🔬 Start Analysis" to begin
   - Monitor progress in the status bar and log tab
   - Results will appear in the results table when complete

5. **Export Results**:
   - Use "📊 Export to Excel" or "📄 Export to CSV"
   - Choose your preferred export location

### Interface Overview

#### Control Panel (Left)
- **📁 File Selection**: Browse and select data files
- **⚙️ Analysis Settings**: Configure analysis parameters
- **🚀 Analysis Control**: Start/cancel analysis operations
- **💾 Export Results**: Export data in various formats
- **ℹ️ Information**: Quick reference about capabilities

#### Results Panel (Right)
- **📊 Results Table**: Detailed tabular results with sorting
- **📈 Plots**: Interactive nanoindentation curves and analysis plots
- **📝 Analysis Log**: Real-time analysis progress and debugging information

## 📊 Data Format

The GUI expects Excel files with the following structure:
- **Results sheet**: Summary results with test numbers and hardness values
- **Test XX sheets**: Individual test data with columns:
  - `Displacement Into Surface` (nm)
  - `Load On Sample` (mN)
  - Additional columns as needed

## 🔍 Analysis Process

The GUI performs the following analysis steps:

### Phase 1: Data Collection for Tip Calibration
1. Loads all test data from Excel sheets
2. Performs initial curve fitting on each test
3. Collects contact depth and stiffness measurements
4. Prepares calibration dataset

### Phase 2: Tip Area Function Calibration
1. Analyzes collected measurements using fused silica reference
2. Calculates calibrated area function coefficients (C₀-C₈)
3. Validates calibration quality and generates correction factors
4. Displays calibration results and statistics

### Phase 3: Final Analysis with Calibrated Tip
1. Re-analyzes all tests using calibrated area function
2. Applies ISO 14577-4:2016 quality validation
3. Performs Oliver-Pharr analysis with corrected contact areas
4. Generates comprehensive results with compliance scoring

## 📈 Results

### Key Measurements
- **Hardness (GPa)**: Calibrated hardness using area function
- **Oliver-Pharr Hardness (GPa)**: Standard Oliver-Pharr calculation
- **Oliver-Pharr Modulus (GPa)**: Reduced elastic modulus
- **Contact Area (m²)**: Calibrated contact area
- **Contact Stiffness (N/m)**: Elastic contact stiffness
- **Loading/Unloading R²**: Curve fit quality metrics

### Quality Indicators
- **Loading R²**: Quality of loading curve fit (ISO min: 0.98)
- **Unloading R²**: Quality of unloading curve fit
- **Calibration Factor**: Tip calibration correction factor
- **ISO Compliance**: Overall compliance with ISO 14577-4:2016

## 🎨 Plotting Features

The GUI generates comprehensive plots including:
- Loading and unloading curves with fitted models
- Oliver-Pharr depth annotations (hc, hs, he)
- Contact stiffness visualization
- Fitted parameters display
- Area function calibration information
- Quality metrics and compliance indicators

## 🔧 Troubleshooting

### Common Issues

**GUI doesn't start**:
- Ensure PyQt5 is installed: `pip install PyQt5`
- Check Python version (3.8+ required)
- Try running directly: `python nanoindentation_gui.py`

**Analysis fails**:
- Check Excel file format and structure
- Ensure test sheets exist (Test 01, Test 02, etc.)
- Verify data columns have correct names
- Check the Analysis Log tab for detailed error messages

**Plots not displaying**:
- Ensure matplotlib backend is compatible
- Check "Generate Plots" setting is enabled
- Try different matplotlib backends if needed

**Export fails**:
- Ensure write permissions to target directory
- Check that openpyxl is installed for Excel export
- Verify file is not open in another application

### Performance Tips

- **Large datasets**: Consider analyzing subsets of tests for initial validation
- **Memory usage**: Close other applications if analysis uses significant memory
- **Plot performance**: Disable plot generation for batch processing of many files

## 🏗️ Architecture

### GUI Components
- **NanoindentationGUI**: Main application window
- **AnalysisWorker**: Background thread for analysis execution
- **MatplotlibWidget**: Embedded plotting widget
- **ResultsTableWidget**: Enhanced results display table

### Integration
- **FixedIndentXLSAnalyzer**: Your sophisticated analysis engine
- **Thread Safety**: Analysis runs in separate thread to prevent GUI freezing
- **Error Handling**: Comprehensive error catching and user feedback

## 📝 Example Workflow

1. **Launch**: `./launch_gui.sh`
2. **Load Data**: Browse to `HEC14S1.xls`
3. **Configure**: Set R² threshold to 0.98
4. **Analyze**: Click "Start Analysis"
5. **Review**: Check results table and plots
6. **Export**: Save results as Excel file
7. **Repeat**: Load different file or adjust settings

## 🤝 Integration with Existing Code

The GUI seamlessly integrates with your existing `run_hec14s1_analysis.py` script:
- Uses your `FixedIndentXLSAnalyzer` class directly
- Preserves all sophisticated analysis logic
- Maintains ISO 14577-4:2016 compliance
- Keeps advanced tip calibration features
- Provides same quality results with better user experience

## 📜 License

This GUI interface extends your existing nanoindentation analysis system and follows the same licensing terms as your research code.

---

**Happy Analyzing! 🔬✨**

For questions or issues, refer to the Analysis Log tab in the GUI for detailed diagnostic information.
