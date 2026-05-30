# Taller LatonPaint — Sistema de Gestión de Taller

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-green)
![Estado](https://img.shields.io/badge/Estado-En%20Desarrollo-yellow)

Sistema de gestión operacional completo para un taller de latonería y pintura automotriz. Cubre el ciclo de vida del vehículo desde el ingreso hasta la entrega, incluyendo peritaje, cotización, facturación y seguimiento por fases.

> **Proyecto de portafolio** — Desarrollado por [Sebastian Miranda](https://github.com/Sebastian-DevIA) para demostrar competencias en Python, FastAPI, SQLAlchemy, Pydantic v2 y desarrollo de APIs REST.

---

## Flujo del Vehículo

```
┌─────────────────────────────────────────────────────────────────────┐
│                     FLUJO OPERACIONAL DEL TALLER                    │
└─────────────────────────────────────────────────────────────────────┘

  1. INGRESO DEL VEHÍCULO
     └─ Registro del cliente y del vehículo (placa, marca, modelo, color)

  2. PERITAJE
     └─ Inspección visual y registro de cada área dañada con precio individual
        (cada daño puede tener diferente gravedad → precio editable por ítem)

  3. COTIZACIÓN
     └─ Suma de ítems + aplicación de descuento opcional
        → Cliente revisa y aprueba

  4. APROBACIÓN + PAGO DEL 50% ADELANTO
     └─ Cliente paga el anticipo para autorizar el inicio del trabajo

  5. EMISIÓN DE FACTURA
     └─ Factura con fecha estimada de entrega + saldo pendiente (50%)

  6. FASES DE TRABAJO
     ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
     │   INGRESO   │ → │ REPARACIÓN  │ → │   ENTREGA   │
     │  (recepción)│   │(latonería y │   │(solo si el  │
     │             │   │  pintura)   │   │saldo = $0)  │
     └─────────────┘   └─────────────┘   └─────────────┘

  7. ENTREGA FINAL
     └─ Solo se habilita tras confirmar el pago del 50% restante
        → Cierre de la orden de trabajo
```

**Volumen típico del taller:** 10–20 vehículos por mes / 4–5 vehículos por semana.

---

## Stack Tecnológico

| Capa            | Tecnología                         | Versión  |
|-----------------|------------------------------------|----------|
| Lenguaje        | Python                             | 3.11+    |
| Framework API   | FastAPI                            | 0.111.1  |
| ORM             | SQLAlchemy                         | 2.0.31   |
| Base de datos   | SQLite 3                           | —        |
| Migraciones     | Alembic                            | 1.13.2   |
| Validación      | Pydantic v2                        | 2.8.2    |
| Autenticación   | JWT (python-jose) + passlib/bcrypt | 3.3.0    |
| Generación PDF  | WeasyPrint + Jinja2                | 62.3     |
| Frontend        | HTML / CSS / JavaScript (Vanilla)  | —        |
| Servidor        | Uvicorn                            | 0.30.1   |
| Tests           | Pytest + httpx                     | 8.3.2    |
| CI/CD           | GitHub Actions                     | —        |

---

## Arquitectura del Software

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         ARQUITECTURA GENERAL                             │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   NAVEGADOR (Frontend)                                                   │
│   ┌──────────────────────────────────────┐                               │
│   │  index.html  (SPA con hash routing)  │                               │
│   │  ├── css/  (estilos propios)         │                               │
│   │  └── js/                             │                               │
│   │      ├── api.js      (fetch + JWT)   │                               │
│   │      ├── router.js   (hash router)   │                               │
│   │      └── pages/      (una por vista) │                               │
│   └──────────────┬───────────────────────┘                               │
│                  │  HTTP/REST (JSON)                                     │
│   SERVIDOR (Backend — uvicorn)                                           │
│   ┌──────────────▼───────────────────────┐                               │
│   │  FastAPI app  (main.py)              │                               │
│   │  ├── routers/   (endpoints)          │                               │
│   │  ├── services/  (lógica de negocio)  │                               │
│   │  ├── models/    (SQLAlchemy ORM)     │                               │
│   │  └── schemas/   (Pydantic I/O)       │                               │
│   └──────────────┬───────────────────────┘                               │
│                  │  SQLAlchemy ORM                                       │
│   BASE DE DATOS                                                          │
│   ┌──────────────▼───────────────────────┐                               │
│   │  SQLite 3   (taller.db)              │                               │
│   │  Migraciones gestionadas con Alembic │                               │
│   └──────────────────────────────────────┘                               │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Modelo de datos

```
Cliente ──< Vehiculo ──< OrdenTrabajo ──< ItemCotizacion
                              │
                              ├──── Factura ──< Pago
                              │
                              └──< FaseTrabajo ──< Asignacion ──> Personal
```

### Estado de la orden (state machine)

```
PERITAJE → COTIZACION → APROBACION → EN_PROCESO → ENTREGADO
                                          └──────→ CANCELADO
```

---

## Estructura del Proyecto

```
Sof_Lat%Pin/
├── .github/
│   ├── workflows/ci.yml          ← GitHub Actions (lint + tests)
│   └── ISSUE_TEMPLATE/
├── backend/
│   ├── app/
│   │   ├── main.py              ← punto de entrada FastAPI
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/              ← tablas SQLAlchemy
│   │   ├── schemas/             ← Pydantic v2 (Request/Response)
│   │   ├── routers/             ← endpoints por dominio
│   │   ├── services/            ← lógica de negocio
│   │   ├── dependencies/        ← auth JWT, get_db
│   │   └── utils/
│   ├── templates/               ← Jinja2 para PDF de factura
│   ├── tests/                   ← pytest + SQLite en memoria
│   ├── scripts/                 ← seed_db.py, create_admin.py
│   └── alembic/                 ← migraciones
├── frontend/
│   ├── index.html               ← SPA shell
│   ├── css/
│   └── js/pages/                ← dashboard, cotización, kanban...
├── docs/
├── .env.example
├── requirements.txt
├── CLAUDE.md
└── SECURITY.md
```

---

## Cómo Correr el Proyecto Localmente

### Requisitos previos

- Python 3.11 o superior
- pip

### Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/Sebastian-DevIA/taller-latonpaint.git
cd taller-latonpaint

# 2. Crear y activar entorno virtual
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env y cambiar SECRET_KEY por una cadena aleatoria larga

# 5. Ejecutar migraciones (crea taller.db)
alembic -c backend/alembic.ini upgrade head

# 6. Crear usuario administrador
python backend/scripts/create_admin.py

# 7. (Opcional) Cargar datos de demo
python backend/scripts/seed_db.py

# 8. Iniciar el servidor
uvicorn app.main:app --reload --app-dir backend
```

El servidor estará disponible en: `http://localhost:8000`

### Documentación interactiva de la API

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Frontend

Abrir directamente en el navegador:

```bash
# Linux/Mac
open frontend/index.html

# O simplemente arrastrar el archivo al navegador
```

---

## Variables de Entorno

Ver [`.env.example`](.env.example) para la lista completa.

| Variable                      | Descripción                                    | Ejemplo                    |
|-------------------------------|------------------------------------------------|----------------------------|
| `SECRET_KEY`                  | Clave para firmar JWT (mínimo 32 caracteres)   | `mi-clave-super-secreta`   |
| `DATABASE_URL`                | URL de conexión SQLAlchemy                     | `sqlite:///./backend/taller.db` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duración del token de sesión                   | `480`                      |

---

## Tests

```bash
# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Ejecutar todos los tests
pytest backend/tests/ -v

# Con reporte de cobertura
pytest backend/tests/ -v --cov=app --cov-report=term-missing
```

Los tests usan SQLite en memoria — no necesitan configuración adicional.

---

## API — Endpoints Principales

| Método | Ruta                            | Descripción                              |
|--------|---------------------------------|------------------------------------------|
| POST   | `/api/v1/auth/login`            | Autenticación → token JWT                |
| GET    | `/api/v1/clientes/`             | Listar clientes                          |
| POST   | `/api/v1/clientes/`             | Registrar cliente                        |
| GET    | `/api/v1/ordenes/`              | Listar órdenes de trabajo                |
| POST   | `/api/v1/ordenes/`              | Crear orden (ingreso de vehículo)        |
| GET    | `/api/v1/ordenes/{id}`          | Detalle completo de una orden            |
| PATCH  | `/api/v1/ordenes/{id}/aprobar`  | Cliente aprueba cotización               |
| POST   | `/api/v1/ordenes/{id}/items`    | Agregar ítem de peritaje                 |
| POST   | `/api/v1/facturas/`             | Emitir factura                           |
| GET    | `/api/v1/facturas/{id}/pdf`     | Descargar factura en PDF                 |
| POST   | `/api/v1/pagos/`                | Registrar pago (adelanto o saldo)        |
| PATCH  | `/api/v1/fases/{id}/estado`     | Avanzar fase de trabajo                  |

---

## Asignación de Personal

El sistema permite delegar funciones por fase:

| Fase        | Roles típicos asignables               |
|-------------|----------------------------------------|
| Ingreso     | Recepcionista, Jefe de taller          |
| Reparación  | Latonero, Pintor, Auxiliar             |
| Entrega     | Jefe de taller, Pulidor                |

---

## Uso de Claude Code

Este proyecto fue desarrollado con asistencia de **Claude Code** (Anthropic), utilizando:
- Planificación de arquitectura y diseño del modelo de datos
- Generación del esqueleto de código con buenas prácticas (separación services/routers)
- Revisión de seguridad para repositorio público
- Documentación técnica en `CLAUDE.md`

El código fue revisado y validado manualmente por el autor en cada fase.

---

## Autor

**Sebastian Miranda**
- GitHub: [@Sebastian-DevIA](https://github.com/Sebastian-DevIA)
- Email: sebastian.miranda@arcaoexdi.com

---

## Licencia

[MIT](LICENSE) — Libre para clonar, estudiar y adaptar. Ver `SECURITY.md` antes de desplegar en producción.
