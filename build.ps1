# build.ps1 — build a one-file, windowed idel-faker.exe with PyInstaller.
$ErrorActionPreference = "Stop"

pip install -r requirements-dev.txt
python scripts/make_ico.py
pyinstaller --clean --noconfirm idel-faker.spec

Write-Host "Built dist/idel-faker.exe"
