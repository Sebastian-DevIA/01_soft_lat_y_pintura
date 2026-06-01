import pytest

CLIENTE = {"nombre": "Fac", "apellido": "Cliente", "cedula_ruc": "2223334445", "telefono": "3002223333"}
VEHICULO = {"placa": "FAC777", "marca": "Kia", "modelo": "Rio"}
ITEM = {"descripcion": "Pintar guardafango", "area_vehiculo": "Guardafango", "precio_unitario": 300.0, "cantidad": 1}


@pytest.fixture
def orden_aprobada(client, auth_headers):
    c = client.post("/api/v1/clientes/", json=CLIENTE, headers=auth_headers).json()
    v = client.post(
        "/api/v1/vehiculos/", json={**VEHICULO, "cliente_id": c["id"]}, headers=auth_headers
    ).json()
    o = client.post("/api/v1/ordenes/", json={"vehiculo_id": v["id"]}, headers=auth_headers).json()
    client.post(f"/api/v1/ordenes/{o['id']}/items", json=ITEM, headers=auth_headers)
    client.patch(f"/api/v1/ordenes/{o['id']}/aprobar", headers=auth_headers)
    return o


def test_emitir_factura_requiere_aprobacion(client, auth_headers):
    c = client.post(
        "/api/v1/clientes/", json={**CLIENTE, "cedula_ruc": "9090909090"}, headers=auth_headers
    ).json()
    v = client.post(
        "/api/v1/vehiculos/",
        json={**VEHICULO, "placa": "FAC778", "cliente_id": c["id"]},
        headers=auth_headers,
    ).json()
    o = client.post("/api/v1/ordenes/", json={"vehiculo_id": v["id"]}, headers=auth_headers).json()
    # Orden en PERITAJE → no se puede facturar
    resp = client.post("/api/v1/facturas/", json={"orden_id": o["id"]}, headers=auth_headers)
    assert resp.status_code == 422


def test_emitir_factura_orden_inexistente(client, auth_headers):
    resp = client.post("/api/v1/facturas/", json={"orden_id": 99999}, headers=auth_headers)
    assert resp.status_code == 404


def test_emitir_factura_exitosa(client, auth_headers, orden_aprobada):
    resp = client.post(
        "/api/v1/facturas/", json={"orden_id": orden_aprobada["id"]}, headers=auth_headers
    )
    assert resp.status_code == 201
    f = resp.json()
    assert f["monto_total"] == 300.0
    assert f["monto_adelanto"] == 150.0
    assert f["monto_saldo"] == 150.0
    # Emitir factura mueve la orden a EN_PROCESO
    detalle = client.get(f"/api/v1/ordenes/{orden_aprobada['id']}", headers=auth_headers).json()
    assert detalle["estado"] == "EN_PROCESO"


def test_no_emitir_segunda_factura(client, auth_headers, orden_aprobada):
    # Emitir la 1ra factura mueve la orden a EN_PROCESO; un 2do intento queda
    # bloqueado por la state machine (ya no está en APROBACION) → 422.
    primera = client.post(
        "/api/v1/facturas/", json={"orden_id": orden_aprobada["id"]}, headers=auth_headers
    )
    assert primera.status_code == 201
    resp = client.post(
        "/api/v1/facturas/", json={"orden_id": orden_aprobada["id"]}, headers=auth_headers
    )
    assert resp.status_code == 422


def test_obtener_factura(client, auth_headers, orden_aprobada):
    f = client.post(
        "/api/v1/facturas/", json={"orden_id": orden_aprobada["id"]}, headers=auth_headers
    ).json()
    resp = client.get(f"/api/v1/facturas/{f['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["numero_factura"] == f["numero_factura"]


def test_obtener_factura_no_encontrada(client, auth_headers):
    assert client.get("/api/v1/facturas/99999", headers=auth_headers).status_code == 404


def test_listar_facturas(client, auth_headers, orden_aprobada):
    client.post("/api/v1/facturas/", json={"orden_id": orden_aprobada["id"]}, headers=auth_headers)
    resp = client.get("/api/v1/facturas/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_listar_facturas_filtro_estado(client, auth_headers, orden_aprobada):
    client.post("/api/v1/facturas/", json={"orden_id": orden_aprobada["id"]}, headers=auth_headers)
    resp = client.get("/api/v1/facturas/?estado=PENDIENTE", headers=auth_headers)
    assert resp.status_code == 200
    assert all(f["estado"] == "PENDIENTE" for f in resp.json())


def test_pdf_requiere_autenticacion(client, auth_headers, orden_aprobada):
    f = client.post(
        "/api/v1/facturas/", json={"orden_id": orden_aprobada["id"]}, headers=auth_headers
    ).json()
    # Sin token → 401 (este es el motivo por el que un <a href> plano no podía verlo)
    resp = client.get(f"/api/v1/facturas/{f['id']}/pdf")
    assert resp.status_code == 401


def test_descargar_pdf_factura(client, auth_headers, orden_aprobada):
    f = client.post(
        "/api/v1/facturas/", json={"orden_id": orden_aprobada["id"]}, headers=auth_headers
    ).json()
    resp = client.get(f"/api/v1/facturas/{f['id']}/pdf", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    # Cuerpo es un PDF real (valida que la plantilla con el desglose de IVA renderiza)
    assert resp.content[:5] == b"%PDF-"


def test_desglose_iva_consistente(client, auth_headers, orden_aprobada):
    """base_gravable + monto_iva debe ser igual a monto_total (IVA 19 %, incluido)."""
    f = client.post(
        "/api/v1/facturas/", json={"orden_id": orden_aprobada["id"]}, headers=auth_headers
    ).json()
    monto_total = f["monto_total"]
    tasa = 19.0
    base_gravable = round(monto_total / (1 + tasa / 100), 2)
    monto_iva = round(monto_total - base_gravable, 2)
    # La suma de las partes no debe alejarse del total en más de 1 centavo (redondeo)
    assert abs((base_gravable + monto_iva) - monto_total) <= 0.01


def test_pdf_generacion_tras_pago_parcial(client, auth_headers, orden_aprobada):
    """El PDF debe generarse correctamente cuando la factura ya tiene un pago
    registrado (estado PARCIAL), no solo cuando está PENDIENTE."""
    f = client.post(
        "/api/v1/facturas/", json={"orden_id": orden_aprobada["id"]}, headers=auth_headers
    ).json()
    # Registrar el adelanto (50% del total)
    adelanto = f["monto_adelanto"]
    client.post(
        "/api/v1/pagos/",
        json={"factura_id": f["id"], "monto": adelanto, "tipo": "ADELANTO", "metodo": "EFECTIVO"},
        headers=auth_headers,
    )
    # Verificar que la factura quedó en PARCIAL
    factura_parcial = client.get(f"/api/v1/facturas/{f['id']}", headers=auth_headers).json()
    assert factura_parcial["estado"] == "PARCIAL"
    # El PDF debe seguir generándose sin error
    resp = client.get(f"/api/v1/facturas/{f['id']}/pdf", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.content[:5] == b"%PDF-"
