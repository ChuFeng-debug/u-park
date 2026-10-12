from tests.test_disponibilites import _creneau, _zone_libres
from tests.test_reservations import _create_place, _slot


def _blocage_payload(id_zone: int, start_hour: int = 9, duration_hours: int = 4) -> dict:
    slot = _slot(start_hour=start_hour, duration_hours=duration_hours)
    return {
        "id_zone": id_zone,
        "motif_blocage": "Travaux de marquage",
        "date_debut_blocage": slot["date_debut"],
        "date_fin_blocage": slot["date_fin"],
    }


# ---------- Blocages ----------


def test_blocage_cancels_overlapping_reservations(client, make_user):
    admin = make_user("administrateur")
    place = _create_place(client, admin)
    user = make_user()
    reservation = client.post(
        "/reservations", json={"id_place": place["id_place"], **_slot(10)}, headers=user
    ).json()

    response = client.post("/blocages", json=_blocage_payload(place["id_zone"]), headers=admin)
    assert response.status_code == 201
    assert response.json()["reservations_annulees"] == 1

    detail = client.get(f"/reservations/{reservation['id_reservation']}", headers=user).json()
    assert detail["statut_reservation"] == "annulee"
    assert detail["motif_annulation"].startswith("Zone bloquée")
    assert _zone_libres(client, place["id_zone"], _creneau(10)) == 0

    deleted = client.delete(f"/blocages/{response.json()['id_blocage']}", headers=admin)
    assert deleted.status_code == 204
    assert _zone_libres(client, place["id_zone"], _creneau(10)) == 1


def test_blocage_requires_admin(client, make_user):
    place = _create_place(client, make_user("administrateur"))
    response = client.post(
        "/blocages", json=_blocage_payload(place["id_zone"]), headers=make_user("personnel")
    )
    assert response.status_code == 403


# ---------- Règles d'accès ----------


def test_admin_manages_access_rules(client, make_user):
    admin = make_user("administrateur")
    place = _create_place(client, admin)
    payload = {
        "id_zone": place["id_zone"],
        "libelle_regle": "Réservé personnels",
        "niveau_priorite": 1,
        "date_debut_validite": "2020-01-01",
        "roles": ["personnel"],
    }
    created = client.post("/regles-acces", json=payload, headers=admin)
    assert created.status_code == 201
    regle = created.json()
    assert regle["roles"] == ["personnel"]

    reservation = {"id_place": place["id_place"], **_slot()}
    assert client.post("/reservations", json=reservation, headers=make_user()).status_code == 403

    updated = client.patch(
        f"/regles-acces/{regle['id_regle']}", json={"roles": ["etudiant"]}, headers=admin
    )
    assert updated.json()["roles"] == ["etudiant"]
    assert client.post("/reservations", json=reservation, headers=make_user()).status_code == 201

    listed = client.get("/regles-acces", params={"id_zone": place["id_zone"]}, headers=admin)
    assert [r["id_regle"] for r in listed.json()] == [regle["id_regle"]]

    assert client.delete(f"/regles-acces/{regle['id_regle']}", headers=admin).status_code == 204


def test_access_rule_with_unknown_role_rejected(client, make_user):
    admin = make_user("administrateur")
    place = _create_place(client, admin)
    response = client.post(
        "/regles-acces",
        json={
            "id_zone": place["id_zone"],
            "libelle_regle": "Règle",
            "niveau_priorite": 1,
            "date_debut_validite": "2020-01-01",
            "roles": ["fantome"],
        },
        headers=admin,
    )
    assert response.status_code == 400


def test_simple_user_cannot_modify_parking_rules(client, make_user):
    """Critère d'acceptation : un utilisateur simple ne modifie pas les règles."""
    admin = make_user("administrateur")
    place = _create_place(client, admin)
    for role in ("etudiant", "personnel", "visiteur"):
        headers = make_user(role)
        assert client.get("/regles-acces", headers=headers).status_code == 403
        response = client.post(
            "/regles-acces",
            json={
                "id_zone": place["id_zone"],
                "libelle_regle": "Pirate",
                "niveau_priorite": 1,
                "date_debut_validite": "2020-01-01",
                "roles": [role],
            },
            headers=headers,
        )
        assert response.status_code == 403
        zone_update = client.patch(
            f"/zones/{place['id_zone']}", json={"zone_active": False}, headers=headers
        )
        assert zone_update.status_code == 403


# ---------- Demandes visiteurs ----------


def _demande_payload(start_hour: int = 10) -> dict:
    slot = _slot(start_hour=start_hour)
    return {
        "date_visite_souhaitee": slot["date_debut"],
        "date_fin_visite_souhaitee": slot["date_fin"],
        "motif_demande": "Jury de soutenance",
    }


def test_visitor_cannot_reserve_directly(client, make_user):
    place = _create_place(client, make_user("administrateur"))
    response = client.post(
        "/reservations",
        json={"id_place": place["id_place"], **_slot()},
        headers=make_user("visiteur"),
    )
    assert response.status_code == 403


