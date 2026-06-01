from datetime import datetime
from pydantic import BaseModel


class FaseEstadoRequest(BaseModel):
    estado: str
    notas: str | None = None


class AsignacionRequest(BaseModel):
    personal_id: int
    notas: str | None = None


class AsignacionResponse(BaseModel):
    id: int
    fase_id: int
    personal_id: int
    notas: str | None
    created_at: datetime
    # Nombre plano del técnico asignado (contrato con el Kanban del frontend)
    personal_nombre: str | None = None

    model_config = {"from_attributes": True}


class FaseResponse(BaseModel):
    id: int
    orden_id: int
    fase: str
    estado: str
    fecha_inicio: datetime | None
    fecha_fin: datetime | None
    notas: str | None
    asignaciones: list[AsignacionResponse]
    created_at: datetime

    model_config = {"from_attributes": True}
