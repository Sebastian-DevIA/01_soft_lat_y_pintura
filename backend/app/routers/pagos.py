from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.pago import Pago
from app.models.usuario import Usuario
from app.schemas.pago import PagoRequest, PagoResponse
from app.services import pago_service

router = APIRouter(prefix="/api/v1/pagos", tags=["Pagos"])


@router.get("/", response_model=list[PagoResponse])
def listar_pagos(
    factura_id: int | None = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    q = db.query(Pago)
    if factura_id:
        q = q.filter(Pago.factura_id == factura_id)
    return q.order_by(Pago.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/", response_model=PagoResponse, status_code=status.HTTP_201_CREATED)
def registrar_pago(
    data: PagoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return pago_service.registrar_pago(db, data, current_user.id)


@router.get("/factura/{factura_id}", response_model=list[PagoResponse])
def pagos_por_factura(
    factura_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return db.query(Pago).filter(Pago.factura_id == factura_id).all()
