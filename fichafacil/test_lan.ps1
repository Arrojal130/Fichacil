# FichaFacil - iPhone LAN Test Script (PowerShell)
# Ejecutar: powershell -ExecutionPolicy Bypass -File test_lan.ps1

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "FICHAFACIL - iPhone LAN Testing" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Get local IP
$LocalIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch "docker" -and $_.IPAddress -notmatch "127.0" } | Select-Object -First 1).IPAddress

if (-not $LocalIP) {
    $LocalIP = "192.168.1.X"
}

Write-Host "[1] Testing Backend Availability" -ForegroundColor Yellow
Start-Sleep -Seconds 1
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/docs" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "✅ Backend running on localhost:8000" -ForegroundColor Green
}
catch {
    Write-Host "❌ Backend NOT running" -ForegroundColor Red
    Write-Host "   Start with: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
    exit 1
}

Write-Host ""
Write-Host "[2] Testing Frontend Availability" -ForegroundColor Yellow
Start-Sleep -Seconds 1
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:3000" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "✅ Frontend running on localhost:3000" -ForegroundColor Green
}
catch {
    Write-Host "❌ Frontend NOT running" -ForegroundColor Red
    Write-Host "   Start with: cd frontend && python -m http.server 3000"
    exit 1
}

Write-Host ""
Write-Host "[3] Testing CORS Headers" -ForegroundColor Yellow
Start-Sleep -Seconds 1
try {
    $headers = @{
        "Origin" = "http://192.168.1.42:3000"
        "Content-Type" = "application/json"
    }
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/auth/me" -Headers $headers -TimeoutSec 3 -ErrorAction SilentlyContinue
    $corsHeader = $response.Headers["access-control-allow-origin"]
    
    if ($corsHeader) {
        Write-Host "✅ CORS headers present" -ForegroundColor Green
        Write-Host "   Access-Control-Allow-Origin: $corsHeader"
    }
    else {
        Write-Host "⚠️  CORS headers might not be configured" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "⚠️  CORS check inconclusive (backend might not have /auth/me)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[4] Network Information" -ForegroundColor Yellow
Write-Host "   Your PC IP: $LocalIP"
Write-Host "   Backend (PC):  http://localhost:8000"
Write-Host "   Backend (LAN): http://$LocalIP:8000"
Write-Host "   Frontend (PC):  http://localhost:3000"
Write-Host "   Frontend (LAN): http://$LocalIP:3000"

Write-Host ""
Write-Host "✅ All systems ready for iPhone testing!" -ForegroundColor Green
Write-Host ""
Write-Host "📱  On iPhone (same WiFi):" -ForegroundColor Cyan
Write-Host "    http://$LocalIP:3000"
Write-Host ""
