# Windows Installation Guide

End users install the app by running `IndentAnalyzer-Setup-2.0.0.exe`. Python is
not required on the destination computer.

## Building the installer

Build on Windows 10 or 11 with x64 Python 3.11+ and Inno Setup 6 installed:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\windows\build-installer.ps1
```

The signed-or-unsigned installer is written to `dist\installer`. It bundles the
required FigureForge plot editor as a separate helper executable. The build uses
an x64-compatible executable, which also runs under Windows 11 ARM emulation.

## Video walkthrough

Follow the instructions in **IndentAnalyzer Windows Installation Guide**:

<iframe width="100%" height="405" src="https://www.youtube.com/embed/B07MHajiaPU" title="IndentAnalyzer Windows Installation Guide" frameborder="0" allowfullscreen></iframe>

[Watch IndentAnalyzer Windows Installation Guide on YouTube](https://www.youtube.com/watch?v=B07MHajiaPU)
