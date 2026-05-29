Set-StrictMode -Version Latest
python -m pip install --upgrade pip
pip install pyinstaller
pip install -r requirements.txt

# Build a single-file, windowed (no console) executable
pyinstaller --clean --onefile --windowed --name IndentAnalyzer src/indent_analyzer_app.py

Write-Output "Build complete. EXE will be in the 'dist' folder."
