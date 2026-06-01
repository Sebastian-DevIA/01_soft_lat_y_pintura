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


def test_actualizar_cliente(client, auth_headers):
    created = client.post("/api/v1/clientes/", json=CLIENTE_DATA, headers=auth_headers).json()
    cambios = {**CLIENTE_DATA, "telefono": "3009999999", "direccion": "Calle 1"}
    resp = client.put(
        f"/api/v1/clientes/{created['id']}", json=cambios, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["telefono"] == "3009999999"
    assert data["direccion"] == "Calle 1"


def test_actualizar_cliente_cedula_duplicada(client, auth_headers):
    # Dos clientes; intentar darle al segundo la cédula del primero → 409
    c1 = client.post("/api/v1/clientes/", json=CLIENTE_DATA, headers=auth_headers).json()
    otro = {**CLIENTE_DATA, "cedula_ruc": "9999999999"}
    c2 = client.post("/api/v1/clientes/", json=otro, headers=auth_headers).json()
    resp = client.put(
        f"/api/v1/clientes/{c2['id']}",
        json={**otro, "cedula_ruc": c1["cedula_ruc"]},
        headers=auth_headers,
    )
    assert resp.status_code == 409


def test_actualizar_cliente_misma_cedula_ok(client, auth_headers):
    # Actualizar otros campos sin cambiar la propia cédula NO debe dar 409
    created = client.post("/api/v1/clientes/", json=CLIENTE_DATA, headers=auth_headers).json()
    resp = client.put(
        f"/api/v1/clientes/{created['id']}",
        json={**CLIENTE_DATA, "nombre": "Juan Carlos"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["nombre"] == "Juan Carlos"


def test_toggle_reactivar_cliente(client, auth_headers):
    created = client.post("/api/v1/clientes/", json=CLIENTE_DATA, headers=auth_headers).json()
    client.delete(f"/api/v1/clientes/{created['id']}", headers=auth_headers)  # activo=False
    resp = client.patch(
        f"/api/v1/clientes/{created['id']}/activar", headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["activo"] is True
    # Vuelve a alternar → inactivo
    resp2 = client.patch(
        f"/api/v1/clientes/{created['id']}/activar", headers=auth_headers
    )
    assert resp2.json()["activo"] is False


def test_toggle_cliente_inexistente(client, auth_headers):
    resp = client.patch("/api/v1/clientes/9999/activar", headers=auth_headers)
    assert resp.status_code == 404


def test_toggle_afecta_listado_por_activo(client, auth_headers):
    """Tras soft-delete el cliente desaparece del listado default (activo=True)
    y aparece en activo=False; tras reactivar vuelve al default."""
    created = client.post("/api/v1/clientes/", json=CLIENTE_DATA, headers=auth_headers).json()

    # Recién creado: visible en listado activo=True, ausente en activo=False
    activos = client.get("/api/v1/clientes/?activo=true", headers=auth_headers).json()
    inactivos = client.get("/api/v1/clientes/?activo=false", headers=auth_headers).json()
    assert any(c["id"] == created["id"] for c in activos)
    assert not any(c["id"] == created["id"] for c in inactivos)

    # Soft-delete (activo=False)
    client.delete(f"/api/v1/clientes/{created['id']}", headers=auth_headers)
    activos2 = client.get("/api/v1/clientes/?activo=true", headers=auth_headers).json()
    inactivos2 = client.get("/api/v1/clientes/?activo=false", headers=auth_headers).json()
    assert not any(c["id"] == created["id"] for c in activos2)
    assert any(c["id"] == created["id"] for c in inactivos2)

    # Reactivar via toggle → vuelve al listado activo=True
    client.patch(f"/api/v1/clientes/{created['id']}/activar", headers=auth_headers)
    activos3 = client.get("/api/v1/clientes/?activo=true", headers=auth_headers).json()
    assert any(c["id"] == created["id"] for c in activos3)
