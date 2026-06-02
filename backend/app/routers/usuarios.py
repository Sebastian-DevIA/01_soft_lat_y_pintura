from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from app.dependencies.auth import get_current_admin
from app.models.usuario import Usuario
from app.schemas.usuario import (
    UsuarioCreateRequest,
    UsuarioUpdateRequest,
    UsuarioAdminResponse,
)
from app.services import usuario_service

router = APIRouter(prefix="/api/v1/usuarios", tags=["Usuarios"])


@router.get("/", response_model=list[UsuarioAdminResponse])
def listar_usuarios(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_admin),
):
    return usuario_service.listar_usuarios(db)


@router.post(
    "/", response_model=UsuarioAdminResponse, status_code=status.HTTP_201_CREATED
)
def crear_usuario(
    data: UsuarioCreateRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_admin),
):
    return usuario_service.crear_usuario(db, data)


@router.patch("/{usuario_id}", response_model=UsuarioAdminResponse)
def actualizar_usuario(
    usuario_id: int,
    data: UsuarioUpdateRequest,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_admin),
):
    return usuario_service.actualizar_usuario(db, usuario_id, data, admin)
