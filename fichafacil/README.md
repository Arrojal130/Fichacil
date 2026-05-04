# 🕐 FichaFácil MVP

Sistema de control horario para PYMES españolas, diseñado para ayudar al cumplimiento del registro horario.

## 🎯 Características

- ✅ **Fichaje rápido** - PIN + Geolocalización en <3 segundos
- ✅ **PWA instalable** - Funciona como app nativa en móvil
- ✅ **Dashboard realtime** - Actualización en tiempo real vía SSE
- ✅ **Correcciones con aprobación mutua** - Auditoría completa
- ✅ **PDF de registro** - Exportación diseñada para revisión laboral
- ✅ **Multi-tenant** - Múltiples negocios independientes
- ✅ **Infraestructura $0** - Render.com + Netlify free tier

## 🏗️ Arquitectura

```
┌──────────────────┐     ┌──────────────────┐
│   Frontend PWA   │────▶│   Backend API    │
│    (Netlify)     │     │   (Render.com)   │
│                  │     │                  │
│  - index.html    │     │  - FastAPI       │
│  - empleado.html │     │  - SQLAlchemy    │
│  - dashboard.html│     │  - PostgreSQL prod│
│  - Service Worker│     │  - ReportLab PDF │
└──────────────────┘     └──────────────────┘
```

## 🚀 Quick Start (Local)

### Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno (solo local)
copy .env.example .env
# Editar .env con tu SECRET_KEY

# Ejecutar
uvicorn app.main:app --reload --port 8000
```

API disponible en: http://localhost:8000

### Frontend

```bash
cd frontend

# Servir archivos estáticos (cualquier servidor HTTP)
python -m http.server 3000
# O usar Live Server en VS Code
```

Frontend disponible en: http://localhost:3000

## 📱 Uso

### 1. Registrar negocio

1. Ir a `http://localhost:3000`
2. Click "Administrador"
3. Click "Registrar nuevo negocio"
4. Completar datos del negocio y admin

### 2. Añadir empleados

1. Login como admin en Dashboard
2. Tab "Empleados" → "Añadir"
3. Introducir nombre y PIN de 4 dígitos

### 3. Fichar (empleado)

1. Ir a `http://localhost:3000`
2. Click "Soy Empleado"
3. Buscar el negocio
4. Introducir PIN
5. Pulsar "ENTRADA" o "SALIDA"

## 🌐 Deploy (Producción)

### Backend → Render.com

