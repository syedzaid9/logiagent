# Start LogiAgent Backend and Frontend together
$root = $PSScriptRoot

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "      LogiAgent AI Logistics Operations Platform" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $root "start_backend.ps1")
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $root "start_frontend.ps1")

Write-Host "Services launched successfully!" -ForegroundColor Green
Write-Host "Backend API : http://127.0.0.1:8000" -ForegroundColor White
Write-Host "Swagger Docs: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "Frontend App: http://localhost:5173" -ForegroundColor White
