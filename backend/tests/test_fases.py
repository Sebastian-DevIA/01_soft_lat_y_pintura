import pytest

CLIENTE = {"nombre": "Fase", "apellido": "Test", "cedula_ruc": "2222222222", "telefono": "3002222222"}
VEHICULO = {"placa": "FAS001", "marca": "Kia", "modelo": "Picanto"}
ITEM = {"descripcion": "Pintar capó", "area_vehiculo": "Capó", "precio_unitario": 300.0, "cantidad": 1}


@pytest.fixture
def orden_en_proceso(client, auth_headers):
    c = client.post("/api/v1/clientes/", json=CLIENTE, headers=auth_headers).json()
    v = client.post("/api/v1/vehiculos/", json={**VEHICULO, "cliente_id": c["id"]}, headers=auth_headers).json()
    o = client.post("/api/v1/ordenes/", json={"vehiculo_id": v["id"]}, headers=auth_headers).json()
    client.post(f"/api/v1/ordenes/{o['id']}/items", json=ITEM, headers=auth_headers)
    client.patch(f"/api/v1/ordenes/{o['id']}/aprobar", headers=auth_headers)
    client.post("/api/v1/facturas/", json={"orden_id": o["id"]}, headers=auth_headers)
    return o


def test_fases_se_crean_al_aprobar(client, auth_headers, orden_en_proceso):
    orden = orden_en_proceso
    resp = client.get(f"/api/v1/fases/orden/{orden['id']}", headers=auth_headers)
    assert resp.status_code == 200
    fases = resp.json()
    assert len(fases) == 3
    nombres = [f["fase"] for f in fases]
    assert "INGRESO" in nombres
    assert "REPARACION" in nombres
    assert "ENTREGA" in nombres
    for f in fases:
        assert f["estado"] == "PENDIENTE"


def test_avanzar_fase_a_en_progreso(client, auth_headers, orden_en_proceso):
    orden = orden_en_proceso
    fases = client.get(f"/api/v1/fases/orden/{orden['id']}", headers=auth_headers).json()
    ingreso = next(f for f in fases if f["fase"] == "INGRESO")
    resp = client.patch(f"/api/v1/fases/{ingreso['id']}/estado", json={"estado": "EN_PROGRESO"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["estado"] == "EN_PROGRESO"
    assert resp.json()["fecha_inicio"] is not None


def test_no_entregar_sin_pago_completo(client, auth_headers, orden_en_proceso):
    orden = orden_en_proceso
    fases = client.get(f"/api/v1/fases/orden/{orden['id']}", headers=auth_headers).json()
    entrega = next(f for f in fases if f["fase"] == "ENTREGA")
    resp = client.patch(f"/api/v1/fases/{entrega['id']}/estado", json={"estado": "COMPLETADA"}, headers=auth_headers)
    assert resp.status_code == 422


def test_asignar_personal_a_fase(client, auth_headers, orden_en_proceso):
    orden = orden_en_proceso
    personal = client.post(
        "/api/v1/personal/",
        json={"nombre": "Luis", "apellido": "Ríos", "rol": "LATONERO", "telefono": "3000000001"},
        headers=auth_headers,
    ).json()
    fases = client.get(f"/api/v1/fases/orden/{orden['id']}", headers=auth_headers).json()
    ingreso = next(f for f in fases if f["fase"] == "INGRESO")
    resp = client.post(
        f"/api/v1/fases/{ingreso['id']}/personal",
        json={"personal_id": personal["id"]},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["personal_id"] == personal["id"]


def test_no_asignar_personal_duplicado(client, auth_headers, orden_en_proceso):
    orden = orden_en_proceso
    personal = client.post(
        "/api/v1/personal/",
        json={"nombre": "Pedro", "apellido": "Vega", "rol": "PINTOR", "telefono": "3000000002"},
        headers=auth_headers,
    ).json()
    fases = client.get(f"/api/v1/fases/orden/{orden['id']}", headers=auth_headers).json()
    ingreso = next(f for f in fases if f["fase"] == "INGRESO")
    client.post(f"/api/v1/fases/{ingreso['id']}/personal", json={"personal_id": personal["id"]}, headers=auth_headers)
    resp = client.post(f"/api/v1/fases/{ingreso['id']}/personal", json={"personal_id": personal["id"]}, headers=auth_headers)
    assert resp.status_code == 409