def test_visitor_request_validated_with_chosen_place(client, make_user):
    admin = make_user("administrateur")
    place = _create_place(client, admin)
    visiteur = make_user("visiteur")

    demande = client.post("/demandes-visiteurs", json=_demande_payload(), headers=visiteur)
    assert demande.status_code == 201
    id_demande = demande.json()["id_demande"]
    assert demande.json()["statut_demande"] == "en_attente"

    en_attente = client.get(
        "/demandes-visiteurs", params={"statut": "en_attente"}, headers=admin
    ).json()
    assert id_demande in [d["id_demande"] for d in en_attente]

    validee = client.post(
        f"/demandes-visiteurs/{id_demande}/valider",
        json={"id_place": place["id_place"]},
        headers=admin,
    )
    assert validee.status_code == 200
    assert validee.json()["statut_demande"] == "validee"

    reservations = client.get("/reservations", headers=visiteur).json()
    assert reservations[0]["id_reservation"] == validee.json()["id_reservation"]
    assert reservations[0]["id_place"] == place["id_place"]

    again = client.post(f"/demandes-visiteurs/{id_demande}/valider", json={}, headers=admin)
    assert again.status_code == 409


def test_visitor_request_auto_assigns_a_place(client, make_user):
    admin = make_user("administrateur")
    _create_place(client, admin)
    visiteur = make_user("visiteur")
    id_demande = client.post(
        "/demandes-visiteurs", json=_demande_payload(), headers=visiteur
    ).json()["id_demande"]

    validee = client.post(f"/demandes-visiteurs/{id_demande}/valider", json={}, headers=admin)
    assert validee.status_code == 200
    assert validee.json()["id_reservation"] is not None


def test_visitor_request_refused(client, make_user):
    admin = make_user("administrateur")
    visiteur = make_user("visiteur")
    id_demande = client.post(
        "/demandes-visiteurs", json=_demande_payload(), headers=visiteur
    ).json()["id_demande"]

    refusee = client.post(
        f"/demandes-visiteurs/{id_demande}/refuser",
        json={"commentaire_traitement": "Parking complet ce jour-là"},
        headers=admin,
    )
    assert refusee.status_code == 200
    mes_demandes = client.get("/demandes-visiteurs/mes-demandes", headers=visiteur).json()
    assert mes_demandes[0]["statut_demande"] == "refusee"
    assert mes_demandes[0]["commentaire_traitement"] == "Parking complet ce jour-là"


def test_only_visitors_create_requests(client, make_user):
    response = client.post("/demandes-visiteurs", json=_demande_payload(), headers=make_user())
    assert response.status_code == 403


# ---------- Incidents ----------


def test_incident_lifecycle(client, make_user):
    admin = make_user("administrateur")
    place = _create_place(client, admin)
    user = make_user()

    created = client.post(
        "/incidents",
        json={
            "id_zone": place["id_zone"],
            "description_incident": "Barrière bloquée en position fermée",
            "priorite_incident": "haute",
        },
        headers=user,
    )
    assert created.status_code == 201
    incident = created.json()
    assert incident["statut_incident"] == "ouvert"

    assert client.get("/incidents", headers=user).status_code == 403
    assert client.patch(
        f"/incidents/{incident['id_incident']}", json={"statut_incident": "resolu"}, headers=user
    ).status_code == 403

    ouverts = client.get("/incidents", params={"statut": "ouvert"}, headers=admin).json()
    assert incident["id_incident"] in [i["id_incident"] for i in ouverts]

    resolu = client.patch(
        f"/incidents/{incident['id_incident']}", json={"statut_incident": "resolu"}, headers=admin
    ).json()
    assert resolu["statut_incident"] == "resolu"
    assert resolu["date_resolution"] is not None

    mes = client.get("/incidents/mes-signalements", headers=user).json()
    assert mes[0]["statut_incident"] == "resolu"


# ---------- Réservations (vue admin) ----------


def test_admin_lists_and_cancels_any_reservation(client, make_user):
    admin = make_user("administrateur")
    place = _create_place(client, admin)
    user = make_user()
    reservation = client.post(
        "/reservations", json={"id_place": place["id_place"], **_slot()}, headers=user
    ).json()

    listed = client.get(
        "/admin/reservations", params={"id_zone": place["id_zone"]}, headers=admin
    ).json()
    assert [r["id_reservation"] for r in listed] == [reservation["id_reservation"]]
    assert listed[0]["numero_place"] == "R1"

    assert client.get("/admin/reservations", headers=user).status_code == 403

    cancelled = client.patch(
        f"/admin/reservations/{reservation['id_reservation']}/annuler",
        json={"motif_annulation": "Véhicule non autorisé"},
        headers=admin,
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["statut_reservation"] == "annulee"
