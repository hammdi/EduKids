# Script PowerShell pour démarrer le serveur EduKids avec Daphne (supporte WebSocket)
# Usage: .\start_server.ps1

Write-Host "🚀 Démarrage du serveur EduKids avec support WebSocket..." -ForegroundColor Green

# Configuration de la clé API Mistral
$env:MISTRAL_API_KEY = '2WC2TOx7fBperEqMgasE390GYC0Isenq'

# Vérifier si le port 8000 est déjà utilisé
$existingProcess = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($existingProcess) {
    Write-Host "⚠️  Le port 8000 est déjà utilisé. Arrêt du processus existant..." -ForegroundColor Yellow
    Stop-Process -Id $existingProcess.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Chemin vers l'environnement virtuel
$venvPath = Join-Path $PSScriptRoot "..\venv\Scripts\python.exe"

# Vérifier que le venv existe
if (-not (Test-Path $venvPath)) {
    Write-Host "❌ Environnement virtuel introuvable : $venvPath" -ForegroundColor Red
    Write-Host "Assurez-vous que le venv est créé et activé." -ForegroundColor Red
    exit 1
}

Write-Host "📦 Utilisation de Python : $venvPath" -ForegroundColor Cyan
Write-Host "🔑 MISTRAL_API_KEY configurée" -ForegroundColor Cyan
Write-Host "🌐 Serveur disponible sur : http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "🔌 WebSocket disponible sur : ws://127.0.0.1:8000/ws/assistant/" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pour arrêter le serveur, appuyez sur Ctrl+C" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

# Démarrer Daphne
& $venvPath -m daphne -b 127.0.0.1 -p 8000 EduKids.asgi:application
