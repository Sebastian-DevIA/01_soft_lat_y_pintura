CLIENTE_DATA = {
    "nombre": "Juan",
    "apellido": "Pérez",
    "cedula_ruc": "1234567890",
    "telefono": "3001234567",
    "email": "juan@test.com",
}


def test_crear_cliente(client, auth_headers):
    resp = client.post("/api/v1/clientes/", json=CLIENTE_DATA, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["cedula_ruc"] == "1234567890"
    assert data["activo"] is True


def test_crear_cliente_duplicado(client, auth_headers):
    client.post("/api/v1/clientes/", json=CLIENTE_DATA, headers=auth_headers)
    resp = client.post("/api/v1/clientes/", json=CLIENTE_DATA, headers=auth_headers)
    assert resp.status_code == 409


def test_listar_clientes(client, auth_headers):
    client.post("/api/v1/clientes/", json=CLIENTE_DATA, headers=auth_headers)
    resp = client.get("/api/v1/clientes/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_obtener_cliente(client, auth_headers):
    created = client.post("/api/v1/clientes/", json=CLIENTE_DATA, headers=auth_headers).json()
    resp = client.get(f"/api/v1/clientes/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_cliente_no_encontrado(client, auth_headers):
    resp = client.get("/api/v1/clientes/9999", headers=auth_headers)
    assert resp.status_code == 404


def test_desactivar_cliente(client, auth_headers):
    created = client.post("/api/v1/clientes/", json=CLIENTE_DATA, headers=auth_headers).json()
    resp = client.delete(f"/api/v1/clientes/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204
