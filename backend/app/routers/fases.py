from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.fase_trabajo import FaseTrabajo
from app.models.usuario import Usuario
from app.schemas.fase import FaseEstadoRequest, FaseResponse, AsignacionRequest, AsignacionResponse
from app.services import fase_service

router = APIRouter(prefix="/api/v1/fases", tags=["Fases de Trabajo"])


@router.get("/orden/{orden_id}", response_model=list[FaseResponse])
def fases_por_orden(
    orden_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return db.query(FaseTrabajo).filter(FaseTrabajo.orden_id == orden_id).all()


@router.patch("/{fase_id}/estado", response_model=FaseResponse)
def avanzar_fase(
    fase_id: int,
    data: FaseEstadoRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return fase_service.avanzar_fase(db, fase_id, data.estado, data.notas)


@router.post("/{fase_id}/personal", response_model=AsignacionResponse, status_code=status.HTTP_201_CREATED)
def asignar_personal(
    fase_id: int,
    data: AsignacionRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return fase_service.asignar_personal(db, fase_id, data.personal_id, data.notas)


@router.delete("/{fase_id}/personal/{personal_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_personal(
    fase_id: int,
    personal_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    fase_service.remover_personal(db, fase_id, personal_id)
