from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.database import Base

TIPOS_PAGO = ("ADELANTO", "SALDO", "ABONO")
METODOS_PAGO = ("EFECTIVO", "TRANSFERENCIA", "TARJETA")


class Pago(Base):
    __tablename__ = "pagos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    factura_id: Mapped[int] = mapped_column(
        ForeignKey("facturas.id"), nullable=False, index=True
    )
    registrado_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )

    monto: Mapped[float] = mapped_column(Float, nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    metodo: Mapped[str] = mapped_column(String(20), nullable=False)
    referencia: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fecha_pago: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    factura: Mapped["Factura"] = relationship(  # noqa: F821
        "Factura", back_populates="pagos"
    )
    registrado_por: Mapped["Usuario"] = relationship(  # noqa: F821
        "Usuario", back_populates="pagos_registrados"
    )
