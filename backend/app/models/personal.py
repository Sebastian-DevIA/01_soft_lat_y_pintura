from sqlalchemy import Boolean, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression
from datetime import datetime

from app.database import Base

ROLES_PERSONAL = (
    "LATONERO",
    "PINTOR",
    "PULIDOR",
    "AUXILIAR",
    "JEFE_TALLER",
    "RECEPCIONISTA",
)


class Personal(Base):
    __tablename__ = "personal"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido: Mapped[str] = mapped_column(String(100), nullable=False)
    rol: Mapped[str] = mapped_column(String(30), nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(20), nullable=True)
    activo: Mapped[bool] = mapped_column(
        Boolean, server_default=expression.true(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    asignaciones: Mapped[list["Asignacion"]] = relationship(  # noqa: F821
        "Asignacion", back_populates="personal_asignado"
    )

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"
