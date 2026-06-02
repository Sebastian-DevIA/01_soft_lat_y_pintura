from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreateRequest, UsuarioUpdateRequest
from app.utils.security import hash_password


def _get_usuario_o_404(db: Session, usuario_id: int) -> Usuario:
    user = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )
    return user


def listar_usuarios(db: Session) -> list[Usuario]:
    return db.query(Usuario).order_by(Usuario.id.asc()).all()


def crear_usuario(db: Session, data: UsuarioCreateRequest) -> Usuario:
    existe = db.query(Usuario).filter(Usuario.username == data.username).first()
    if existe:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese nombre de usuario",
        )
    if data.email:
        email_dup = db.query(Usuario).filter(Usuario.email == data.email).first()
        if email_dup:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un usuario con ese email",
            )

    user = Usuario(
        username=data.username,
        email=data.email,
        nombre_completo=data.nombre_completo,
        hashed_password=hash_password(data.password),
        perfil=data.perfil,
        is_admin=(data.perfil == "ADMIN"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def actualizar_usuario(
    db: Session, usuario_id: int, data: UsuarioUpdateRequest, actor: Usuario
) -> Usuario:
    user = _get_usuario_o_404(db, usuario_id)

    if data.perfil is not None:
        # Evitar que el admin se quite a sí mismo el rol y se quede sin acceso.
        if user.id == actor.id and data.perfil != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No puedes quitarte a ti mismo el perfil de administrador",
            )
        user.perfil = data.perfil
        user.is_admin = data.perfil == "ADMIN"

    if data.is_active is not None:
        if user.id == actor.id and data.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No puedes desactivar tu propio usuario",
            )
        user.is_active = data.is_active

    if data.nombre_completo is not None:
        user.nombre_completo = data.nombre_completo

    if data.email is not None:
        if data.email:
            email_dup = (
                db.query(Usuario)
                .filter(Usuario.email == data.email, Usuario.id != user.id)
                .first()
            )
            if email_dup:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe un usuario con ese email",
                )
        user.email = data.email or None

    if data.password:
        user.hashed_password = hash_password(data.password)

    db.commit()
    db.refresh(user)
    return user
