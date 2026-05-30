from datetime import datetime
from pydantic import BaseModel


class PersonalRequest(BaseModel):
    nombre: str
    apellido: str
    rol: str
    telefono: str | None = None


class PersonalResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    rol: str
    telefono: str | None
    activo: bool
    created_at: datetime

    model_config = {"from_attributes": True}
