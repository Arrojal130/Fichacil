# SPEC FICHAFÁCIL - MVP Registro Horario Legal (2026)

**Para agente dev:** Crea MVP funcional en VSCode + Copilot. Stack libre (Python preferido por cliente). Prioridad: **simple, legal-compliant, móvil-first**. Testeable con 1 bar real. Tiempo estimado: 3 días.

---

## 1. CONTEXTO LEGAL (RD 318/2021 + actualizaciones 2026)

**Obligatorio desde 2026 para TODAS empresas:**
- Registro **DIARIO** por empleado: **fecha + hora inicio + hora fin jornada**.
- **Inalterabilidad**: No editable directamente. Correcciones auditadas.
- **Trazabilidad**: Identifica empleado + negocio + timestamp servidor.
- **Geolocalización**: Recomendada (prueba ubicación).
- **Conservación**: 4 años mínimo.
- **PDF inmediato**: Formato Inspección de Trabajo.
- **Multas**: 626€-187.515€.

**Sin selfie/foto** (no obligatorio, descartado por invasivo).

---

## 2. ARQUITECTURA PRODUCTO

**Multi-tenant**: Varios negocios independientes. Cada negocio = cuenta separada.

```
USUARIOS:
├── Dueños (admin/negocio): Config, dashboard, aprobaciones
└── Empleados (user/negocio): Solo fichar entrada/salida

NEGOCIOS:
├── Bar001 (Pedro, 60 años): 1 empleado
├── Peluquería002 (María): 2 empleadas
└── Taller003 (Antonio): 3 mecánicos
```

---

## 3. FLUJOS COMPLETOS (MVP)

### 3.1. REGISTRO NUEVO NEGOCIO (Onboarding presencial - 20min)

```
1. Dueño: "Me llamo Pedro, Bar Madrid, 1 empleado Juan"
2. Sistema: Crea negocio "bar001" + usuario admin Pedro
3. Admin crea empleado: "Juan Pérez - PIN: 1234"
4. Sistema genera enlace invitación empleado
5. Pedro envía WhatsApp: "Juan, usa este enlace + PIN 1234"
6. Imprime pegatina: "FichaFacil - abre fichafacil.es"
```

### 3.2. FICHAJE EMPLEADO (Móvil PWA - 8 segundos)

```
1. Abre fichafacil.es → "Entrar como empleado"
2. Selecciona negocio: "Bar Pedro" (o busca)
3. Introduce PIN: "1234"
4. Geoloc auto (guarda lat/lon)
5. Botón gigante: "🚪 ENTRADA" o "🏠 SALIDA"
6. ✅ "Fichado 08:23 ✓" + sonido/vibración
7. Dueño ve realtime dashboard
```

**Anti-fraude:**
- PIN personal + negocio específico
- Geoloc ±500m del negocio registrado
- Timestamp SERVIDOR (no cliente)

### 3.3. DASHBOARD DUEÑO (Web responsive)

```
PANTALLA PRINCIPAL (tabs):
└── HOY: Tabla realtime
    ├── Juan Pérez | 08:23 | ⏳ Pendiente salida | 40.42/-3.70
    └── María García | 09:15 | 17:32 | 8h17m | 40.43/-3.71

└── ALERTAS ROJAS:
    └── "Juan no fichó salida ayer" → Botón corregir

└── BOTONES:
    ├── 📄 "PDF Personalizado" (elige fechas)
    ├── 👤 "Gestionar empleados" (añadir/editar PIN)
    └── 📧 "Recordatorio Juan" (WhatsApp/email)
```

### 3.4. CORRECCIONES (Aprobación mutua)

```
ESCENARIO: Juan olvidó fichar salida ayer

1. Dueño ve "⏳ Pendiente" rojo
2. Dueño: "Añadir salida manual → 18:00 → Motivo: Olvido"
3. Sistema: "Pendiente aprobación Juan"
4. Juan abre app → "Aprobar corrección" (PIN)
5. Dueño recibe notif: "Juan aprobó. Horas totales: 9h37m"

LOG AUDITORÍA:
"26/02/26 10:15 - Pedro añadió salida Juan 18:00 [Olvido] → Aprobado Juan"
```

### 3.5. EXPORT PDF LEGAL (Personalizable)

