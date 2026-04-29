"""Build script for RD AudioRip.

Produces a single Windows EXE in dist/ using PyInstaller.
Run with: python build.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SOURCE = ROOT / "source"
RESOURCES = SOURCE / "resources"
ICON = RESOURCES / "rd_audiorip_logo.ico"
ENTRY = SOURCE / "main.py"

PYINSTALLER = Path(sys.executable).parent / "pyinstaller.exe"
if not PYINSTALLER.exists():
    PYINSTALLER = Path(sys.executable).parent / "pyinstaller"

args = [
    str(PYINSTALLER),
    "--onefile",
    "--windowed",
    f"--icon={ICON}",
    f"--add-data={RESOURCES}{';' if sys.platform == 'win32' else ':'}resources",
    "--name=RD AudioRip",
    f"--paths={SOURCE}",
    str(ENTRY),
]

print("Building RD AudioRip...")
print(f"  Entry : {ENTRY}")
print(f"  Icon  : {ICON}")
print(f"  Output: {ROOT / 'dist' / 'RD AudioRip.exe'}")
print()

result = subprocess.run(args, cwd=ROOT)
if result.returncode == 0:
    print("\nBuild complete! Output: dist/RD AudioRip.exe")
else:
    print(f"\nBuild failed (exit code {result.returncode})")
    sys.exit(result.returncode)
