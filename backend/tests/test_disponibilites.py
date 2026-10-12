from datetime import date, datetime, time, timedelta, timezone

from app.db.session import SessionLocal
from app.models import Blocage, Utilisateur
from tests.test_reservations import PARIS, _create_place, _slot


def _creneau(start_hour: int, duration_hours: int = 2) -> dict:
    slot = _slot(start_hour=start_hour, duration_hours=duration_hours)
    return {"debut": slot["date_debut"], "fin": slot["date_fin"]}


def _zone_libres(client, id_zone: int, creneau: dict) -> int:
    response = client.get(f"/zones/{id_zone}", params=creneau)
    assert response.status_code == 200
    return response.json()["nombre_places_libres"]


def test_reservation_reduces_availability_only_on_its_slot(client, make_user):
    place = _create_place(client, make_user("administrateur"))
    matin, apres_midi = _creneau(10), _creneau(14)
    assert _zone_libres(client, place["id_zone"], matin) == 1

    created = client.post(
        "/reservations", json={"id_place": place["id_place"], **_slot(10)}, headers=make_user()
    )
    assert created.status_code == 201

    assert _zone_libres(client, place["id_zone"], matin) == 0
    assert _zone_libres(client, place["id_zone"], apres_midi) == 1

    places = client.get("/places", params={"id_zone": place["id_zone"], **matin}).json()
    assert places[0]["disponible"] is False
    places = client.get("/places", params={"id_zone": place["id_zone"], **apres_midi}).json()
    assert places[0]["disponible"] is True


def test_cancellation_frees_the_slot(client, make_user):
    place = _create_place(client, make_user("administrateur"))
    user_headers = make_user()
    created = client.post(
        "/reservations", json={"id_place": place["id_place"], **_slot(10)}, headers=user_headers
    ).json()
    client.patch(f"/reservations/{created['id_reservation']}/annuler", json={}, headers=user_headers)

    assert _zone_libres(client, place["id_zone"], _creneau(10)) == 1


def test_blocage_makes_zone_unavailable_on_its_period(client, make_user):
    place = _create_place(client, make_user("administrateur"))
    demain = date.today() + timedelta(days=1)
    debut = datetime.combine(demain, time(9), tzinfo=PARIS).astimezone(timezone.utc)
    with SessionLocal() as db:
        id_admin = db.query(Utilisateur.id_utilisateur).order_by(
            Utilisateur.id_utilisateur.desc()
        ).first()[0]
        db.add(
            Blocage(
                id_zone=place["id_zone"],
                id_utilisateur=id_admin,
                motif_blocage="Travaux",
                date_debut_blocage=debut.replace(tzinfo=None),
                date_fin_blocage=(debut + timedelta(hours=4)).replace(tzinfo=None),
            )
        )
        db.commit()

    assert _zone_libres(client, place["id_zone"], _creneau(10)) == 0
    assert _zone_libres(client, place["id_zone"], _creneau(15)) == 1

    refused = client.post(
        "/reservations", json={"id_place": place["id_place"], **_slot(10)}, headers=make_user()
    )
    assert refused.status_code == 409
    accepted = client.post(
        "/reservations", json={"id_place": place["id_place"], **_slot(15)}, headers=make_user()
    )
    assert accepted.status_code == 201


def test_invalid_slot_parameters(client):
    creneau = _creneau(10)
    assert client.get("/zones", params={"debut": creneau["debut"]}).status_code == 400
    inverse = {"debut": creneau["fin"], "fin": creneau["debut"]}
    assert client.get("/zones", params=inverse).status_code == 400


def test_zone_exposes_allowed_roles(client, make_user):
    from tests.test_reservations import _add_rule

    place = _create_place(client, make_user("administrateur"))
    assert client.get(f"/zones/{place['id_zone']}").json()["roles_autorises"] is None

    _add_rule(place["id_zone"], ["personnel", "visiteur"])
    zone = client.get(f"/zones/{place['id_zone']}", params=_creneau(10)).json()
    assert zone["roles_autorises"] == ["personnel", "visiteur"]
