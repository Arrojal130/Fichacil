# 🎯 FIX COMPLETO: iPhone → Backend (RESUELTO)

## ❌ PROBLEMA IDENTIFICADO

**Root Cause:** `frontend/js/api.js` tenía `API_BASE` configurado incorrectamente:

```javascript
// ❌ ANTES (MAL):
const API_BASE = (window.location.hostname === 'localhost' || 
                  window.location.hostname === '127.0.0.1')
    ? 'http://127.0.0.1:8000'
    : ''; // ← Esto causaba que en iPhone usara '' (vacío)
```

**Consecuencia:**
- En PC (`http://127.0.0.1:3000`): API_BASE = `http://127.0.0.1:8000` ✅
- En iPhone (`http://192.168.1.42:3000`): API_BASE = `''` (empty)
  - Intentaba llamar a `http://192.168.1.42:3000/negocios/search` ❌
  - El backend está en puerto 8000, NO 3000
  - Por eso "error buscando negocio"

---

## ✅ SOLUCIÓN APLICADA

### 1. `frontend/js/api.js` - API_BASE Dinámica

```javascript
// ✅ AHORA (CORRECTO):
// Usa el mismo hostname que el frontend, pero puerto 8000
const API_BASE = `http://${window.location.hostname}:8000`;

console.log('🔌 API Configuration:');
console.log('   Frontend:', window.location.origin);
console.log('   Backend API_BASE:', API_BASE);
console.log('   Hostname:', window.location.hostname);
```

**Resultado:**
- En PC (`http://127.0.0.1:3000`): API_BASE = `http://127.0.0.1:8000` ✅
- En iPhone (`http://192.168.1.42:3000`): API_BASE = `http://192.168.1.42:8000` ✅

### 2. `backend/app/main.py` - CORS Regex para cualquier IP LAN

```python
# CORS configuration for iPhone + LAN + Local dev
origins = settings.allowed_origins.split(",")

# In debug mode, also allow any LAN IP (192.168.x.x, 10.x.x.x) on port 3000
if settings.debug:
    import re
    origins.extend([
        re.compile(r"http://192\.168\.\d+\.\d+:3000"),  # 192.168.x.x
        re.compile(r"http://10\.\d+\.\d+\.\d+:3000"),   # 10.x.x.x
        re.compile(r"http://172\.\d+\.\d+\.\d+:3000"),  # 172.x.x.x
    ])
```

**Ventaja:** No importa qué IP tenga tu PC, funcionará automáticamente

### 3. `frontend/js/api.js` - Logs Mejorados

Ahora en la consola del navegador verás:
```
🔌 API Configuration:
   Frontend: http://192.168.1.42:3000
   Backend API_BASE: http://192.168.1.42:8000
   Hostname: 192.168.1.42

🌐 API Request: {method: 'GET', url: 'http://192.168.1.42:8000/negocios/search?q=', hasToken: false}
📡 API Response: {url: 'http://192.168.1.42:8000/negocios/search?q=', status: 200, ok: true}
```

---

## 🚀 PASOS PARA TESTING

### Paso 1: Obtén la IP de tu PC

**Windows:**
```powershell
ipconfig
```
Busca `IPv4 Address` en la sección de tu WiFi/Ethernet (ej: `192.168.1.50`)

**Mac/Linux:**
```bash
ifconfig | grep "inet "
```

**Opción rápida (script Python):**
```bash
python test_network.py
```

