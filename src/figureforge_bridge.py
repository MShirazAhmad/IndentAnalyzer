#!/usr/bin/env python3
"""Bundled FigureForge bridge for editing an IndentAnalyzer Matplotlib figure."""

from __future__ import annotations

import pickle
import os
import sys
from pathlib import Path

from matplotlib.figure import Figure
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QHBoxLayout, QPushButton, QWidget

from FigureForge.gui import MainWindow
from FigureForge.preferences import Preferences


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
    if len(sys.argv) != 3:
        print("Usage: IndentAnalyzerFigureForge INPUT.pkl OUTPUT.pkl", file=sys.stderr)
        return 2

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    with input_path.open("rb") as handle:
        figure = pickle.load(handle)
    if not isinstance(figure, Figure):
        raise TypeError(f"Expected a Matplotlib Figure, got {type(figure).__name__}")

    preferences = Preferences()
    preferences.set("show_welcome", False)
    preferences.set("check_for_updates", False)

    app = QApplication.instance() or QApplication(sys.argv)
    splash = _SilentSplash()
    window = MainWindow(splash, figure)
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
    app.exec()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as handle:
        pickle.dump(window.fm.figure, handle, protocol=4)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
