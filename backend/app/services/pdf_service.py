import os
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates"
)

_jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


def generar_pdf_factura(factura) -> bytes:
    template = _jinja_env.get_template("factura_pdf.html")
    orden = factura.orden
    cliente = orden.vehiculo.cliente if orden and orden.vehiculo else None

    html_str = template.render(
        factura=factura,
        orden=orden,
        cliente=cliente,
        vehiculo=orden.vehiculo if orden else None,
        items=orden.items if orden else [],
        pagos=factura.pagos,
    )
    return HTML(string=html_str).write_pdf()
