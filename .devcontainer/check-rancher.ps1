clear
# Eenvoudig Rancher Desktop controle script
Write-Host "=== Rancher Desktop Controle ===" -ForegroundColor Green
Write-Host ""

# Controleer Docker
Write-Host "Controleer Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker CLI werkt: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker CLI werkt niet" -ForegroundColor Red
}

# Controleer of containers kunnen draaien
Write-Host ""
Write-Host "Test container functionaliteit..." -ForegroundColor Yellow
try {
    $result = docker run --rm hello-world 2>&1
    if ($result -match "Hello from Docker") {
        Write-Host "✓ Container test succesvol" -ForegroundColor Green
    } else {
        Write-Host "✗ Container test gefaald" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Container test kon niet uitgevoerd worden" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Volgende Stappen ===" -ForegroundColor Cyan
Write-Host "1. Installeer Rancher Desktop van: https://rancherdesktop.io/" -ForegroundColor White
Write-Host "2. Start Rancher Desktop" -ForegroundColor White
Write-Host "3. Open je project in Cursor AI" -ForegroundColor White
Write-Host "4. Gebruik Dev Containers met Rancher Desktop" -ForegroundColor White

Write-Host ""
Write-Host "Klaar!" -ForegroundColor Green


