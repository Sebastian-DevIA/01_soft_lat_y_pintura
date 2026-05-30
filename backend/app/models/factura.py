from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.database import Base

ESTADOS_FACTURA = ("PENDIENTE", "PARCIAL", "PAGADA")


class Factura(Base):
    __tablename__ = "facturas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    orden_id: Mapped[int] = mapped_column(ForeignKey("ordenes_trabajo.id"), nullable=False, unique=True)
    numero_factura: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)

    fecha_emision: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    fecha_estimada_entrega: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    monto_total: Mapped[float] = mapped_column(Float, nullable=False)
    monto_adelanto: Mapped[float] = mapped_column(Float, nullable=False)
    monto_saldo: Mapped[float] = mapped_column(Float, nullable=False)
    monto_pagado: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    estado: Mapped[str] = mapped_column(String(20), default="PENDIENTE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    orden: Mapped["OrdenTrabajo"] = relationship(  # noqa: F821
        "OrdenTrabajo", back_populates="factura"
    )
    pagos: Mapped[list["Pago"]] = relationship(  # noqa: F821
        "Pago", back_populates="factura", cascade="all, delete-orphan"
    )
