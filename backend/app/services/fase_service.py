from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.fase_trabajo import FaseTrabajo
from app.models.asignacion import Asignacion
from app.models.factura import Factura
from app.models.orden_trabajo import OrdenTrabajo


def avanzar_fase(db: Session, fase_id: int, nuevo_estado: str, notas: str | None) -> FaseTrabajo:
    fase = _get_fase_o_404(db, fase_id)

    if nuevo_estado == "COMPLETADA" and fase.fase == "ENTREGA":
        _validar_pago_completo(db, fase.orden_id)

    if nuevo_estado == "EN_PROGRESO":
        fase.fecha_inicio = datetime.now(timezone.utc)
    elif nuevo_estado == "COMPLETADA":
        fase.fecha_fin = datetime.now(timezone.utc)
        if fase.fase == "ENTREGA":
            orden = db.query(OrdenTrabajo).filter(OrdenTrabajo.id == fase.orden_id).first()
            if orden:
                orden.estado = "ENTREGADO"
                orden.fecha_entrega_real = datetime.now(timezone.utc)

    fase.estado = nuevo_estado
    if notas:
        fase.notas = notas
    db.commit()
    db.refresh(fase)
    return fase


def asignar_personal(db: Session, fase_id: int, personal_id: int, notas: str | None) -> Asignacion:
    _get_fase_o_404(db, fase_id)
    existente = db.query(Asignacion).filter(
        Asignacion.fase_id == fase_id, Asignacion.personal_id == personal_id
    ).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este empleado ya está asignado a esta fase",
        )
    asignacion = Asignacion(fase_id=fase_id, personal_id=personal_id, notas=notas)
    db.add(asignacion)
    db.commit()
    db.refresh(asignacion)
    return asignacion


def remover_personal(db: Session, fase_id: int, personal_id: int) -> None:
    asignacion = db.query(Asignacion).filter(
        Asignacion.fase_id == fase_id, Asignacion.personal_id == personal_id
    ).first()
    if not asignacion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignación no encontrada")
    db.delete(asignacion)
    db.commit()


def _get_fase_o_404(db: Session, fase_id: int) -> FaseTrabajo:
    fase = db.query(FaseTrabajo).filter(FaseTrabajo.id == fase_id).first()
    if not fase:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fase no encontrada")
    return fase


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
