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

## Estado actual / cambios recientes

**Iteración "mejoras profesionales" (clientes / facturas / partes del carro / UI):**
- **Clientes**: `PATCH /clientes/{id}/activar` (reactivar/alternar tras soft-delete) y
  `PUT /clientes/{id}` devuelve **409** si la `cedula_ruc` ya existe en otro cliente.
  La UI (`clientes.js`) tiene CRUD completo en la lista (editar/eliminar/reactivar),
  filtro Activos/Inactivos y formulario unificado con validación.
- **Factura/PDF**: el visor del PDF en el front usa `api.facturas.pdfBlob()`
  (`fetch` con JWT → `Blob` → object URL); un `<a href>` plano daba **401** porque el
  navegador no manda el header. Helpers nuevos en `utils.js`: `showPdfViewer`,
  `confirmDialog`. La plantilla del PDF muestra **desglose de IVA** (display-only,
  no toca `monto_total` ni el 50%); tasa en `Settings.iva_porcentaje` (default 19) y
  `pdf_service` la calcula con `round()`. **Jinja con `autoescape`** (datos de cliente).
  Botón "Enviar al cliente" comparte resumen por WhatsApp (`wa.me`).
- **Partes del carro**: `frontend/js/components/CarDiagram.js` — SVG 2D (vista superior,
  carro normal/sedán) con 13 zonas nombradas y clicables; integrado en el form de ítem
  de peritaje (rellena `area_vehiculo`; el texto libre sigue disponible para otras partes)
  y como mapa de daños solo-lectura en la orden. Reutilizar `createCarDiagram(...)`.
- **Auth**: `isAuthenticated()` (`auth.js`) valida la **expiración** del JWT (lee `exp`)
  para no dejar "entrar" con un token viejo y rebotar con 401.
- **Dev**: `scripts/dev_frontend.py` sirve el frontend **sin caché** (evita módulos JS
  viejos). `frontend/_boot.html` está en `.gitignore` (página puente solo para screenshots).
- Confirmaciones migradas de `confirm()` nativo a `confirmDialog` (clientes/ordenes/seguimiento).

**Esquema:**
- `Vehiculo` tiene flag `activo` (bool, default True) — mismo patrón que `Cliente`/`Personal`.
  Lo agrega la migración `0002_vehiculo_activo`. `DELETE /vehiculos/{id}` es soft-delete
  (`activo=False`, 204) y `GET /vehiculos/` filtra por `?activo=`.
- La **fuente de verdad del esquema es Alembic** (`alembic upgrade head`). Los scripts
  (`create_admin.py`/`seed_db.py`) usan `Base.metadata.create_all`, que **no** aplica
  `ALTER` sobre tablas existentes: si reutilizas un `taller.db` viejo puede quedar
  desfasado (le faltarían columnas nuevas como `vehiculos.activo`).

**Endpoints añadidos:** `DELETE /vehiculos/{id}`, `GET /facturas/` (filtro `estado`),
`GET /pagos/` (filtro `factura_id`), `GET/PUT /personal/{id}`, `PATCH /personal/{id}/activar`.
La state machine se opera por UI vía `PATCH /ordenes/{id}/estado` (incluye CANCELADO).

**Respuestas enriquecidas (para la UI):**
- `OrdenResumenResponse` y `OrdenDetalleResponse` incluyen `vehiculo_placa`,
  `vehiculo_descripcion` (marca+modelo) y `cliente_nombre`. Se pueblan en
  `orden_service` (`_campos_planos` + `_a_resumen_response`/`_a_detalle_response`)
  vía `OrdenTrabajo.vehiculo → Vehiculo.cliente`. **Importante:** cualquier endpoint
  nuevo que retorne una orden debe pasar por estos helpers (no retornar el ORM crudo)
  o los campos planos saldrán `null`.
- `AsignacionResponse` incluye `personal_nombre`; se puebla en `fase_service`
  (`joinedload(FaseTrabajo.asignaciones).joinedload(Asignacion.personal_asignado)`).

---

## Pendientes (próxima iteración)

Tareas anotadas para continuar más tarde. **No están implementadas todavía.**

