# PowerShell script voor Rancher Desktop setup
# Uitvoeren als Administrator

Write-Host "=== Rancher Desktop Setup voor Cursor AI ===" -ForegroundColor Green
Write-Host ""

# Controleer of Rancher Desktop is geïnstalleerd
$rancherPath = Get-Command rancher-desktop -ErrorAction SilentlyContinue
if ($rancherPath) {
    Write-Host "✓ Rancher Desktop is geïnstalleerd" -ForegroundColor Green
    Write-Host "  Locatie: $($rancherPath.Source)" -ForegroundColor Gray
} else {
    Write-Host "✗ Rancher Desktop is niet geïnstalleerd" -ForegroundColor Red
    Write-Host "  Download van: https://rancherdesktop.io/" -ForegroundColor Yellow
    Write-Host "  Installeer en herstart dit script" -ForegroundColor Yellow
    exit 1
}

# Controleer of Rancher Desktop draait
Write-Host ""
Write-Host "Controleer Rancher Desktop status..." -ForegroundColor Yellow
try {
    $status = & rancher-desktop status --output json 2>$null | ConvertFrom-Json
    if ($status.status -eq "running") {
        Write-Host "✓ Rancher Desktop draait" -ForegroundColor Green
    } else {
        Write-Host "✗ Rancher Desktop draait niet (Status: $($status.status))" -ForegroundColor Red
        Write-Host "  Start Rancher Desktop handmatig op" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Kan Rancher Desktop status niet controleren" -ForegroundColor Red
    Write-Host "  Zorg dat Rancher Desktop draait" -ForegroundColor Yellow
}

# Controleer Docker CLI
Write-Host ""
Write-Host "Controleer Docker CLI..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>$null
    if ($dockerVersion) {
        Write-Host "✓ Docker CLI werkt" -ForegroundColor Green
        Write-Host "  $dockerVersion" -ForegroundColor Gray
    } else {
        Write-Host "✗ Docker CLI werkt niet" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Docker CLI niet beschikbaar" -ForegroundColor Red
}

# Controleer container runtime
Write-Host ""
Write-Host "Controleer container runtime..." -ForegroundColor Yellow
try {
    $containerdVersion = containerd --version 2>$null
    if ($containerdVersion) {
        Write-Host "✓ Containerd runtime beschikbaar" -ForegroundColor Green
        Write-Host "  $containerdVersion" -ForegroundColor Gray
    } else {
        Write-Host "✗ Containerd runtime niet beschikbaar" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Containerd runtime niet beschikbaar" -ForegroundColor Red
}

# Test container functionaliteit
Write-Host ""
Write-Host "Test container functionaliteit..." -ForegroundColor Yellow
try {
    $testContainer = docker run --rm hello-world 2>$null
    if ($testContainer -match "Hello from Docker") {
        Write-Host "✓ Container test succesvol" -ForegroundColor Green
    } else {
        Write-Host "✗ Container test gefaald" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Container test kon niet uitgevoerd worden" -ForegroundColor Red
}

# Aanbevelingen
Write-Host ""
Write-Host "=== Aanbevelingen ===" -ForegroundColor Cyan
Write-Host "1. Open Cursor AI en je project" -ForegroundColor White
Write-Host "2. Druk op Ctrl+Shift+P en kies 'Dev Containers: Reopen in Container'" -ForegroundColor White
Write-Host "3. Kies de Rancher Desktop configuratie" -ForegroundColor White
Write-Host ""
Write-Host "Als je problemen ondervindt:" -ForegroundColor Yellow
Write-Host "- Controleer de logs in Rancher Desktop" -ForegroundColor White
Write-Host "- Herstart Rancher Desktop" -ForegroundColor White
Write-Host "- Controleer de README_RANCHER.md voor meer info" -ForegroundColor White

Write-Host ""
Write-Host "Setup voltooid!" -ForegroundColor Green

