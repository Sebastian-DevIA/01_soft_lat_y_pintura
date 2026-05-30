from sqlalchemy import Boolean, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression
from datetime import datetime

from app.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    cedula_ruc: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    telefono: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    direccion: Mapped[str | None] = mapped_column(String(300), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, server_default=expression.true(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    vehiculos: Mapped[list["Vehiculo"]] = relationship(  # noqa: F821
        "Vehiculo", back_populates="cliente"
    )

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"
