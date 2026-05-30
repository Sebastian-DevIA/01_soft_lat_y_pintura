from datetime import datetime
from pydantic import BaseModel


class FacturaCreateRequest(BaseModel):
    orden_id: int
    fecha_estimada_entrega: datetime | None = None


class FacturaResponse(BaseModel):
    id: int
    orden_id: int
    numero_factura: str
    fecha_emision: datetime
    fecha_estimada_entrega: datetime | None
    monto_total: float
    monto_adelanto: float
    monto_saldo: float
    monto_pagado: float
    estado: str
    created_at: datetime

    model_config = {"from_attributes": True}
