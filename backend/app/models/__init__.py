# Importar todos los modelos para que Alembic los detecte en autogenerate
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.models.vehiculo import Vehiculo
from app.models.orden_trabajo import OrdenTrabajo
from app.models.item_cotizacion import ItemCotizacion
from app.models.factura import Factura
from app.models.pago import Pago
from app.models.fase_trabajo import FaseTrabajo
from app.models.personal import Personal
from app.models.asignacion import Asignacion

__all__ = [
    "Usuario",
    "Cliente",
    "Vehiculo",
    "OrdenTrabajo",
    "ItemCotizacion",
    "Factura",
    "Pago",
    "FaseTrabajo",
    "Personal",
    "Asignacion",
]
