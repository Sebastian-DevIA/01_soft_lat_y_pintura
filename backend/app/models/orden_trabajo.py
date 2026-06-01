from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.database import Base

# Estados válidos de la orden
ESTADOS_ORDEN = (
    "PERITAJE",
    "COTIZACION",
    "APROBACION",
    "EN_PROCESO",
    "ENTREGADO",
    "CANCELADO",
)

# Transiciones permitidas (state machine)
TRANSICIONES_VALIDAS: dict[str, list[str]] = {
    "PERITAJE": ["COTIZACION", "CANCELADO"],
    "COTIZACION": ["APROBACION", "CANCELADO"],
    "APROBACION": ["EN_PROCESO", "CANCELADO"],
    "EN_PROCESO": ["ENTREGADO", "CANCELADO"],
    "ENTREGADO": [],
    "CANCELADO": [],
}


class OrdenTrabajo(Base):
    __tablename__ = "ordenes_trabajo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehiculo_id: Mapped[int] = mapped_column(
        ForeignKey("vehiculos.id"), nullable=False, index=True
    )
    creado_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )

    estado: Mapped[str] = mapped_column(
        String(20), default="PERITAJE", nullable=False, index=True
    )
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    descuento_porcentaje: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    total_cotizado: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_con_descuento: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )

    aprobado_por_cliente: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    fecha_aprobacion: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fecha_ingreso: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    fecha_estimada_entrega: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    fecha_entrega_real: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    vehiculo: Mapped["Vehiculo"] = relationship(  # noqa: F821
        "Vehiculo", back_populates="ordenes"
    )
    creado_por: Mapped["Usuario"] = relationship(  # noqa: F821
        "Usuario", back_populates="ordenes_creadas"
    )
    items: Mapped[list["ItemCotizacion"]] = relationship(  # noqa: F821
        "ItemCotizacion", back_populates="orden", cascade="all, delete-orphan"
    )
    factura: Mapped["Factura | None"] = relationship(  # noqa: F821
        "Factura", back_populates="orden", uselist=False
    )
    fases: Mapped[list["FaseTrabajo"]] = relationship(  # noqa: F821
        "FaseTrabajo", back_populates="orden", cascade="all, delete-orphan"
    )
