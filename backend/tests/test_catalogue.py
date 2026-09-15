import uuid


def _unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:10]}@campus.fr"


def _register_and_login(client, role: str) -> str:
    email = _unique_email()
    client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "motdepasse123",
            "nom_utilisateur": "Test",
            "prenom_utilisateur": "User",
            "role": role,
        },
    )
    login = client.post(
        "/auth/login", data={"username": email, "password": "motdepasse123"}
    )
    return login.json()["access_token"]


def _admin_headers(client) -> dict[str, str]:
    token = _register_and_login(client, "administrateur")
    return {"Authorization": f"Bearer {token}"}


def _create_parking(client, headers) -> dict:
    response = client.post(
        "/parkings",
        json={"nom_parking": f"P-{uuid.uuid4().hex[:6]}", "localisation_parking": "Campus"},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def test_list_parkings_is_public(client):
    response = client.get("/parkings")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_parking_requires_admin(client):
    response = client.post(
        "/parkings", json={"nom_parking": "X", "localisation_parking": "Y"}
    )
    assert response.status_code == 401

    etudiant_token = _register_and_login(client, "etudiant")
    response = client.post(
        "/parkings",
        json={"nom_parking": "X", "localisation_parking": "Y"},
        headers={"Authorization": f"Bearer {etudiant_token}"},
    )
    assert response.status_code == 403


def test_create_zone_and_disponibilite(client):
    headers = _admin_headers(client)
    parking = _create_parking(client, headers)

    zone_response = client.post(
        "/zones",
        json={
            "id_parking": parking["id_parking"],
            "nom_zone": "Zone A",
            "capacite_theorique": 2,
            "heure_ouverture": "07:00:00",
            "heure_fermeture": "20:00:00",
        },
        headers=headers,
    )
    assert zone_response.status_code == 201
    zone = zone_response.json()

    place1 = client.post(
        "/places",
        json={"id_zone": zone["id_zone"], "numero_place": "A1", "type_place": "standard"},
        headers=headers,
    )
    place2 = client.post(
        "/places",
        json={
            "id_zone": zone["id_zone"],
            "numero_place": "A2",
            "type_place": "standard",
            "etat_place": "occupee",
        },
        headers=headers,
    )
    assert place1.status_code == 201
    assert place2.status_code == 201

    zone_detail = client.get(f"/zones/{zone['id_zone']}").json()
    assert zone_detail["nombre_places"] == 2
    assert zone_detail["nombre_places_libres"] == 1


def test_blocked_zone_has_zero_disponibilite(client):
    headers = _admin_headers(client)
    parking = _create_parking(client, headers)
    zone = client.post(
        "/zones",
        json={
            "id_parking": parking["id_parking"],
            "nom_zone": "Zone B",
            "capacite_theorique": 1,
            "heure_ouverture": "07:00:00",
            "heure_fermeture": "20:00:00",
        },
        headers=headers,
    ).json()
    client.post(
        "/places",
        json={"id_zone": zone["id_zone"], "numero_place": "B1", "type_place": "standard"},
        headers=headers,
    )

    blocked = client.patch(
        f"/zones/{zone['id_zone']}", json={"zone_active": False}, headers=headers
    )
    assert blocked.status_code == 200
    assert blocked.json()["zone_active"] is False

    zone_detail = client.get(f"/zones/{zone['id_zone']}").json()
    assert zone_detail["nombre_places_libres"] == 0
