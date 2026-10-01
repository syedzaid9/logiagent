# Start LogiAgent Backend Server
$backendDir = Join-Path $PSScriptRoot "backend"
Set-Location $backendDir

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  LogiAgent AI Logistics Operations Backend Server" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Starting FastAPI with Uvicorn on http://127.0.0.1:8000 ..." -ForegroundColor Green
Write-Host "API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Yellow

if (Get-Command py -ErrorAction SilentlyContinue) {
    py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
} else {
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}
