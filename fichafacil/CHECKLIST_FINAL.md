# 🚀 FICHAFACIL - FINAL CHECKLIST

## ✅ FASE COMPLETADA: Depuración + iPhone + PWA

### 🔧 Cambios Realizados

#### Backend (CORS + LAN)
- ✅ `backend/app/main.py` - CORS configurado para:
  - `http://localhost:3000` (dev local)
  - `http://127.0.0.1:3000` (dev local)
  - `http://192.168.1.42:3000` (iPhone LAN)
  - Y otros locales en env

- ✅ Ejecutar con: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
  - `--host 0.0.0.0` = accesible desde toda la LAN
  - `--port 8000` = puerto consistente

#### Frontend (PWA iPhone)
- ✅ `frontend/manifest.json`
  - `"start_url": "./index.html"` (entry point correcto)
  - `"scope": "./"` (PWA scope)
  - Icons 192x192 + 512x512 (SVG maskable)
  - Shortcuts agregados (Fichar directamente)

- ✅ `frontend/empleado.html`
  - PIN input: `inputmode="numeric"` ✓
  - PIN input: `autocomplete="one-time-code"` (mejor que "off" para iPhone)
  - PIN: 4 dígitos exactos
  - CSS mejorado (grande, visible)

- ✅ `frontend/dashboard.html`
  - Login es entrada por defecto
  - "Registra tu negocio" → Wizard Onboarding
  - Logout limpia `localStorage.clear()`
  - Logout redirige a login
  - Sistema de Favoritos implementado

#### Service Worker (sw.js)
- ✅ Cache crítico:
  - `index.html`, `empleado.html`, `dashboard.html`
  - `js/api.js` (API client)
  - `manifest.json`
  - CSS crítico

---

## 🧪 TESTING CHECKLIST

### PC (Localhost)
```
✅ http://localhost:3000 → Login screen
✅ Login → Dashboard o Onboarding
✅ Fichar → Seleccionar negocio → Validar PIN
✅ Dashboard → Gráficos, estadísticas
✅ Logout → localStorage limpio, vuelve a login
```

### iPhone (LAN)
```
⏳ http://192.168.1.42:3000 → Debe ver frontend
⏳ Login → Debe conectar backend en 192.168.1.42:8000
⏳ Network tab (F12) → No hay errores CORS
⏳ Fichar → Registra hora en backend
⏳ "Add to Home Screen" → PWA instalada
⏳ Modo offline → Último fichaje en cache
```

### CORS Test (PC Terminal)
```bash
curl -H "Origin: http://192.168.1.42:3000" \
     -H "Content-Type: application/json" \
     http://localhost:8000/auth/me

# Respuesta esperada:
# {
#   "access-control-allow-origin": "http://192.168.1.42:3000",
#   "access-control-allow-credentials": "true"
# }
```

---

## 🚀 EJECUCIÓN RÁPIDA

### Opción 1: Script Batch (Windows)
```
Doble click en: START_LAN.bat
- Abre Terminal 1: Backend (8000)
- Abre Terminal 2: Frontend (3000)
- Muestra instrucciones
```

### Opción 2: Manual (2 Terminales)

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

### Opción 3: Docker (Producción)
```bash
docker-compose up
# Backend en 0.0.0.0:8000
# Frontend en 0.0.0.0:3000
```

---

## 📱 iPhone Access

1. **Obtén tu IP PC:**
   ```powershell
   ipconfig
   # Busca IPv4 Address: 192.168.1.X
   ```

2. **En iPhone (mismo WiFi):**
   - Safari: `http://192.168.1.X:3000`
   - F12 (Remoto) → DevTools en PC

3. **PWA Installation:**
   - Share button → "Add to Home Screen"
   - Icon aparece en home
   - Funciona sin internet (últimas acciones)

---

## 🐛 Si Algo Falla

### CORS Error (iPhone)
```
❌ Failed to fetch (CORS)
→ Verifica: http://192.168.1.42:3000 en config.py:allowed_origins
→ Uvicorn corriendo con --host 0.0.0.0
→ Backend accesible: curl http://192.168.1.42:8000/docs
```

### PIN Error 422
```
❌ Validation error
→ PIN debe ser EXACTAMENTE 4 dígitos
→ Verificar: backend/app/schemas/user.py EmpleadoCreate
→ Verificar: empleado.html PIN input maxlength="4"
```

### Sin conexión en iPhone
```
❌ Network error
→ iPhone y PC en mismo WiFi
→ Firewall permite puertos 3000 y 8000
→ Backend log muestra origen: "Origin: http://192.168.1.42:3000"
```

### PWA no instala
```
❌ No puede añadir a pantalla principal
→ Acceder vía HTTPS o localhost (PWA requires HTTPS en prod)
→ manifest.json en <head> de index.html
→ Icons correctos en manifest
```

---

## 🎯 PRÓXIMOS PASOS (Producción)

1. **HTTPS:** Usar Let's Encrypt + Nginx
2. **Domain:** fichafacil.app o custom domain
3. **Push Notifications:** Configurar VAPID keys
4. **Backend Env:** PostgreSQL + Producción secrets
5. **CI/CD:** GitHub Actions → Deploy automático
6. **Monitoring:** Sentry + DataDog

---

## 📋 DATOS DE PRUEBA

**Negocio:**
- Nombre: "BAR PADRE"
- Slug: "bar-padre"
- Ubicación: 40.4168, -3.7038 (Madrid)

**Empleado:**
- Nombre: "Juan García"
- PIN: "1234"
- DNI: "12345678A"

---

## ✨ FEATURES COMPLETADAS

### Fase 1: UX Móvil ✅
- Responsive login/onboarding
- Wizard setup (3 pasos)
- Dashboard con gráficos

### Fase 2: Dashboard Visual ✅
- Badges de color por estado
- Tabla responsive
- Total de semana

### Fase 3: Correcciones ✅
- Modal edición
- PDF con asteriscos
- Justificaciones

### Fase 4: Push Notifications ✅
- PWA Service Worker
- SSE Backend
- Permisos en navegador

### Fase 5: Onboarding Wizard ✅
- 3-step fullscreen
- 4-dígit PIN
- Validación backend

### Fase 6: Depuración ✅
- Login flow correcto
- CORS iPhone configurado
- PWA optimizada
- Favoritos implementados
- Logout limpia storage

---

**Estado:** 🟢 PRODUCCIÓN READY (LAN Testing)

**Próximo:** Deploy a servidor accesible desde internet

