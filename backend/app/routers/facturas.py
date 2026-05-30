from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.factura import Factura
from app.models.usuario import Usuario
from app.schemas.factura import FacturaCreateRequest, FacturaResponse
from app.services import factura_service
from app.services.pdf_service import generar_pdf_factura

router = APIRouter(prefix="/api/v1/facturas", tags=["Facturas"])


@router.post("/", response_model=FacturaResponse, status_code=status.HTTP_201_CREATED)
def emitir_factura(
    data: FacturaCreateRequest,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return factura_service.emitir_factura(db, data)


@router.get("/{factura_id}", response_model=FacturaResponse)
def obtener_factura(
    factura_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factura no encontrada")
    return factura


@router.get("/{factura_id}/pdf")
def descargar_pdf(
    factura_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factura no encontrada")
    pdf_bytes = generar_pdf_factura(factura)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={factura.numero_factura}.pdf"},
    )
