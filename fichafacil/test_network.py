#!/usr/bin/env python3
"""
FichaFacil - Network Diagnostic Tool
Tests backend connectivity from different network locations
"""
import subprocess
import socket
import sys
import json

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Connect to external address to find local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Unable to detect"

def test_backend(host, port=8000):
    """Test if backend is reachable"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def test_cors(origin, backend_url):
    """Test CORS headers using curl"""
    cmd = [
        'curl', '-i', '-s',
        '-H', f'Origin: {origin}',
        '-H', 'Content-Type: application/json',
        f'{backend_url}/negocios/search?q='
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        output = result.stdout
        
        # Check for CORS header
        has_cors = 'access-control-allow-origin' in output.lower()
        has_200 = 'HTTP/1.1 200 OK' in output or '200 OK' in output
        
        return has_cors, has_200, output
    except Exception as e:
        return False, False, str(e)

def main():
    print("=" * 60)
    print("FichaFácil - Network Diagnostic Tool")
    print("=" * 60)
    print()
    
    # Get local IP
    local_ip = get_local_ip()
    print(f"📍 Your PC IP: {local_ip}")
    print()
    
    # Test backend on localhost
    print("🧪 Testing Backend Connectivity:")
    print("-" * 60)
    
    localhost_ok = test_backend('127.0.0.1', 8000)
    print(f"   localhost:8000  ... {'✅ REACHABLE' if localhost_ok else '❌ NOT REACHABLE'}")
    
    if local_ip != "Unable to detect":
        lan_ok = test_backend(local_ip, 8000)
        print(f"   {local_ip}:8000 ... {'✅ REACHABLE' if lan_ok else '❌ NOT REACHABLE'}")
    
    print()
    
    if not localhost_ok:
        print("❌ Backend is NOT running!")
        print("   Start it with:")
        print("   cd backend")
        print("   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        print()
        return 1
    
    # Test CORS
    print("🔐 Testing CORS Configuration:")
    print("-" * 60)
    
    test_cases = [
        ("http://localhost:3000", f"http://127.0.0.1:8000"),
        ("http://127.0.0.1:3000", f"http://127.0.0.1:8000"),
    ]
    
    if local_ip != "Unable to detect":
        test_cases.append((f"http://{local_ip}:3000", f"http://{local_ip}:8000"))
    
    all_ok = True
    for origin, backend in test_cases:
        has_cors, has_200, output = test_cors(origin, backend)
        
        status = "✅" if (has_cors and has_200) else "❌"
        print(f"   {status} Origin: {origin}")
        
        if has_cors:
            print(f"      CORS: ✅ Headers present")
        else:
            print(f"      CORS: ❌ Headers missing")
            all_ok = False
        
        if has_200:
            print(f"      HTTP: ✅ 200 OK")
        else:
            print(f"      HTTP: ❌ Error response")
            all_ok = False
        
        print()
    
    # Summary
    print("=" * 60)
    print("📋 Summary:")
    print("=" * 60)
    
    if all_ok:
        print("✅ All tests passed! iPhone should work.")
        print()
        print("📱 On iPhone (same WiFi), open Safari and go to:")
        print(f"   http://{local_ip}:3000")
        print()
        print("🔧 Make sure:")
        print("   1. Backend running: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("   2. Frontend running: python -m http.server 3000 (in frontend/)")
        print("   3. iPhone on same WiFi network")
        print()
        return 0
    else:
        print("⚠️  Some tests failed. Check:")
        print("   1. Backend running with --host 0.0.0.0")
        print("   2. CORS configured in backend/app/config.py")
        print("   3. Firewall allows ports 3000 and 8000")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