```
Botón → Modal fechas:
Desde: 20/02 → Hasta: 26/02 → GENERAR

PDF AUTOMÁTICO:
EMPRESA: Bar Pedro Madrid
NIF: X1234567Z | DIRECCIÓN: C/GranVía 123
PERIODO: 20-26 Febrero 2026

EMPLEADO: Juan Pérez
DNI: 12345678Z
LUN 20/02 | 08:23-18:00 | 9h37m | [Lat/Lon]
MAR 21/02 | 08:30-17:45 | 9h15m | [Lat/Lon]
...

TOTAL SEMANA: 46h45m | HORAS EXTRA: 6h45m
✓ CUMPLE RD 318/2021 | Generado: 27/02/26 09:15 UTC
[Firma digital: UUID]
```

### 3.6. NOTIFICACIONES AUTOMÁTICAS

```
DUEÑO (semanal):
- Email/WhatsApp: "Semana OK. Juan: 46h45m. 0 incidencias"

EMPLEADO (diario):
- Push PWA: "🚨 Ficha salida si no lo has hecho"

CORRECCIONES:
- "Juan debe aprobar tu corrección"
- "Pedro corrigió tu fichaje"
```

---

## 4. ESQUEMA DATOS (DB Relacional)

```sql
TABLA negocios
- id (PK)
- nombre: "Bar Pedro"
- dueño_id (FK users)
- direccion
- lat, lon (centro negocio)
- created_at

TABLA users
- id (PK)
- email
- rol: "admin" | "empleado"
- negocio_id (FK)
- nombre: "Juan Pérez"
- dni
- pin_hash (4 dígitos)
- active

TABLA fichajes
- id (PK)
- empleado_id (FK)
- negocio_id (FK)
- timestamp (servidor)
- tipo: "ENTRADA" | "SALIDA"
- lat, lon
- ip_address
- user_agent
- created_at

TABLA correcciones
- id (PK)
- fichaje_id (FK)
- creador_id (FK)  -- quién propuso
- aprobado_id (FK) -- quién aprobó
- timestamp_original
- timestamp_corregido
- motivo: "Olvido", "Error", "Acuerdo"
- estado: "pendiente", "aprobado", "rechazado"
```

---

## 5. INTERFACES (Wireframes texto)

### 5.1. PWA EMPLEADO (Móvil)

```
[LOGO FichaFacil]          [Notif push activa]

🔍 Buscar negocio: "Bar Pedro"

PIN: [1234]  👁 Ver

[🚪 ENTRADA] [🏠 SALIDA]  ← Botones 80% ancho

Último fichaje:
✅ 08:23 ENTRADA (hace 2h)
📍 120m del bar ✓

Correcciones pendientes: 1
[> Aprobar "Pedro cambió salida 18:00"]
```

### 5.2. DASHBOARD DUEÑO (Web/Móvil)

```
FICHAFÁCIL - Bar Pedro     👤 Juan | ⏳ Pendiente

📊 HOY
Juan Pérez     08:23   ⏳     40.42/-3.70    🔧 Corregir
-----------------------------------------

📄 PDF Semana  👤 Empleados  🔔 Notificaciones

ALERTAS (3)
❌ Juan sin salida ayer
⏰ María llega tarde habitual
📧 Recordatorio pendiente
```

---

## 6. REQUISITOS TÉCNICOS MVP

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| **Frontend** | HTML/JS PWA + Tailwind | React/Vue + PWA |
| **Backend** | Python FastAPI | Node/Express |
| **DB** | SQLite (MVP) | PostgreSQL |
| **Auth** | JWT simple | Auth0/Supabase |
| **Realtime** | Server-Sent Events | WebSocket/Socket.io |
| **PDF** | ReportLab/jsPDF | Puppeteer |
| **Hosting** | Vercel/Netlify free | Railway/Render |
| **Notifs** | Email SMTP | Web Push API |

**Métricas rendimiento:**
- Fichaje: <3seg 99% casos
- PDF: <10seg cualquier rango
- Realtime: <2seg latencia

---

## 7. WORKFLOW DESARROLLO (3 días agente)

```
DÍA 1: Backend + DB
- [ ] Modelos DB (negocios/users/fichajes/correcciones)
- [ ] API fichar (PIN + geoloc + timestamp servidor)
- [ ] API dashboard (fichajes realtime)
- [ ] API PDF rango fechas

DÍA 2: Frontend PWA
- [ ] Pantalla fichaje empleado (buscar + PIN + botones)
- [ ] Dashboard dueño (tabla + alertas + PDF)
- [ ] Sistema correcciones (proponer/aprobar)

DÍA 3: Polish + Deploy
- [ ] Notificaciones básicas (email semanal)
- [ ] Responsive móvil perfecto
- [ ] Deploy Vercel/Netlify
- [ ] Test end-to-end con datos bar padre
```

