# CLAUDE.md — Contexto para Agentes IA

Este archivo está dirigido a Claude Code y otros agentes de IA que trabajen en este repositorio.
No es documentación para humanos — para eso está el `README.md`.

---

## Propósito del proyecto

Sistema de gestión operacional para un taller pequeño de latonería y pintura automotriz.
**Contexto real del negocio:** 10–20 vehículos/mes, 4–5 vehículos/semana, 1–3 operadores del sistema.

**Objetivo del repositorio:** Portafolio público del desarrollador Sebastian Miranda para postulaciones
a posiciones junior de Python/FastAPI. El código debe ser legible, bien estructurado y demostrar
buenas prácticas sin sobre-ingeniería.

---

## Stack y versiones exactas

```
Python          3.11+
FastAPI         0.111.1
SQLAlchemy      2.0.x    (modo síncrono — no async, para mantener simplicidad)
SQLite          3        (archivo: backend/taller.db — en .gitignore)
Alembic         1.13.2
Pydantic        v2       (usar @field_validator, no @validator de v1)
pydantic-settings 2.3.x  (configuración desde .env)
python-jose     3.3.0    (JWT)
passlib         1.7.4    (bcrypt para hashing de contraseñas)
WeasyPrint      62.3     (generación de PDF)
Jinja2          3.1.4    (solo para plantilla de factura PDF)
pytest          8.3.2
httpx           0.27.0   (TestClient de FastAPI)
```

---

## Convenciones del código

### Schemas Pydantic
- Sufijo `Request` para schemas de entrada: `ClienteRequest`, `OrdenCreateRequest`
- Sufijo `Response` para schemas de salida: `ClienteResponse`, `OrdenDetalleResponse`
- Nunca devolver el modelo SQLAlchemy directamente — siempre pasar por schema Response

### Separación de capas
- **`routers/`** — Solo orquestación: recibir request, llamar service, devolver response
- **`services/`** — Toda la lógica de negocio va aquí. Los routers NO deben tener lógica
- **`models/`** — Solo definición de tablas SQLAlchemy, sin lógica de negocio
- **`dependencies/`** — FastAPI dependencies: `get_db`, `get_current_user`

### Modelos SQLAlchemy
- IDs: enteros autoincrement (`Integer, primary_key=True`)
- Timestamps: `created_at` y `updated_at` con `server_default=func.now()`
- Enums en Python, almacenados como `String` en SQLite
- Nombres de tabla en español y plural: `clientes`, `ordenes_trabajo`, `items_cotizacion`
- Relaciones: usar `relationship()` con `back_populates` explícito

### Nombramiento
- Archivos Python: snake_case
- Clases Python: PascalCase
- Variables/funciones: snake_case
- Columnas de BD: snake_case en español

---

## State machine de OrdenTrabajo

```
PERITAJE → COTIZACION → APROBACION → EN_PROCESO → ENTREGADO
                                          └──────→ CANCELADO
```

**Transiciones válidas:**
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

La validación de transiciones vive en `backend/app/services/orden_service.py`.

---

## Reglas de negocio críticas

1. **Factura** solo se puede emitir si `OrdenTrabajo.estado == "APROBACION"`
2. **Fase ENTREGA** solo puede marcarse como COMPLETADA si `Factura.estado == "PAGADA"`
3. Al **aprobar** la orden, el service crea automáticamente 3 registros `FaseTrabajo`:
   `INGRESO`, `REPARACION`, `ENTREGA` — todos en estado `PENDIENTE`
4. **Descuento** se aplica sobre el total de ítems (no sobre ítems individuales)
5. El **adelanto** es exactamente el 50% del `total_con_descuento`
6. Una orden **CANCELADA** o **ENTREGADA** no puede modificarse

---

## Estructura de archivos críticos

