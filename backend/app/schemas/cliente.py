from datetime import datetime
from pydantic import BaseModel, field_validator


class ClienteRequest(BaseModel):
    nombre: str
    apellido: str
    cedula_ruc: str
    telefono: str
    email: str | None = None
    direccion: str | None = None

    @field_validator("nombre", "apellido", "cedula_ruc", "telefono")
    @classmethod
    def no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Este campo no puede estar vacío")
        return v.strip()


class ClienteResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    cedula_ruc: str
    telefono: str
    email: str | None
    direccion: str | None
    activo: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ClienteListResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    cedula_ruc: str
    telefono: str
    activo: bool

    model_config = {"from_attributes": True}
