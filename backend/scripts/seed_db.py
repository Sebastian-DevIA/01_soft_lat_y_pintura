#!/usr/bin/env python3
"""Carga datos de demo para desarrollo y presentación del proyecto."""
import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal, engine, Base
import app.models  # noqa: F401
from app.models.cliente import Cliente
from app.models.vehiculo import Vehiculo
from app.models.personal import Personal
from app.models.usuario import Usuario
from app.utils.security import hash_password


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Cliente).count() > 0:
            print("La base de datos ya tiene datos. Omitiendo seed.")
            return

        # Usuario admin
        if not db.query(Usuario).filter(Usuario.username == "admin").first():
            db.add(Usuario(
                username="admin",
                email="admin@taller.com",
                hashed_password=hash_password("admin123"),
                nombre_completo="Administrador",
                is_active=True,
                is_admin=True,
            ))

        # Personal del taller
        personal_data = [
            {"nombre": "Carlos", "apellido": "Ríos", "rol": "LATONERO", "telefono": "3001234567"},
            {"nombre": "Miguel", "apellido": "Torres", "rol": "PINTOR", "telefono": "3007654321"},
            {"nombre": "Laura", "apellido": "Gómez", "rol": "RECEPCIONISTA", "telefono": "3009876543"},
            {"nombre": "Pedro", "apellido": "Sánchez", "rol": "JEFE_TALLER", "telefono": "3005551234"},
        ]
        for p in personal_data:
            db.add(Personal(**p))

        # Clientes
        c1 = Cliente(
            nombre="Juan", apellido="Pérez", cedula_ruc="1234567890",
            telefono="3001112233", email="juan.perez@email.com",
        )
        c2 = Cliente(
            nombre="Ana", apellido="Martínez", cedula_ruc="0987654321",
            telefono="3004445566", email="ana.martinez@email.com",
        )
        c3 = Cliente(
            nombre="Roberto", apellido="Herrera", cedula_ruc="1122334455",
            telefono="3007778899",
        )
        db.add_all([c1, c2, c3])
        db.flush()

        # Vehículos
        v1 = Vehiculo(cliente_id=c1.id, placa="ABC123", marca="Toyota", modelo="Corolla", anio=2019, color="Blanco")
        v2 = Vehiculo(cliente_id=c2.id, placa="XYZ789", marca="Chevrolet", modelo="Spark", anio=2021, color="Rojo")
        v3 = Vehiculo(cliente_id=c3.id, placa="DEF456", marca="Renault", modelo="Sandero", anio=2018, color="Gris")
        db.add_all([v1, v2, v3])
        db.flush()

        db.commit()
        print(f"Datos de demo cargados:")
        print(f"  - 3 clientes")
        print(f"  - 3 vehículos")
        print(f"  - 4 empleados")
        print(f"  - Usuario admin (admin / admin123)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
