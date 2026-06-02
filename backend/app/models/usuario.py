from sqlalchemy import Boolean, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression
from datetime import datetime

from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    email: Mapped[str | None] = mapped_column(String(150), unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)
    nombre_completo: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default=expression.true(), nullable=False
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean, server_default=expression.false(), nullable=False
    )
    # Perfil operativo (RBAC ligero): ADMIN, RECEPCION, TECNICO, ENTREGA.
    # ADMIN va siempre con is_admin=True; los demás mapean a una fase del taller.
    perfil: Mapped[str] = mapped_column(
        String(20), server_default="RECEPCION", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    ordenes_creadas: Mapped[list["OrdenTrabajo"]] = relationship(  # noqa: F821
        "OrdenTrabajo", back_populates="creado_por"
    )
    pagos_registrados: Mapped[list["Pago"]] = relationship(  # noqa: F821
        "Pago", back_populates="registrado_por"
    )