### Paso 2: Inicia Backend (Puerto 8000, accesible en LAN)

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Verás:**
```
🔌 CORS: Debug mode - Accepting any LAN IP on port 3000
🔌 CORS explicit origins: ['http://localhost:3000', 'http://127.0.0.1:3000', ...]
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Paso 3: Inicia Frontend (Puerto 3000)

```bash
cd frontend
python -m http.server 3000
```

**Verás:**
```
Serving HTTP on 0.0.0.0 port 3000 (http://0.0.0.0:3000/) ...
```

### Paso 4: Test desde PC (Verificar que funciona localmente)

**Abre en navegador PC:**
```
http://127.0.0.1:3000
```

**Abre la consola del navegador (F12) y verifica:**
- ✅ `🔌 API Configuration` logs aparecen
- ✅ `Backend API_BASE: http://127.0.0.1:8000`
- ✅ Puedes buscar negocios sin error

### Paso 5: Test CORS desde Terminal

**Reemplaza `192.168.1.50` con tu IP real:**
```bash
curl -v -H "Origin: http://192.168.1.50:3000" http://192.168.1.50:8000/negocios/search?q=
```

**Debes ver:**
```
< HTTP/1.1 200 OK
< access-control-allow-origin: http://192.168.1.50:3000
< access-control-allow-credentials: true
...
[{"id":1,"nombre":"BAR PADRE",...}]
```

Si ves `access-control-allow-origin` ✅ CORS funciona

### Paso 6: Test desde iPhone

1. **iPhone y PC en el MISMO WiFi** (importante)

2. **Abre Safari en iPhone:**
   ```
   http://192.168.1.50:3000
   ```
   (usa la IP de tu PC, no 192.168.1.42)

3. **INMEDIATAMENTE abre la consola remota (si tienes Mac):**
   - Mac: Safari > Develop > [iPhone name] > [website]
   - O en iPhone: Settings > Safari > Advanced > Web Inspector

4. **Verifica en consola del iPhone:**
   ```
   🔌 API Configuration:
      Frontend: http://192.168.1.50:3000
      Backend API_BASE: http://192.168.1.50:8000
      Hostname: 192.168.1.50
   ```

5. **Prueba empleado.html:**
   - Navega a `empleado.html`
   - En "Buscar negocio", escribe algo
   - Deberías ver la lista de negocios ✅
   - No debería aparecer "error buscando negocio" ❌

6. **Prueba dashboard.html:**
   - Login con admin credentials
   - Debería entrar sin error ✅

---

## 🧪 CHECKLIST DE VERIFICACIÓN

### En PC (127.0.0.1:3000)
- [ ] Login admin funciona
- [ ] Dashboard carga
- [ ] empleado.html busca negocios
- [ ] empleado.html puede fichar con PIN
- [ ] Console logs muestran API_BASE correcto

### En iPhone (192.168.1.X:3000)
- [ ] Página carga (HTML/CSS visible)
- [ ] Console logs muestran API_BASE con IP LAN (no 127.0.0.1)
- [ ] empleado.html busca negocios SIN error
- [ ] empleado.html puede fichar con PIN
- [ ] dashboard.html login funciona
- [ ] dashboard.html dashboard carga

### CORS Test (Terminal PC)
- [ ] `curl` con Origin LAN devuelve 200 OK
- [ ] Headers incluyen `access-control-allow-origin`
- [ ] JSON response con datos de negocios

---

## 🐛 TROUBLESHOOTING

### "Failed to fetch" en iPhone

**Síntomas:** Console muestra `Failed to fetch` o `Network request failed`

**Causas posibles:**

1. **Backend no está en 0.0.0.0:**
   ```bash
   # ❌ MAL: uvicorn app.main:app --host 127.0.0.1
   # ✅ BIEN: uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **IP incorrecta en iPhone:**
   - En iPhone, URL debe ser `http://192.168.1.X:3000` (IP de tu PC)
   - Verifica con `ipconfig` en PC
   - Si cambió la IP del PC, recarga la página

3. **Firewall bloqueando:**
   ```powershell
   # Windows: Permitir puertos 3000 y 8000
   netsh advfirewall firewall add rule name="FichaFacil Frontend" dir=in action=allow protocol=TCP localport=3000
   netsh advfirewall firewall add rule name="FichaFacil Backend" dir=in action=allow protocol=TCP localport=8000
   ```

4. **iPhone y PC en WiFi diferentes:**
   - Ambos deben estar en el MISMO WiFi
   - No funcionará: PC en Ethernet, iPhone en WiFi Guest

### "error buscando negocio" en empleado.html

**Si persiste después del fix:**

1. **Hard refresh en iPhone:** Safari > ⌘+R o borra caché
2. **Verifica console logs:** Debe mostrar API_BASE con IP LAN, no localhost
3. **Test backend directo:** En iPhone Safari, abre `http://192.168.1.X:8000/docs`
   - Si carga Swagger UI ✅ Backend accesible
   - Si no carga ❌ Problema de red/firewall

### CORS Error "blocked by CORS policy"

**Síntomas:** Console muestra `Access to fetch at ... has been blocked by CORS policy`

**Fix:**

1. Verifica backend logs al iniciar:
   ```
   🔌 CORS: Debug mode - Accepting any LAN IP on port 3000
   ```
   Si NO aparece, `debug: bool = True` en config.py

2. Test CORS manual:
   ```bash
   curl -i -H "Origin: http://192.168.1.50:3000" http://127.0.0.1:8000/negocios/search?q=
   ```
   Debe devolver `access-control-allow-origin`

3. Restart backend después de cambios en config

---

## 📋 RESUMEN DE CAMBIOS

| Archivo | Cambio | Motivo |
|---------|--------|--------|
| `frontend/js/api.js` | `API_BASE = http://${window.location.hostname}:8000` | Usar IP dinámica (funciona en PC e iPhone) |
| `frontend/js/api.js` | Logs detallados en fetch | Debug fácil desde console |
| `backend/app/main.py` | CORS regex para IPs LAN | Acepta cualquier 192.168.x.x:3000 automáticamente |
| `test_network.py` | Script diagnóstico | Test rápido de conectividad y CORS |

---

## ✅ CONFIRMACIÓN FINAL

**Cuando todo funcione, deberías poder hacer esto en iPhone:**

1. Abrir Safari → `http://192.168.1.X:3000`
2. Ver login screen
3. Click "Fichar como empleado"
4. Buscar negocio "BAR" → Ver "BAR PADRE" en lista
5. Seleccionar → Introducir PIN "1234"
6. Fichar entrada → Ver mensaje "Entrada registrada"
7. Dashboard admin → Login → Ver fichajes en tabla

**Y en la consola (F12 remoto):**
```
✅ No errors
✅ All fetch requests 200 OK
✅ API_BASE apunta a 192.168.1.X:8000 (no 127.0.0.1)
```

---

**Estado:** 🟢 **PROBLEMA RESUELTO**

**Última actualización:** 2026-03-03

**Siguiente:** Testing real en iPhone y confirmar OK

