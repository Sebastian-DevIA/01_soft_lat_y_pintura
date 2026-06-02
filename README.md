# Taller LatonPaint — Sistema de Gestión de Taller

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-green)
![Tests](https://img.shields.io/badge/Tests-29%2F29-brightgreen)

Sistema de gestión operacional para un taller de latonería y pintura automotriz. Cubre el ciclo completo del vehículo: ingreso, peritaje, cotización, aprobación, facturación, fases de trabajo y entrega.

La interfaz usa un tema **Liquid Glass** (vidrio translúcido tipo Apple) implementado en **CSS puro**, sin frameworks. Ver [Interfaz — Tema Liquid Glass](#interfaz--tema-liquid-glass).

> **Proyecto de portafolio** — Desarrollado por [Sebastian Miranda](https://github.com/Sebastian-DevIA) para demostrar competencias en Python, FastAPI, SQLAlchemy, Pydantic v2 y desarrollo de APIs REST.

---

## Acceso rápido (demo local)

| Recurso | URL / Valor |
|---------|-------------|
| 🖥️ **Frontend (interfaz)** | **http://localhost:8080** |
| ⚙️ **API + Swagger** | http://localhost:8000/docs |
| 👤 **Usuario** | `admin` |
| 🔑 **Contraseña** | `admin123` |

Levanta **siempre** ambos servidores antes de usar la app (backend en `:8000`, frontend
en `:8080`). El paso a paso está en [Cómo correr el proyecto](#cómo-correr-el-proyecto).

> ⚠️ Las credenciales `admin / admin123` son **solo para demo/desarrollo** (las crea
> `backend/scripts/create_admin.py`). Cámbialas antes de cualquier despliegue real.

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
│       │   ├── 0001_initial_schema.py  ← migración inicial completa
│       │   └── 0002_vehiculo_activo.py ← agrega vehiculos.activo (soft-delete)
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
│           ├── clientes.js      ← lista + búsqueda + CRUD + detalle con vehículos
│           ├── ordenes.js       ← lista + asistente "Nueva Orden" + detalle con tabs
│           ├── seguimiento.js   ← Kanban + asignación de personal a fases
│           └── personal.js      ← tabla del equipo + edición
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
| GET    | `/api/v1/clientes/`               | Listar clientes (búsqueda/activo)  |
| POST   | `/api/v1/clientes/`               | Crear cliente                      |
| GET    | `/api/v1/clientes/{id}`           | Obtener cliente                    |
| PUT    | `/api/v1/clientes/{id}`           | Actualizar cliente                 |
| DELETE | `/api/v1/clientes/{id}`           | Desactivar cliente (soft-delete)   |
| PATCH  | `/api/v1/clientes/{id}/activar`   | Reactivar / alternar cliente       |
| GET    | `/api/v1/vehiculos/`              | Listar vehículos (placa/cliente/activo) |
| POST   | `/api/v1/vehiculos/`              | Crear vehículo                     |
| GET    | `/api/v1/vehiculos/{id}`          | Obtener vehículo                   |
| PUT    | `/api/v1/vehiculos/{id}`          | Actualizar vehículo                |
| DELETE | `/api/v1/vehiculos/{id}`          | Desactivar vehículo (soft-delete)  |
| GET    | `/api/v1/ordenes/`                | Listar órdenes (filtro por estado) |
| POST   | `/api/v1/ordenes/`                | Crear orden                        |
| GET    | `/api/v1/ordenes/{id}`            | Detalle completo (con factura)     |
| PATCH  | `/api/v1/ordenes/{id}/estado`     | Cambiar estado (state machine / cancelar) |
| PATCH  | `/api/v1/ordenes/{id}/aprobar`    | Aprobar cotización                 |
| PATCH  | `/api/v1/ordenes/{id}/descuento`  | Aplicar descuento                  |
| POST   | `/api/v1/ordenes/{id}/items`      | Agregar ítem de peritaje           |
| PUT    | `/api/v1/ordenes/{id}/items/{id}` | Actualizar ítem                    |
| DELETE | `/api/v1/ordenes/{id}/items/{id}` | Eliminar ítem                      |
| POST   | `/api/v1/facturas/`               | Emitir factura                     |
| GET    | `/api/v1/facturas/`               | Listar facturas (filtro por estado)|
| GET    | `/api/v1/facturas/{id}`           | Obtener factura                    |
| GET    | `/api/v1/facturas/{id}/pdf`       | Descargar PDF                      |
| POST   | `/api/v1/pagos/`                  | Registrar pago                     |
| GET    | `/api/v1/pagos/`                  | Listar pagos (filtro por factura)  |
| GET    | `/api/v1/pagos/factura/{id}`      | Pagos de una factura               |
| GET    | `/api/v1/fases/orden/{id}`        | Fases de una orden (con técnicos)  |
| PATCH  | `/api/v1/fases/{id}/estado`       | Avanzar fase                       |
| POST   | `/api/v1/fases/{id}/personal`     | Asignar personal a fase            |
| DELETE | `/api/v1/fases/{id}/personal/{id}`| Remover personal de fase           |
| GET    | `/api/v1/personal/`               | Listar personal (filtro activo)    |
| POST   | `/api/v1/personal/`               | Crear empleado                     |
| GET    | `/api/v1/personal/{id}`           | Obtener empleado                   |
| PUT    | `/api/v1/personal/{id}`           | Actualizar empleado                |
| PATCH  | `/api/v1/personal/{id}/activar`   | Activar / desactivar empleado      |

---

## Interfaz — Tema Liquid Glass

El frontend (SPA Vanilla, sin frameworks) está estilizado con un tema **Liquid
Glass** inspirado en la estética de vidrio translúcido de Apple, implementado
**100% en CSS** (no se usa la librería React `liquid-glass-react`, ya que el
proyecto es Vanilla por diseño).

**Cómo está construido:**

| Técnica | Dónde |
|---------|-------|
| `backdrop-filter: blur() saturate()` sobre superficies translúcidas | sidebar, header, cards, modales, tablas, kanban |
| Fondo "aurora" (mesh de gradientes radiales animados) que el vidrio refracta | `body` en `frontend/css/main.css` |
| Bordes de luz + brillo interior superior + sombra profunda suave | variables `--glass-*` en `main.css` |
| Filtro SVG de refracción real (`feTurbulence` + `feDisplacementMap`) | `<filter id="liquid-glass">` en `frontend/index.html` |
| Favicon emoji inline + `theme-color` | `<head>` de `frontend/index.html` |

**Archivos clave del tema:**
- `frontend/css/main.css` — variables del vidrio, layout, fondo aurora, login.
- `frontend/css/components.css` — vidrio aplicado a botones, cards, tablas, kanban, modales, toasts; skeletons y spinners.
- `frontend/index.html` — filtro SVG de refracción y meta tags.

**Accesibilidad y rendimiento:**
- **Legibilidad primero**: contraste objetivo AA; el vidrio nunca dificulta leer el texto.
- `:focus-visible` consistente y navegación por teclado.
- `@media (prefers-reduced-motion: reduce)` desactiva las animaciones de fondo.
- Layout responsive (el sidebar colapsa en pantallas pequeñas).

### Mejoras de UX incluidas

- **Estados de carga**: spinner y skeletons de vidrio mientras `fetch` resuelve.
- **Estados vacíos y de error** claros (mensajes de red entendibles, no `Failed to fetch`).
- **Modales accesibles**: cierre con `Escape`, clic fuera del cuadro y foco automático.
- **Microtransiciones** sutiles en cards, filas y tabs (respetando reduced-motion).
- Helper `escapeHtml()` en `frontend/js/utils.js` para renderizar datos del usuario de forma segura.

---

## Funcionalidades destacadas

### Gestión de clientes (CRUD completo)
- Crear, ver, **editar**, **eliminar** (soft-delete) y **reactivar** clientes desde la lista.
- Filtro **Activos / Inactivos** y búsqueda por nombre/cédula.
- Confirmaciones con modal de vidrio (no diálogos nativos), validación de campos y estados de carga/vacío/error.
- Ficha de cliente con sus **vehículos** (CRUD anidado).

### Facturación y PDF
- Emisión de factura (adelanto 50%) y registro de pagos.
- **Visor de PDF integrado**: ver, descargar e imprimir. La descarga es **autenticada por
  JWT** (`fetch` → `Blob` → object URL), por eso funciona aunque el endpoint exija token.
- **Desglose de IVA** en el PDF (base gravable + IVA), tasa configurable (`IVA_PORCENTAJE`).
- **Enviar al cliente**: botón que comparte un resumen de la factura por WhatsApp
  (`wa.me`), sin necesidad de servidor de correo.

### Mapa de daños del vehículo (SVG interactivo)
- Componente `frontend/js/components/CarDiagram.js`: vista superior de un carro con
  zonas clicables (capó, techo, baúl, 4 puertas, 4 guardabarros, 2 paragolpes), cada una
  con su **nombre**. Accesible (teclado, `role`/`aria-label`).
- En el **peritaje**, al registrar un área dañada se selecciona la zona en el diagrama
  (rellena el campo `area_vehiculo`); también se puede escribir libremente otra parte.
- En la vista de la orden, las zonas con daño registrado se resaltan en rojo (solo lectura).

---

## Pendientes (roadmap)

> 📌 El **control vivo de pendientes** se gestiona en [`MEMORY.md`](MEMORY.md): es la
> fuente única de lo que falta. Al completar un punto se marca y se elimina de allí, y
> se actualizan este README y `CLAUDE.md` si cambian hechos del proyecto.

Pendientes actuales (resumen — ver detalle y estado en [`MEMORY.md`](MEMORY.md)):

| # | Pendiente | Descripción |
|---|-----------|-------------|
| 1 | Mejorar el **CRUD de órdenes** | Desde el **historial/listado** de órdenes: **editar** cada orden y **eliminar** (cuando se requiera), al nivel del CRUD de clientes (validación, estados de carga/vacío/error y confirmaciones con modal). |
| 2 | Mapa de daños en **horizontal** | El diagrama del vehículo está en vertical; dejarlo en **orientación horizontal** (vista superior apaisada). |
| 3 | Áreas dañadas **junto al mapa** | Mostrar la visualización de las zonas dañadas **al lado** del diagrama del carro (dos columnas) para que sea más visible. |

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

# 7. Iniciar el backend (API)
uvicorn app.main:app --reload --app-dir backend

# 8. Servir el frontend (en otra terminal) — NO lo abras como archivo file://
#    porque el navegador bloquea las llamadas por CORS. Sírvelo por HTTP.
#    Recomendado en desarrollo (sin caché, evita módulos JS viejos):
python scripts/dev_frontend.py
#    Alternativa simple:
python -m http.server 8080 --directory frontend
```

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs` (solo con `DEBUG=true`)
- **Frontend: abrir `http://localhost:8080`** y entrar con `admin` / `admin123`.

> ⚠️ **CORS:** el origen donde sirves el frontend debe estar en `ALLOWED_ORIGINS`
> del `.env` (p. ej. `http://localhost:8080`). Si abres `index.html` con `file://`
> el login fallará con *Failed to fetch*. La URL de la API la define `BASE_URL` en
> `frontend/js/api.js` (por defecto `http://localhost:8000`).

> 💡 La base de datos se crea con `alembic upgrade head` (fuente de verdad del
> esquema). Si reutilizas un `taller.db` antiguo, aplica las migraciones para que
> tenga las últimas columnas (p. ej. `vehiculos.activo`).

---

## Variables de entorno

| Variable                      | Descripción                          | Default                         |
|-------------------------------|--------------------------------------|---------------------------------|
| `SECRET_KEY`                  | Clave JWT (mín. 32 caracteres)       | —                               |
| `DATABASE_URL`                | URL SQLAlchemy                       | `sqlite:///./backend/taller.db` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duración del token                   | `480`                           |
| `DEBUG`                       | Activa `/docs` y `/redoc`            | `false`                         |
| `ALLOWED_ORIGINS`             | CORS (separados por coma)            | `http://localhost:8000`         |
| `IVA_PORCENTAJE`              | % de IVA mostrado en el PDF (display)| `19.0`                          |

---

## Despliegue gratuito

El proyecto separa **frontend** (estático) y **backend** (API), así que se pueden
desplegar por separado usando tiers gratuitos. Recomendaciones vigentes (2026):

### Frontend (SPA estática)

| Plataforma | Por qué | Notas |
|------------|---------|-------|
| **Cloudflare Pages** (recomendado) | Ancho de banda **ilimitado** en el plan gratis + CDN global | Conecta el repo o sube `frontend/` |
| **GitHub Pages** | Lo más simple si el repo ya está en GitHub | Publica la carpeta `frontend/` |
| Netlify / Vercel | Buena DX | 100 GB/mes de ancho de banda gratis |

Pasos (cualquiera): publicar la carpeta `frontend/` y editar `BASE_URL` en
`frontend/js/api.js` para que apunte a la URL pública del backend.

### Backend (FastAPI)

| Plataforma | Free tier | Notas |
|------------|-----------|-------|
| **Render** (recomendado) | Web service siempre gratis (512 MB, 0.1 CPU), sin tarjeta | Se "duerme" tras inactividad → primer request lento (cold start) |
| **Koyeb** | 1 web service + 1 Postgres gratis, sin tarjeta | Buena opción con DB persistente |
| Railway | Solo ~$1/mes de crédito | Útil para pruebas, no para 24/7 |
| ~~Fly.io~~ | Ya **no** tiene free tier para nuevos usuarios | — |

**Consideraciones al desplegar el backend gratis:**

1. **SQLite es efímero** en estos tiers: el disco se reinicia en cada redeploy/sleep
   y se pierden los datos. Para una demo está bien (ejecutar `seed_db.py` al arrancar).
   Para persistencia real y gratuita, usar un **Postgres gratis** (Neon o Supabase) y
   cambiar `DATABASE_URL` (SQLAlchemy 2.0 funciona igual; revisar el driver `psycopg`).
2. **CORS:** poner el dominio público del frontend en `ALLOWED_ORIGINS`.
3. **SECRET_KEY:** generar una larga y aleatoria como variable de entorno (nunca commitearla).
4. **WeasyPrint (PDF)** necesita librerías del sistema (`pango`, `cairo`, `gdk-pixbuf`).
   En Render conviene un **Dockerfile** que las instale (`apt-get install -y libpango-1.0-0
   libpangocairo-1.0-0 libgdk-pixbuf2.0-0`) o un build con esos paquetes.
5. Comando de arranque típico: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir backend`.

> Alternativa "todo en uno": servir también el `frontend/` desde el propio backend
> (montando `StaticFiles` en FastAPI) para desplegar un **único servicio** gratuito.

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
