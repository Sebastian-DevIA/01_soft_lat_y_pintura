# CLAUDE.md — Contexto para Agentes IA

Archivo dirigido a Claude Code y agentes IA. Documentación para humanos: ver `README.md`.

---

## Protocolo de trabajo (leer primero)

Al iniciar **cualquier** sesión o tarea en este proyecto:

1. Lee este `CLAUDE.md` y el `README.md`.
2. Abre `MEMORY.md` (en la raíz del repo). **Si no existe, créalo.** Es el
   **control vivo de pendientes** y la fuente de qué hay que hacer.
3. Trabaja los pendientes **desde `MEMORY.md`**, en **modo agents teams** (delega a
   los sub-agentes; ver "Equipo de agentes").
4. Al **completar** un pendiente: márcalo `- [x]` y **elimínalo** de `MEMORY.md`
   (deja solo lo que sigue pendiente). Pendientes nuevos se **agregan** ahí.
5. Mantén `CLAUDE.md` y `README.md` **actualizados** cuando cambien hechos del
   proyecto (endpoints, convenciones, estructura), **sin agregar de más**.

---

## Propósito

Sistema de gestión operacional para un taller de latonería y pintura automotriz.
**Contexto real:** 10–20 vehículos/mes, 1–3 operadores. **Objetivo del repo:**
portafolio público de Sebastian Miranda para postulaciones junior Python/FastAPI.

---

## Stack

```
Python 3.11+ · FastAPI 0.111 · SQLAlchemy 2.0 (síncrono) · SQLite 3
Alembic 1.13 · Pydantic v2 · python-jose (JWT) · passlib/bcrypt
WeasyPrint 62.3 + Jinja2 (PDF) · pytest 8.3 + httpx · python-multipart
Frontend: HTML/CSS/JS Vanilla (sin frameworks)
```

---

## Convenciones de código

- **Schemas Pydantic v2**: sufijo `Request` (entrada) / `Response` (salida). Nunca
  retornar un modelo SQLAlchemy directo — siempre pasar por un schema `Response`.
- **Separación de capas**: `routers/` solo orquesta (request → service → response);
  `services/` toda la lógica de negocio; `models/` solo tablas; `dependencies/` =
  `get_db`, `get_current_user`.
- **`autoflush=False`**: `SessionLocal` no auto-flushea. En los services, antes de
  `_recalcular_totales` (que hace un query) llama `db.flush()` para que los objetos
  pendientes (`add`/`delete`) sean visibles en el query.

---

## State machine de OrdenTrabajo

```python
TRANSICIONES_VALIDAS = {
    "PERITAJE":   ["COTIZACION", "CANCELADO"],
    "COTIZACION": ["APROBACION", "CANCELADO"],
    "APROBACION": ["EN_PROCESO", "CANCELADO"],
    "EN_PROCESO": ["ENTREGADO",  "CANCELADO"],
    "ENTREGADO":  [],
    "CANCELADO":  [],
}
```

Validación en `backend/app/services/orden_service.py`.

### Reglas de negocio críticas

1. **Factura** solo se emite si `OrdenTrabajo.estado == "APROBACION"`.
2. **Fase ENTREGA** solo se completa si `Factura.estado == "PAGADA"`.
3. Al **aprobar**, `orden_service._crear_fases()` crea 3 `FaseTrabajo`
   (`INGRESO`, `REPARACION`, `ENTREGA`) en `PENDIENTE`.
4. **Descuento** se aplica sobre el total de ítems (no individual).
5. El **adelanto** es exactamente el 50% del `total_con_descuento`.
6. Orden **CANCELADA** o **ENTREGADA** no se puede modificar.

---

## Detalles no obvios (gotchas)

- **Respuestas de órdenes enriquecidas**: `OrdenResumenResponse` y
  `OrdenDetalleResponse` incluyen `vehiculo_placa`, `vehiculo_descripcion` y
  `cliente_nombre`, poblados en `orden_service` (`_campos_planos` +
  `_a_resumen_response`/`_a_detalle_response`). **Cualquier endpoint nuevo que
  retorne una orden debe pasar por esos helpers** o los campos planos saldrán `null`.
