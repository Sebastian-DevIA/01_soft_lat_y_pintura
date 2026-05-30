from datetime import datetime
from pydantic import BaseModel, field_validator


class VehiculoRequest(BaseModel):
    cliente_id: int
    placa: str
    marca: str
    modelo: str
    anio: int | None = None
    color: str | None = None
    vin: str | None = None
    kilometraje: int | None = None

    @field_validator("placa", "marca", "modelo")
    @classmethod
    def no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Este campo no puede estar vacío")
        return v.strip().upper()


class VehiculoResponse(BaseModel):
    id: int
    cliente_id: int
    placa: str
    marca: str
    modelo: str
    anio: int | None
    color: str | None
    vin: str | None
    kilometraje: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
