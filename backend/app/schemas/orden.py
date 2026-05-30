from datetime import datetime
from pydantic import BaseModel, field_validator
from app.schemas.factura import FacturaResponse


class OrdenCreateRequest(BaseModel):
    vehiculo_id: int
    observaciones: str | None = None
    fecha_estimada_entrega: datetime | None = None


class OrdenEstadoRequest(BaseModel):
    estado: str

    @field_validator("estado")
    @classmethod
    def estado_valido(cls, v: str) -> str:
        validos = ("PERITAJE", "COTIZACION", "APROBACION", "EN_PROCESO", "ENTREGADO", "CANCELADO")
        if v not in validos:
            raise ValueError(f"Estado debe ser uno de: {validos}")
        return v


class OrdenDescuentoRequest(BaseModel):
    descuento_porcentaje: float

    @field_validator("descuento_porcentaje")
    @classmethod
    def descuento_valido(cls, v: float) -> float:
        if not (0 <= v <= 100):
            raise ValueError("El descuento debe estar entre 0 y 100")
        return v


class ItemCotizacionRequest(BaseModel):
    descripcion: str
    area_vehiculo: str
    precio_unitario: float
    cantidad: int = 1
    notas: str | None = None

    @field_validator("precio_unitario")
    @classmethod
    def precio_positivo(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("El precio debe ser mayor a 0")
        return v

    @field_validator("cantidad")
    @classmethod
    def cantidad_positiva(cls, v: int) -> int:
        if v < 1:
            raise ValueError("La cantidad debe ser al menos 1")
        return v


class ItemCotizacionResponse(BaseModel):
    id: int
    orden_id: int
    descripcion: str
    area_vehiculo: str
    precio_unitario: float
    cantidad: int
    subtotal: float
    notas: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class OrdenResumenResponse(BaseModel):
    id: int
    vehiculo_id: int
    estado: str
    total_cotizado: float
    total_con_descuento: float
    descuento_porcentaje: float
    aprobado_por_cliente: bool
    fecha_ingreso: datetime
    fecha_estimada_entrega: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class OrdenDetalleResponse(BaseModel):
    id: int
    vehiculo_id: int
    estado: str
    observaciones: str | None
    descuento_porcentaje: float
    total_cotizado: float
    total_con_descuento: float
    aprobado_por_cliente: bool
    fecha_aprobacion: datetime | None
    fecha_ingreso: datetime
    fecha_estimada_entrega: datetime | None
    fecha_entrega_real: datetime | None
    items: list[ItemCotizacionResponse]
    factura: FacturaResponse | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
