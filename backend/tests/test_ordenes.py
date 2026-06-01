import pytest

CLIENTE = {"nombre": "Ana", "apellido": "Torres", "cedula_ruc": "9876543210", "telefono": "3009999999"}
VEHICULO_EXTRA = {"placa": "TEST01", "marca": "Toyota", "modelo": "Corolla"}
ITEM = {"descripcion": "Latonear puerta", "area_vehiculo": "Puerta delantera izq.", "precio_unitario": 150.0, "cantidad": 1}


@pytest.fixture
def orden_base(client, auth_headers):
    cliente = client.post("/api/v1/clientes/", json=CLIENTE, headers=auth_headers).json()
    vehiculo_data = {**VEHICULO_EXTRA, "cliente_id": cliente["id"]}
    vehiculo = client.post("/api/v1/vehiculos/", json=vehiculo_data, headers=auth_headers).json()
    orden = client.post("/api/v1/ordenes/", json={"vehiculo_id": vehiculo["id"]}, headers=auth_headers).json()
    return orden, vehiculo, cliente


def test_crear_orden(client, auth_headers, orden_base):
    orden, _, _ = orden_base
    assert orden["estado"] == "PERITAJE"
    assert orden["total_cotizado"] == 0.0


def test_agregar_item_cambia_estado_a_cotizacion(client, auth_headers, orden_base):
    orden, _, _ = orden_base
    resp = client.post(f"/api/v1/ordenes/{orden['id']}/items", json=ITEM, headers=auth_headers)
    assert resp.status_code == 201
    detalle = client.get(f"/api/v1/ordenes/{orden['id']}", headers=auth_headers).json()
    assert detalle["estado"] == "COTIZACION"
    assert detalle["total_cotizado"] == 150.0


def test_aplicar_descuento(client, auth_headers, orden_base):
    orden, _, _ = orden_base
    client.post(f"/api/v1/ordenes/{orden['id']}/items", json=ITEM, headers=auth_headers)
    resp = client.patch(f"/api/v1/ordenes/{orden['id']}/descuento", json={"descuento_porcentaje": 10}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total_con_descuento"] == 135.0


def test_aprobar_orden(client, auth_headers, orden_base):
    orden, _, _ = orden_base
    client.post(f"/api/v1/ordenes/{orden['id']}/items", json=ITEM, headers=auth_headers)
    resp = client.patch(f"/api/v1/ordenes/{orden['id']}/aprobar", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["estado"] == "APROBACION"
    assert resp.json()["aprobado_por_cliente"] is True


def test_no_aprobar_sin_items(client, auth_headers, orden_base):
    orden, _, _ = orden_base
    resp = client.patch(f"/api/v1/ordenes/{orden['id']}/aprobar", headers=auth_headers)
    assert resp.status_code == 422


def test_transicion_invalida(client, auth_headers, orden_base):
    orden, _, _ = orden_base
    resp = client.patch(f"/api/v1/ordenes/{orden['id']}/estado", json={"estado": "ENTREGADO"}, headers=auth_headers)
    assert resp.status_code == 422


def test_eliminar_item(client, auth_headers, orden_base):
    orden, _, _ = orden_base
    item = client.post(f"/api/v1/ordenes/{orden['id']}/items", json=ITEM, headers=auth_headers).json()
    resp = client.delete(f"/api/v1/ordenes/{orden['id']}/items/{item['id']}", headers=auth_headers)
    assert resp.status_code == 204
    detalle = client.get(f"/api/v1/ordenes/{orden['id']}", headers=auth_headers).json()
    assert detalle["total_cotizado"] == 0.0


def test_cambiar_estado_cancelar(client, auth_headers, orden_base):
    orden, _, _ = orden_base
    resp = client.patch(
        f"/api/v1/ordenes/{orden['id']}/estado",
        json={"estado": "CANCELADO"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["estado"] == "CANCELADO"


def test_descuento_invalido(client, auth_headers, orden_base):
    orden, _, _ = orden_base
    resp = client.patch(
        f"/api/v1/ordenes/{orden['id']}/descuento",
        json={"descuento_porcentaje": 150},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_orden_response_enriquecida(client, auth_headers, orden_base):
    orden, vehiculo, cliente = orden_base
    esperado_cliente = f"{cliente['nombre']} {cliente['apellido']}"
    # POST /ordenes ya trae los campos planos (bug de enriquecimiento corregido)
    assert orden["vehiculo_placa"] == vehiculo["placa"]
    assert orden["cliente_nombre"] == esperado_cliente
    # GET detalle también
    detalle = client.get(f"/api/v1/ordenes/{orden['id']}", headers=auth_headers).json()
    assert detalle["vehiculo_placa"] == vehiculo["placa"]
    assert detalle["cliente_nombre"] == esperado_cliente


def test_asignacion_personal_nombre_en_fases(client, auth_headers, orden_base):
    orden, _, _ = orden_base
    client.post(f"/api/v1/ordenes/{orden['id']}/items", json=ITEM, headers=auth_headers)
    client.patch(f"/api/v1/ordenes/{orden['id']}/aprobar", headers=auth_headers)
    empleado = client.post(
        "/api/v1/personal/",
        json={"nombre": "Carlos", "apellido": "Méndez", "rol": "PINTOR"},
        headers=auth_headers,
    ).json()
    fases = client.get(f"/api/v1/fases/orden/{orden['id']}", headers=auth_headers).json()
    fase_id = fases[0]["id"]
    resp = client.post(
        f"/api/v1/fases/{fase_id}/personal",
        json={"personal_id": empleado["id"]},
        headers=auth_headers,
    )
    assert resp.status_code in (200, 201)
    fases2 = client.get(f"/api/v1/fases/orden/{orden['id']}", headers=auth_headers).json()
    fase = next(f for f in fases2 if f["id"] == fase_id)
    assert fase["asignaciones"][0]["personal_nombre"] == "Carlos Méndez"
