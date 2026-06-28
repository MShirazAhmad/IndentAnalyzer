#!/usr/bin/env python3
"""Bundled FigureForge bridge for editing an IndentAnalyzer Matplotlib figure."""

from __future__ import annotations

import pickle
import os
import sys
import importlib.abc
import importlib.util
import faulthandler
from pathlib import Path

from matplotlib.figure import Figure
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QHBoxLayout, QPushButton, QWidget


def _smoke_trace(message: str):
    trace_path = os.environ.get("INDENTANALYZER_FIGUREFORGE_TRACE")
    if trace_path:
        with open(trace_path, "a", encoding="utf-8") as handle:
            handle.write(message + "\n")


_smoke_trace("bridge imported")
_trace_handle = None
if os.environ.get("INDENTANALYZER_FIGUREFORGE_TRACE"):
    _trace_handle = open(
        os.environ["INDENTANALYZER_FIGUREFORGE_TRACE"], "a", encoding="utf-8"
    )
    faulthandler.dump_traceback_later(15, repeat=True, file=_trace_handle)

# FigureForge 0.3.3 imports its initializer a second time under the synthetic
# name ``FigureForge.__init__`` before its root package defines resource paths.
# Supply that metadata module directly so frozen layouts use the real package
# directory and do not need a duplicate tree of Python plugin files.
class _FigureForgeMetadataLoader(importlib.abc.Loader):
    def exec_module(self, module):
        package_dir = Path(sys.modules["FigureForge"].__path__[0]).resolve()
        module.__version__ = "0.3.3"
        module.CURRENT_DIR = str(package_dir)
        module.ASSETS_DIR = str(package_dir / "resources" / "assets")
        module.ICONS_DIR = str(package_dir / "resources" / "icons")
        module.PLUGINS_DIR = str(package_dir / "plugins")


class _FigureForgeMetadataFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "FigureForge.__init__":
            return importlib.util.spec_from_loader(fullname, _FigureForgeMetadataLoader())
        return None


sys.meta_path.insert(0, _FigureForgeMetadataFinder())

_smoke_trace("before FigureForge GUI import")
import FigureForge
_smoke_trace("FigureForge package imported")
import qdarktheme
_smoke_trace("qdarktheme imported")
import FigureForge.dialogs.ff_dialogs
_smoke_trace("FigureForge dialogs imported")
import FigureForge.figure_manager
_smoke_trace("FigureForge manager imported")
import FigureForge.preferences
_smoke_trace("FigureForge preferences imported")
from FigureForge.gui import MainWindow
from FigureForge.preferences import Preferences
_smoke_trace("after FigureForge GUI import")


class _SilentSplash:
    def showMessage(self, *_args, **_kwargs):
        pass

    def finish(self, *_args, **_kwargs):
        pass


def _current_canvas_container(window: MainWindow):
    current = window.tab_widget.currentWidget()
    layout = current.layout() if hasattr(current, "layout") else None
    return current, layout


def _stack_axes(window: MainWindow, mode: str):
    figure = window.fm.figure
    axes = [axis for axis in figure.axes if axis.get_visible()]
    if len(axes) < 2:
        return

    left, right = 0.10, 0.96
    bottom, top = 0.12, 0.90
    gap = 0.075
    if mode == "vertical":
        height = max((top - bottom - gap * (len(axes) - 1)) / len(axes), 0.05)
        for index, axis in enumerate(axes):
            y0 = top - (index + 1) * height - index * gap
            axis.set_position([left, y0, right - left, height])
    else:
        width = max((right - left - gap * (len(axes) - 1)) / len(axes), 0.05)
        for index, axis in enumerate(axes):
            x0 = left + index * (width + gap)
            axis.set_position([x0, bottom, width, top - bottom])

    window.fm.unsaved_changes = True
    window.fm.fe.build_tree(figure)
    window.fm.canvas.draw_idle()


def _install_stack_controls(window: MainWindow):
    _current, layout = _current_canvas_container(window)
    if layout is None:
        return

    controls = QWidget()
    row = QHBoxLayout(controls)
    row.setContentsMargins(6, 4, 6, 4)
    row.setSpacing(6)
    vertical_button = QPushButton("Stack Vertical")
    horizontal_button = QPushButton("Stack Horizontal")
    vertical_button.setToolTip("Arrange visible subplots from top to bottom.")
    horizontal_button.setToolTip("Arrange visible subplots from left to right.")
    vertical_button.clicked.connect(lambda: _stack_axes(window, "vertical"))
    horizontal_button.clicked.connect(lambda: _stack_axes(window, "horizontal"))
    row.addStretch()
    row.addWidget(vertical_button)
    row.addWidget(horizontal_button)
    layout.insertWidget(0, controls)
    window._indent_stack_controls = controls


def _simplify_menus(window: MainWindow):
    menubar = window.menuBar()
    for action in list(menubar.actions()):
        menu = action.menu()
        title = action.text().replace("&", "")
        if title == "Help":
            menubar.removeAction(action)
        elif title == "Plugins" and menu is not None:
            for plugin_action in list(menu.actions()):
                text = plugin_action.text().replace("&", "")
                if text in {
                    "Plugins Documentation",
                    "New Plugin",
                    "Open Plugins Folder...",
                }:
                    menu.removeAction(plugin_action)


def main() -> int:
    _smoke_trace("main entered")
    if len(sys.argv) != 3:
        print("Usage: IndentAnalyzerFigureForge INPUT.pkl OUTPUT.pkl", file=sys.stderr)
        return 2

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    with input_path.open("rb") as handle:
        figure = pickle.load(handle)
    _smoke_trace("figure loaded")
    if not isinstance(figure, Figure):
        raise TypeError(f"Expected a Matplotlib Figure, got {type(figure).__name__}")

    preferences = Preferences()
    preferences.set("show_welcome", False)
    preferences.set("check_for_updates", False)
    _smoke_trace("preferences set")

    app = QApplication.instance() or QApplication(sys.argv)
    _smoke_trace("application created")
    splash = _SilentSplash()
    _smoke_trace("before window creation")
    window = MainWindow(splash, figure)
    _smoke_trace("window created")
    window.setWindowIcon(QIcon())
    window.setWindowTitle("Plot Editor")
    _install_stack_controls(window)
    _simplify_menus(window)
    window.show()
    splash.finish(window)

    def select_initial_item():
        root = window.fm.fe.tree.topLevelItem(0)
        if root is not None:
            window.fm.fe.tree.setCurrentItem(root)
            window.fm.on_item_selected(root.reference)

    QTimer.singleShot(0, select_initial_item)
    smoke_delay = os.environ.get("INDENTANALYZER_FIGUREFORGE_SMOKE_MS")
    if smoke_delay:
        QTimer.singleShot(max(int(smoke_delay), 1), app.quit)
    _smoke_trace("before event loop")
    app.exec()
    _smoke_trace("after event loop")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as handle:
        pickle.dump(window.fm.figure, handle, protocol=4)
    _smoke_trace("output written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
