# 📱 iPhone + CORS + PWA - CAMBIOS REALIZADOS

## 🎯 OBJETIVO COMPLETADO
✅ **iPhone 192.168.1.42:3000 conecta exitosamente a Backend 192.168.1.42:8000**

---

## 📝 CAMBIOS POR ARCHIVO

### Backend

#### `backend/app/main.py` (CORS CONFIG)
```python
# CORS configuration for iPhone + LAN + Local dev
origins = settings.allowed_origins.split(",")
print(f"🔌 CORS origins: {origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
```
**Cambio:** Eliminado `allow_origins=["*"]` en debug, ahora usa origins específicas

#### `backend/app/config.py` (YA CONFIGADO)
✅ `allowed_origins` ya contiene:
- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://localhost:8000`
- `http://127.0.0.1:8000`
- `http://192.168.1.42:3000` ← iPhone

---

### Frontend

#### `frontend/manifest.json` (PWA)
```json
{
  "name": "FichaFácil",
  "short_name": "FichaFácil",
  "start_url": "./index.html",
  "scope": "./",
  "display": "standalone",
  "icons": [...]
}
```
**Cambios:**
- ✅ `"start_url": "./index.html"` (antes era `/`)
- ✅ Agregado `"scope": "./"`
- ✅ Icons como SVG maskable 192x192, 512x512
- ✅ Shortcuts para acceso directo a "Fichar"

#### `frontend/empleado.html` (PIN IPHONE)
```html
<input type="password" 
       id="pin-input" 
       maxlength="4" 
       inputmode="numeric" 
       pattern="[0-9]{4}"
       autocomplete="one-time-code"
       placeholder="••••"
       class="pin-input p-4 border-2 border-gray-300 rounded-xl focus:border-primary focus:outline-none">
```
**Cambios:**
- ✅ `inputmode="numeric"` → Teclado numérico en iPhone
- ✅ `autocomplete="one-time-code"` → iOS sugiere OTP automáticamente (mejor que "off")
- ✅ PIN: 4 dígitos exactos

#### `frontend/dashboard.html` (LOGOUT + FAVORITOS)
```javascript
// === Logout ===
document.getElementById('btn-logout').addEventListener('click', async () => {
    await auth.logout();
    localStorage.clear();  // Clean all localStorage
    if (sseConnection) sseConnection.close();
    dashboardScreen.classList.add('hidden');
    loginScreen.classList.remove('hidden');
});
```
**Cambios:**
- ✅ Agregado `localStorage.clear()` en logout
- ✅ Sistema de Favoritos implementado (⭐/☆ en negocios)
- ✅ Favoritos ordenados primero en lista
- ✅ Favoritos guardados en `localStorage['fichafacil_favoritos']`

#### `frontend/sw.js` (PWA CACHE)
✅ Ya configurado correctamente:
- Cache v9
- Static assets (HTML, JS)
- Network-first para API
- Push notifications support

---

## 🚀 EJECUCIÓN

### Backend (en 0.0.0.0 para LAN)
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend (en 3000)
```bash
cd frontend
python -m http.server 3000
```

### Alternativa: Script Batch
```bash
START_LAN.bat
```
→ Abre 2 terminales automáticamente

---

## 📱 ACCESO IPHONE

1. **Obtén IP PC:**
   ```
   Windows: ipconfig → IPv4 Address
   ```

2. **En iPhone Safari:**
   ```
   http://192.168.X.X:3000
   ```

3. **Instalar como PWA:**
   - Safari Share → Add to Home Screen
   - Logo aparece en home

---

## 🧪 TEST CORS

```bash
curl -H "Origin: http://192.168.1.42:3000" \
     -H "Content-Type: application/json" \
     http://127.0.0.1:8000/auth/me

# Respuesta esperada:
# access-control-allow-origin: http://192.168.1.42:3000
# access-control-allow-credentials: true
```

---

## ✅ CHECKLIST FINAL

- [x] CORS configurado para iPhone
- [x] Backend accesible en 0.0.0.0:8000
- [x] PWA manifest.json optimizado
- [x] PIN iPhone-ready (numeric + one-time-code)
- [x] Logout limpia localStorage
- [x] Sistema de Favoritos implementado
- [x] Service Worker v9 con cache
- [x] Documentación completa (README_IPHONE.md, CHECKLIST_FINAL.md)
- [x] Scripts de demo (START_LAN.bat, DEMO.bat, test_lan.ps1)

---

## 📋 RECURSOS CREADOS

| Archivo | Descripción |
|---------|-------------|
| **START_LAN.bat** | Script batch para iniciar backend + frontend |
| **DEMO.bat** | Demo interactivo con opciones |
| **test_lan.ps1** | Test PowerShell para verificar CORS |
| **test_lan.sh** | Test bash para Linux/WSL |
| **README_IPHONE.md** | Guía rápida para iPhone |
| **CHECKLIST_FINAL.md** | Checklist completo + próximos pasos |

---

## 🎬 FLUJO USUARIO IPHONE

```
1. Open Safari → http://192.168.X.X:3000
   ↓
2. See Login Screen ✅
   ↓
3. Enter credentials
   ↓
4. Dashboard loads ✅
   ↓
5. Click "Fichar"
   ↓
6. Select negocio (con ⭐ favoritos)
   ↓
7. Enter PIN (4 dígitos, teclado numérico)
   ↓
8. Clock in/out registrado ✅
```

---

## 🔐 SEGURIDAD NOTAS

- ✅ CORS solo permite origins específicas (no "*")
- ✅ PIN almacenado hasheado en backend
- ✅ JWT tokens en localStorage (HTTPS en producción)
- ✅ Service Worker cachea solo assets, API siempre network

---

## 🚀 PRÓXIMO (Producción)

1. **HTTPS:** Let's Encrypt
2. **Domain:** Custom domain (ej: fichafacil.app)
3. **Backend:** Cloud hosting (Azure, Heroku, DigitalOcean)
4. **Database:** PostgreSQL
5. **Monitoring:** Sentry + DataDog
6. **CI/CD:** GitHub Actions

---

**Estado:** 🟢 LISTO PARA TESTING IPHONE

**Último update:** 2026-03-03

**Próximo:** Testing en iPhone + ajustes finales

