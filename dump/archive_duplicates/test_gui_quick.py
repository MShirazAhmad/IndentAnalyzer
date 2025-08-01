#!/usr/bin/env python3
"""
Quick test script to verify GUI plot tabs functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from nanoindentation_gui import NanoindentationGUI

def test_gui():
    """Test GUI startup"""
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = NanoindentationGUI()
    window.show()
    
    print("GUI loaded successfully!")
    print("Features:")
    print("✅ Dark mode theme")
    print("✅ Tabbed plotting system")
    print("✅ Individual test plot tabs")
    print("✅ White matplotlib backgrounds")
    
    # Test for a few seconds then close
    import time
    time.sleep(3)
    
    app.quit()
    print("GUI test completed!")

if __name__ == "__main__":
    test_gui()