---

## 8. SUCCESS CRITERIOS MVP

✅ **Funciona con bar padre** (Pedro + Juan real)  
✅ **Empleado ficha en 8seg** desde móvil Android básico  
✅ **Dueño genera PDF legal en 10seg**  
✅ **Corrección completa**: Proponer → Aprobar → Auditada  
✅ **Geoloc guarda/rankea distancia** al negocio  
✅ **Multi-tenant**: 2 negocios independientes  
✅ **0€ infra** (Vercel/Supabase free tier)  
✅ **Instalable PWA** home screen  

---

## 9. DECISIONES TÉCNICAS CLAVE

### 9.1. PIN vs QR
**Decisión:** PIN 4 dígitos (prioridad)
- Más rápido (no sacar cámara)
- Validación: PIN + negocio_id único
- Anti-fraude: Geoloc ±500m

### 9.2. Geolocalización
**Decisión:** Validación flexible ±500m
- Guardar lat/lon siempre
- Mostrar distancia al dueño
- Alerta si >500m pero no bloquea

### 9.3. Correcciones
**Decisión:** Aprobación mutua obligatoria
- Dueño propone → Empleado aprueba
- Empleado propone → Dueño aprueba
- Log auditoría completa

### 9.4. Múltiples locales
**Decisión:** No en MVP (post-lanzamiento)

### 9.5. Horas extras
**Decisión:** Calcular automático, no gestionar
- Mostrar total semanal
- Marcar extras (>40h)
- No cálculo económico (gestión interna)

### 9.6. Export PDF
**Decisión:** Rango personalizable
- Diario/semanal/mensual/custom
- Formato fijo legal
- Descarga inmediata

### 9.7. Invitación empleado
**Decisión:** Link + PIN por WhatsApp
- Dueño genera en dashboard
- Empleado click → registra
- No email obligatorio empleado

### 9.8. Nombre producto
**Opciones:** FichaFacil, FichAgil, Fichacil, FichaTú
**Decisión:** Pendiente validación (usar "FichaFacil" placeholder)

---

## 10. CASOS DE USO DETALLADOS

### Caso 1: Fichaje normal
```
1. Juan llega bar 08:23
2. Abre app → PIN 1234 → ENTRADA
3. Geoloc: 40.42/-3.70 (35m del bar ✓)
4. Timestamp servidor: 2026-02-27 08:23:45 UTC
5. Pedro ve dashboard: "Juan ENTRADA 08:23 ✓"
```

### Caso 2: Olvido fichaje salida
```
1. Juan sale 18:00, olvida fichar
2. Pedro ve "⏳ Pendiente" rojo
3. Pedro: "Añadir salida → 18:00 → Motivo: Olvido"
4. Sistema: Notif Juan "Aprobar corrección"
5. Juan: PIN → "Aprobar"
6. Sistema: 9h37m registradas
```

### Caso 3: Inspección sorpresa
```
1. Inspección: "Fichajes Juan última semana"
2. Pedro: Dashboard → PDF → 20-26 Feb → Generar
3. PDF descarga: 10seg
4. Imprime/entrega → ✓ Cumple RD318/2021
```

### Caso 4: Empleado lejos
```
1. Juan ficha desde casa (2km)
2. Geoloc: 2.1km del bar ⚠️
3. Sistema: Guarda fichaje + alerta Pedro
4. Pedro ve: "Juan fichó 2.1km lejos"
5. Pedro: Llama Juan → Aclarar
```

---

## 11. NOTAS IMPLEMENTACIÓN

### Seguridad
- PIN hash bcrypt (no plaintext)
- JWT tokens (1h expiry)
- HTTPS obligatorio
- Rate limiting (10 req/min)

### Performance
- Index DB: empleado_id, negocio_id, timestamp
- Cache fichajes día actual
- PDF async generation
- Lazy load histórico

### UX Crítico
- Botones táctiles grandes (min 60px)
- Feedback inmediato (<100ms)
- Offline-first PWA (cache last fichaje)
- Modo oscuro opcional

### Legal
- Timestamp UTC + timezone local
- Backup automático 4 años
- Logs inmutables (append-only)
- RGPD: Consentimiento geoloc

---

**AGENTE: Despliega URL testeable. Cliente prueba con bar real. Iteramos.**

**¿Listo para desarrollo?** Copia este MD → VSCode → Copilot → 3 días MVP.