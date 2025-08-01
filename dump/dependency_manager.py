#!/usr/bin/env python3
"""
GUI Requirements Generator
Creates requirements.txt for the isolated GUI folder
"""

import subprocess
import sys

def get_installed_version(package):
    """Get the installed version of a package"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'show', package], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    return line.split(':', 1)[1].strip()
    except:
        pass
    return None

# Core GUI dependencies
gui_requirements = [
    'PyQt5',
    'matplotlib', 
    'pandas',
    'numpy',
    'scipy',
    'openpyxl'
]

print("🔍 Checking installed package versions...")

requirements_content = "# Nanoindentation GUI Requirements\n"
requirements_content += "# Generated automatically from installed packages\n\n"

for package in gui_requirements:
    version = get_installed_version(package)
    if version:
        requirements_content += f"{package}=={version}\n"
        print(f"✅ {package}=={version}")
    else:
        requirements_content += f"{package}\n"
        print(f"⚠️ {package} (version not found)")

# Write requirements file
with open('requirements.txt', 'w') as f:
    f.write(requirements_content)

print(f"\n📄 Created requirements.txt with {len(gui_requirements)} dependencies")
print("🚀 To install in a new environment: pip install -r requirements.txt")
