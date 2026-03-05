# 🎯 iPhone Backend Fix - RESUMEN EJECUTIVO

## 🔴 PROBLEMA
iPhone (`http://192.168.1.42:3000`) no podía comunicarse con el backend:
- ❌ "error buscando negocio" en empleado.html
- ❌ Login/registro falla en dashboard.html
- ✅ En PC todo funcionaba perfectamente

## 🔍 CAUSA RAÍZ
`frontend/js/api.js` tenía `API_BASE` mal configurada:
```javascript
// ❌ ANTES (MAL)
const API_BASE = (hostname === 'localhost') ? 'http://127.0.0.1:8000' : '';
//                                                                        ^^^ Vacío!
```

Cuando iPhone abría `http://192.168.1.42:3000`:
- `hostname` = `192.168.1.42` (no es localhost)
- `API_BASE` = `''` (empty string)
- Intentaba llamar a `/negocios/search` → se resolvía como `http://192.168.1.42:3000/negocios/search`
- Backend está en puerto **8000**, no 3000 → **404 Not Found**

## ✅ SOLUCIÓN IMPLEMENTADA

### 1. API_BASE Dinámica (api.js)
```javascript
// ✅ AHORA (CORRECTO)
const API_BASE = `http://${window.location.hostname}:8000`;
```

**Resultado:**
- PC: `http://127.0.0.1:3000` → API_BASE = `http://127.0.0.1:8000` ✅
- iPhone: `http://192.168.1.42:3000` → API_BASE = `http://192.168.1.42:8000` ✅

### 2. CORS Regex para cualquier IP LAN (backend main.py)
```python
if settings.debug:
    origins.extend([
        re.compile(r"http://192\.168\.\d+\.\d+:3000"),  # Acepta cualquier 192.168.x.x
        re.compile(r"http://10\.\d+\.\d+\.\d+:3000"),   # Acepta cualquier 10.x.x.x
    ])
```

### 3. Logs de Debugging (api.js)
Ahora en console verás:
```
🔌 API Configuration:
   Frontend: http://192.168.1.42:3000
   Backend API_BASE: http://192.168.1.42:8000
   Hostname: 192.168.1.42

🌐 API Request: {method: 'GET', url: 'http://192.168.1.42:8000/negocios/search?q='}
📡 API Response: {status: 200, ok: true}
```

### 4. Service Worker Cache Bump
- De v9 → v10 (fuerza reload de api.js cacheado)

---

## 🚀 TESTING (3 PASOS)

### OPCIÓN A: Script Automático (Recomendado)
```bash
# Doble click en:
START_IPHONE.bat

# Hace todo automático:
# 1. Detecta tu IP
# 2. Inicia backend (0.0.0.0:8000)
# 3. Inicia frontend (3000)
# 4. Te dice qué URL abrir en iPhone
```

### OPCIÓN B: Manual

**1. Obtén tu IP:**
```powershell
ipconfig
# Busca: IPv4 Address . . . . . : 192.168.1.X
```

**2. Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verás:
```
🔌 CORS: Debug mode - Accepting any LAN IP on port 3000
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**3. Terminal 2 - Frontend:**
```bash
cd frontend
python -m http.server 3000
```

---

## 📱 VALIDACIÓN EN iPHONE

### Test 1: Backend Accesible
En iPhone Safari, abre:
```
http://192.168.1.X:8000/docs
```
(reemplaza X con tu IP)

✅ **Debería ver:** Swagger UI del backend
❌ **Si no carga:** Backend no accesible desde iPhone (firewall/red)

### Test 2: Frontend + API
En iPhone Safari, abre:
```
http://192.168.1.X:3000
```

**Inmediatamente abre Console (si tienes Mac):**
- Mac Safari > Develop > [iPhone] > [website]

**En Console debes ver:**
```
✅ 🔌 API Configuration:
   Backend API_BASE: http://192.168.1.X:8000   ← Debe ser tu IP, NO 127.0.0.1
   
