# Piloto gratis FichaFácil

Objetivo: publicar una URL usable para un piloto muy pequeño y controlado —por ejemplo 1 negocio familiar con 1 empleado y otro negocio con 2 empleados— intentando mantener coste 0 € durante la validación inicial.

## Qué es este entorno

Este entorno es un **piloto de validación**, no producción contractual.

Sirve para:

- Probar el flujo real desde móvil.
- Validar si el fichaje por PIN es cómodo.
- Detectar fallos de UX antes de pagar infraestructura.
- Enseñar una URL a usuarios de confianza.

No debe venderse todavía como:

- Sistema legal definitivo.
- Servicio con disponibilidad garantizada.
- Entorno con backup profesional.

Texto recomendado si alguien pregunta:

> Estamos probando una herramienta diseñada para ayudar al registro horario. Durante el piloto revisaremos funcionamiento, exportación de datos y fiabilidad.

## Stack de coste 0 objetivo

```text
Netlify Free frontend
  -> /api/* proxy
Render Free web service
  -> Render PostgreSQL Free, si está disponible en la cuenta
```

Notas importantes:

- Render y Netlify pueden cambiar sus planes gratuitos.
- Si Render no ofrece PostgreSQL gratis en la cuenta, hay que elegir entre usar trial/free credits, otro PostgreSQL gratuito, SQLite demo, o pasar a un plan de pago.
- El plan free puede tener cold starts: la primera petición puede tardar bastante.
- El plan free puede tener límites de horas, CPU, memoria, retención o borrado de datos.

## Coste esperado

Coste objetivo inicial:

```text
0 €/mes
```

Coste si hay que pasar a piloto serio:

```text
15-35 €/mes aprox.
```

Desglose típico de piloto serio:

- Netlify Free: 0 €/mes.
- Render web Starter: ~7 $/mes.
- PostgreSQL gestionado de pago/backups: coste según plan, normalmente el principal salto de coste.

## Archivos preparados

Backend Render:

```text
fichafacil/backend/render.yaml
```

Valores clave actuales:

```yaml
services:
  - name: fichafacil-api
    plan: free

databases:
  - name: fichafacil-postgres
    plan: free
```

Frontend Netlify:

```text
fichafacil/frontend/netlify.toml
```

El proxy `/api/*` debe apuntar a la URL real que dé Render. Si Render usa otro nombre de servicio, cambia:

```toml
to = "https://fichafacil-api.onrender.com/:splat"
```

## Pasos que puede hacer Hermes

Hermes puede dejar preparado localmente:

1. Rama y commit de configuración free-pilot.
2. Validación de tests backend.
3. Validación de sintaxis frontend.
4. Documentación de despliegue.
5. Seed demo o instrucciones de seed.
6. E2E contra URLs públicas cuando Álvaro las proporcione.

Hermes no debe crear servicios remotos ni introducir métodos de pago sin confirmación explícita.

## Pasos que debe hacer Álvaro

### 1. GitHub

Subir la rama o mergear a `main`:

```bash
git push -u origin deploy/free-pilot
```

O mergear en GitHub si se abre PR.

### 2. Render

1. Entrar en Render.
2. New > Blueprint.
3. Conectar el repo `Arrojal130/Fichacil`.
4. Seleccionar el blueprint `fichafacil/backend/render.yaml`.
5. Confirmar que el web service y la DB aparecen como `free`.
6. No aceptar cambios a planes de pago si el objetivo es coste 0.
7. Esperar a que el deploy termine.
8. Copiar la URL pública del backend.
9. Probar:

```text
https://<backend-render-url>/health
```

### 3. Netlify

1. Entrar en Netlify.
2. New site from Git.
3. Conectar el mismo repo.
4. Base directory:

```text
fichafacil/frontend
```

5. Publish directory:

```text
.
```

6. Build command vacío, salvo que Netlify obligue a uno.
7. Deploy.
8. Copiar la URL pública del frontend.

### 4. Ajustar CORS y proxy

Cuando existan las URLs reales:

- En Render, `CORS_ORIGINS` debe ser la URL real de Netlify.
- En `fichafacil/frontend/netlify.toml`, `/api/*` debe apuntar a la URL real de Render.

Ejemplo:

```env
CORS_ORIGINS=https://fichafacil-demo.netlify.app
```

```toml
[[redirects]]
  from = "/api/*"
  to = "https://fichafacil-api.onrender.com/:splat"
  status = 200
  force = true
```

Si se cambian estos valores en código, hacer commit y redeploy. Si solo se cambia `CORS_ORIGINS`, redeploy/restart del backend.

## Seed inicial

Para una demo genérica, usar:

```bash
cd fichafacil/backend
DATABASE_URL=<render-postgres-url> DEBUG=false SECRET_KEY=<secret> python scripts/seed_demo.py
```

Credenciales demo actuales:

```text
Admin: gestion@example.com / Test1234!
Empleado 1: DNI 00000001T / PIN 1111
Empleado 2: DNI 00000002R / PIN 2222
```

Para piloto real con tu padre/peluquero, es mejor crear los negocios desde la interfaz admin y evitar dejar datos personales en scripts/commits.

## Backup manual mínimo para piloto gratis

Durante el piloto gratuito, hacer al menos una exportación periódica.

Si Render permite acceder a PostgreSQL por URL externa:

```bash
pg_dump "$DATABASE_URL" > fichafacil-piloto-$(date +%F).sql
```

Si no hay `pg_dump` local, usar la herramienta/export de Render o migrar a plan con backups antes de depender del sistema diariamente.

Frecuencia recomendada durante piloto:

```text
cada 2-3 días o antes/después de una prueba importante
```

## Checklist antes de dar la URL

- `/health` backend responde 200.
- Frontend carga desde Netlify.
- Registro/login admin funciona.
- Crear empleado funciona.
- Login empleado por PIN funciona desde móvil.
- Fichar entrada/salida funciona.
- Historial empleado funciona.
- PIN no aparece en la URL.
- `/debug.html` y `/tests.html` devuelven 404.
- Se entiende que es piloto y no producción con garantía.

## Criterio para pasar a pago

Pasar a plan de pago si se cumple cualquiera:

- Lo usan todos los días durante más de 1-2 semanas.
- Hay que conservar datos laborales sin riesgo.
- El cold start molesta.
- Se lo vas a enseñar a clientes no cercanos.
- Necesitas backups/restore más serios.
- Hay más de 2-3 negocios probándolo.
