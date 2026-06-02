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


def _llevar_a_en_proceso(client, auth_headers, orden_id):
    """Avanza la orden por la state machine: PERITAJE → ... → EN_PROCESO."""
    client.post(f"/api/v1/ordenes/{orden_id}/items", json=ITEM, headers=auth_headers)
    client.patch(f"/api/v1/ordenes/{orden_id}/aprobar", headers=auth_headers)
    client.patch(
        f"/api/v1/ordenes/{orden_id}/estado",
        json={"estado": "EN_PROCESO"},
        headers=auth_headers,
    )


def test_actualizar_orden_observaciones_y_fecha(client, auth_headers, orden_base):
    orden, _, _ = orden_base
    payload = {
        "observaciones": "Cliente prefiere recoger por la tarde",
        "fecha_estimada_entrega": "2026-07-15T17:00:00",
    }
    resp = client.put(f"/api/v1/ordenes/{orden['id']}", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["observaciones"] == "Cliente prefiere recoger por la tarde"
    assert body["fecha_estimada_entrega"].startswith("2026-07-15T17:00:00")
    # los campos planos siguen poblándose tras pasar por el helper de response
    assert body["vehiculo_placa"] is not None


def test_actualizar_orden_cancelada_da_409(client, auth_headers, orden_base):
    orden, _, _ = orden_base
    client.patch(
        f"/api/v1/ordenes/{orden['id']}/estado",
        json={"estado": "CANCELADO"},
        headers=auth_headers,
    )
    resp = client.put(
        f"/api/v1/ordenes/{orden['id']}",
        json={"observaciones": "no debería entrar"},
        headers=auth_headers,
    )
    assert resp.status_code == 409


def test_actualizar_orden_entregada_da_409(client, auth_headers, orden_base):
    orden, _, _ = orden_base
    _llevar_a_en_proceso(client, auth_headers, orden["id"])
    client.patch(
        f"/api/v1/ordenes/{orden['id']}/estado",
        json={"estado": "ENTREGADO"},
        headers=auth_headers,
    )
    resp = client.put(
        f"/api/v1/ordenes/{orden['id']}",
        json={"observaciones": "no debería entrar"},
        headers=auth_headers,
    )
    assert resp.status_code == 409


def test_reasignar_vehiculo_en_peritaje(client, auth_headers, orden_base):
    orden, _, cliente = orden_base
    otro = client.post(
        "/api/v1/vehiculos/",
        json={"placa": "TEST02", "marca": "Mazda", "modelo": "3", "cliente_id": cliente["id"]},
        headers=auth_headers,
    ).json()
    resp = client.put(
        f"/api/v1/ordenes/{orden['id']}",
        json={"vehiculo_id": otro["id"]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["vehiculo_id"] == otro["id"]
    assert body["vehiculo_placa"] == "TEST02"


def test_reasignar_vehiculo_en_estado_posterior_da_409(client, auth_headers, orden_base):
    orden, _, cliente = orden_base
    otro = client.post(
        "/api/v1/vehiculos/",
        json={"placa": "TEST03", "marca": "Kia", "modelo": "Rio", "cliente_id": cliente["id"]},
        headers=auth_headers,
    ).json()
    _llevar_a_en_proceso(client, auth_headers, orden["id"])
    resp = client.put(
        f"/api/v1/ordenes/{orden['id']}",
        json={"vehiculo_id": otro["id"]},
        headers=auth_headers,
    )
    assert resp.status_code == 409


def test_reasignar_vehiculo_inexistente_da_404(client, auth_headers, orden_base):
    orden, _, _ = orden_base
    resp = client.put(
        f"/api/v1/ordenes/{orden['id']}",
        json={"vehiculo_id": 999999},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_eliminar_orden_soft_delete(client, auth_headers, orden_base):
    orden, _, _ = orden_base
    resp = client.delete(f"/api/v1/ordenes/{orden['id']}", headers=auth_headers)
    assert resp.status_code == 204
    # por defecto (activo=True) ya no aparece en el listado
    activas = client.get("/api/v1/ordenes/", headers=auth_headers).json()
    assert all(o["id"] != orden["id"] for o in activas)
    # con ?activo=false sí aparece
    inactivas = client.get("/api/v1/ordenes/?activo=false", headers=auth_headers).json()
    assert any(o["id"] == orden["id"] for o in inactivas)


def test_activar_orden_tras_soft_delete(client, auth_headers, orden_base):
    orden, _, _ = orden_base
    client.delete(f"/api/v1/ordenes/{orden['id']}", headers=auth_headers)
    resp = client.patch(f"/api/v1/ordenes/{orden['id']}/activar", headers=auth_headers)
    assert resp.status_code == 200
    # vuelve a estar activa: aparece en el listado por defecto
    activas = client.get("/api/v1/ordenes/", headers=auth_headers).json()
    assert any(o["id"] == orden["id"] for o in activas)


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


# ── Edge cases añadidos ────────────────────────────────────────────────────────


def test_put_body_vacio_no_cambia_nada(client, auth_headers, orden_base):
    """PUT con body vacío {} no cambia nada y devuelve 200."""
    orden, vehiculo, cliente = orden_base
    resp = client.put(f"/api/v1/ordenes/{orden['id']}", json={}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    # Los valores no cambiaron
    assert body["observaciones"] is None
    assert body["vehiculo_id"] == orden["vehiculo_id"]
    # Los campos planos siguen poblados
    assert body["vehiculo_placa"] == vehiculo["placa"]
    assert body["cliente_nombre"] == f"{cliente['nombre']} {cliente['apellido']}"


def test_put_observaciones_null_limpia_campo(client, auth_headers, orden_base):
    """PUT con observaciones: null limpia el campo (lo pone en None)."""
    orden, _, _ = orden_base
    # Primero ponemos un valor
    client.put(
        f"/api/v1/ordenes/{orden['id']}",
        json={"observaciones": "texto inicial"},
        headers=auth_headers,
    )
    # Ahora lo borramos enviando null explícitamente
    resp = client.put(
        f"/api/v1/ordenes/{orden['id']}",
        json={"observaciones": None},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["observaciones"] is None


def test_put_orden_inexistente_da_404(client, auth_headers):
    """PUT en una orden que no existe devuelve 404."""
    resp = client.put(
        "/api/v1/ordenes/999999",
        json={"observaciones": "x"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_activar_orden_inexistente_da_404(client, auth_headers):
    """PATCH /activar en orden inexistente devuelve 404."""
    resp = client.patch("/api/v1/ordenes/999999/activar", headers=auth_headers)
    assert resp.status_code == 404


def test_activar_alterna_ida_y_vuelta(client, auth_headers, orden_base):
    """PATCH /activar alterna activo: True→False→True."""
    orden, _, _ = orden_base
    # Primera llamada: desactiva (True → False)
    r1 = client.patch(f"/api/v1/ordenes/{orden['id']}/activar", headers=auth_headers)
    assert r1.status_code == 200
    inactivas = client.get("/api/v1/ordenes/?activo=false", headers=auth_headers).json()
    assert any(o["id"] == orden["id"] for o in inactivas)

    # Segunda llamada: reactiva (False → True)
    r2 = client.patch(f"/api/v1/ordenes/{orden['id']}/activar", headers=auth_headers)
    assert r2.status_code == 200
    activas = client.get("/api/v1/ordenes/", headers=auth_headers).json()
    assert any(o["id"] == orden["id"] for o in activas)


def test_delete_orden_inexistente_da_404(client, auth_headers):
    """DELETE en orden inexistente devuelve 404."""
    resp = client.delete("/api/v1/ordenes/999999", headers=auth_headers)
    assert resp.status_code == 404


def test_filtro_combinado_estado_y_activo(client, auth_headers, orden_base):
    """GET con ?estado=PERITAJE&activo=true devuelve solo las órdenes que coinciden."""
    orden, _, _ = orden_base
    # La orden_base está en PERITAJE y activo=True
    resp = client.get(
        "/api/v1/ordenes/?estado=PERITAJE&activo=true", headers=auth_headers
    )
    assert resp.status_code == 200
    ids = [o["id"] for o in resp.json()]
    assert orden["id"] in ids
    # Todos los resultados deben tener estado PERITAJE
    assert all(o["estado"] == "PERITAJE" for o in resp.json())

    # Con otro estado no debe aparecer
    resp2 = client.get(
        "/api/v1/ordenes/?estado=CANCELADO&activo=true", headers=auth_headers
    )
    assert resp2.status_code == 200
    ids2 = [o["id"] for o in resp2.json()]
    assert orden["id"] not in ids2


def test_delete_soft_no_elimina_fases_ni_factura(client, auth_headers, orden_base):
    """Soft-delete NO borra en cascada facturas ni fases (solo marca activo=False)."""
    orden, _, _ = orden_base
    # Llegar a APROBACION para que se creen fases
    client.post(f"/api/v1/ordenes/{orden['id']}/items", json=ITEM, headers=auth_headers)
    client.patch(f"/api/v1/ordenes/{orden['id']}/aprobar", headers=auth_headers)
    # Emitir factura (avanza la orden a EN_PROCESO)
    factura = client.post(
        "/api/v1/facturas/",
        json={"orden_id": orden["id"]},
        headers=auth_headers,
    ).json()
    # Soft-delete la orden
    resp_del = client.delete(
        f"/api/v1/ordenes/{orden['id']}", headers=auth_headers
    )
    assert resp_del.status_code == 204

    # La factura sigue accesible
    resp_fac = client.get(
        f"/api/v1/facturas/{factura['id']}", headers=auth_headers
    )
    assert resp_fac.status_code == 200
    assert resp_fac.json()["id"] == factura["id"]

    # Las fases de la orden siguen accesibles
    resp_fases = client.get(
        f"/api/v1/fases/orden/{orden['id']}", headers=auth_headers
    )
    assert resp_fases.status_code == 200
    assert len(resp_fases.json()) == 3  # INGRESO, REPARACION, ENTREGA


def test_aprobar_orden_en_estado_aprobacion_da_422(client, auth_headers, orden_base):
    """Aprobar una orden ya en APROBACION (no en COTIZACION) devuelve 422."""
    orden, _, _ = orden_base
    client.post(f"/api/v1/ordenes/{orden['id']}/items", json=ITEM, headers=auth_headers)
    client.patch(f"/api/v1/ordenes/{orden['id']}/aprobar", headers=auth_headers)
    # Intentar aprobar de nuevo (ya está en APROBACION)
    resp = client.patch(
        f"/api/v1/ordenes/{orden['id']}/aprobar", headers=auth_headers
    )
    assert resp.status_code == 422


def test_descuento_en_estado_aprobacion_da_422(client, auth_headers, orden_base):
    """Aplicar descuento cuando la orden está en APROBACION devuelve 422."""
    orden, _, _ = orden_base
    client.post(f"/api/v1/ordenes/{orden['id']}/items", json=ITEM, headers=auth_headers)
    client.patch(f"/api/v1/ordenes/{orden['id']}/aprobar", headers=auth_headers)
    resp = client.patch(
        f"/api/v1/ordenes/{orden['id']}/descuento",
        json={"descuento_porcentaje": 5},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_agregar_item_en_estado_aprobacion_da_422(client, auth_headers, orden_base):
    """Agregar ítem cuando la orden está en APROBACION devuelve 422."""
    orden, _, _ = orden_base
    client.post(f"/api/v1/ordenes/{orden['id']}/items", json=ITEM, headers=auth_headers)
    client.patch(f"/api/v1/ordenes/{orden['id']}/aprobar", headers=auth_headers)
    resp = client.post(
        f"/api/v1/ordenes/{orden['id']}/items",
        json=ITEM,
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_actualizar_item_exitoso(client, auth_headers, orden_base):
    """PUT /ordenes/{id}/items/{item_id} actualiza descripcion y precio correctamente."""
    orden, _, _ = orden_base
    item = client.post(
        f"/api/v1/ordenes/{orden['id']}/items", json=ITEM, headers=auth_headers
    ).json()
    nuevo = {
        "descripcion": "Latonear capó",
        "area_vehiculo": "Capó",
        "precio_unitario": 200.0,
        "cantidad": 2,
    }
    resp = client.put(
        f"/api/v1/ordenes/{orden['id']}/items/{item['id']}",
        json=nuevo,
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["descripcion"] == "Latonear capó"
    assert body["precio_unitario"] == 200.0
    assert body["cantidad"] == 2
    assert body["subtotal"] == 400.0

    # El total de la orden también se recalcula
    detalle = client.get(f"/api/v1/ordenes/{orden['id']}", headers=auth_headers).json()
    assert detalle["total_cotizado"] == 400.0


def test_actualizar_item_inexistente_da_404(client, auth_headers, orden_base):
    """PUT /ordenes/{id}/items/{item_id} con ítem que no existe devuelve 404."""
    orden, _, _ = orden_base
    resp = client.put(
        f"/api/v1/ordenes/{orden['id']}/items/999999",
        json=ITEM,
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_eliminar_item_inexistente_da_404(client, auth_headers, orden_base):
    """DELETE /ordenes/{id}/items/{item_id} con ítem inexistente devuelve 404."""
    orden, _, _ = orden_base
    resp = client.delete(
        f"/api/v1/ordenes/{orden['id']}/items/999999", headers=auth_headers
    )
    assert resp.status_code == 404


def test_reasignar_vehiculo_en_cotizacion(client, auth_headers, orden_base):
    """Reasignar vehículo en estado COTIZACION también está permitido (409 solo >COTIZACION)."""
    orden, _, cliente = orden_base
    # Avanzar a COTIZACION agregando un ítem
    client.post(f"/api/v1/ordenes/{orden['id']}/items", json=ITEM, headers=auth_headers)
    detalle = client.get(f"/api/v1/ordenes/{orden['id']}", headers=auth_headers).json()
    assert detalle["estado"] == "COTIZACION"

    otro = client.post(
        "/api/v1/vehiculos/",
        json={"placa": "TEST04", "marca": "Honda", "modelo": "Civic", "cliente_id": cliente["id"]},
        headers=auth_headers,
    ).json()
    resp = client.put(
        f"/api/v1/ordenes/{orden['id']}",
        json={"vehiculo_id": otro["id"]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["vehiculo_id"] == otro["id"]
    assert resp.json()["vehiculo_placa"] == "TEST04"


def test_aprobar_con_total_cero_en_cotizacion_da_422(client, auth_headers, orden_base):
    """Aprobar cuando el total_con_descuento es 0 (ítem con precio 0 no es posible por validación,
    pero si se aplica descuento 100% el total queda en 0) devuelve 422."""
    orden, _, _ = orden_base
    # Agregar ítem y aplicar descuento del 100%
    client.post(f"/api/v1/ordenes/{orden['id']}/items", json=ITEM, headers=auth_headers)
    client.patch(
        f"/api/v1/ordenes/{orden['id']}/descuento",
        json={"descuento_porcentaje": 100},
        headers=auth_headers,
    )
    detalle = client.get(f"/api/v1/ordenes/{orden['id']}", headers=auth_headers).json()
    assert detalle["estado"] == "COTIZACION"
    assert detalle["total_con_descuento"] == 0.0

    resp = client.patch(
        f"/api/v1/ordenes/{orden['id']}/aprobar", headers=auth_headers
    )
    assert resp.status_code == 422


def test_put_campos_planos_poblados_tras_edicion(client, auth_headers, orden_base):
    """Los campos vehiculo_placa y cliente_nombre vienen poblados en la respuesta de PUT."""
    orden, vehiculo, cliente = orden_base
    resp = client.put(
        f"/api/v1/ordenes/{orden['id']}",
        json={"observaciones": "revisar pintura"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["vehiculo_placa"] == vehiculo["placa"]
    assert body["vehiculo_descripcion"] is not None
    assert body["cliente_nombre"] == f"{cliente['nombre']} {cliente['apellido']}"
