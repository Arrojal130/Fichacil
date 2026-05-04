# FichaFácil Production Hardening Implementation Plan

> **For Hermes:** Use test-driven-development for behavior changes and requesting-code-review before final commit/PR.

**Goal:** Make FichaFácil safe enough for real-client MVP pilots by closing blocking risks in data integrity, secrets, backups, tests, deploy, and UX/security.

**Architecture:** Keep the current FastAPI + static PWA architecture for speed, but harden the boundaries. The legal time-register domain must become append-only: original fichajes remain immutable and corrections are represented as audit events/effective timestamps, not destructive updates. Operationally, move from ad-hoc SQLite-on-free-tier assumptions toward documented backup/restore and a path to managed PostgreSQL.

**Tech Stack:** FastAPI, SQLAlchemy async, Pydantic v2, SQLite for local/demo, Render/Netlify deployment, vanilla JS frontend, Python unittest/pytest-compatible tests, GitHub Actions.

---

## Phase 0 — Bloqueante antes de clientes reales

### Task 0.1: Remove secrets and SQLite data from Git tracking

**Objective:** Prevent `.env` and runtime databases from being committed again.

**Files:**
- Modify: `fichafacil/.gitignore`
- Untrack: `fichafacil/backend/.env`
- Untrack: `fichafacil/backend/data/fichafacil.db`
- Modify: `fichafacil/backend/.env.example`

**Steps:**
1. Add explicit ignore rules for `**/.env`, `backend/data/`, `*.db`, and SQLite sidecar files.
2. Run `git rm --cached fichafacil/backend/.env fichafacil/backend/data/fichafacil.db` from repo root.
3. Replace `.env.example` placeholders with safe documentation-only values.
4. Generate a fresh local `SECRET_KEY` in untracked `.env`.
5. Verify with `git ls-files | grep -E '(\.env$|\.db$)'` returns nothing.

**Verification:**
```bash
git status --porcelain=v1
git ls-files | grep -E '(\.env$|\.db$)' || true
```

### Task 0.2: Make fichajes immutable under correction approval

**Objective:** Corrections must never overwrite the original `Fichaje.timestamp`.

**Files:**
- Modify: `fichafacil/backend/app/routers/correcciones.py`
- Test: `fichafacil/backend/tests/test_correcciones_immutability.py`

**Steps:**
1. Add a failing unit test proving approval does not assign `fichaje.timestamp`.
2. Remove destructive updates in both admin and employee approval flows.
3. Add helper functions later for effective timestamp in reports if needed.
4. Run correction tests and full unittest suite.

**Verification:**
```bash
cd fichafacil/backend
python -m unittest tests.test_correcciones_immutability -v
python -m unittest discover -s tests -v
```

### Task 0.3: Design real backup/restore path

**Objective:** Document an operationally realistic backup/restore runbook before client data.

**Files:**
- Create: `fichafacil/docs/ops/backup-restore.md`
- Modify: `fichafacil/README.md`

**Minimum content:**
- Current SQLite demo backup procedure.
- Recommended MVP production PostgreSQL path.
- Daily encrypted backup schedule.
- 4-year retention policy.
- Monthly restore drill.
- RPO/RTO targets.
- Incident response if backup fails.

**Verification:**
Documentation reviewed and linked from README.

### Task 0.4: Stop sending PINs in query strings

**Objective:** Employee PINs must only travel in request bodies or short-lived tokens, never URL query strings.

**Files:**
- Modify: `fichafacil/backend/app/schemas/fichaje.py`
- Modify: `fichafacil/backend/app/schemas/correccion.py`
- Modify: `fichafacil/backend/app/routers/fichajes.py`
- Modify: `fichafacil/backend/app/routers/correcciones.py`
- Modify: `fichafacil/frontend/js/api.js`
- Tests: add request-schema/router tests.

**Endpoints to change:**
- `GET /fichajes/ultimo?negocio_id=...&pin=...` -> `POST /fichajes/ultimo`
- `GET /fichajes/historial-empleado?...&pin=...` -> `POST /fichajes/historial-empleado`
- `GET /correcciones/pendientes-empleado?...&pin=...` -> `POST /correcciones/pendientes-empleado`

