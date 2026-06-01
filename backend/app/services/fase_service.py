from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.fase_trabajo import FaseTrabajo
from app.models.asignacion import Asignacion
from app.models.orden_trabajo import OrdenTrabajo
from app.schemas.fase import AsignacionResponse, FaseResponse


def listar_fases_por_orden(db: Session, orden_id: int) -> list[FaseResponse]:
    fases = (
        db.query(FaseTrabajo)
        .filter(FaseTrabajo.orden_id == orden_id)
        .options(
            joinedload(FaseTrabajo.asignaciones).joinedload(
                Asignacion.personal_asignado
            )
        )
        .order_by(FaseTrabajo.id)
        .all()
    )
    return [_a_fase_response(fase) for fase in fases]


def avanzar_fase(
    db: Session, fase_id: int, nuevo_estado: str, notas: str | None
) -> FaseResponse:
    fase = _get_fase_o_404(db, fase_id)

    if nuevo_estado == "COMPLETADA" and fase.fase == "ENTREGA":
        _validar_pago_completo(db, fase.orden_id)

    if nuevo_estado == "EN_PROGRESO":
        fase.fecha_inicio = datetime.now(timezone.utc)
    elif nuevo_estado == "COMPLETADA":
        fase.fecha_fin = datetime.now(timezone.utc)
        if fase.fase == "ENTREGA":
            orden = (
                db.query(OrdenTrabajo).filter(OrdenTrabajo.id == fase.orden_id).first()
            )
            if orden:
                orden.estado = "ENTREGADO"
                orden.fecha_entrega_real = datetime.now(timezone.utc)

    fase.estado = nuevo_estado
    if notas:
        fase.notas = notas
    db.commit()
    db.refresh(fase)
    return _a_fase_response(fase)


def asignar_personal(
    db: Session, fase_id: int, personal_id: int, notas: str | None
) -> AsignacionResponse:
    _get_fase_o_404(db, fase_id)
    existente = (
        db.query(Asignacion)
        .filter(Asignacion.fase_id == fase_id, Asignacion.personal_id == personal_id)
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este empleado ya está asignado a esta fase",
        )
    asignacion = Asignacion(fase_id=fase_id, personal_id=personal_id, notas=notas)
    db.add(asignacion)
    db.commit()
    db.refresh(asignacion)
    return _a_asignacion_response(asignacion)


def remover_personal(db: Session, fase_id: int, personal_id: int) -> None:
    asignacion = (
        db.query(Asignacion)
        .filter(Asignacion.fase_id == fase_id, Asignacion.personal_id == personal_id)
        .first()
    )
    if not asignacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Asignación no encontrada"
        )
    db.delete(asignacion)
    db.commit()


def _get_fase_o_404(db: Session, fase_id: int) -> FaseTrabajo:
    fase = db.query(FaseTrabajo).filter(FaseTrabajo.id == fase_id).first()
    if not fase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Fase no encontrada"
        )
    return fase


def _a_asignacion_response(asignacion: Asignacion) -> AsignacionResponse:
    resp = AsignacionResponse.model_validate(asignacion)
    persona = asignacion.personal_asignado
    nombre = f"{persona.nombre} {persona.apellido}" if persona else None
    return resp.model_copy(update={"personal_nombre": nombre})


def _a_fase_response(fase: FaseTrabajo) -> FaseResponse:
    resp = FaseResponse.model_validate(fase)
    asignaciones = [_a_asignacion_response(a) for a in fase.asignaciones]
    return resp.model_copy(update={"asignaciones": asignaciones})


def _validar_pago_completo(db: Session, orden_id: int) -> None:
    orden = db.query(OrdenTrabajo).filter(OrdenTrabajo.id == orden_id).first()
    if not orden or not orden.factura:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La orden no tiene factura emitida",
        )
    if orden.factura.estado != "PAGADA":
        saldo = orden.factura.monto_total - orden.factura.monto_pagado
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"El vehículo no puede ser entregado. Saldo pendiente: ${saldo:.2f}",
        )
