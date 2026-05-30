from datetime import datetime
from pydantic import BaseModel, field_validator


class PagoRequest(BaseModel):
    factura_id: int
    monto: float
    tipo: str
    metodo: str
    referencia: str | None = None
    notas: str | None = None

    @field_validator("monto")
    @classmethod
    def monto_positivo(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        return v

    @field_validator("tipo")
    @classmethod
    def tipo_valido(cls, v: str) -> str:
        if v not in ("ADELANTO", "SALDO", "ABONO"):
            raise ValueError("Tipo debe ser ADELANTO, SALDO o ABONO")
        return v

    @field_validator("metodo")
    @classmethod
    def metodo_valido(cls, v: str) -> str:
        if v not in ("EFECTIVO", "TRANSFERENCIA", "TARJETA"):
            raise ValueError("Método debe ser EFECTIVO, TRANSFERENCIA o TARJETA")
        return v


class PagoResponse(BaseModel):
    id: int
    factura_id: int
    monto: float
    tipo: str
    metodo: str
    referencia: str | None
    fecha_pago: datetime
    notas: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
