#!/bin/bash
# Nanoindentation Analysis Application Launcher
# Launches the restructured nanoindentation analysis GUI

echo "🔬 Launching Nanoindentation Analysis GUI..."
echo "📁 Location: $(pwd)"
if [ -x ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
else
    PYTHON_BIN="$(which python3)"
fi
echo "🐍 Python: $PYTHON_BIN"
echo "🖥️  Display: $DISPLAY"
echo ""

# Stay in the current directory (where the script is located)
# cd "$(dirname "$0")/.."

# Check if required packages are installed
echo "Checking dependencies..."
"$PYTHON_BIN" -c "import PyQt5; print('✅ PyQt5 installed')" 2>/dev/null || { echo "❌ PyQt5 not found. Installing..."; "$PYTHON_BIN" -m pip install PyQt5; }
"$PYTHON_BIN" -c "import matplotlib; print('✅ matplotlib installed')" 2>/dev/null || { echo "❌ matplotlib not found. Installing..."; "$PYTHON_BIN" -m pip install matplotlib; }
"$PYTHON_BIN" -c "import pandas; print('✅ pandas installed')" 2>/dev/null || { echo "❌ pandas not found. Installing..."; "$PYTHON_BIN" -m pip install pandas; }
"$PYTHON_BIN" -c "import numpy; print('✅ numpy installed')" 2>/dev/null || { echo "❌ numpy not found. Installing..."; "$PYTHON_BIN" -m pip install numpy; }
"$PYTHON_BIN" -c "import scipy; print('✅ scipy installed')" 2>/dev/null || { echo "❌ scipy not found. Installing..."; "$PYTHON_BIN" -m pip install scipy; }
"$PYTHON_BIN" -c "import xlrd; print('✅ xlrd installed')" 2>/dev/null || { echo "❌ xlrd not found. Installing..."; "$PYTHON_BIN" -m pip install xlrd; }
"$PYTHON_BIN" -c "import plotly; print('✅ plotly installed')" 2>/dev/null || { echo "❌ plotly not found. Installing..."; "$PYTHON_BIN" -m pip install plotly; }
"$PYTHON_BIN" -c "from PyQt5.QtWebEngineWidgets import QWebEngineView; print('✅ PyQtWebEngine installed')" 2>/dev/null || { echo "❌ PyQtWebEngine not found. Installing..."; "$PYTHON_BIN" -m pip install PyQtWebEngine; }

echo ""
echo "🚀 Starting GUI application..."
echo "   • ISO 14577-4:2016 compliant analysis"
echo "   • Advanced tip calibration"
echo "   • Oliver-Pharr method"
echo "   • Quality validation"
echo "   • Restructured modular architecture"
echo ""

# Launch the GUI from the new structure
"$PYTHON_BIN" -c "
import sys
sys.path.insert(0, '.')
from src.gui.main_interface import NanoindentationGUI
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)
window = NanoindentationGUI()
window.show()
sys.exit(app.exec_())
"

echo ""
echo "👋 GUI application closed."
