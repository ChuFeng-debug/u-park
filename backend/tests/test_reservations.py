import uuid
from datetime import datetime, timedelta, timezone


def _unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:10]}@campus.fr"


def _register_and_login(client, role: str) -> tuple[str, dict[str, str]]:
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
    login = client.post("/auth/login", data={"username": email, "password": "motdepasse123"})
    token = login.json()["access_token"]
    return email, {"Authorization": f"Bearer {token}"}


def _create_place(client, admin_headers) -> dict:
    parking = client.post(
        "/parkings",
        json={"nom_parking": f"P-{uuid.uuid4().hex[:6]}", "localisation_parking": "Campus"},
        headers=admin_headers,
    ).json()
    zone = client.post(
        "/zones",
        json={
            "id_parking": parking["id_parking"],
            "nom_zone": "Zone résa",
            "capacite_theorique": 1,
            "heure_ouverture": "07:00:00",
            "heure_fermeture": "20:00:00",
        },
        headers=admin_headers,
    ).json()
    place = client.post(
        "/places",
        json={"id_zone": zone["id_zone"], "numero_place": "R1", "type_place": "standard"},
        headers=admin_headers,
    ).json()
    return place


def _slot(hours_from_now: int, duration_hours: int = 2) -> dict:
    start = datetime.now(timezone.utc) + timedelta(hours=hours_from_now)
    end = start + timedelta(hours=duration_hours)
    return {"date_debut": start.isoformat(), "date_fin": end.isoformat()}


def test_create_and_list_reservation(client):
    _, admin_headers = _register_and_login(client, "administrateur")
    place = _create_place(client, admin_headers)
    _, user_headers = _register_and_login(client, "etudiant")

    response = client.post(
        "/reservations",
        json={"id_place": place["id_place"], **_slot(1)},
        headers=user_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["statut_reservation"] == "confirmee"

    listing = client.get("/reservations", headers=user_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_reservation_requires_auth(client):
    response = client.post("/reservations", json={"id_place": 1, **_slot(1)})
    assert response.status_code == 401


def test_overlapping_reservation_rejected(client):
    _, admin_headers = _register_and_login(client, "administrateur")
    place = _create_place(client, admin_headers)
    _, user_headers = _register_and_login(client, "etudiant")

    slot = _slot(1)
    first = client.post(
        "/reservations", json={"id_place": place["id_place"], **slot}, headers=user_headers
    )
    assert first.status_code == 201

    second = client.post(
        "/reservations", json={"id_place": place["id_place"], **slot}, headers=user_headers
    )
    assert second.status_code == 409


def test_cancel_reservation(client):
    _, admin_headers = _register_and_login(client, "administrateur")
    place = _create_place(client, admin_headers)
    _, user_headers = _register_and_login(client, "etudiant")

    created = client.post(
        "/reservations", json={"id_place": place["id_place"], **_slot(1)}, headers=user_headers
    ).json()

    cancelled = client.patch(
        f"/reservations/{created['id_reservation']}/annuler",
        json={"motif_annulation": "Changement de plan"},
        headers=user_headers,
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["statut_reservation"] == "annulee"

    # Le créneau redevient disponible pour un autre utilisateur.
    _, other_headers = _register_and_login(client, "etudiant")
    retry = client.post(
        "/reservations", json={"id_place": place["id_place"], **_slot(1)}, headers=other_headers
    )
    assert retry.status_code == 201


def test_cannot_cancel_others_reservation(client):
    _, admin_headers = _register_and_login(client, "administrateur")
    place = _create_place(client, admin_headers)
    _, owner_headers = _register_and_login(client, "etudiant")
    _, other_headers = _register_and_login(client, "etudiant")

    created = client.post(
        "/reservations", json={"id_place": place["id_place"], **_slot(1)}, headers=owner_headers
    ).json()

    response = client.patch(
        f"/reservations/{created['id_reservation']}/annuler",
        json={},
        headers=other_headers,
    )
    assert response.status_code == 404


def test_reservation_on_blocked_zone_rejected(client):
    _, admin_headers = _register_and_login(client, "administrateur")
    place = _create_place(client, admin_headers)
    zone_id = client.get(f"/places/{place['id_place']}").json()["id_zone"]
    client.patch(f"/zones/{zone_id}", json={"zone_active": False}, headers=admin_headers)

    _, user_headers = _register_and_login(client, "etudiant")
    response = client.post(
        "/reservations", json={"id_place": place["id_place"], **_slot(1)}, headers=user_headers
    )
    assert response.status_code == 409
