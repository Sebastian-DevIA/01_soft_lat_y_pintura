from sqlalchemy import ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.database import Base


class Asignacion(Base):
    __tablename__ = "asignaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fase_id: Mapped[int] = mapped_column(
        ForeignKey("fases_trabajo.id"), nullable=False, index=True
    )
    personal_id: Mapped[int] = mapped_column(
        ForeignKey("personal.id"), nullable=False, index=True
    )
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    fase: Mapped["FaseTrabajo"] = relationship(  # noqa: F821
        "FaseTrabajo", back_populates="asignaciones"
    )
    personal_asignado: Mapped["Personal"] = relationship(  # noqa: F821
        "Personal", back_populates="asignaciones"
    )
