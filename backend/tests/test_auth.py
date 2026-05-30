def test_login_exitoso(client, admin_user):
    resp = client.post("/api/v1/auth/login", data={"username": "admin", "password": "testpass"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_password_incorrecta(client, admin_user):
    resp = client.post("/api/v1/auth/login", data={"username": "admin", "password": "mala"})
    assert resp.status_code == 401


def test_login_usuario_inexistente(client):
    resp = client.post("/api/v1/auth/login", data={"username": "noexiste", "password": "abc"})
    assert resp.status_code == 401


def test_me_con_token(client, auth_headers):
    resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "admin"


def test_me_sin_token(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_ruta_protegida_token_invalido(client):
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer token_falso"})
    assert resp.status_code == 401
