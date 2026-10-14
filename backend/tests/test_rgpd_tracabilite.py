import uuid

from tests.test_reservations import _create_place, _slot


def _register(client, role: str = "etudiant") -> tuple[str, dict[str, str]]:
    email = f"test-{uuid.uuid4().hex[:10]}@campus.fr"
    client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "motdepasse123",
            "nom_utilisateur": "Durand",
            "prenom_utilisateur": "Alix",
            "role": role,
        },
    )
    return email, _login(client, email)


def _login(client, email: str, password: str = "motdepasse123") -> dict[str, str]:
    response = client.post("/auth/login", data={"username": email, "password": password})
    if response.status_code != 200:
        return {}
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _me(client, headers) -> dict:
    return client.get("/auth/me", headers=headers).json()


def _traces(client, admin, id_utilisateur: int) -> list[dict]:
    return client.get(
        "/admin/traces", params={"id_utilisateur": id_utilisateur}, headers=admin
    ).json()


# ---------- Profil ----------


def test_update_profile(client):
    _, headers = _register(client)
    response = client.patch(
        "/auth/me", json={"prenom_utilisateur": "Alexis", "besoin_pmr": True}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["prenom_utilisateur"] == "Alexis"
    assert response.json()["besoin_pmr"] is True


def test_change_password(client):
    email, headers = _register(client)
    wrong = client.post(
        "/auth/me/mot-de-passe",
        json={"mot_de_passe_actuel": "mauvais", "nouveau_mot_de_passe": "nouveau-mdp-123"},
        headers=headers,
    )
    assert wrong.status_code == 403

    ok = client.post(
        "/auth/me/mot-de-passe",
        json={"mot_de_passe_actuel": "motdepasse123", "nouveau_mot_de_passe": "nouveau-mdp-123"},
        headers=headers,
    )
    assert ok.status_code == 204
    assert _login(client, email) == {}
    assert _login(client, email, "nouveau-mdp-123") != {}


# ---------- RGPD ----------


def test_export_contains_user_data_without_password(client, make_user):
    place = _create_place(client, make_user("administrateur"))
    _, headers = _register(client)
    client.post("/reservations", json={"id_place": place["id_place"], **_slot()}, headers=headers)

    export = client.get("/auth/me/export", headers=headers)
    assert export.status_code == 200
    data = export.json()
    assert data["profil"]["nom_utilisateur"] == "Durand"
    assert "mot_de_passe_hash" not in data["profil"]
    assert data["roles"] == ["etudiant"]
    assert len(data["reservations"]) == 1


def test_delete_account_anonymizes_and_cancels_future_reservations(client, make_user):
    admin = make_user("administrateur")
    place = _create_place(client, admin)
    email, headers = _register(client)
    id_user = _me(client, headers)["id_utilisateur"]
    reservation = client.post(
        "/reservations", json={"id_place": place["id_place"], **_slot()}, headers=headers
    ).json()

    wrong = client.request("DELETE", "/auth/me", json={"mot_de_passe": "mauvais"}, headers=headers)
    assert wrong.status_code == 403

    deleted = client.request(
        "DELETE", "/auth/me", json={"mot_de_passe": "motdepasse123"}, headers=headers
    )
    assert deleted.status_code == 204

    assert client.get("/auth/me", headers=headers).status_code == 403
    assert _login(client, email) == {}

    [anonyme] = [
        u for u in client.get("/admin/utilisateurs", params={"recherche": "compte-supprime"},
                              headers=admin).json()
        if u["id_utilisateur"] == id_user
    ]
    assert anonyme["statut_compte"] == "supprime"
    assert email not in anonyme["email"]
    assert anonyme["nom_utilisateur"] != "Durand"

    listed = client.get(
        "/admin/reservations", params={"id_zone": place["id_zone"]}, headers=admin
    ).json()
    [resa] = [r for r in listed if r["id_reservation"] == reservation["id_reservation"]]
    assert resa["statut_reservation"] == "annulee"


# ---------- Traçabilité ----------


def test_important_actions_are_logged_without_personal_data(client, make_user):
    admin = make_user("administrateur")
    place = _create_place(client, admin)
    email, headers = _register(client)
    id_user = _me(client, headers)["id_utilisateur"]

    client.post("/reservations", json={"id_place": place["id_place"], **_slot()}, headers=headers)
    client.patch("/auth/me", json={"nom_utilisateur": "Nouveau-Nom"}, headers=headers)
    _login(client, email, "mauvais-mot-de-passe")

    traces = _traces(client, admin, id_user)
    actions = {trace["type_action"] for trace in traces}
    assert {
        "compte.creation",
        "connexion.reussie",
        "connexion.echec",
        "reservation.creation",
        "compte.modification",
    } <= actions
    for trace in traces:
        detail = trace["detail_action"] or ""
        assert "@" not in detail and "Nouveau-Nom" not in detail and "motdepasse" not in detail


def test_admin_actions_are_logged(client, make_user):
    admin = make_user("administrateur")
    place = _create_place(client, admin)
    id_admin = _me(client, admin)["id_utilisateur"]
    client.patch(f"/zones/{place['id_zone']}", json={"zone_active": False}, headers=admin)

    traces = _traces(client, admin, id_admin)
    modif = [t for t in traces if t["type_action"] == "zone.modification"]
    assert modif and modif[0]["detail_action"] == "champs : zone_active"

    filtered = client.get("/admin/traces", params={"type_action": "zone."}, headers=admin).json()
    assert all(t["type_action"].startswith("zone.") for t in filtered)


def test_traces_require_admin(client, make_user):
    assert client.get("/admin/traces", headers=make_user()).status_code == 403


# ---------- Administration des comptes ----------


def test_admin_promotes_and_suspends_users(client, make_user):
    admin = make_user("administrateur")
    email, headers = _register(client)
    id_user = _me(client, headers)["id_utilisateur"]

    assert client.get("/admin/statistiques", headers=headers).status_code == 403
    promoted = client.patch(
        f"/admin/utilisateurs/{id_user}", json={"roles": ["administrateur"]}, headers=admin
    )
    assert promoted.json()["roles"] == ["administrateur"]
    assert client.get("/admin/statistiques", headers=headers).status_code == 200

    suspended = client.patch(
        f"/admin/utilisateurs/{id_user}", json={"statut_compte": "suspendu"}, headers=admin
    )
    assert suspended.json()["statut_compte"] == "suspendu"
    assert client.post(
        "/auth/login", data={"username": email, "password": "motdepasse123"}
    ).status_code == 403


def test_admin_cannot_lock_themselves_out(client, make_user):
    admin = make_user("administrateur")
    id_admin = _me(client, admin)["id_utilisateur"]
    url = f"/admin/utilisateurs/{id_admin}"
    assert client.patch(url, json={"roles": ["etudiant"]}, headers=admin).status_code == 409
    assert client.patch(url, json={"statut_compte": "suspendu"}, headers=admin).status_code == 409


def test_user_management_requires_admin(client, make_user):
    headers = make_user("personnel")
    assert client.get("/admin/utilisateurs", headers=headers).status_code == 403
