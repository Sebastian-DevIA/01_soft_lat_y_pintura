from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.database import Base

FASES = ("INGRESO", "REPARACION", "ENTREGA")
ESTADOS_FASE = ("PENDIENTE", "EN_PROGRESO", "COMPLETADA")

ORDEN_FASES = ["INGRESO", "REPARACION", "ENTREGA"]


class FaseTrabajo(Base):
    __tablename__ = "fases_trabajo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    orden_id: Mapped[int] = mapped_column(ForeignKey("ordenes_trabajo.id"), nullable=False, index=True)
    fase: Mapped[str] = mapped_column(String(20), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="PENDIENTE", nullable=False)
    fecha_inicio: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fecha_fin: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    orden: Mapped["OrdenTrabajo"] = relationship(  # noqa: F821
        "OrdenTrabajo", back_populates="fases"
    )
    asignaciones: Mapped[list["Asignacion"]] = relationship(  # noqa: F821
        "Asignacion", back_populates="fase", cascade="all, delete-orphan"
    )
