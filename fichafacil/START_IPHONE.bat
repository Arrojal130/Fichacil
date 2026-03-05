@echo off
REM FichaFacil - Quick Start for iPhone Testing
REM This script starts backend + frontend and shows your PC IP

setlocal enabledelayedexpansion
color 0A
cls

echo.
echo ============================================================
echo   FICHAFACIL - iPhone Testing Quick Start
echo ============================================================
echo.

REM Get local IP using PowerShell
echo [1/4] Getting your PC IP address...
for /f "delims=" %%a in ('powershell -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notmatch '127.0' -and $_.IPAddress -notmatch '169.254' -and $_.InterfaceAlias -notmatch 'Loopback'}).IPAddress | Select-Object -First 1"') do set "LOCAL_IP=%%a"

if not defined LOCAL_IP (
    echo    WARNING: Could not auto-detect IP
    echo    Run 'ipconfig' manually to find your IPv4 Address
    set "LOCAL_IP=[YOUR_IP_HERE]"
) else (
    echo    Your PC IP: %LOCAL_IP%
)

echo.
echo [2/4] Starting Backend (port 8000)...
echo    Command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
cd backend
start "FichaFacil Backend" cmd /k "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
cd ..
timeout /t 3 >nul

echo.
echo [3/4] Starting Frontend (port 3000)...
echo    Command: python -m http.server 3000
cd frontend
start "FichaFacil Frontend" cmd /k "python -m http.server 3000"
cd ..
timeout /t 2 >nul

echo.
echo [4/4] Running network diagnostics...
timeout /t 3 >nul
python test_network.py

echo.
echo ============================================================
echo   READY FOR TESTING!
echo ============================================================
echo.
echo   PC (Browser):
echo      http://127.0.0.1:3000
echo.
echo   iPhone (Safari - same WiFi):
echo      http://%LOCAL_IP%:3000
echo.
echo   Backend API:
echo      http://%LOCAL_IP%:8000
echo      http://%LOCAL_IP%:8000/docs (Swagger UI)
echo.
echo ============================================================
echo   DEBUGGING TIPS:
echo ============================================================
echo.
echo   1. Open Safari on iPhone and go to:
echo      http://%LOCAL_IP%:3000
echo.
echo   2. Open Console in Safari (Mac):
echo      Safari ^> Develop ^> [iPhone] ^> [Website]
echo.
echo   3. Check console logs for:
echo      - API Configuration (should show %LOCAL_IP%:8000)
echo      - API Request/Response logs
echo      - Any errors (should be none)
echo.
echo   4. Test backend directly in iPhone Safari:
echo      http://%LOCAL_IP%:8000/docs
echo      (Should see Swagger UI)
echo.
echo ============================================================
echo.
echo Press any key to test CORS manually...
pause >nul

echo.
echo Testing CORS with curl...
echo.
curl -i -H "Origin: http://%LOCAL_IP%:3000" "http://127.0.0.1:8000/negocios/search?q=" 2>nul | findstr /i "access-control HTTP/1.1"

echo.
echo.
echo Press any key to exit...
pause >nul
