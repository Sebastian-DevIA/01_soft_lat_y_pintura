from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.database import Base


class Vehiculo(Base):
    __tablename__ = "vehiculos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False, index=True)
    placa: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    marca: Mapped[str] = mapped_column(String(50), nullable=False)
    modelo: Mapped[str] = mapped_column(String(80), nullable=False)
    anio: Mapped[int | None] = mapped_column(Integer, nullable=True)
    color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vin: Mapped[str | None] = mapped_column(String(50), nullable=True)
    kilometraje: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    cliente: Mapped["Cliente"] = relationship(  # noqa: F821
        "Cliente", back_populates="vehiculos"
    )
    ordenes: Mapped[list["OrdenTrabajo"]] = relationship(  # noqa: F821
        "OrdenTrabajo", back_populates="vehiculo"
    )
