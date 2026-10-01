# Start LogiAgent Frontend Client
$frontendDir = Join-Path $PSScriptRoot "frontend"
Set-Location $frontendDir

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  LogiAgent AI Logistics Operations Frontend UI" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Starting Vite Dev Server on http://localhost:5173 ..." -ForegroundColor Green

npm run dev
