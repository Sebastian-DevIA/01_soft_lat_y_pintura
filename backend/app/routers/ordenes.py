from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.orden_trabajo import OrdenTrabajo
from app.models.usuario import Usuario
from app.schemas.orden import (
    OrdenCreateRequest,
    OrdenDetalleResponse,
    OrdenResumenResponse,
    OrdenEstadoRequest,
    OrdenDescuentoRequest,
    ItemCotizacionRequest,
    ItemCotizacionResponse,
)
from app.services import orden_service

router = APIRouter(prefix="/api/v1/ordenes", tags=["Órdenes de Trabajo"])


@router.get("/", response_model=list[OrdenResumenResponse])
def listar_ordenes(
    estado: str | None = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    q = db.query(OrdenTrabajo)
    if estado:
        q = q.filter(OrdenTrabajo.estado == estado)
    return q.order_by(OrdenTrabajo.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/", response_model=OrdenResumenResponse, status_code=status.HTTP_201_CREATED)
def crear_orden(
    data: OrdenCreateRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return orden_service.crear_orden(db, data, current_user.id)


@router.get("/{orden_id}", response_model=OrdenDetalleResponse)
def obtener_orden(
    orden_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return orden_service._get_orden_o_404(db, orden_id)


@router.patch("/{orden_id}/estado", response_model=OrdenResumenResponse)
def cambiar_estado(
    orden_id: int,
    data: OrdenEstadoRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return orden_service.avanzar_estado(db, orden_id, data.estado)


@router.patch("/{orden_id}/aprobar", response_model=OrdenResumenResponse)
def aprobar_orden(
    orden_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return orden_service.aprobar_orden(db, orden_id)


@router.patch("/{orden_id}/descuento", response_model=OrdenResumenResponse)
def aplicar_descuento(
    orden_id: int,
    data: OrdenDescuentoRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return orden_service.aplicar_descuento(db, orden_id, data.descuento_porcentaje)


@router.post("/{orden_id}/items", response_model=ItemCotizacionResponse, status_code=status.HTTP_201_CREATED)
def agregar_item(
    orden_id: int,
    data: ItemCotizacionRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return orden_service.agregar_item(db, orden_id, data)


@router.put("/{orden_id}/items/{item_id}", response_model=ItemCotizacionResponse)
def actualizar_item(
    orden_id: int,
    item_id: int,
    data: ItemCotizacionRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return orden_service.actualizar_item(db, orden_id, item_id, data)


@router.delete("/{orden_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_item(
    orden_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    orden_service.eliminar_item(db, orden_id, item_id)
