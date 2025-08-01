#!/usr/bin/env python3
"""Quick Launch - Compact Version"""
import sys, os
sys.path.insert(0, '.')

try:
    from src.gui.main_interface import NanoindentationGUI
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    gui = NanoindentationGUI()
    gui.show()
    sys.exit(app.exec_())
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Install requirements: pip install PyQt5 matplotlib pandas numpy scipy xlrd")
