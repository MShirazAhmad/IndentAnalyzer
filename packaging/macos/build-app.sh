#!/bin/bash

set -euo pipefail

PYTHON="${1:-/opt/homebrew/bin/python3.11}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

if [[ ! -x ".venv-macos/bin/python" ]]; then
    "$PYTHON" -m venv .venv-macos
fi

VENV_PYTHON="$PROJECT_ROOT/.venv-macos/bin/python"
"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install -r requirements.txt pyinstaller "FigureForge==0.3.3" PySide6

# FigureForge 0.3.3 imports its initializer as a synthetic submodule, which is
# incompatible with frozen importers. Normalize those imports and define its
# resource constants before the helper package is frozen.
FIGUREFORGE_DIR="$PROJECT_ROOT/.venv-macos/lib/python3.11/site-packages/FigureForge"
cp "$PROJECT_ROOT/packaging/windows/figureforge_init.py" "$FIGUREFORGE_DIR/__init__.py"
while IFS= read -r -d '' source_file; do
    sed -i '' \
        -e 's/from FigureForge\.__init__ import/from FigureForge import/g' \
        -e 's/from PySide6\.__init__ import/from PySide6 import/g' \
        "$source_file"
done < <(find "$FIGUREFORGE_DIR" -type f -name '*.py' -print0)

rm -rf \
    build/macos \
    build/macos-helper \
    build/macos-helper-dist \
    dist/IndentAnalyzer \
    dist/IndentAnalyzer.app

"$VENV_PYTHON" -m PyInstaller \
    --noconfirm \
    --clean \
    --distpath build/macos-helper-dist \
    --workpath build/macos-helper \
    packaging/macos/IndentAnalyzerFigureForge.spec

"$VENV_PYTHON" -m PyInstaller \
    --noconfirm \
    --clean \
    --distpath dist \
    --workpath build/macos \
    packaging/macos/IndentAnalyzer.spec

echo "Application created at dist/IndentAnalyzer.app"