**Verification:**
Search for `pin=` in frontend/backend and ensure no URL usage remains.

### Task 0.5: Fix tests and add CI

**Objective:** Make quality gate repeatable locally and in GitHub Actions.

**Files:**
- Modify: `fichafacil/backend/tests/test_config_cors_settings.py` or config test bootstrap.
- Modify: `fichafacil/backend/requirements.txt` or add test requirements.
- Create: `.github/workflows/backend-tests.yml`

**Steps:**
1. Ensure tests are isolated from real `.env`.
2. Add pytest if the workflow uses pytest, or standardize on unittest.
3. CI installs backend requirements and runs test suite.

**Verification:**
```bash
cd fichafacil/backend
python -m unittest discover -s tests -v
```

### Task 0.6: Remove debug/test pages from production

**Objective:** Prevent production deployment/caching of `debug.html` and `tests.html`.

**Files:**
- Modify: `fichafacil/frontend/sw.js`
- Modify: `fichafacil/frontend/netlify.toml`
- Optionally move pages to `frontend/dev/` or block them in Netlify.

**Verification:**
- `sw.js` no longer lists `/debug.html`.
- Netlify returns 404/blocked for `/debug.html` and `/tests.html`.

---

## Phase 1 — Antes de demo con terceros

### Task 1.1: Sanitize frontend rendering against XSS

**Objective:** User-controlled names/details must not be injected through raw `innerHTML`.

**Files:**
- Modify: `fichafacil/frontend/js/utils.js`
- Modify: `fichafacil/frontend/dashboard.html`

**Steps:**
1. Add `escapeHtml(value)` utility.
2. Replace interpolated untrusted values in `innerHTML` templates.
3. Prefer `textContent`/DOM APIs where simple.

**Verification:**
Manual browser test with employee name `<img src=x onerror=alert(1)>` renders as text.

### Task 1.2: Disable or protect Swagger/OpenAPI in production

**Objective:** API docs should not be public unless debug is enabled.

**Files:**
- Modify: `fichafacil/backend/app/main.py`
- Test: config/main app docs URLs.

**Verification:**
`DEBUG=false` disables `/docs`, `/redoc`, `/openapi.json`; debug keeps local docs.

### Task 1.3: Make deployment always-on for demos

**Objective:** Avoid cold starts during demos and pilots.

**Files:**
- Modify: `fichafacil/backend/render.yaml`
- Modify docs.

**Steps:**
1. Change Render plan from `free` to at least `starter` for production/demo service.
2. Document free tier as local/demo only.

### Task 1.4: Improve backend unavailable UX

**Objective:** Users must see a clear message when the backend is sleeping/down.

**Files:**
- Modify: `fichafacil/frontend/js/api.js`
- Modify pages that call API if needed.

**Behavior:**
Network failures should show: “No se ha podido contactar con FichaFácil. El fichaje no se ha registrado todavía. Reintenta en unos segundos.”

### Task 1.5: Remove over-strong legal claims

**Objective:** Avoid claiming full compliance before legal validation.

**Files:**
- Modify: `fichafacil/README.md`
- Modify: `fichafacil/backend/app/main.py`
- Modify: `fichafacil/backend/app/routers/pdf.py`
- Modify frontend marketing copy if present.

**Replacement principle:** “Diseñado para ayudar al cumplimiento” instead of “cumple”.

---

## Final verification checklist

Run before PR/merge:

```bash
cd /opt/data/repos/Fichacil-git

git status --porcelain=v1
git ls-files | grep -E '(\.env$|\.db$|__pycache__|\.pyc$)' || true
cd fichafacil/backend && python -m unittest discover -s tests -v
```

Manual smoke tests:
- Admin register/login.
- Add employee.
- Employee fichar entrada/salida.
- Correction approval preserves original record and PDF/report shows corrected effective value or correction note.
- Backend-down UX message appears on network failure.
- `/debug.html` and `/tests.html` are unavailable in production deployment.
