from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UsuarioResponse(BaseModel):
    id: int
    username: str
    email: str | None
    nombre_completo: str | None
    is_active: bool
    is_admin: bool

    model_config = {"from_attributes": True}
