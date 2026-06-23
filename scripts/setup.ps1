# Script de mise en place de l'environnement de développement (Windows / PowerShell).
# Usage :  ./scripts/setup.ps1
$ErrorActionPreference = "Stop"

Write-Host "== MaturAI : mise en place de l'environnement ==" -ForegroundColor Cyan

# 1. Vérifier Python 3.11+
$python = $null
foreach ($cmd in @("python", "py -3")) {
    try {
        $v = & cmd /c "$cmd --version" 2>$null
        if ($v -match "Python 3\.(1[1-9]|[2-9]\d)") { $python = $cmd; break }
    } catch { }
}
if (-not $python) {
    Write-Host "Python 3.11+ introuvable. Installer depuis https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "(Le 'python' du Windows Store ne convient pas.)" -ForegroundColor Yellow
    exit 1
}
Write-Host "Python détecté : $python" -ForegroundColor Green

# 2. Créer le venv
if (-not (Test-Path ".venv")) {
    Write-Host "Création du venv .venv ..."
    & cmd /c "$python -m venv .venv"
}

# 3. Installer les dépendances (cœur + dev)
Write-Host "Installation des dépendances (cœur + dev) ..."
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -e ".[dev]"

Write-Host ""
Write-Host "Terminé. Activer l'environnement avec :" -ForegroundColor Green
Write-Host "    .\.venv\Scripts\Activate.ps1"
Write-Host "Puis lancer la démo :" -ForegroundColor Green
Write-Host "    python scripts/run_scoring_demo.py"
Write-Host "Extras optionnels : pip install -e `".[graphrag,fuzzy,report]`""
