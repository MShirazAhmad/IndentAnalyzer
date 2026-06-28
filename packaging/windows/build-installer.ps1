param(
    [string]$Python = "py",
    [string]$Iscc = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $ProjectRoot

if (-not (Test-Path ".venv-windows\Scripts\python.exe")) {
    & $Python -m venv .venv-windows
}

$VenvPython = Join-Path $ProjectRoot ".venv-windows\Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r requirements.txt pyinstaller "FigureForge==0.3.3" PySide6

# FigureForge 0.3.3 imports its initializer as a synthetic submodule, which is
# incompatible with frozen importers. Normalize those imports and define its
# resource constants before the plugin package is loaded.
$FigureForgeDir = Join-Path $ProjectRoot ".venv-windows\Lib\site-packages\FigureForge"
Copy-Item (Join-Path $PSScriptRoot "figureforge_init.py") (Join-Path $FigureForgeDir "__init__.py") -Force
Get-ChildItem $FigureForgeDir -Recurse -Filter "*.py" | ForEach-Object {
    $Source = [IO.File]::ReadAllText($_.FullName)
    $Updated = $Source.Replace("from FigureForge.__init__ import", "from FigureForge import")
    $Updated = $Updated.Replace("from PySide6.__init__ import", "from PySide6 import")
    if ($Updated -ne $Source) {
        [IO.File]::WriteAllText($_.FullName, $Updated)
    }
}

Remove-Item -Recurse -Force "build\windows", "build\windows-helper", "build\windows-helper-dist", "dist\IndentAnalyzer", "dist\installer" -ErrorAction SilentlyContinue
& $VenvPython -m PyInstaller --noconfirm --clean --distpath "build\windows-helper-dist" --workpath "build\windows-helper" "packaging\windows\IndentAnalyzerFigureForge.spec"
& $VenvPython -m PyInstaller --noconfirm --clean --distpath "dist" --workpath "build\windows" "packaging\windows\IndentAnalyzer.spec"

if (-not (Test-Path $Iscc)) {
    throw "Inno Setup compiler not found at '$Iscc'. Install Inno Setup 6 or pass -Iscc."
}

& $Iscc "packaging\windows\IndentAnalyzer.iss"
Write-Host "Installer created in dist\installer"
