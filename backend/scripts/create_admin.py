#!/usr/bin/env python3
"""Script para crear el usuario administrador inicial del taller."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal, engine, Base
import app.models  # noqa: F401 — registrar todos los modelos
from app.models.usuario import Usuario
from app.utils.security import hash_password


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existente = db.query(Usuario).filter(Usuario.username == "admin").first()
        if existente:
            print("El usuario 'admin' ya existe.")
            return

        admin = Usuario(
            username="admin",
            email="admin@tallerlatonpaint.com",
            hashed_password=hash_password("admin123"),
            nombre_completo="Administrador Taller",
            is_active=True,
            is_admin=True,
        )
        db.add(admin)
        db.commit()
        print("Usuario 'admin' creado exitosamente.")
        print("  Username: admin")
        print("  Password: admin123")
        print("  ⚠️  Cambia la contraseña después del primer inicio de sesión.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
