EMPLEADO = {"nombre": "Luis", "apellido": "Ríos", "rol": "LATONERO", "telefono": "3001112222"}


def test_personal_requiere_autenticacion(client):
    assert client.get("/api/v1/personal/").status_code == 401


def test_crear_personal(client, auth_headers):
    resp = client.post("/api/v1/personal/", json=EMPLEADO, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["rol"] == "LATONERO"
    assert data["activo"] is True


def test_listar_personal_activos_por_defecto(client, auth_headers):
    client.post("/api/v1/personal/", json=EMPLEADO, headers=auth_headers)
    resp = client.get("/api/v1/personal/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert all(p["activo"] for p in resp.json())


def test_obtener_personal(client, auth_headers):
    p = client.post("/api/v1/personal/", json=EMPLEADO, headers=auth_headers).json()
    resp = client.get(f"/api/v1/personal/{p['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == p["id"]


def test_obtener_personal_no_encontrado(client, auth_headers):
    assert client.get("/api/v1/personal/99999", headers=auth_headers).status_code == 404


def test_actualizar_personal(client, auth_headers):
    p = client.post("/api/v1/personal/", json=EMPLEADO, headers=auth_headers).json()
    resp = client.put(
        f"/api/v1/personal/{p['id']}",
        json={**EMPLEADO, "rol": "PINTOR"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["rol"] == "PINTOR"


def test_toggle_desactiva_y_reactiva(client, auth_headers):
    p = client.post("/api/v1/personal/", json=EMPLEADO, headers=auth_headers).json()
    # Desactivar
    resp = client.patch(f"/api/v1/personal/{p['id']}/activar", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["activo"] is False
    # Ya no aparece en el listado de activos por defecto
    activos = client.get("/api/v1/personal/", headers=auth_headers).json()
    assert all(item["id"] != p["id"] for item in activos)
    # Reactivar
    resp = client.patch(f"/api/v1/personal/{p['id']}/activar", headers=auth_headers)
    assert resp.json()["activo"] is True