✅ 🌐 API Request: {url: 'http://192.168.1.X:8000/...'}
✅ 📡 API Response: {status: 200, ok: true}
```

### Test 3: Funcionalidad Completa

**empleado.html:**
1. Click "Fichar como empleado"
2. En buscador, escribe "BAR"
3. ✅ Debería aparecer "BAR PADRE" (NO "error buscando negocio")
4. Click en el negocio
5. Introduce PIN: 1234
6. ✅ Debería fichar correctamente

**dashboard.html:**
1. Click "Login" o botón de admin
2. Introduce credenciales
3. ✅ Debería entrar al dashboard
4. ✅ Ver tabla de fichajes

---

## 🧪 VERIFICACIÓN CORS (Terminal PC)

```bash
# Reemplaza 192.168.1.X con tu IP real
curl -i -H "Origin: http://192.168.1.X:3000" http://127.0.0.1:8000/negocios/search?q=
```

**Debes ver:**
```
HTTP/1.1 200 OK
access-control-allow-origin: http://192.168.1.X:3000   ← IMPORTANTE
access-control-allow-credentials: true
...
[{"id":1,"nombre":"BAR PADRE",...}]
```

Si NO ves `access-control-allow-origin` → CORS no configurado correctamente

---

## 🐛 SI ALGO FALLA

### "Failed to fetch" en iPhone Console

**1. Verifica que backend escucha en 0.0.0.0:**
```bash
# ❌ MAL:
uvicorn app.main:app --host 127.0.0.1

# ✅ BIEN:
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**2. Test conectividad directa:**
```
# En iPhone Safari:
http://192.168.1.X:8000/docs

# Si carga → Backend OK
# Si no carga → Problema de red (firewall/WiFi)
```

**3. Firewall Windows:**
```powershell
# Ejecuta en PowerShell como admin:
netsh advfirewall firewall add rule name="FichaFacil Backend" dir=in action=allow protocol=TCP localport=8000
netsh advfirewall firewall add rule name="FichaFacil Frontend" dir=in action=allow protocol=TCP localport=3000
```

### "error buscando negocio" persiste

**1. Hard refresh en iPhone:**
- Safari > Clear History and Website Data
- O: Hold Shift + Reload

**2. Verifica Console logs:**
- API_BASE debe mostrar IP LAN (192.168.x.x)
- NO debe mostrar 127.0.0.1
- Si muestra 127.0.0.1 → caché viejo de api.js

**3. Verifica Service Worker:**
```javascript
// En Console iPhone:
navigator.serviceWorker.getRegistrations().then(r => r[0].unregister())
// Luego reload
```

### CORS Error

**Console muestra: "blocked by CORS policy"**

1. Verifica backend logs al iniciar:
   ```
   🔌 CORS: Debug mode - Accepting any LAN IP on port 3000
   ```

2. Si no aparece, en `backend/app/config.py`:
   ```python
   debug: bool = True  # ← Asegúrate que está en True
   ```

3. Restart backend después de cambio

---

## ✅ CONFIRMACIÓN FINAL

**Cuando todo funcione, en iPhone podrás:**

| Acción | Resultado Esperado |
|--------|-------------------|
| Abrir `http://192.168.1.X:3000` | ✅ Login screen carga |
| Click "Fichar como empleado" | ✅ Pantalla buscar negocio |
| Buscar "BAR" | ✅ Aparece "BAR PADRE" |
| Seleccionar negocio + PIN 1234 | ✅ Fichar entrada OK |
| Dashboard login | ✅ Entra sin error |
| Ver fichajes | ✅ Tabla con datos |

**Y en Console (F12 remoto):**
- ✅ No hay errores rojos
- ✅ API_BASE = `http://192.168.1.X:8000` (no 127.0.0.1)
- ✅ Todos los fetch devuelven 200 OK

---

## 📋 ARCHIVOS MODIFICADOS

| Archivo | Cambio | Líneas |
|---------|--------|--------|
| `frontend/js/api.js` | API_BASE dinámica + logs | 11-18, 48-65, 88-95 |
| `backend/app/main.py` | CORS regex LAN IPs | 48-61 |
| `frontend/sw.js` | Cache v9 → v10 | 6 |

**Archivos nuevos creados:**
- `START_IPHONE.bat` - Script inicio automático
- `test_network.py` - Diagnóstico red y CORS
- `FIX_IPHONE_BACKEND.md` - Documentación completa

---

## 📊 ANTES vs DESPUÉS

### ANTES ❌
```
iPhone: http://192.168.1.42:3000
   ↓
API_BASE = '' (vacío)
   ↓
Fetch a: http://192.168.1.42:3000/negocios/search
   ↓
404 Not Found (backend está en :8000, no :3000)
   ↓
"error buscando negocio"
```

### DESPUÉS ✅
```
iPhone: http://192.168.1.42:3000
   ↓
API_BASE = http://192.168.1.42:8000 (dinámica!)
   ↓
Fetch a: http://192.168.1.42:8000/negocios/search
   ↓
200 OK + JSON response
   ↓
Lista de negocios aparece correctamente
```

---

**Estado:** 🟢 **PROBLEMA RESUELTO - READY FOR TESTING**

**Último update:** 2026-03-03

**Próximo:** Validar en iPhone real + confirmar todo OK

