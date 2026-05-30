# Taller LatonPaint — Sistema de Gestión de Taller

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-green)
![Tests](https://img.shields.io/badge/Tests-29%2F29-brightgreen)

Sistema de gestión operacional para un taller de latonería y pintura automotriz. Cubre el ciclo completo del vehículo: ingreso, peritaje, cotización, aprobación, facturación, fases de trabajo y entrega.

> **Proyecto de portafolio** — Desarrollado por [Sebastian Miranda](https://github.com/Sebastian-DevIA) para demostrar competencias en Python, FastAPI, SQLAlchemy, Pydantic v2 y desarrollo de APIs REST.

---

## Flujo del Vehículo

```
1. INGRESO     → registro del cliente y vehículo (placa, marca, modelo, color)
2. PERITAJE    → inspección visual, registro de áreas dañadas con precio por ítem
3. COTIZACIÓN  → suma de ítems + descuento opcional
4. APROBACIÓN  → cliente aprueba; se genera adelanto del 50%
5. FACTURA     → emisión con fecha estimada de entrega + saldo pendiente (50%)
6. FASES       → INGRESO → REPARACIÓN → ENTREGA (Kanban)
7. ENTREGA     → solo disponible tras confirmar pago completo
```

---

## Stack

| Capa          | Tecnología                       | Versión  |
|---------------|----------------------------------|----------|
| Lenguaje      | Python                           | 3.11+    |
| Framework API | FastAPI                          | 0.111.1  |
| ORM           | SQLAlchemy (modo síncrono)       | 2.0.x    |
| Base de datos | SQLite 3                         | —        |
| Migraciones   | Alembic                          | 1.13.2   |
| Validación    | Pydantic v2                      | 2.8.x    |
| Auth          | JWT (python-jose) + passlib/bcrypt | 3.3.0  |
| PDF           | WeasyPrint + Jinja2              | 62.3     |
| Frontend      | HTML / CSS / JavaScript Vanilla  | —        |
| Tests         | Pytest + httpx                   | 8.3.2    |
| CI/CD         | GitHub Actions                   | —        |

---

## Estructura del Proyecto

```
01_soft_lat_y_pintura/
├── .github/
│   ├── workflows/ci.yml          ← lint (flake8 + black) + tests (pytest)
│   └── ISSUE_TEMPLATE/
├── backend/
│   ├── app/
│   │   ├── main.py              ← FastAPI app + CORS + routers
│   │   ├── config.py            ← Settings con pydantic-settings
│   │   ├── database.py          ← engine + SessionLocal + Base
│   │   ├── models/              ← SQLAlchemy ORM (10 modelos)
│   │   ├── schemas/             ← Pydantic v2 Request/Response
│   │   ├── routers/             ← endpoints por dominio (8 routers)
│   │   ├── services/            ← lógica de negocio (4 services)
│   │   ├── dependencies/        ← get_db, get_current_user (JWT)
│   │   └── utils/               ← hash_password, verify_password
│   ├── templates/
│   │   └── factura_pdf.html     ← plantilla Jinja2 para PDF
│   ├── tests/                   ← 29 tests con SQLite en memoria
│   ├── scripts/
│   │   ├── create_admin.py      ← crea usuario admin inicial
│   │   └── seed_db.py           ← datos de demo (3 clientes, 3 vehículos)
│   └── alembic/
│       ├── versions/
│       │   └── 0001_initial_schema.py  ← migración inicial completa
│       └── env.py
├── frontend/
│   ├── index.html               ← SPA shell (hash routing)
│   ├── css/
│   │   ├── main.css
│   │   └── components.css
│   └── js/
│       ├── api.js               ← fetch wrapper con JWT automático
│       ├── auth.js              ← login/logout/token
│       ├── router.js            ← hash router (#/ruta → función)
│       ├── utils.js             ← toast, modal, formatCurrency
│       └── pages/
│           ├── dashboard.js     ← métricas y últimas órdenes
│           ├── clientes.js      ← lista + búsqueda + CRUD
│           ├── ordenes.js       ← lista + detalle con tabs
│           ├── seguimiento.js   ← Kanban: Ingreso | Reparación | Entrega
│           └── personal.js      ← tabla del equipo
├── docs/
├── .env.example
├── requirements.txt
├── requirements-dev.txt
├── CLAUDE.md
└── SECURITY.md
```

---

## Modelo de Datos

```
Cliente ──< Vehiculo ──< OrdenTrabajo ──< ItemCotizacion
                              │
                              ├──── Factura ──< Pago
                              │
                              └──< FaseTrabajo ──< Asignacion ──> Personal
```

## State Machine de OrdenTrabajo

```
PERITAJE → COTIZACION → APROBACION → EN_PROCESO → ENTREGADO
                                          └──────→ CANCELADO
```

---

## Endpoints principales

| Método | Ruta                              | Descripción                        |
|--------|-----------------------------------|------------------------------------|
| POST   | `/api/v1/auth/login`              | Login → JWT                        |
| GET    | `/api/v1/auth/me`                 | Usuario autenticado                |
| GET    | `/api/v1/clientes/`               | Listar clientes                    |
| POST   | `/api/v1/clientes/`               | Crear cliente                      |
| GET    | `/api/v1/vehiculos/`              | Listar vehículos                   |
| POST   | `/api/v1/vehiculos/`              | Crear vehículo                     |
| GET    | `/api/v1/ordenes/`                | Listar órdenes (filtro por estado) |
| POST   | `/api/v1/ordenes/`                | Crear orden                        |
| GET    | `/api/v1/ordenes/{id}`            | Detalle completo (con factura)     |
| PATCH  | `/api/v1/ordenes/{id}/aprobar`    | Aprobar cotización                 |
| PATCH  | `/api/v1/ordenes/{id}/descuento`  | Aplicar descuento                  |
| POST   | `/api/v1/ordenes/{id}/items`      | Agregar ítem de peritaje           |
| PUT    | `/api/v1/ordenes/{id}/items/{id}` | Actualizar ítem                    |
| DELETE | `/api/v1/ordenes/{id}/items/{id}` | Eliminar ítem                      |
| POST   | `/api/v1/facturas/`               | Emitir factura                     |
| GET    | `/api/v1/facturas/{id}`           | Obtener factura                    |
| GET    | `/api/v1/facturas/{id}/pdf`       | Descargar PDF                      |
| POST   | `/api/v1/pagos/`                  | Registrar pago                     |
| GET    | `/api/v1/fases/orden/{id}`        | Fases de una orden                 |
| PATCH  | `/api/v1/fases/{id}/estado`       | Avanzar fase                       |
| POST   | `/api/v1/fases/{id}/personal`     | Asignar personal a fase            |
| DELETE | `/api/v1/fases/{id}/personal/{id}`| Remover personal de fase           |
| GET    | `/api/v1/personal/`               | Listar personal                    |
| POST   | `/api/v1/personal/`               | Crear empleado                     |

---

## Cómo correr el proyecto

```bash
# 1. Clonar
git clone https://github.com/Sebastian-DevIA/01_soft_lat_y_pintura.git
cd 01_soft_lat_y_pintura

# 2. Entorno virtual e instalar dependencias
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Variables de entorno
cp .env.example .env
# Editar .env: cambiar SECRET_KEY por una cadena aleatoria larga

# 4. Crear base de datos
alembic -c backend/alembic.ini upgrade head

# 5. Crear usuario admin
python backend/scripts/create_admin.py

# 6. (Opcional) Datos de demo
python backend/scripts/seed_db.py

# 7. Iniciar servidor
uvicorn app.main:app --reload --app-dir backend
```

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Frontend: abrir `frontend/index.html` en el navegador

---

## Variables de entorno

| Variable                      | Descripción                          | Default                         |
|-------------------------------|--------------------------------------|---------------------------------|
| `SECRET_KEY`                  | Clave JWT (mín. 32 caracteres)       | —                               |
| `DATABASE_URL`                | URL SQLAlchemy                       | `sqlite:///./backend/taller.db` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duración del token                   | `480`                           |
| `DEBUG`                       | Activa `/docs` y `/redoc`            | `false`                         |
| `ALLOWED_ORIGINS`             | CORS (separados por coma)            | `http://localhost:8000`         |

---

## Tests

```bash
pip install -r requirements-dev.txt
pytest backend/tests/ -v --cov=app
```

29 tests — SQLite en memoria, sin configuración adicional.

---

## Autor

**Sebastian Miranda** · [@Sebastian-DevIA](https://github.com/Sebastian-DevIA) · sebastian.miranda@arcaoexdi.com

---

## Licencia

[MIT](LICENSE) — Ver `SECURITY.md` antes de desplegar en producción.