- `AsignacionResponse.personal_nombre` se puebla en `fase_service` con
  `joinedload(FaseTrabajo.asignaciones).joinedload(Asignacion.personal_asignado)`.
- **PDF de factura**: el front lo descarga con `fetch`+JWT → `Blob` → object URL
  (`api.facturas.pdfBlob()`); un `<a href>` plano da **401**. Jinja con `autoescape`
  (datos de cliente). El IVA es **display-only** (no toca `monto_total` ni el 50%);
  tasa en `Settings.iva_porcentaje` (default 19).
- **Soft-delete**: `Cliente`, `Vehiculo`, `Personal` y `OrdenTrabajo` tienen flag
  `activo`; `DELETE` desactiva (no borra) y `GET` filtra por `?activo=`. En órdenes,
  editar (`PUT`) está vetado en `CANCELADO`/`ENTREGADO` y el `vehiculo_id` solo se
  reasigna en `PERITAJE`/`COTIZACION`.
- **Esquema**: la fuente de verdad es **Alembic** (`alembic upgrade head`). Los
  scripts (`create_admin.py`/`seed_db.py`) usan `create_all`, que **no** aplica
  `ALTER` sobre tablas existentes (un `taller.db` viejo puede quedar desfasado).

---

## Estructura

```
backend/app/
├── main.py          ← registrar routers, configurar CORS
├── config.py        ← Settings (pydantic-settings)
├── database.py      ← engine, SessionLocal, Base   (NO editar sin cuidado)
├── models/          ← tablas SQLAlchemy; __init__.py importa TODOS (Alembic)
├── schemas/         ← Pydantic v2 Request/Response
├── routers/         ← auth, clientes, vehiculos, ordenes, facturas, pagos, fases, personal
├── services/        ← orden_service (state machine), factura, pago, fase, pdf
├── dependencies/    ← db.py (get_db), auth.py (get_current_user)
└── utils/           ← security.py (hash/verify password)
backend/templates/factura_pdf.html   ← plantilla Jinja2 del PDF
backend/tests/       ← conftest (StaticPool), test_*.py
backend/alembic/versions/   ← 0001_initial, 0002_vehiculo_activo, 0003_orden_activo
```

**No editar sin revisar impacto:** `database.py`, `models/__init__.py`, `alembic/env.py`.

---

## Tests

`backend/tests/conftest.py`: SQLite en memoria con **StaticPool** (crítico: sin él
cada sesión ve una DB vacía); `import app.models` ANTES de `from app.main import app`;
los tests **no** usan `taller.db`. Correr: `pytest backend/tests/ -v --cov=app`.

---

## Frontend — SPA Vanilla + tema "Liquid Glass"

- Hash router (`js/router.js`: `#/ruta` → render). `js/api.js` envuelve `fetch()` y
  agrega el JWT (en `localStorage`, clave `taller_token`). `auth.js` →
  `isAuthenticated()` valida la **expiración** del JWT (lee `exp`).
- Páginas: `#/dashboard`, `#/clientes`, `#/ordenes`, `#/ordenes/:id` (tabs
  Peritaje/Cotización/Factura/Seguimiento), `#/seguimiento` (Kanban), `#/personal`.
- **Tema glass (CSS puro, NO React)**: variables `--glass-*` en `css/main.css`
  (reutilizarlas, no hardcodear `rgba()`/blur). Patrón: `background: var(--glass-bg)`
  + `backdrop-filter: blur() saturate()` (incluir `-webkit-`) + `border` + sombra.
  Fondo "aurora" en `body`; filtro SVG `#liquid-glass` en `index.html`.
  **Regla de oro: legibilidad primero** (contraste AA; respetar
  `prefers-reduced-motion`).
- Helpers en `js/utils.js`: `renderLoader`, `renderSkeleton`, `renderEmpty`,
  `renderError` (traduce errores de red), `escapeHtml` (al inyectar datos del
  usuario), `confirmDialog` (reemplaza `confirm()` nativo), `showPdfViewer`.
