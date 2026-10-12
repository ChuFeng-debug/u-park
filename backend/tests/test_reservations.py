import uuid
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.db.session import SessionLocal
from app.models import CibleRole, RegleAcces

PARIS = ZoneInfo("Europe/Paris")


def _create_place(client, admin_headers, type_place: str = "standard") -> dict:
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
        json={"id_zone": zone["id_zone"], "numero_place": "R1", "type_place": type_place},
        headers=admin_headers,
    ).json()
    return place


def _slot(start_hour: int = 10, duration_hours: int = 2, days_from_now: int = 1) -> dict:
    """Créneau en heure de Paris, par défaut demain 10h-12h (dans les horaires)."""
    day = date.today() + timedelta(days=days_from_now)
    start = datetime.combine(day, time(start_hour), tzinfo=PARIS)
    end = start + timedelta(hours=duration_hours)
    return {"date_debut": start.isoformat(), "date_fin": end.isoformat()}


def _add_rule(id_zone: int, roles: list[str]) -> None:
    with SessionLocal() as db:
        regle = RegleAcces(
            id_zone=id_zone,
            libelle_regle="Règle de test",
            niveau_priorite=1,
            date_debut_validite=date.today(),
            regle_active=True,
        )
        db.add(regle)
        db.flush()
        db.add_all([CibleRole(id_regle=regle.id_regle, code_role=role) for role in roles])
        db.commit()


def test_create_and_list_reservation(client, make_user):
    place = _create_place(client, make_user("administrateur"))
    user_headers = make_user("etudiant")

    response = client.post(
        "/reservations", json={"id_place": place["id_place"], **_slot()}, headers=user_headers
    )
    assert response.status_code == 201
    assert response.json()["statut_reservation"] == "confirmee"

    listing = client.get("/reservations", headers=user_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_reservation_requires_auth(client):
    response = client.post("/reservations", json={"id_place": 1, **_slot()})
    assert response.status_code == 401


def test_overlapping_reservation_rejected(client, make_user):
    place = _create_place(client, make_user("administrateur"))

    first = client.post(
        "/reservations", json={"id_place": place["id_place"], **_slot()}, headers=make_user()
    )
    assert first.status_code == 201

    second = client.post(
        "/reservations",
        json={"id_place": place["id_place"], **_slot(start_hour=11)},
        headers=make_user(),
    )
    assert second.status_code == 409


def test_user_cannot_hold_two_places_on_same_slot(client, make_user):
    admin_headers = make_user("administrateur")
    place_a = _create_place(client, admin_headers)
    place_b = _create_place(client, admin_headers)
    user_headers = make_user("etudiant")

    first = client.post(
        "/reservations", json={"id_place": place_a["id_place"], **_slot()}, headers=user_headers
    )
    assert first.status_code == 201

    second = client.post(
        "/reservations", json={"id_place": place_b["id_place"], **_slot()}, headers=user_headers
    )
    assert second.status_code == 409


def test_past_slot_rejected(client, make_user):
    place = _create_place(client, make_user("administrateur"))
    response = client.post(
        "/reservations",
        json={"id_place": place["id_place"], **_slot(days_from_now=-1)},
        headers=make_user(),
    )
    assert response.status_code == 400


def test_slot_outside_opening_hours_rejected(client, make_user):
    place = _create_place(client, make_user("administrateur"))
    response = client.post(
        "/reservations",
        json={"id_place": place["id_place"], **_slot(start_hour=19, duration_hours=3)},
        headers=make_user(),
    )
    assert response.status_code == 400


def test_pmr_place_requires_pmr_need(client, make_user):
    place = _create_place(client, make_user("administrateur"), type_place="pmr")

    refused = client.post(
        "/reservations", json={"id_place": place["id_place"], **_slot()}, headers=make_user()
    )
    assert refused.status_code == 403

    accepted = client.post(
        "/reservations",
        json={"id_place": place["id_place"], **_slot()},
        headers=make_user(besoin_pmr=True),
    )
    assert accepted.status_code == 201


def test_access_rule_restricts_zone_to_target_roles(client, make_user):
    place = _create_place(client, make_user("administrateur"))
    _add_rule(place["id_zone"], ["personnel"])

    refused = client.post(
        "/reservations", json={"id_place": place["id_place"], **_slot()}, headers=make_user()
    )
    assert refused.status_code == 403

    accepted = client.post(
        "/reservations",
        json={"id_place": place["id_place"], **_slot()},
        headers=make_user("personnel"),
    )
    assert accepted.status_code == 201


def test_cancel_reservation(client, make_user):
    place = _create_place(client, make_user("administrateur"))
    user_headers = make_user()

    created = client.post(
        "/reservations", json={"id_place": place["id_place"], **_slot()}, headers=user_headers
    ).json()

    cancelled = client.patch(
        f"/reservations/{created['id_reservation']}/annuler",
        json={"motif_annulation": "Changement de plan"},
        headers=user_headers,
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["statut_reservation"] == "annulee"

    # Le créneau redevient disponible pour un autre utilisateur.
    retry = client.post(
        "/reservations", json={"id_place": place["id_place"], **_slot()}, headers=make_user()
    )
    assert retry.status_code == 201


def test_cannot_cancel_others_reservation(client, make_user):
    place = _create_place(client, make_user("administrateur"))
    owner_headers = make_user()

    created = client.post(
        "/reservations", json={"id_place": place["id_place"], **_slot()}, headers=owner_headers
    ).json()

    response = client.patch(
        f"/reservations/{created['id_reservation']}/annuler", json={}, headers=make_user()
    )
    assert response.status_code == 404


def test_reservation_on_blocked_zone_rejected(client, make_user):
    admin_headers = make_user("administrateur")
    place = _create_place(client, admin_headers)
    client.patch(f"/zones/{place['id_zone']}", json={"zone_active": False}, headers=admin_headers)

    response = client.post(
        "/reservations", json={"id_place": place["id_place"], **_slot()}, headers=make_user()
    )
    assert response.status_code == 409


def test_database_rejects_overlapping_confirmed_reservations(client, make_user):
    import pytest
    from sqlalchemy.exc import IntegrityError

    from app.models import Reservation, Utilisateur

    place = _create_place(client, make_user("administrateur"))
    make_user()
    start = datetime(2030, 1, 7, 9)
    with SessionLocal() as db:
        id_user = db.query(Utilisateur.id_utilisateur).order_by(Utilisateur.id_utilisateur.desc()).first()[0]

        def resa(debut: datetime, fin: datetime) -> Reservation:
            return Reservation(
                id_utilisateur=id_user,
                id_place=place["id_place"],
                date_debut=debut,
                date_fin=fin,
                statut_reservation="confirmee",
                date_creation_resa=start,
            )

        db.add(resa(start, start + timedelta(hours=2)))
        db.commit()
        db.add(resa(start + timedelta(hours=1), start + timedelta(hours=3)))
        with pytest.raises(IntegrityError):
            db.commit()
