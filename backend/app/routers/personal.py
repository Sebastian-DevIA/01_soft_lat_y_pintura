from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.personal import Personal
from app.models.usuario import Usuario
from app.schemas.personal import PersonalRequest, PersonalResponse

router = APIRouter(prefix="/api/v1/personal", tags=["Personal"])


@router.get("/", response_model=list[PersonalResponse])
def listar_personal(
    activo: bool = True,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return db.query(Personal).filter(Personal.activo == activo).all()


@router.post("/", response_model=PersonalResponse, status_code=status.HTTP_201_CREATED)
def registrar_personal(
    data: PersonalRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    empleado = Personal(**data.model_dump())
    db.add(empleado)
    db.commit()
    db.refresh(empleado)
    return empleado


@router.get("/{personal_id}", response_model=PersonalResponse)
def obtener_personal(
    personal_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    empleado = db.query(Personal).filter(Personal.id == personal_id).first()
    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Empleado no encontrado"
        )
    return empleado


@router.put("/{personal_id}", response_model=PersonalResponse)
def actualizar_personal(
    personal_id: int,
    data: PersonalRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    empleado = db.query(Personal).filter(Personal.id == personal_id).first()
    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Empleado no encontrado"
        )
    for campo, valor in data.model_dump().items():
        setattr(empleado, campo, valor)
    db.commit()
    db.refresh(empleado)
    return empleado


@router.patch("/{personal_id}/activar", response_model=PersonalResponse)
def toggle_activo(
    personal_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    empleado = db.query(Personal).filter(Personal.id == personal_id).first()
    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Empleado no encontrado"
        )
    empleado.activo = not empleado.activo
    db.commit()
    db.refresh(empleado)
    return empleado
