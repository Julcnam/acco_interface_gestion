$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Write-Host "=== Installation des dependances Python ==="

# Installer modules Python
python\python.exe -m pip install --upgrade pip
python\python.exe -m pip install -r "$PSScriptRoot\requirements.txt"

Write-Host "Lancement de l'App..."

$PythonUrl = "$PSScriptRoot\app.py"
python\python.exe -m streamlit run $PythonUrl --server.port 8501