from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.factura import Factura
from app.models.orden_trabajo import OrdenTrabajo, TRANSICIONES_VALIDAS
from app.schemas.factura import FacturaCreateRequest


def _generar_numero_factura(db: Session) -> str:
    anio = datetime.now(timezone.utc).year
    total = db.query(Factura).count()
    return f"FAC-{anio}-{total + 1:04d}"


def emitir_factura(db: Session, data: FacturaCreateRequest) -> Factura:
    orden = db.query(OrdenTrabajo).filter(OrdenTrabajo.id == data.orden_id).first()
    if not orden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Orden no encontrada"
        )
    if orden.estado != "APROBACION":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Solo se puede emitir factura para órdenes en estado APROBACION",
        )
    if orden.factura:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta orden ya tiene una factura emitida",
        )

    monto_total = orden.total_con_descuento
    monto_adelanto = round(monto_total * 0.5, 2)
    monto_saldo = round(monto_total - monto_adelanto, 2)

    factura = Factura(
        orden_id=data.orden_id,
        numero_factura=_generar_numero_factura(db),
        fecha_estimada_entrega=data.fecha_estimada_entrega,
        monto_total=monto_total,
        monto_adelanto=monto_adelanto,
        monto_saldo=monto_saldo,
        monto_pagado=0.0,
        estado="PENDIENTE",
    )
    db.add(factura)

    # Respetar la state machine: APROBACION → EN_PROCESO (validar antes de avanzar).
    # No usamos orden_service.avanzar_estado para no partir esta transacción en dos commits.
    if "EN_PROCESO" not in TRANSICIONES_VALIDAS.get(orden.estado, []):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No se puede pasar de '{orden.estado}' a 'EN_PROCESO'",
        )
    orden.estado = "EN_PROCESO"
    if data.fecha_estimada_entrega:
        orden.fecha_estimada_entrega = data.fecha_estimada_entrega

    db.commit()
    db.refresh(factura)
    return factura
