import pytest

CLIENTE = {"nombre": "Veh", "apellido": "Owner", "cedula_ruc": "5550001111", "telefono": "3001230000"}
VEHICULO = {"placa": "VEH100", "marca": "Mazda", "modelo": "3"}


@pytest.fixture
def cliente_id(client, auth_headers):
    c = client.post("/api/v1/clientes/", json=CLIENTE, headers=auth_headers).json()
    return c["id"]


def _crear(client, auth_headers, cliente_id, **extra):
    payload = {**VEHICULO, "cliente_id": cliente_id, **extra}
    return client.post("/api/v1/vehiculos/", json=payload, headers=auth_headers)


def test_vehiculo_requiere_autenticacion(client):
    assert client.get("/api/v1/vehiculos/").status_code == 401


def test_crear_vehiculo(client, auth_headers, cliente_id):
    resp = _crear(client, auth_headers, cliente_id)
    assert resp.status_code == 201
    data = resp.json()
    assert data["placa"] == "VEH100"
    assert data["activo"] is True


def test_crear_vehiculo_campos_opcionales(client, auth_headers, cliente_id):
    resp = _crear(
        client, auth_headers, cliente_id,
        placa="VEH101", anio=2020, color="Azul", vin="VIN123", kilometraje=45000,
    )
    assert resp.status_code == 201
    assert resp.json()["anio"] == 2020


def test_crear_vehiculo_placa_duplicada(client, auth_headers, cliente_id):
    _crear(client, auth_headers, cliente_id)
    resp = _crear(client, auth_headers, cliente_id)
    assert resp.status_code == 409


def test_listar_vehiculos(client, auth_headers, cliente_id):
    _crear(client, auth_headers, cliente_id)
    resp = client.get("/api/v1/vehiculos/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_listar_vehiculos_filtro_cliente(client, auth_headers, cliente_id):
    _crear(client, auth_headers, cliente_id)
    resp = client.get(f"/api/v1/vehiculos/?cliente_id={cliente_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert all(v["cliente_id"] == cliente_id for v in resp.json())


def test_obtener_vehiculo(client, auth_headers, cliente_id):
    v = _crear(client, auth_headers, cliente_id).json()
    resp = client.get(f"/api/v1/vehiculos/{v['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == v["id"]


def test_obtener_vehiculo_no_encontrado(client, auth_headers):
    assert client.get("/api/v1/vehiculos/99999", headers=auth_headers).status_code == 404


def test_actualizar_vehiculo(client, auth_headers, cliente_id):
    v = _crear(client, auth_headers, cliente_id).json()
    resp = client.put(
        f"/api/v1/vehiculos/{v['id']}",
        json={**VEHICULO, "cliente_id": cliente_id, "color": "Rojo"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["color"] == "Rojo"


def test_soft_delete_vehiculo(client, auth_headers, cliente_id):
    v = _crear(client, auth_headers, cliente_id).json()
    resp = client.delete(f"/api/v1/vehiculos/{v['id']}", headers=auth_headers)
    assert resp.status_code == 204
    # Tras el soft-delete no aparece en el listado por defecto (activo=True)...
    listado = client.get("/api/v1/vehiculos/", headers=auth_headers).json()
    assert all(item["id"] != v["id"] for item in listado)
    # ...pero sí con ?activo=false
    inactivos = client.get("/api/v1/vehiculos/?activo=false", headers=auth_headers).json()
    assert any(item["id"] == v["id"] for item in inactivos)


def test_soft_delete_vehiculo_no_encontrado(client, auth_headers):
    assert client.delete("/api/v1/vehiculos/99999", headers=auth_headers).status_code == 404
