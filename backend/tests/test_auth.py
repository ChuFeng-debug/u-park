import uuid


def _unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:10]}@campus.fr"


def _register(client, email=None, role="etudiant", password="motdepasse123"):
    email = email or _unique_email()
    return client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "nom_utilisateur": "Martin",
            "prenom_utilisateur": "Léa",
            "role": role,
        },
    )


def test_register_success(client):
    email = _unique_email()
    response = _register(client, email=email)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == email
    assert body["roles"] == ["etudiant"]
    assert "mot_de_passe_hash" not in body


def test_register_duplicate_email(client):
    email = _unique_email()
    _register(client, email=email)
    response = _register(client, email=email)
    assert response.status_code == 400


def test_register_unknown_role(client):
    response = _register(client, role="fantome")
    assert response.status_code == 400


def test_login_success_and_me(client):
    email = _unique_email()
    _register(client, email=email, password="motdepasse123")
    login_response = client.post(
        "/auth/login",
        data={"username": email, "password": "motdepasse123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == email


def test_login_wrong_password(client):
    email = _unique_email()
    _register(client, email=email, password="motdepasse123")
    response = client.post(
        "/auth/login",
        data={"username": email, "password": "incorrect"},
    )
    assert response.status_code == 401


def test_me_without_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401
