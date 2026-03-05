@echo off
echo.
echo ========================================
echo  FICHAFACIL - START LAN (iPhone Ready)
echo ========================================
echo.
echo PC IP: 192.168.1.X (check with ipconfig)
echo iPhone: http://192.168.1.42:3000
echo.
echo [1] Backend (http://0.0.0.0:8000)
echo [2] Frontend (http://127.0.0.1:3000)
echo [3] Test CORS with curl
echo.

REM Get local IP
for /f "delims=" %%a in ('powershell -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -like '*Ethernet*' -or $_.InterfaceAlias -like '*Wi-Fi*'}).IPAddress | Select-Object -First 1"') do set "LOCAL_IP=%%a"

if not defined LOCAL_IP (
    for /f "delims=" %%a in ('powershell -Command "hostname"') do set "PC_NAME=%%a"
    set "LOCAL_IP=%PC_NAME%.local"
)

echo Your PC IP: %LOCAL_IP%
echo On iPhone, use: http://%LOCAL_IP%:3000
echo.

REM Backend terminal
start "FichaFacil Backend" cmd /k cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
timeout /t 2

REM Frontend terminal
start "FichaFacil Frontend" cmd /k cd frontend && python -m http.server 3000
timeout /t 1

echo.
echo ✅ Backend and Frontend started!
echo.
echo 📱 iPhone Access:
echo    http://%LOCAL_IP%:3000
echo.
echo 💻 PC Access:
echo    http://192.168.1.42:3000
echo.
echo 🧪 Test Backend (PC terminal):
echo    curl -H "Origin: http://192.168.1.42:3000" http://localhost:8000/auth/me
echo.
