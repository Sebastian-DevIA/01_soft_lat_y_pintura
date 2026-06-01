from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    auth,
    clientes,
    vehiculos,
    ordenes,
    facturas,
    pagos,
    fases,
    personal,
)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Sistema de gestión operacional para taller de latonería y pintura automotriz.",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(clientes.router)
app.include_router(vehiculos.router)
app.include_router(ordenes.router)
app.include_router(facturas.router)
app.include_router(pagos.router)
app.include_router(fases.router)
app.include_router(personal.router)


@app.get("/health", tags=["Sistema"])
def health_check():
    return {"status": "ok", "version": settings.app_version}
