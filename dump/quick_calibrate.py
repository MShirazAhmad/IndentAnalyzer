#!/usr/bin/env python3
"""Quick Tip Calibration - Compact Version"""
import sys, os
sys.path.insert(0, '.')
from src.calibration.tip_calibrator import run_complete_tip_calibration

if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else "data/reference/fused_silica_reference.xls"
    print(f"🔬 Calibrating tip using: {file_path}")
    result = run_complete_tip_calibration(file_path)
    print("✅ Calibration complete!")
