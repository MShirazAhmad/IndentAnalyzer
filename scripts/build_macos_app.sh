#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

PYTHON_BIN="${PYTHON_BIN:-$PROJECT_ROOT/.venv/bin/python}"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="$(command -v python3)"
fi

if ! "$PYTHON_BIN" -m PyInstaller --version >/dev/null 2>&1; then
  echo "PyInstaller is not installed in $PYTHON_BIN"
  echo "Install it with: $PYTHON_BIN -m pip install pyinstaller"
  exit 1
fi

ICON_SOURCE="$PROJECT_ROOT/src/logo/NanoInd.png"
ICON_FILE="$PROJECT_ROOT/build/IndentAnalyzer.icns"
if [ -f "$ICON_SOURCE" ] && command -v sips >/dev/null 2>&1 && command -v iconutil >/dev/null 2>&1; then
  ICONSET="$PROJECT_ROOT/build/IndentAnalyzer.iconset"
  mkdir -p "$ICONSET"
  sips -z 16 16 "$ICON_SOURCE" --out "$ICONSET/icon_16x16.png" >/dev/null
  sips -z 32 32 "$ICON_SOURCE" --out "$ICONSET/icon_16x16@2x.png" >/dev/null
  sips -z 32 32 "$ICON_SOURCE" --out "$ICONSET/icon_32x32.png" >/dev/null
  sips -z 64 64 "$ICON_SOURCE" --out "$ICONSET/icon_32x32@2x.png" >/dev/null
  sips -z 128 128 "$ICON_SOURCE" --out "$ICONSET/icon_128x128.png" >/dev/null
  sips -z 256 256 "$ICON_SOURCE" --out "$ICONSET/icon_128x128@2x.png" >/dev/null
  sips -z 256 256 "$ICON_SOURCE" --out "$ICONSET/icon_256x256.png" >/dev/null
  sips -z 512 512 "$ICON_SOURCE" --out "$ICONSET/icon_256x256@2x.png" >/dev/null
  sips -z 512 512 "$ICON_SOURCE" --out "$ICONSET/icon_512x512.png" >/dev/null
  sips -z 1024 1024 "$ICON_SOURCE" --out "$ICONSET/icon_512x512@2x.png" >/dev/null
  if ! iconutil -c icns "$ICONSET" -o "$ICON_FILE"; then
    echo "Warning: could not create .icns file; building app without Finder icon."
    rm -f "$ICON_FILE"
  fi
fi

PYINSTALLER_ARGS=(
  --clean
  --noconfirm
  --windowed
  --name IndentAnalyzer
  --osx-bundle-identifier com.indentanalyzer.app
  --add-data "config:config"
  --add-data "samples:samples"
  --add-data "src/logo:src/logo"
  --add-data "src/fileloader:src/fileloader"
  --hidden-import PyQt5.QtWebEngineWidgets
  --hidden-import plotly.graph_objects
  --hidden-import openpyxl
  --hidden-import xlrd
)

if [ -f "$ICON_FILE" ]; then
  PYINSTALLER_ARGS+=(--icon "$ICON_FILE")
fi

"$PYTHON_BIN" -m PyInstaller "${PYINSTALLER_ARGS[@]}" src/indent_analyzer_app.py

echo "Built: $PROJECT_ROOT/dist/IndentAnalyzer.app"
