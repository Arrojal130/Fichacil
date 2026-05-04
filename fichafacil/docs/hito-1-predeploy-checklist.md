# Hito 1 - MVP predeploy checklist

Objetivo: dejar FichaFácil listo para desplegar, pero parar antes de crear servicios remotos o publicar URLs.

## Stack recomendado

- Frontend: Netlify static site desde `fichafacil/frontend`.
- Backend: Render web service desde `fichafacil/backend`.
- Base de datos: Render PostgreSQL gestionado.
- HTTPS: automático en Netlify/Render.

## Configuración backend Render

Blueprint preparado en:

```text
fichafacil/backend/render.yaml
```

Variables clave antes de desplegar:

```env
DEBUG=false
SECRET_KEY=<generada por Render o valor aleatorio largo>
DATABASE_URL=<Render PostgreSQL connection string>
CORS_ORIGINS=https://<frontend-netlify-o-dominio-final>
TRUSTED_PROXY_IPS=
```

Notas:

- Si Render entrega `postgres://...` o `postgresql://...`, el backend lo normaliza internamente a `postgresql+asyncpg://...`.
- No usar SQLite para datos reales de clientes.
- El comando de arranque debe usar `$PORT`:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Configuración frontend Netlify

Config preparada en:

```text
fichafacil/frontend/netlify.toml
```

Antes de desplegar, revisar:

```toml
[[redirects]]
  from = "/api/*"
  to = "https://<backend-render-url>/:splat"
```

El frontend llama a `/api` en producción y Netlify reescribe hacia Render.

## Seed demo mínimo

Script preparado en:

```text
fichafacil/backend/scripts/seed_demo.py
```

Uso local/remoto:

```bash
cd fichafacil/backend
DATABASE_URL=<database-url> DEBUG=false SECRET_KEY=<secret> python scripts/seed_demo.py
```

Crea o reutiliza:

- Negocio: `demo-fichafacil`
- Admin: `gestion@test.local` / `Test1234!`
- Empleado 1: DNI `00000001T` / PIN `1111`
- Empleado 2: DNI `00000002R` / PIN `2222`

No ejecutar automáticamente en producción real; usar solo para demo/piloto controlado.

## Validación antes de hacer deploy

Desde repo raíz:

```bash
cd /opt/data/repos/Fichacil-git
```

Backend:

```bash
cd fichafacil/backend
../../.venv/bin/python -m unittest discover -s tests -v
```

Frontend:

```bash
cd fichafacil
node --check frontend/js/api.js
node --check frontend/js/utils.js
node --check frontend/sw.js
```

E2E local:

- Arrancar backend con `DEBUG=true` y SQLite temporal.
- Registrar admin.
- Crear empleado.
- Login empleado.
- Fichar entrada/salida.
- Consultar último fichaje e historial.

## Parar aquí antes de desplegar

Cuando este checklist esté verde, el siguiente paso ya tiene efecto externo:

1. Push a GitHub.
2. Crear/actualizar servicios Render/Netlify.
3. Configurar variables reales.
4. Publicar URLs.

Ese punto requiere confirmación explícita.
