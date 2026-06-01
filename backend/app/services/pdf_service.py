import os
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.config import settings

TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates"
)

_jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


def generar_pdf_factura(factura) -> bytes:
    template = _jinja_env.get_template("factura_pdf.html")
    orden = factura.orden
    cliente = orden.vehiculo.cliente if orden and orden.vehiculo else None

    # Desglose de IVA (display-only): se asume que monto_total YA incluye IVA, así que
    # se descompone hacia atrás. No altera la lógica financiera ni el adelanto del 50%.
    tasa = settings.iva_porcentaje
    base_gravable = round(factura.monto_total / (1 + tasa / 100), 2)
    monto_iva = round(factura.monto_total - base_gravable, 2)

    html_str = template.render(
        factura=factura,
        orden=orden,
        cliente=cliente,
        vehiculo=orden.vehiculo if orden else None,
        items=orden.items if orden else [],
        pagos=factura.pagos,
        iva_tasa=tasa,
        base_gravable=base_gravable,
        monto_iva=monto_iva,
    )
    return HTML(string=html_str).write_pdf()
