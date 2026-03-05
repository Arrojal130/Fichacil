@echo off
REM FichaFacil - Interactive Demo Script for iPhone Testing
REM This script guides through the complete setup and testing process

setlocal enabledelayedexpansion

color 0B
cls

echo.
echo.
echo    ██████╗ ██╗ ██████╗██╗  ██╗ █████╗ ███████╗ █████╗  ██████╗██╗     
echo    ██╔════╝ ██║██╔════╝██║  ██║██╔══██╗██╔════╝██╔══██╗██╔════╝██║     
echo    ██║  ███╗██║██║     ███████║███████║█████╗  ███████║██║     ██║     
echo    ██║   ██║██║██║     ██╔══██║██╔══██║██╔══╝  ██╔══██║██║     ██║     
echo    ╚██████╔╝██║╚██████╗██║  ██║██║  ██║███████╗██║  ██║╚██████╗███████╗
echo     ╚═════╝ ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝╚══════╝
echo.
echo    iPhone LAN Testing - Complete Setup
echo.
echo ========================================================
echo.

REM Get current directory
set "PROJECT_DIR=%cd%"
echo Project directory: %PROJECT_DIR%
echo.

REM Get local IP
for /f "delims=" %%a in ('powershell -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notmatch '127.0' -and $_.IPAddress -notmatch '169.254'}).IPAddress | Select-Object -First 1"') do set "LOCAL_IP=%%a"

if not defined LOCAL_IP (
    set "LOCAL_IP=192.168.X.X (run ipconfig to find)"
)

echo Your PC IP: %LOCAL_IP%
echo.

:MENU
echo.
echo ========================================================
echo  DEMO OPTIONS
echo ========================================================
echo.
echo  [1] QUICK START   - Launch Backend + Frontend (2 terminals)
echo  [2] TEST CORS     - Verify CORS headers working
echo  [3] DEBUG MODE    - Frontend devtools + console
echo  [4] PWA CHECK     - Verify manifest and service worker
echo  [5] IPHONE INFO   - Instructions for iPhone access
echo  [6] EXIT
echo.
set /p choice="Select option (1-6): "

if "%choice%"=="1" goto QUICK_START
if "%choice%"=="2" goto TEST_CORS
if "%choice%"=="3" goto DEBUG_MODE
if "%choice%"=="4" goto PWA_CHECK
if "%choice%"=="5" goto IPHONE_INFO
if "%choice%"=="6" goto EXIT_DEMO
goto MENU

:QUICK_START
cls
echo.
echo ========================================================
echo  [1] QUICK START - Launching services...
echo ========================================================
echo.
echo Starting Backend (Terminal 1)...
timeout /t 2
start "FichaFacil Backend" cmd /k cd backend ^& python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

echo Starting Frontend (Terminal 2)...
timeout /t 2
start "FichaFacil Frontend" cmd /k cd frontend ^& python -m http.server 3000

echo.
echo ✅ Services starting...
echo.
echo    Backend:  http://127.0.0.1:8000
echo    Frontend: http://127.0.0.1:3000
echo.
echo On iPhone (same WiFi):
echo    http://%LOCAL_IP%:3000
echo.
pause
goto MENU

:TEST_CORS
cls
echo.
echo ========================================================
echo  [2] TEST CORS - Verifying headers
echo ========================================================
echo.
echo Testing if CORS is correctly configured...
echo.

curl -i -H "Origin: http://192.168.1.42:3000" ^
     -H "Content-Type: application/json" ^
     http://127.0.0.1:8000/auth/me 2>nul >cors_test.txt

type cors_test.txt | find "access-control-allow-origin"
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ CORS headers present!
) else (
    echo.
    echo ⚠️  CORS headers not found - check if backend is running
)

echo.
pause
goto MENU

:DEBUG_MODE
cls
echo.
echo ========================================================
echo  [3] DEBUG MODE - Navigate to debug interface
echo ========================================================
echo.
echo Opening debug console at: http://127.0.0.1:3000/#debug
echo.
start http://127.0.0.1:3000/#debug
echo.
echo Right-click > Inspect > Network tab
echo Watch requests between frontend and backend
echo.
pause
goto MENU

:PWA_CHECK
cls
echo.
echo ========================================================
echo  [4] PWA CHECK - Verifying manifest and SW
echo ========================================================
echo.
echo Checking manifest.json...
if exist frontend\manifest.json (
    echo ✅ manifest.json found
    echo.
    type frontend\manifest.json | find "start_url"
    echo.
) else (
    echo ❌ manifest.json not found
)

echo.
echo Checking service worker...
if exist frontend\sw.js (
    echo ✅ sw.js found
    echo Cache name: !
    type frontend\sw.js | find "CACHE_NAME"
) else (
    echo ❌ sw.js not found
)

echo.
pause
goto MENU

:IPHONE_INFO
cls
echo.
echo ========================================================
echo  [5] IPHONE - Complete Access Guide
echo ========================================================
echo.
echo STEP 1: Verify Network
echo --------
echo Your PC IP: %LOCAL_IP%
echo Your Phone: Connected to same WiFi? (YES/NO)
echo.

echo STEP 2: Open in Safari
echo --------
echo On iPhone:
echo   -> Safari
echo   -> URL bar: http://%LOCAL_IP%:3000
echo   -> Go
echo.

echo STEP 3: Test Login
echo --------
echo You should see:
echo   ✅ Login screen
echo   ✅ Onboarding button
echo   ✅ Can type credentials
echo.

echo STEP 4: Install as App
echo --------
echo In Safari:
echo   -> Share button (box with arrow up)
echo   -> "Add to Home Screen"
echo   -> Name: FichaFácil
echo   -> Add
echo.

echo STEP 5: Debug (Optional)
echo --------
echo On Mac with iPhone connected:
echo   -> Mac Safari > Develop > [iPhone] > [website]
echo   -> Watch Network tab for errors
echo.

pause
goto MENU

:EXIT_DEMO
cls
echo.
echo Thank you for using FichaFacil!
echo.
echo Remember:
echo   Backend:  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
echo   Frontend: python -m http.server 3000
echo.
timeout /t 2
exit /b 0

