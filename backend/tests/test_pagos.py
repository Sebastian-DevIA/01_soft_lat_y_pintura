import pytest

CLIENTE = {"nombre": "Test", "apellido": "Pago", "cedula_ruc": "1111111111", "telefono": "3001111111"}
VEHICULO = {"placa": "PAG001", "marca": "Ford", "modelo": "Fiesta"}
ITEM = {"descripcion": "Reparar capó", "area_vehiculo": "Capó", "precio_unitario": 200.0, "cantidad": 1}


@pytest.fixture
def factura_pendiente(client, auth_headers):
    c = client.post("/api/v1/clientes/", json=CLIENTE, headers=auth_headers).json()
    v = client.post("/api/v1/vehiculos/", json={**VEHICULO, "cliente_id": c["id"]}, headers=auth_headers).json()
    o = client.post("/api/v1/ordenes/", json={"vehiculo_id": v["id"]}, headers=auth_headers).json()
    client.post(f"/api/v1/ordenes/{o['id']}/items", json=ITEM, headers=auth_headers)
    client.patch(f"/api/v1/ordenes/{o['id']}/aprobar", headers=auth_headers)
    f = client.post("/api/v1/facturas/", json={"orden_id": o["id"]}, headers=auth_headers).json()
    return f


def test_emitir_factura_crea_50_50(client, auth_headers, factura_pendiente):
    f = factura_pendiente
    assert f["monto_total"] == 200.0
    assert f["monto_adelanto"] == 100.0
    assert f["monto_saldo"] == 100.0
    assert f["estado"] == "PENDIENTE"


def test_registrar_adelanto(client, auth_headers, factura_pendiente):
    f = factura_pendiente
    pago = {"factura_id": f["id"], "monto": 100.0, "tipo": "ADELANTO", "metodo": "EFECTIVO"}
    resp = client.post("/api/v1/pagos/", json=pago, headers=auth_headers)
    assert resp.status_code == 201
    factura_actualizada = client.get(f"/api/v1/facturas/{f['id']}", headers=auth_headers).json()
    assert factura_actualizada["estado"] == "PARCIAL"
    assert factura_actualizada["monto_pagado"] == 100.0


def test_registrar_saldo_completa_factura(client, auth_headers, factura_pendiente):
    f = factura_pendiente
    client.post("/api/v1/pagos/", json={"factura_id": f["id"], "monto": 100.0, "tipo": "ADELANTO", "metodo": "EFECTIVO"}, headers=auth_headers)
    resp = client.post("/api/v1/pagos/", json={"factura_id": f["id"], "monto": 100.0, "tipo": "SALDO", "metodo": "TRANSFERENCIA"}, headers=auth_headers)
    assert resp.status_code == 201
    factura_actualizada = client.get(f"/api/v1/facturas/{f['id']}", headers=auth_headers).json()
    assert factura_actualizada["estado"] == "PAGADA"


def test_pago_excede_saldo(client, auth_headers, factura_pendiente):
    f = factura_pendiente
    resp = client.post("/api/v1/pagos/", json={"factura_id": f["id"], "monto": 9999.0, "tipo": "ADELANTO", "metodo": "EFECTIVO"}, headers=auth_headers)
    assert resp.status_code == 422


def test_no_pagar_factura_ya_pagada(client, auth_headers, factura_pendiente):
    f = factura_pendiente
    client.post("/api/v1/pagos/", json={"factura_id": f["id"], "monto": 200.0, "tipo": "ADELANTO", "metodo": "EFECTIVO"}, headers=auth_headers)
    resp = client.post("/api/v1/pagos/", json={"factura_id": f["id"], "monto": 1.0, "tipo": "ABONO", "metodo": "EFECTIVO"}, headers=auth_headers)
    assert resp.status_code == 422