| # | Pendiente | Detalle | Dónde |
|---|-----------|---------|-------|
| 1 | Mejorar el **CRUD de órdenes** | Pulir alta/edición/eliminación de órdenes al nivel del CRUD de clientes (validación, estados de carga/vacío/error, confirmaciones con `confirmDialog`). | `frontend/js/pages/ordenes.js` |
| 2 | Mapa de daños en **horizontal** | El `CarDiagram` está en orientación vertical; debe quedar **horizontal** (vista superior apaisada). | `frontend/js/components/CarDiagram.js`, `frontend/css/components.css` |
| 3 | Áreas dañadas **al lado** del mapa | Mostrar la lista/visualización de zonas dañadas **junto** al diagrama del carro (layout en dos columnas) para que sea más visible. | `frontend/js/pages/ordenes.js`, `frontend/css/components.css` |

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
    │   ├── 0001_initial_schema.py   ← migración inicial completa
    │   └── 0002_vehiculo_activo.py  ← add column vehiculos.activo (down_revision="0001")
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

## Desarrollo local (entorno WSL)

> **Arranque rápido (hazlo SIEMPRE al iniciar sesión, para poder ver los cambios en vivo):**
>
> ```bash
> # backend (API) + frontend (UI), desde la raíz del repo en WSL
> python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend &
> python3 scripts/dev_frontend.py &   # frontend SIN caché (evita módulos JS viejos)
> ```
>
> **Nota WSL+Windows:** al lanzar por `wsl.exe -- bash -lc "...$VAR..."`, las variables
> de shell se pierden por el anidamiento de comillas. Usa **rutas literales** (no `$VAR`)
> o un **script** (`bash script.sh`, normalizado a LF). Para `uvicorn` usa `cd <raíz> &&`
> (la `DATABASE_URL` es relativa) o `--app-dir backend`; **no** uses `--reload` en ese
> contexto (el reloader pierde el `--app-dir`).
>
> | Recurso | URL / Valor |
> |---------|-------------|
> | Frontend (UI) | http://localhost:8080 |
> | API + Swagger | http://localhost:8000/docs |
> | **Usuario** | `admin` |
> | **Contraseña** | `admin123` |
>
> Credenciales demo creadas por `backend/scripts/create_admin.py` (cambiar en producción).

El proyecto vive en WSL (`/home/arcaoexdi/ao_development/01_soft_lat_y_pintura`) y se
edita desde Windows por `\\wsl.localhost\Ubuntu\...`. Notas para correr/validar:

- El `python3` del **sistema en WSL** (3.12) tiene todas las dependencias (FastAPI,
  SQLAlchemy, Alembic, passlib, jose, WeasyPrint, pytest, flake8, black). El `.venv`
  del repo puede estar incompleto. Ejecutar comandos vía `wsl.exe -d Ubuntu -- bash -lc "..."`.
- El Python de **Windows** y la herramienta Bash de Git Bash **no** tienen las deps:
  no sirven para levantar el backend.
- Backend: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend`.
  Frontend: servirlo por HTTP (`python3 -m http.server 8080 --directory frontend`),
  **nunca** `file://` (CORS → *Failed to fetch*).
- `.env` debe incluir el origen del frontend en `ALLOWED_ORIGINS` (p. ej. `http://localhost:8080`).
  WSL2 reenvía `localhost` a Windows, así que el navegador alcanza ambos puertos.
- Usuario demo: `admin` / `admin123` (de `create_admin.py`/`seed_db.py`).

## Despliegue (gratuito)

Frontend y backend se despliegan por separado (ver README → "Despliegue gratuito"):
- **Frontend** estático: Cloudflare Pages (ancho de banda ilimitado) o GitHub Pages.
  Ajustar `BASE_URL` en `frontend/js/api.js` a la URL pública del backend.
- **Backend**: Render (free, se duerme por inactividad) o Koyeb. Fly.io ya no tiene free
  tier; Railway solo da ~$1/mes. **SQLite es efímero** en estos tiers → para persistir,
  usar Postgres gratis (Neon/Supabase) y cambiar `DATABASE_URL`. WeasyPrint requiere
  libs del sistema (pango/cairo) → usar Dockerfile. CORS y `SECRET_KEY` por env.

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
