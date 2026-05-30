from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.pago import Pago
from app.models.usuario import Usuario
from app.schemas.pago import PagoRequest, PagoResponse
from app.services import pago_service

router = APIRouter(prefix="/api/v1/pagos", tags=["Pagos"])


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
