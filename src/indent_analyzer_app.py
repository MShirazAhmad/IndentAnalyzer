#!/usr/bin/env python3
"""macOS app entry point for the PyInstaller bundle."""

from __future__ import annotations

import sys
import os
from pathlib import Path
from tempfile import gettempdir

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    sys.path.insert(0, str(Path(sys._MEIPASS)))
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

APP_SUPPORT_DIR = Path.home() / "Library" / "Application Support" / "IndentAnalyzer"
try:
    APP_SUPPORT_DIR.mkdir(parents=True, exist_ok=True)
except OSError:
    APP_SUPPORT_DIR = Path(gettempdir()) / "IndentAnalyzer"
    APP_SUPPORT_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(APP_SUPPORT_DIR / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(APP_SUPPORT_DIR / "cache"))

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication

from src.gui.main_interface import NanoindentationGUI, resolve_app_icon_path


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("IndentAnalyzer")
    app.setApplicationDisplayName("IndentAnalyzer")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("IndentAnalyzer")

    icon_path = resolve_app_icon_path()
    if icon_path:
        from PyQt5.QtGui import QIcon

        app.setWindowIcon(QIcon(str(icon_path)))

    window = NanoindentationGUI()
    window.setWindowTitle("IndentAnalyzer")
    window.show()
    window.raise_()
    window.activateWindow()
    QTimer.singleShot(
        0,
        lambda: (
            window.setWindowState(window.windowState() & ~Qt.WindowMinimized),
            window.raise_(),
            window.activateWindow(),
        ),
    )
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