```
backend/
├── app/
│   ├── main.py              ← registrar todos los routers aquí, configurar CORS
│   ├── config.py            ← Settings con pydantic-settings, leer desde .env
│   ├── database.py          ← engine, SessionLocal, Base — NO EDITAR sin cuidado
│   ├── models/
│   │   └── __init__.py      ← importar todos los modelos para que Alembic los detecte
│   ├── services/
│   │   ├── orden_service.py ← state machine + lógica central del negocio
│   │   ├── pago_service.py  ← validación del 50%, actualización de Factura.estado
│   │   └── pdf_service.py   ← WeasyPrint, renderiza factura_pdf.html con Jinja2
│   └── dependencies/
│       ├── db.py            ← def get_db(): yield SessionLocal()
│       └── auth.py          ← def get_current_user(): verifica JWT, devuelve Usuario
├── alembic/
│   └── env.py               ← CRÍTICO: importa Base y todos los modelos
└── alembic.ini              ← apunta a database.py para la URL de conexión
```

**Archivos que NO editar sin revisar impacto:**
- `backend/app/database.py` — base de la sesión SQLAlchemy
- `backend/app/models/__init__.py` — importaciones necesarias para Alembic
- `backend/alembic/env.py` — configuración de migraciones

---

## Comandos frecuentes de desarrollo

```bash
# Iniciar servidor (desde la raíz del repo)
uvicorn app.main:app --reload --app-dir backend

# Crear nueva migración tras cambiar modelos
alembic -c backend/alembic.ini revision --autogenerate -m "descripcion"

# Aplicar migraciones
alembic -c backend/alembic.ini upgrade head

# Revertir última migración
alembic -c backend/alembic.ini downgrade -1

# Ejecutar tests
pytest backend/tests/ -v --cov=app

# Crear usuario admin inicial
python backend/scripts/create_admin.py

# Cargar datos de demo
python backend/scripts/seed_db.py

# Linting
flake8 backend/app/ --max-line-length=100
black backend/app/
```

---

## Configuración de tests

`backend/tests/conftest.py` configura:
- SQLite en memoria (`sqlite:///:memory:`)
- `TestClient` de FastAPI
- `override_dependency` para `get_db` → sesión de test
- Fixtures para crear usuario admin y datos base

Los tests **no** deben usar la base de datos real (`taller.db`).

---

## Frontend — Arquitectura SPA Vanilla

- **No usar frameworks** (sin React, sin Vue, sin Angular)
- Router de hash en `frontend/js/router.js` — mapea `#/ruta` → función que renderiza la página
- Comunicación con backend en `frontend/js/api.js` — wrapper sobre `fetch()` que:
  - Agrega `Authorization: Bearer <token>` automáticamente
  - Redirige a `#/login` si recibe `401`
  - Maneja errores de red con `Toast()`
- JWT almacenado en `localStorage` (clave: `taller_token`)
- `Chart.js` cargado desde CDN (solo en `dashboard.js`)
- CSS propio — sin Bootstrap ni Tailwind

### Páginas del frontend

```
#/login        → formulario de login
#/dashboard    → métricas del taller (Chart.js)
#/clientes     → lista + búsqueda
#/clientes/nuevo → formulario
#/ordenes      → lista con filtro por estado
#/ordenes/nueva → wizard 3 pasos
#/ordenes/:id  → detalle con tabs (Peritaje / Cotización / Factura / Seguimiento)
#/seguimiento  → Kanban global: Ingreso | Reparación | Entrega
#/personal     → tabla del equipo
```

---

## Seguridad (repo público)

- `.env` nunca en git (`.gitignore` estricto)
- Todas las rutas excepto `POST /api/v1/auth/login` requieren JWT válido
- Validación Pydantic v2 en todos los inputs — nunca usar `dict()` sin validar
- Sin hardcode de credenciales en ningún archivo
- `requirements.txt` con versiones exactas (evita supply chain attacks)
- `SECURITY.md` incluye instrucciones para despliegue seguro

---

## Ramas de Git

```
main   ← producción / demo pública (siempre funcional, solo merges desde dev)
dev    ← integración (merge de features aquí primero)
  └── feature/nombre-de-la-feature
  └── fix/nombre-del-bug
```

**Convención de commits:**
```
feat(modulo): descripción breve
fix(modulo): descripción breve
docs(readme): descripción breve
test(modulo): descripción breve
chore: descripción breve
```