1. Crear cuenta en [render.com](https://render.com)
2. Conectar repositorio GitHub
3. Crear nuevo "Web Service" para producción real o un entorno de demo/piloto
4. Seleccionar `backend/` como root
5. Build command: `pip install -r requirements.txt`
6. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
7. Añadir/confirmar environment variables de producción:
   - `DEBUG=false`
   - `SECRET_KEY`: valor aleatorio de al menos 32 caracteres (por ejemplo `openssl rand -hex 32`)
   - `DATABASE_URL`: PostgreSQL gestionado; no usar SQLite para datos reales
   - `CORS_ORIGINS`: origen HTTPS exacto del frontend, por ejemplo `https://tu-app.netlify.app`
   - `TRUSTED_PROXY_IPS`: dejar vacío salvo que la plataforma documente rangos de proxy confiables

**Importante:** `backend/.env` y `backend/data/fichafacil.db` solo deben existir en desarrollo o demos locales. No forman parte del flujo normal de producción real.

### Frontend → Netlify

1. Crear cuenta en [netlify.com](https://netlify.com)
2. Drag & drop carpeta `frontend/`
3. O conectar repositorio y especificar `frontend/` como base

### Actualizar URLs

1. En `frontend/netlify.toml`, ajustar el redirect `/api/*` para apuntar al backend HTTPS final de Render si no se usa el valor por defecto del repo.
2. En las variables de entorno gestionadas del backend, actualizar `CORS_ORIGINS` con la URL HTTPS final de Netlify o del dominio propio.

No edites `frontend/js/api.js` para producción: en localhost/LAN usa `:8000` y en orígenes públicos usa `/api`, evitando mixed content y manteniendo las cookies `HttpOnly` en las peticiones proxied.

## 🛡️ Operación, backups y retención

Antes de usar FichaFácil con clientes reales, revisa y ejecuta el runbook de backup/restore: [`docs/ops/backup-restore.md`](docs/ops/backup-restore.md).

La conservación de registros durante 4 años no debe depender solo del disco del servicio web: requiere backups externos, cifrados y restores probados periódicamente.

## 📋 API Endpoints

### Auth
- `POST /api/auth/register` - Registrar negocio + admin
- `POST /api/auth/login` - Login admin
- `POST /api/auth/pin` - Login empleado con PIN
- `GET /api/auth/me` - Usuario actual

### Fichajes
- `POST /api/fichajes` - Registrar fichaje
- `GET /api/fichajes/hoy` - Fichajes de hoy (dashboard)
- `GET /api/fichajes` - Listar fichajes (con filtros)

### Correcciones
- `POST /api/correcciones` - Crear corrección
- `GET /api/correcciones/pendientes` - Pendientes de aprobación
- `POST /api/correcciones/{id}/aprobar` - Aprobar/rechazar

### PDF
- `GET /api/pdf/legal` - Descargar PDF con registro horario

### SSE
- `GET /sse/{negocio_id}` - Stream de eventos realtime

## 🔒 Seguridad

- Contraseñas hasheadas con bcrypt
- PINes hasheados (nunca en texto plano)
- Sesión JWT en cookie `HttpOnly`; `Secure` se fuerza cuando `DEBUG=false`
- Timestamps SIEMPRE del servidor (nunca del cliente)
- CORS configurado por origen HTTPS explícito (`CORS_ORIGINS`)

## 📄 Cumplimiento y validación legal

El sistema está diseñado para ayudar con:

1. **Registro diario** - Hora exacta de inicio y fin de jornada
2. **Conservación 4 años** - Base de datos con backup
3. **Accesibilidad a trabajadores** - App PWA accesible
4. **Registro fiable** - Sin manipulación (servidor timestamps)
5. **Transparencia** - PDF exportable para Inspección de Trabajo

## 🛠️ Tecnologías

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0, PostgreSQL en producción; SQLite solo local/demo
- **Frontend**: HTML5, Tailwind CSS, Vanilla JS
- **PWA**: Service Worker, Web App Manifest
- **Realtime**: Server-Sent Events (SSE)
- **PDF**: ReportLab
- **Auth**: JWT + bcrypt

## 📁 Estructura

```
fichafacil/
├── backend/
│   ├── app/
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── routers/       # API endpoints
│   │   ├── utils/         # Security, geolocation
│   │   ├── config.py      # Settings
│   │   ├── database.py    # DB connection
│   │   └── main.py        # FastAPI app
│   ├── requirements.txt
│   ├── Dockerfile
│   └── render.yaml
└── frontend/
    ├── js/
    │   ├── api.js         # API client
    │   └── utils.js       # Helpers
    ├── index.html         # Landing
    ├── empleado.html      # Clock-in page
    ├── dashboard.html     # Admin panel
    ├── manifest.json      # PWA manifest
    ├── sw.js              # Service worker
    └── netlify.toml       # Deploy config
```

## ✅ Testing Checklist

- [ ] Registrar negocio
- [ ] Login admin
- [ ] Añadir empleado con PIN
- [ ] Fichar entrada (empleado)
- [ ] Ver fichaje en dashboard (realtime)
- [ ] Fichar salida
- [ ] Crear corrección
- [ ] Aprobar/rechazar corrección
- [ ] Generar PDF
- [ ] Instalar PWA en móvil

## 📞 Soporte

Para el piloto con el bar real, contactar al desarrollador.

---

**FichaFácil** - Control horario simple, legal y gratis.
