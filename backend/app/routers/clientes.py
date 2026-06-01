from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.cliente import Cliente
from app.models.usuario import Usuario
from app.schemas.cliente import ClienteRequest, ClienteResponse, ClienteListResponse

router = APIRouter(prefix="/api/v1/clientes", tags=["Clientes"])


@router.get("/", response_model=list[ClienteListResponse])
def listar_clientes(
    busqueda: str | None = Query(
        None, description="Buscar por nombre, apellido o cédula"
    ),
    activo: bool = Query(True),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    q = db.query(Cliente).filter(Cliente.activo == activo)
    if busqueda:
        termino = f"%{busqueda}%"
        q = q.filter(
            Cliente.nombre.ilike(termino)
            | Cliente.apellido.ilike(termino)
            | Cliente.cedula_ruc.ilike(termino)
        )
    return q.offset(skip).limit(limit).all()


@router.post("/", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
def crear_cliente(
    data: ClienteRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    existente = db.query(Cliente).filter(Cliente.cedula_ruc == data.cedula_ruc).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un cliente con cédula/RUC {data.cedula_ruc}",
        )
    cliente = Cliente(**data.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.get("/{cliente_id}", response_model=ClienteResponse)
def obtener_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado"
        )
    return cliente


@router.put("/{cliente_id}", response_model=ClienteResponse)
def actualizar_cliente(
    cliente_id: int,
    data: ClienteRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado"
        )
    # cedula_ruc es unique: si cambia a una ya usada por otro cliente, evitar el 500.
    if data.cedula_ruc != cliente.cedula_ruc:
        conflicto = (
            db.query(Cliente)
            .filter(Cliente.cedula_ruc == data.cedula_ruc, Cliente.id != cliente_id)
            .first()
        )
        if conflicto:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un cliente con cédula/RUC {data.cedula_ruc}",
            )
    for campo, valor in data.model_dump().items():
        setattr(cliente, campo, valor)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado"
        )
    cliente.activo = False
    db.commit()


@router.patch("/{cliente_id}/activar", response_model=ClienteResponse)
def toggle_activo(
    cliente_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    """Alterna el estado activo/inactivo del cliente (permite reactivar tras soft-delete)."""
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado"
        )
    cliente.activo = not cliente.activo
    db.commit()
    db.refresh(cliente)
    return cliente
