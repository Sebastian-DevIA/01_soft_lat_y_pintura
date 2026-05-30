# CLAUDE.md — Contexto para Agentes IA

Archivo dirigido a Claude Code y agentes IA. No es documentación para humanos (ver `README.md`).

---

## Propósito del proyecto

Sistema de gestión operacional para taller de latonería y pintura automotriz.
**Contexto real:** 10–20 vehículos/mes, 4–5 por semana, 1–3 operadores del sistema.
**Objetivo del repo:** Portafolio público del desarrollador Sebastian Miranda para postulaciones junior Python/FastAPI.

---

## Stack y versiones exactas

```
Python            3.11+
FastAPI           0.111.1
SQLAlchemy        2.0.x    (modo síncrono — sin async)
SQLite            3        (archivo: backend/taller.db — en .gitignore)
Alembic           1.13.2
Pydantic          v2       (@field_validator, no @validator v1)
pydantic-settings 2.3.x
python-jose       3.3.0    (JWT)
passlib           1.7.4    (bcrypt)
WeasyPrint        62.3     (PDF)
Jinja2            3.1.4    (plantilla factura)
pytest            8.3.2
httpx             0.27.0
python-multipart  requerido para OAuth2PasswordRequestForm
```

---

## Convenciones del código

### Schemas Pydantic
- Sufijo `Request` para entrada: `ClienteRequest`, `OrdenCreateRequest`
- Sufijo `Response` para salida: `ClienteResponse`, `OrdenDetalleResponse`
- Nunca retornar modelo SQLAlchemy directo — siempre pasar por schema Response

### Separación de capas
- **`routers/`** — Solo orquestación: recibir request, llamar service, retornar response
- **`services/`** — Toda la lógica de negocio. Los routers NO tienen lógica
- **`models/`** — Solo definición de tablas SQLAlchemy, sin lógica
- **`dependencies/`** — `get_db`, `get_current_user`

### `autoflush=False` — importante
`SessionLocal` usa `autoflush=False`. En los services, antes de llamar a
`_recalcular_totales` (que hace un query), se debe llamar `db.flush()` para que
los objetos pendientes (`add`/`delete`) sean visibles en el query.

---

## State machine de OrdenTrabajo

```
PERITAJE → COTIZACION → APROBACION → EN_PROCESO → ENTREGADO
                                          └──────→ CANCELADO
```

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

Validación vive en `backend/app/services/orden_service.py`.

---

## Reglas de negocio críticas

1. **Factura** solo se emite si `OrdenTrabajo.estado == "APROBACION"`
2. **Fase ENTREGA** solo puede completarse si `Factura.estado == "PAGADA"`
3. Al **aprobar** la orden, `orden_service._crear_fases()` crea automáticamente 3 `FaseTrabajo`: `INGRESO`, `REPARACION`, `ENTREGA` — en estado `PENDIENTE`
4. **Descuento** se aplica sobre el total de ítems (no individual)
5. El **adelanto** es exactamente el 50% del `total_con_descuento`
6. Orden **CANCELADA** o **ENTREGADA** no puede modificarse

---

## Estructura de archivos

```
backend/
├── app/
│   ├── main.py              ← registrar routers aquí, configurar CORS
│   ├── config.py            ← Settings con pydantic-settings
│   ├── database.py          ← engine, SessionLocal, Base — NO EDITAR sin cuidado
│   ├── models/
│   │   ├── __init__.py      ← importar TODOS los modelos (necesario para Alembic)
│   │   ├── usuario.py
│   │   ├── cliente.py
│   │   ├── vehiculo.py
│   │   ├── orden_trabajo.py ← state machine, TRANSICIONES_VALIDAS
│   │   ├── item_cotizacion.py
│   │   ├── factura.py
│   │   ├── pago.py
│   │   ├── fase_trabajo.py  ← ORDEN_FASES = ["INGRESO", "REPARACION", "ENTREGA"]
│   │   ├── personal.py
│   │   └── asignacion.py
│   ├── schemas/             ← Pydantic v2 (Request/Response)
│   ├── routers/             ← auth, clientes, vehiculos, ordenes, facturas, pagos, fases, personal
│   ├── services/
│   │   ├── orden_service.py ← state machine + lógica central
│   │   ├── factura_service.py
│   │   ├── pago_service.py  ← valida 50%, actualiza Factura.estado
│   │   ├── fase_service.py  ← avanzar fase, asignar/remover personal
│   │   └── pdf_service.py   ← WeasyPrint + Jinja2
│   ├── dependencies/
│   │   ├── db.py            ← def get_db(): yield SessionLocal()
│   │   └── auth.py          ← def get_current_user(): verifica JWT
│   └── utils/
│       └── security.py      ← hash_password, verify_password
├── templates/
│   └── factura_pdf.html     ← plantilla Jinja2 para PDF de factura
├── tests/
│   ├── conftest.py          ← StaticPool, override get_db, fixtures admin/auth
│   ├── test_auth.py
│   ├── test_clientes.py
│   ├── test_ordenes.py
│   ├── test_pagos.py
│   └── test_fases.py
├── scripts/
│   ├── create_admin.py
│   └── seed_db.py
└── alembic/
    ├── versions/
    │   └── 0001_initial_schema.py  ← migración inicial completa
    └── env.py
```

