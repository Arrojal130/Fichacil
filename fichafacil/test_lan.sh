#!/bin/bash
# FichaFacil - iPhone LAN Test Script
# Ejecutar en terminal WSL o Linux

echo "=========================================="
echo "FICHAFACIL - iPhone LAN Testing"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get local IP
LOCAL_IP=$(ip route get 1.1.1.1 | awk '{print $7}' | head -n1)
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP="192.168.1.X"
fi

echo -e "${YELLOW}[1] Testing Backend Availability${NC}"
sleep 1
if curl -s http://127.0.0.1:8000/docs > /dev/null; then
    echo -e "${GREEN}✅ Backend running on localhost:8000${NC}"
else
    echo -e "${RED}❌ Backend NOT running${NC}"
    echo "   Start with: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
    exit 1
fi

echo ""
echo -e "${YELLOW}[2] Testing Frontend Availability${NC}"
sleep 1
if curl -s http://127.0.0.1:3000 > /dev/null; then
    echo -e "${GREEN}✅ Frontend running on localhost:3000${NC}"
else
    echo -e "${RED}❌ Frontend NOT running${NC}"
    echo "   Start with: cd frontend && python -m http.server 3000"
    exit 1
fi

echo ""
echo -e "${YELLOW}[3] Testing CORS Headers${NC}"
sleep 1
CORS_TEST=$(curl -i -H "Origin: http://192.168.1.42:3000" \
     -H "Content-Type: application/json" \
     http://127.0.0.1:8000/auth/me 2>/dev/null | grep -i "access-control-allow-origin")

if [ ! -z "$CORS_TEST" ]; then
    echo -e "${GREEN}✅ CORS headers present${NC}"
    echo "   $CORS_TEST"
else
    echo -e "${RED}⚠️  CORS headers might not be configured${NC}"
fi

echo ""
echo -e "${YELLOW}[4] Network Information${NC}"
echo "   Your PC IP: $LOCAL_IP"
echo "   Backend (PC):  http://localhost:8000"
echo "   Backend (LAN): http://$LOCAL_IP:8000"
echo "   Frontend (PC):  http://localhost:3000"
echo "   Frontend (LAN): http://$LOCAL_IP:3000"
echo ""
echo -e "${GREEN}✅ All systems ready for iPhone testing!${NC}"
echo ""
echo "📱  On iPhone (same WiFi):"
echo "    http://$LOCAL_IP:3000"
echo ""
echo "🔍 Debug on PC:"
echo "    http://127.0.0.1:3000/#debug"
echo ""