- Componente `js/components/CarDiagram.js`: `createCarDiagram(...)` (SVG de zonas
  del vehículo); reutilizarlo.

---

## Git

```
main ← producción/demo (solo merges desde dev)    dev ← integración
```

Commits: `feat(modulo): …`, `fix(modulo): …`, `test(modulo): …`, `docs: …`, `chore: …`.

---

## Comandos frecuentes

```bash
uvicorn app.main:app --reload --app-dir backend
alembic -c backend/alembic.ini upgrade head
alembic -c backend/alembic.ini revision --autogenerate -m "descripcion"
pytest backend/tests/ -v --cov=app
flake8 backend/app/ --max-line-length=100 && black backend/app/
python backend/scripts/create_admin.py     # crea admin demo
python backend/scripts/seed_db.py           # datos de demo
```

---

## Desarrollo local (WSL)

> **Levantar SIEMPRE al iniciar** (para ver los cambios en vivo), desde la raíz del repo:
>
> ```bash
> python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend &
> python3 scripts/dev_frontend.py &   # frontend SIN caché (evita módulos JS viejos)
> ```
>
> | Recurso | Valor |
> |---------|-------|
> | Frontend (UI) | http://localhost:8080 |
> | API + Swagger | http://localhost:8000/docs |
> | Usuario / Contraseña | `admin` / `admin123` (demo — cambiar en producción) |

- El proyecto vive en WSL (`/home/arcaoexdi/ao_development/01_soft_lat_y_pintura`) y se
  edita desde Windows por `\\wsl.localhost\Ubuntu\...`. Ejecutar comandos vía
  `wsl.exe -d Ubuntu -- bash -lc "..."`. El `python3` del **sistema WSL** tiene las
  deps; el Python de Windows / Git Bash **no**.
- **Gotchas WSL**: al pasar por `bash -lc "...$VAR..."` las variables y `$(...)` se
  pierden/rompen por el anidamiento de comillas → usa rutas literales o un script
  `.sh` (LF). Para `uvicorn` usa la raíz del repo (la `DATABASE_URL` es relativa) o
  `--app-dir backend`; **no** uses `--reload` en ese contexto (pierde `--app-dir`).
- Servir el frontend por **HTTP** (`dev_frontend.py`), nunca `file://` (CORS).
  El origen del frontend debe estar en `ALLOWED_ORIGINS` del `.env`.

Despliegue gratuito: ver `README.md`.

---

## Seguridad (repo público)

- `.env` nunca en git. Sin hardcode de credenciales. `requirements.txt` con versiones exactas.
- Todas las rutas excepto `POST /api/v1/auth/login` requieren JWT válido.

---

## Equipo de agentes (sub-agentes globales)

Equipo global en `~/.claude/agents/` (reutilizable en todos los proyectos), con un
**líder** que orquesta:

| Agente | Rol |
|--------|-----|
| `tech-lead` | **Líder/orquestador**: descompone, delega vía la tool `Agent`, integra y exige validación. Único con acceso a `Agent`. |
| `backend-fastapi` | Python/FastAPI, SQLAlchemy 2.0 síncrono, Pydantic v2, Alembic. |
| `frontend-web` | HTML/CSS/JS Vanilla, SPA hash-router, tema Liquid Glass, accesibilidad. |
| `qa-tester` | pytest + httpx, StaticPool, cobertura, edge cases. Bloquea cierres con tests rojos. |
| `automation-engineer` | Make/n8n, scripts, integraciones y webhooks. |
| `devops-git` | GitHub Actions (lint + tests), flujo `dev`→`main`, convención de commits. |
| `security-auditor` | Auditoría de repos públicos: secrets, JWT, validación, OWASP. |

**Modo de trabajo:** el `tech-lead` recibe el objetivo, planifica, delega a los
especialistas, integra y hace que `qa-tester` + `security-auditor` validen antes de
cualquier commit/push. Para tareas pequeñas, el agente principal ejecuta directamente.
