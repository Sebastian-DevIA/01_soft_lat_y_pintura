from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.vehiculo import Vehiculo
from app.models.usuario import Usuario
from app.schemas.vehiculo import VehiculoRequest, VehiculoResponse

router = APIRouter(prefix="/api/v1/vehiculos", tags=["Vehículos"])


@router.get("/", response_model=list[VehiculoResponse])
def listar_vehiculos(
    placa: str | None = Query(None),
    cliente_id: int | None = Query(None),
    activo: bool = Query(True),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    q = db.query(Vehiculo).filter(Vehiculo.activo == activo)
    if placa:
        q = q.filter(Vehiculo.placa.ilike(f"%{placa}%"))
    if cliente_id:
        q = q.filter(Vehiculo.cliente_id == cliente_id)
    return q.offset(skip).limit(limit).all()


@router.post("/", response_model=VehiculoResponse, status_code=status.HTTP_201_CREATED)
def registrar_vehiculo(
    data: VehiculoRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    if db.query(Vehiculo).filter(Vehiculo.placa == data.placa).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un vehículo con placa {data.placa}",
        )
    vehiculo = Vehiculo(**data.model_dump())
    db.add(vehiculo)
    db.commit()
    db.refresh(vehiculo)
    return vehiculo


@router.get("/{vehiculo_id}", response_model=VehiculoResponse)
def obtener_vehiculo(
    vehiculo_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
    if not vehiculo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vehículo no encontrado"
        )
    return vehiculo


@router.put("/{vehiculo_id}", response_model=VehiculoResponse)
def actualizar_vehiculo(
    vehiculo_id: int,
    data: VehiculoRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
    if not vehiculo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vehículo no encontrado"
        )
    for campo, valor in data.model_dump().items():
        setattr(vehiculo, campo, valor)
    db.commit()
    db.refresh(vehiculo)
    return vehiculo


@router.delete("/{vehiculo_id}", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_vehiculo(
    vehiculo_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
    if not vehiculo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Vehículo no encontrado"
        )
    vehiculo.activo = False
    db.commit()
