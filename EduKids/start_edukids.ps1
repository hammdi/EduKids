# ============================================
# Script de demarrage EduKids
# ============================================

Write-Host 'Demarrage EduKids...' -ForegroundColor Cyan
Write-Host ''

# Se positionner dans le bon repertoire
$projectPath = 'C:\Users\hadid\Downloads\ahmed\EduKids\Edukids'
Set-Location $projectPath
Write-Host "Repertoire: $projectPath" -ForegroundColor Yellow

# Definir la cle API Mistral
$env:MISTRAL_API_KEY = '2WC2TOx7fBperEqMgasE390GYC0Isenq'
Write-Host 'Cle API Mistral configuree' -ForegroundColor Green

# Arreter tout processus existant sur le port 8000
Write-Host ''
Write-Host 'Verification du port 8000...' -ForegroundColor Yellow
$existingProcess = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($existingProcess) {
    $pid = $existingProcess.OwningProcess
    Write-Host "Port 8000 occupe par le processus $pid. Arret en cours..." -ForegroundColor Yellow
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host 'Port 8000 libere' -ForegroundColor Green
} else {
    Write-Host 'Port 8000 disponible' -ForegroundColor Green
}

# Lancer Daphne
Write-Host ''
Write-Host 'Lancement de Daphne...' -ForegroundColor Cyan
Write-Host '   URL: http://127.0.0.1:8000' -ForegroundColor White
Write-Host ''
Write-Host '   Pour arreter le serveur: Ctrl+C' -ForegroundColor Gray
Write-Host ''

# Activer environnement virtuel et lancer Daphne
$venvPython = 'C:\Users\hadid\Downloads\ahmed\EduKids\venv\Scripts\python.exe'

if (Test-Path $venvPython) {
    Write-Host 'Environnement virtuel trouve' -ForegroundColor Green
    Write-Host ''
    Write-Host '======================================' -ForegroundColor Cyan
    Write-Host '   SERVEUR DAPHNE EN COURS' -ForegroundColor Green
    Write-Host '======================================' -ForegroundColor Cyan
    Write-Host ''
    
    & $venvPython -m daphne -b 127.0.0.1 -p 8000 EduKids.asgi:application
} else {
    Write-Host 'ERREUR: Environnement virtuel introuvable!' -ForegroundColor Red
    Write-Host "   Chemin attendu: $venvPython" -ForegroundColor Yellow
    Write-Host ''
    Write-Host '   Creez environnement virtuel avec:' -ForegroundColor White
    Write-Host '   python -m venv venv' -ForegroundColor Gray
    exit 1
}
