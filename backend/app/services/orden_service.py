from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.orden_trabajo import OrdenTrabajo, TRANSICIONES_VALIDAS
from app.models.fase_trabajo import FaseTrabajo, ORDEN_FASES
from app.schemas.orden import OrdenCreateRequest, ItemCotizacionRequest
from app.models.item_cotizacion import ItemCotizacion


def crear_orden(db: Session, data: OrdenCreateRequest, usuario_id: int) -> OrdenTrabajo:
    orden = OrdenTrabajo(
        vehiculo_id=data.vehiculo_id,
        creado_por_id=usuario_id,
        observaciones=data.observaciones,
        fecha_estimada_entrega=data.fecha_estimada_entrega,
    )
    db.add(orden)
    db.commit()
    db.refresh(orden)
    return orden


def avanzar_estado(db: Session, orden_id: int, nuevo_estado: str) -> OrdenTrabajo:
    orden = _get_orden_o_404(db, orden_id)
    destinos = TRANSICIONES_VALIDAS.get(orden.estado, [])
    if nuevo_estado not in destinos:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"No se puede pasar de '{orden.estado}' a '{nuevo_estado}'",
        )
    orden.estado = nuevo_estado
    db.commit()
    db.refresh(orden)
    return orden


def aprobar_orden(db: Session, orden_id: int) -> OrdenTrabajo:
    orden = _get_orden_o_404(db, orden_id)
    if orden.estado != "COTIZACION":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Solo se puede aprobar una orden en estado COTIZACION",
        )
    if orden.total_con_descuento <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La cotización no tiene ítems con valor. Agregue ítems antes de aprobar.",
        )

    orden.estado = "APROBACION"
    orden.aprobado_por_cliente = True
    orden.fecha_aprobacion = datetime.now(timezone.utc)
    _crear_fases(db, orden)
    db.commit()
    db.refresh(orden)
    return orden


def aplicar_descuento(db: Session, orden_id: int, descuento_porcentaje: float) -> OrdenTrabajo:
    orden = _get_orden_o_404(db, orden_id)
    if orden.estado not in ("PERITAJE", "COTIZACION"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Solo se puede modificar el descuento en estado PERITAJE o COTIZACION",
        )
    orden.descuento_porcentaje = descuento_porcentaje
    _recalcular_totales(db, orden)
    db.commit()
    db.refresh(orden)
    return orden


def agregar_item(db: Session, orden_id: int, data: ItemCotizacionRequest) -> ItemCotizacion:
    orden = _get_orden_o_404(db, orden_id)
    if orden.estado not in ("PERITAJE", "COTIZACION"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Solo se pueden agregar ítems en estado PERITAJE o COTIZACION",
        )
    item = ItemCotizacion(
        orden_id=orden_id,
        descripcion=data.descripcion,
        area_vehiculo=data.area_vehiculo,
        precio_unitario=data.precio_unitario,
        cantidad=data.cantidad,
        subtotal=data.precio_unitario * data.cantidad,
        notas=data.notas,
    )
    db.add(item)
    if orden.estado == "PERITAJE":
        orden.estado = "COTIZACION"
    _recalcular_totales(db, orden)
    db.commit()
    db.refresh(item)
    return item


def actualizar_item(
    db: Session, orden_id: int, item_id: int, data: ItemCotizacionRequest
) -> ItemCotizacion:
    _get_orden_o_404(db, orden_id)
    item = db.query(ItemCotizacion).filter(
        ItemCotizacion.id == item_id, ItemCotizacion.orden_id == orden_id
    ).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ítem no encontrado")

    item.descripcion = data.descripcion
    item.area_vehiculo = data.area_vehiculo
    item.precio_unitario = data.precio_unitario
    item.cantidad = data.cantidad
    item.subtotal = data.precio_unitario * data.cantidad
    item.notas = data.notas

    orden = _get_orden_o_404(db, orden_id)
    _recalcular_totales(db, orden)
    db.commit()
    db.refresh(item)
    return item


def eliminar_item(db: Session, orden_id: int, item_id: int) -> None:
    orden = _get_orden_o_404(db, orden_id)
    item = db.query(ItemCotizacion).filter(
        ItemCotizacion.id == item_id, ItemCotizacion.orden_id == orden_id
    ).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ítem no encontrado")
    db.delete(item)
    _recalcular_totales(db, orden)
    db.commit()


# ── helpers privados ──────────────────────────────────────────────────────────

def _get_orden_o_404(db: Session, orden_id: int) -> OrdenTrabajo:
    orden = db.query(OrdenTrabajo).filter(OrdenTrabajo.id == orden_id).first()
    if not orden:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden no encontrada")
    return orden


def _recalcular_totales(db: Session, orden: OrdenTrabajo) -> None:
    items = db.query(ItemCotizacion).filter(ItemCotizacion.orden_id == orden.id).all()
    total = sum(i.subtotal for i in items)
    descuento_monto = total * (orden.descuento_porcentaje / 100)
    orden.total_cotizado = total
    orden.total_con_descuento = round(total - descuento_monto, 2)


def _crear_fases(db: Session, orden: OrdenTrabajo) -> None:
    for fase_nombre in ORDEN_FASES:
        fase = FaseTrabajo(orden_id=orden.id, fase=fase_nombre, estado="PENDIENTE")
        db.add(fase)
