# 🚀 FICHAFACIL iPhone - GUÍA RÁPIDA

## ✅ TODO LISTO PARA IPHONE

**Cambios realizados:**
- ✅ CORS configurado para `192.168.1.42:3000`
- ✅ Backend accesible en `0.0.0.0:8000` (toda la LAN)
- ✅ PWA optimized (manifest.json, sw.js)
- ✅ PIN iPhone-ready (inputmode numeric, one-time-code)
- ✅ Logout limpia localStorage
- ✅ Sistema de Favoritos implementado

---

## 🎯 INICIO RÁPIDO (5 minutos)

### Opción A: Script Batch (Recomendado)
```bash
# Windows - Doble click
START_LAN.bat
```
Abre 2 terminales automáticamente:
- Terminal 1: Backend (8000)
- Terminal 2: Frontend (3000)

### Opción B: Manual (2 Terminales)

**Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
python -m http.server 3000
```

---

## 📱 ACCESO DESDE IPHONE

1. **PC y iPhone en MISMO WiFi**

2. **Obtén IP de tu PC:**
   ```
   Windows: ipconfig
   Mac: ifconfig
   
   Busca: IPv4 Address: 192.168.X.X
   ```

3. **En iPhone Safari:**
   ```
   http://192.168.X.X:3000
   ```
   (Reemplaza X.X con tu IP)

4. **Prueba:**
   - Login screen debe aparecer ✅
   - Escribe credenciales
   - Debe conectar a backend ✅

---

## 🧪 TEST CORS (PC Terminal)

```bash
curl -H "Origin: http://192.168.1.42:3000" \
     -H "Content-Type: application/json" \
     http://127.0.0.1:8000/auth/me
```

**Espera:** Headers con `access-control-allow-origin`

---

## 📲 PWA en iPhone

1. En Safari: Share button (cuadrado con flecha arriba)
2. "Add to Home Screen"
3. Nombre: FichaFacil
4. Click "Add"

Hecho ✅ - Aparece como app nativa

---

## 🔍 DEBUG en iPhone

**Opción 1: Safari Remote Inspector**
```
Mac: Safari > Develop > <iPhone> > <website>
```

**Opción 2: Console logs en PC**
En Terminal 2 (Frontend), verás los requests

---

## ❌ SI FALLA

### "Cannot reach server" en iPhone
```
✅ Verifica:
1. iPhone y PC en mismo WiFi
2. PC IP correcto (ipconfig)
3. Backend terminal muestra "Application startup complete"
4. Frontend terminal sin errores
5. Firewall no bloquea puertos 3000, 8000
```

### CORS Error en F12
```
✅ Verifica:
1. backend/app/config.py tiene http://192.168.1.X:3000 en allowed_origins
2. main.py está usando esas origins
3. Backend corriendo con --host 0.0.0.0
```

### PIN Error 422
```
✅ PIN debe ser EXACTAMENTE 4 dígitos
1. Test en empleado.html
2. Backend schema permite 4 dígitos
```

---

## 📋 ARCHIVOS MODIFICADOS

- ✅ `backend/app/main.py` - CORS optimizado
- ✅ `frontend/manifest.json` - PWA lista
- ✅ `frontend/empleado.html` - PIN inputmode, autocomplete
- ✅ `frontend/dashboard.html` - Logout limpia localStorage
- ✅ `frontend/sw.js` - Cache PWA

---

## 🎬 DEMO SCRIPT

1. Abre START_LAN.bat
2. En iPhone: http://192.168.X.X:3000
3. Login con credenciales
4. Fichar → Selecciona negocio → PIN 1234
5. ¡Done! ✅

---

## 🚀 PRÓXIMO

Cuando esté todo OK en LAN:
- Deploy a Azure/Heroku (HTTPS)
- Custom domain
- Production secrets

---

**Estado:** 🟢 LISTO PARA IPHONE

**Última actualización:** 2026-03-03

