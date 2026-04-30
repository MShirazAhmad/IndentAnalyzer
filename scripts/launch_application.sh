#!/bin/bash
# Nanoindentation Analysis Application Launcher
# Launches the restructured nanoindentation analysis GUI

echo "🔬 Launching Nanoindentation Analysis GUI..."
echo "📁 Location: $(pwd)"
echo "🐍 Python: $(which python3)"
echo "🖥️  Display: $DISPLAY"
echo ""

# Stay in the current directory (where the script is located)
# cd "$(dirname "$0")/.."

# Check if required packages are installed
echo "Checking dependencies..."
python3 -c "import PyQt5; print('✅ PyQt5 installed')" 2>/dev/null || { echo "❌ PyQt5 not found. Installing..."; pip3 install PyQt5; }
python3 -c "import matplotlib; print('✅ matplotlib installed')" 2>/dev/null || { echo "❌ matplotlib not found. Installing..."; pip3 install matplotlib; }
python3 -c "import pandas; print('✅ pandas installed')" 2>/dev/null || { echo "❌ pandas not found. Installing..."; pip3 install pandas; }
python3 -c "import numpy; print('✅ numpy installed')" 2>/dev/null || { echo "❌ numpy not found. Installing..."; pip3 install numpy; }
python3 -c "import scipy; print('✅ scipy installed')" 2>/dev/null || { echo "❌ scipy not found. Installing..."; pip3 install scipy; }
python3 -c "import xlrd; print('✅ xlrd installed')" 2>/dev/null || { echo "❌ xlrd not found. Installing..."; pip3 install xlrd; }

echo ""
echo "🚀 Starting GUI application..."
echo "   • ISO 14577-4:2016 compliant analysis"
echo "   • Advanced tip calibration"
echo "   • Oliver-Pharr method"
echo "   • Quality validation"
echo "   • Restructured modular architecture"
echo ""

# Launch the GUI from the new structure
python3 -c "
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
