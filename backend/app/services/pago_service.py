from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.factura import Factura
from app.models.pago import Pago
from app.schemas.pago import PagoRequest


def registrar_pago(db: Session, data: PagoRequest, usuario_id: int) -> Pago:
    factura = db.query(Factura).filter(Factura.id == data.factura_id).first()
    if not factura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Factura no encontrada"
        )
    if factura.estado == "PAGADA":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La factura ya está completamente pagada",
        )

    saldo_restante = factura.monto_total - factura.monto_pagado
    if data.monto > saldo_restante + 0.01:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"El monto excede el saldo restante (${saldo_restante:.2f})",
        )

    pago = Pago(
        factura_id=data.factura_id,
        registrado_por_id=usuario_id,
        monto=data.monto,
        tipo=data.tipo,
        metodo=data.metodo,
        referencia=data.referencia,
        notas=data.notas,
    )
    db.add(pago)

    factura.monto_pagado = round(factura.monto_pagado + data.monto, 2)
    if factura.monto_pagado >= factura.monto_total - 0.01:
        factura.estado = "PAGADA"
    elif factura.monto_pagado > 0:
        factura.estado = "PARCIAL"

    db.commit()
    db.refresh(pago)
    return pago
