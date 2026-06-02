from typing import Literal

from pydantic import BaseModel, Field

# Perfiles operativos. ADMIN gestiona todo (is_admin=True); los demás mapean a una
# fase del taller (RECEPCION→INGRESO, TECNICO→REPARACION, ENTREGA→ENTREGA).
PERFILES = ("ADMIN", "RECEPCION", "TECNICO", "ENTREGA")
PerfilLiteral = Literal["ADMIN", "RECEPCION", "TECNICO", "ENTREGA"]


class UsuarioCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)
    perfil: PerfilLiteral = "RECEPCION"
    nombre_completo: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=150)


class UsuarioUpdateRequest(BaseModel):
    perfil: PerfilLiteral | None = None
    is_active: bool | None = None
    nombre_completo: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=150)
    # Reseteo de contraseña opcional (solo admin).
    password: str | None = Field(default=None, min_length=6, max_length=100)


class UsuarioAdminResponse(BaseModel):
    id: int
    username: str
    email: str | None
    nombre_completo: str | None
    is_active: bool
    is_admin: bool
    perfil: str

    model_config = {"from_attributes": True}
