Create this file:

```text
make_installer.ps1
```

in:

```text
C:\Users\shiraz\Documents\IndentAnalyzer
```

Paste this:

```powershell
$ProjectRoot = "C:\Users\shiraz\Documents\IndentAnalyzer"
$AppName = "IndentAnalyzer"
$Version = "1.0.0"

$DistFolder = Join-Path $ProjectRoot "dist\IndentAnalyzer"
$ExePath = Join-Path $DistFolder "IndentAnalyzer.exe"
$IconPath = Join-Path $ProjectRoot "src\logo\NanoInd.ico"
$InstallerFolder = Join-Path $ProjectRoot "installer"
$OutputFolder = Join-Path $ProjectRoot "installer_output"
$IssPath = Join-Path $InstallerFolder "IndentAnalyzer.iss"

if (!(Test-Path $ExePath)) {
    Write-Error "Missing EXE: $ExePath"
    exit 1
}

if (!(Test-Path $IconPath)) {
    Write-Error "Missing icon: $IconPath"
    exit 1
}

New-Item -ItemType Directory -Force -Path $InstallerFolder | Out-Null
New-Item -ItemType Directory -Force -Path $OutputFolder | Out-Null

$IssContent = @"
#define MyAppName "$AppName"
#define MyAppVersion "$Version"
#define MyAppPublisher "M. Shiraz Ahmad"
#define MyAppExeName "IndentAnalyzer.exe"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=$OutputFolder
OutputBaseFilename=IndentAnalyzer_Setup_v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
SetupIconFile=$IconPath
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "$DistFolder\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
"@

Set-Content -Path $IssPath -Value $IssContent -Encoding UTF8

$ISCC = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"

if (!(Test-Path $ISCC)) {
    Write-Error "Inno Setup not found. Install it first from https://jrsoftware.org/isinfo.php"
    exit 1
}

& $ISCC $IssPath

Write-Host ""
Write-Host "Installer created in:"
Write-Host "$OutputFolder"
```

Run it:

```powershell
.\make_installer.ps1
```

Output:

```text
installer_output\IndentAnalyzer_Setup_v1.0.0.exe
```