**Archivos que NO editar sin revisar impacto:**
- `backend/app/database.py`
- `backend/app/models/__init__.py`
- `backend/alembic/env.py`

---

## Tests — configuración importante

`backend/tests/conftest.py`:
- SQLite en memoria con `StaticPool` (CRÍTICO: sin StaticPool, cada sesión ve una DB vacía)
- `import app.models` ANTES de `from app.main import app` para evitar conflicto de nombres
- Los tests NO usan `taller.db`

---

## Frontend — SPA Vanilla

- Sin frameworks (sin React/Vue/Angular)
- Hash router en `frontend/js/router.js` → mapea `#/ruta` → función render
- `frontend/js/api.js` — wrapper de `fetch()` que agrega JWT automáticamente
- JWT en `localStorage` (clave: `taller_token`)
- Sin Bootstrap ni Tailwind — CSS propio en `frontend/css/`

### Tema "Liquid Glass" (vidrio tipo Apple, CSS puro)

- **NO usar React** ni la librería `liquid-glass-react`: el proyecto es Vanilla.
  El efecto se logra solo con CSS + un filtro SVG.
- Variables del vidrio en `frontend/css/main.css` (`:root`): `--glass-bg`,
  `--glass-bg-strong`, `--glass-border`, `--glass-blur`, `--glass-shadow`, etc.
  **Reutilizarlas** en vez de hardcodear `rgba()`/blur al crear componentes nuevos.
- Patrón de superficie de vidrio: `background: var(--glass-bg)` +
  `backdrop-filter: blur() saturate()` + `border: 1px solid var(--glass-border)`
  + `box-shadow: var(--glass-shadow)`. Siempre incluir el prefijo
  `-webkit-backdrop-filter` para Safari.
- Fondo "aurora" animado vive en `body` (`@keyframes auroraShift`).
- Filtro SVG de refracción: `<filter id="liquid-glass">` en `frontend/index.html`.
- **Regla de oro: legibilidad primero.** El vidrio nunca debe dificultar leer el
  texto; mantener contraste AA. Respetar `@media (prefers-reduced-motion)`.
- Helpers de UI en `frontend/js/utils.js`: `renderLoader()` (spinner),
  `renderSkeleton(rows)`, `renderEmpty(msg, icon)`, `renderError(msg)` (traduce
  errores de red), `escapeHtml(value)` (usar al inyectar datos del usuario en HTML).

### Páginas implementadas

```
#/dashboard    → métricas del taller
#/clientes     → lista + búsqueda + CRUD
#/ordenes      → lista con filtro por estado
#/ordenes/:id  → detalle con tabs (Peritaje / Cotización / Factura / Seguimiento)
#/seguimiento  → Kanban: Ingreso | Reparación | Entrega
#/personal     → tabla del equipo
```

---

## Ramas de Git

```
main   ← producción/demo (solo merges desde dev)
dev    ← integración
```

**Convención de commits:**
```
feat(modulo): descripción
fix(modulo): descripción
test(modulo): descripción
docs: descripción
chore: descripción
```

---

## Comandos frecuentes

```bash
uvicorn app.main:app --reload --app-dir backend
alembic -c backend/alembic.ini upgrade head
alembic -c backend/alembic.ini revision --autogenerate -m "descripcion"
pytest backend/tests/ -v --cov=app
python backend/scripts/create_admin.py
python backend/scripts/seed_db.py
flake8 backend/app/ --max-line-length=100
black backend/app/
```

---

## Seguridad (repo público)

- `.env` nunca en git
- Todas las rutas excepto `POST /api/v1/auth/login` requieren JWT válido
- Sin hardcode de credenciales en ningún archivo
- `requirements.txt` con versiones exactas

---

## Equipo de agentes (sub-agentes globales)

El desarrollador trabaja como una agencia de software de IA. Existe un **equipo de
sub-agentes global** en `~/.claude/agents/` (reutilizable en todos sus proyectos),
con un agente **líder** que orquesta el trabajo de inicio a fin:

| Agente | Rol |
|--------|-----|
| `tech-lead` | **Líder/orquestador**: descompone el objetivo, delega vía la tool `Agent`, integra y exige validación antes de cerrar. Único con acceso a `Agent`. |
| `backend-fastapi` | Python/FastAPI, SQLAlchemy 2.0 síncrono, Pydantic v2, Alembic. Respeta la separación routers/services/models. |
| `frontend-web` | HTML/CSS/JS Vanilla, SPA hash-router, tema Liquid Glass, accesibilidad. |
| `qa-tester` | pytest + httpx, StaticPool, cobertura, edge cases. Bloquea cierres con tests rojos. |
| `automation-engineer` | Make/n8n, scripts, integraciones y webhooks. |
| `devops-git` | GitHub Actions (lint + tests), flujo `dev`→`main`, convención de commits. |
| `security-auditor` | Auditoría de repos públicos: secrets, JWT, validación, OWASP. |

**Modo de trabajo:** el `tech-lead` recibe el objetivo, planifica con `TodoWrite`,
delega a los especialistas, integra resultados y hace que `qa-tester` +
`security-auditor` validen antes de cualquier commit/push.

> Nota: en Claude Code los sub-agentes los invoca el agente principal; "líder de
> equipo" = la definición `tech-lead` + orquestación. Para tareas pequeñas, el
> agente principal puede ejecutar directamente y reservar la delegación para
> trabajos amplios o paralelizables.
