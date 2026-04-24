# FichaFácil Backup / Restore Runbook

Estado: obligatorio antes de clientes reales.

## Objetivo

Garantizar que los registros horarios y datos asociados se conservan durante al menos 4 años, con capacidad demostrable de restauración.

## Alcance de datos

Datos a proteger:
- negocios
- usuarios/admins/empleados
- hashes de contraseñas y PINs
- fichajes originales
- correcciones y aprobaciones
- logs/auditoría futuros
- PDFs/exportaciones si se almacenan en el futuro

## Política mínima MVP

- **RPO objetivo:** pérdida máxima aceptable de 24h para piloto inicial; 1h para producción real.
- **RTO objetivo:** restauración en menos de 4h para piloto; menos de 1h para producción real.
- **Retención:** 4 años completos desde la fecha del registro.
- **Cifrado:** backups cifrados en reposo y en tránsito.
- **Prueba de restore:** mensual como mínimo; semanal durante los primeros pilotos.
- **Responsable:** el operador del servicio debe revisar alertas de backup a diario.

## Recomendación para clientes reales

No usar SQLite sobre Render free para clientes reales. Usar PostgreSQL gestionado con:
- backups automáticos diarios del proveedor,
- point-in-time recovery si está disponible,
- snapshots/manual exports antes de despliegues importantes,
- monitorización de job de backup,
- cuenta/credenciales separadas para backup con mínimo privilegio.

## Procedimiento temporal para demo SQLite

Solo aceptable para demos y pilotos sin datos sensibles reales.

### Backup manual SQLite

Desde el host/servicio con acceso al disco persistente:

```bash
sqlite3 /app/data/fichafacil.db ".backup '/app/data/backups/fichafacil-$(date -u +%Y%m%dT%H%M%SZ).db'"
```

Después, copiar el backup a almacenamiento externo cifrado. No dejar la única copia en el mismo disco de Render.

### Verificación de integridad SQLite

```bash
sqlite3 /app/data/backups/<backup>.db "PRAGMA integrity_check;"
```

Debe devolver:

```text
ok
```

### Restore SQLite

1. Parar el servicio o ponerlo en mantenimiento.
2. Guardar copia del estado actual:
   ```bash
   cp /app/data/fichafacil.db /app/data/fichafacil.before-restore.$(date -u +%Y%m%dT%H%M%SZ).db
   ```
3. Restaurar backup:
   ```bash
   cp /app/data/backups/<backup>.db /app/data/fichafacil.db
   ```
4. Verificar integridad:
   ```bash
   sqlite3 /app/data/fichafacil.db "PRAGMA integrity_check;"
   ```
5. Arrancar servicio y probar `/health`, login admin y exportación PDF.

## Procedimiento recomendado PostgreSQL

### Backup lógico diario

```bash
pg_dump "$DATABASE_URL" --format=custom --no-owner --no-acl \
  --file "fichafacil-$(date -u +%Y%m%dT%H%M%SZ).dump"
```

Cifrar antes de subir a almacenamiento externo:

```bash
gpg --symmetric --cipher-algo AES256 fichafacil-YYYYMMDDTHHMMSSZ.dump
```

### Restore PostgreSQL en entorno temporal

```bash
createdb fichafacil_restore_check
pg_restore --dbname fichafacil_restore_check --clean --if-exists fichafacil-YYYYMMDDTHHMMSSZ.dump
```

Verificaciones mínimas:

```sql
select count(*) from negocios;
select count(*) from users;
select count(*) from fichajes;
select count(*) from correcciones;
```

Luego ejecutar smoke test de API contra esa base restaurada.

## Alertas obligatorias

Generar alerta si:
- no se ha creado backup en las últimas 24h,
- el tamaño del backup cambia de forma anómala,
- falla `PRAGMA integrity_check` o restore temporal,
- el almacenamiento externo rechaza subida,
- quedan menos de 20% de disco libre.

## Antes de cada despliegue

1. Confirmar último backup correcto.
2. Crear backup manual si hay migraciones.
3. Ejecutar migraciones en staging/restored copy.
4. Desplegar.
5. Smoke test post-deploy.

## Checklist mensual de restore

- [ ] Descargar backup desde almacenamiento externo.
- [ ] Descifrarlo.
- [ ] Restaurarlo en entorno temporal.
- [ ] Ejecutar checks de conteo e integridad.
- [ ] Generar un PDF de un periodo de prueba.
- [ ] Registrar fecha, backup probado y resultado.

## Incidente: fallo de backup

1. Marcar incidente operativo.
2. No hacer despliegues ni migraciones hasta recuperar backups.
3. Crear backup manual inmediato si la DB está sana.
4. Revisar credenciales, espacio, conectividad y permisos.
5. Documentar causa raíz y corrección.
