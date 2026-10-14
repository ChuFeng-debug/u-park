from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.db.session import SessionLocal
from app.models import Reservation
from tests.test_disponibilites import _zone_libres
from tests.test_reservations import _create_place, _slot

PARIS = ZoneInfo("Europe/Paris")


def _deplacer(id_reservation: int, debut: datetime, duree_heures: float = 2) -> None:
    """Décale une réservation dans le temps (les créneaux passés sont refusés par l'API)."""
    with SessionLocal() as db:
        reservation = db.get(Reservation, id_reservation)
        reservation.date_debut = debut
        reservation.date_fin = debut + timedelta(hours=duree_heures)
        db.commit()


def _maintenant() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@pytest.fixture()
def reservation(client, make_user):
    place = _create_place(client, make_user("administrateur"))
    headers = make_user()
    created = client.post(
        "/reservations", json={"id_place": place["id_place"], **_slot()}, headers=headers
    ).json()
    return {"place": place, "headers": headers, "id": created["id_reservation"]}


# ---------- Passage et no-show ----------


def test_passage_refused_too_early(client, reservation):
    response = client.post(f"/reservations/{reservation['id']}/passage", headers=reservation["headers"])
    assert response.status_code == 400


def test_passage_recorded_once(client, reservation):
    _deplacer(reservation["id"], _maintenant() - timedelta(minutes=5))
    url = f"/reservations/{reservation['id']}/passage"

    first = client.post(url, headers=reservation["headers"])
    assert first.status_code == 200
    assert first.json()["date_passage"] is not None
    assert client.post(url, headers=reservation["headers"]).status_code == 409
    cancel = client.patch(
        f"/reservations/{reservation['id']}/annuler", json={}, headers=reservation["headers"]
    )
    assert cancel.status_code == 409


def test_passage_only_by_owner(client, make_user, reservation):
    _deplacer(reservation["id"], _maintenant() - timedelta(minutes=5))
    response = client.post(f"/reservations/{reservation['id']}/passage", headers=make_user())
    assert response.status_code == 404


def test_missed_reservation_becomes_no_show(client, make_user, reservation):
    _deplacer(reservation["id"], _maintenant() - timedelta(hours=1), duree_heures=3)
    admin = make_user("administrateur")

    marked = client.post("/admin/reservations/no-shows", headers=admin)
    assert marked.status_code == 200
    assert marked.json()["reservations_marquees"] >= 1

    detail = client.get(f"/reservations/{reservation['id']}", headers=reservation["headers"]).json()
    assert detail["statut_reservation"] == "no_show"

    cancel = client.patch(
        f"/reservations/{reservation['id']}/annuler", json={}, headers=reservation["headers"]
    )
    assert cancel.status_code == 409
    # La place non honorée est libérée.
    assert _zone_libres(client, reservation["place"]["id_zone"], {}) == 1


def test_honored_reservation_is_not_a_no_show(client, make_user, reservation):
    _deplacer(reservation["id"], _maintenant() - timedelta(minutes=10), duree_heures=3)
    client.post(f"/reservations/{reservation['id']}/passage", headers=reservation["headers"])
    _deplacer(reservation["id"], _maintenant() - timedelta(hours=1), duree_heures=3)

    client.post("/admin/reservations/no-shows", headers=make_user("administrateur"))
    detail = client.get(f"/reservations/{reservation['id']}", headers=reservation["headers"]).json()
    assert detail["statut_reservation"] == "confirmee"


def test_only_admin_triggers_no_shows(client, make_user):
    assert client.post("/admin/reservations/no-shows", headers=make_user()).status_code == 403


# ---------- Statistiques ----------


def _local(jour: str, heure: int) -> datetime:
    local = datetime.fromisoformat(f"{jour}T{heure:02d}:00").replace(tzinfo=PARIS)
    return local.astimezone(timezone.utc).replace(tzinfo=None)


def test_statistics_reflect_dataset(client, make_user):
    """Critère d'acceptation : le tableau de bord reflète réservations et annulations."""
    admin = make_user("administrateur")
    place = _create_place(client, admin)  # 1 place, zone ouverte de 7 h à 20 h (13 h)
    id_parking = client.get(f"/zones/{place['id_zone']}").json()["id_parking"]
    id_user = client.get("/auth/me", headers=admin).json()["id_utilisateur"]

    def resa(debut: datetime, fin: datetime, statut: str, passage: bool = False) -> Reservation:
        return Reservation(
            id_utilisateur=id_user,
            id_place=place["id_place"],
            date_debut=debut,
            date_fin=fin,
            statut_reservation=statut,
            date_creation_resa=debut - timedelta(days=1),
            date_passage=debut if passage else None,
        )

    with SessionLocal() as db:
        db.add_all(
            [
                resa(_local("2030-01-07", 9), _local("2030-01-07", 12), "confirmee", True),
                resa(_local("2030-01-07", 13), _local("2030-01-07", 15), "annulee"),
                resa(_local("2030-01-07", 15), _local("2030-01-07", 16), "no_show"),
                resa(_local("2030-01-08", 10), _local("2030-01-08", 11), "confirmee", True),
            ]
        )
        db.commit()

    response = client.get(
        "/admin/statistiques",
        params={"du": "2030-01-07", "au": "2030-01-08", "id_parking": id_parking},
        headers=admin,
    )
    assert response.status_code == 200
    stats = response.json()

    totaux = stats["totaux"]
    assert (totaux["reservations"], totaux["honorees"]) == (4, 2)
    assert (totaux["annulees"], totaux["no_show"]) == (1, 1)
    assert totaux["taux_annulation"] == 0.25
    assert totaux["taux_occupation"] == round(4 / 26, 4)  # 4 h honorées sur 2 x 13 h

    lundi, mardi = stats["par_jour"]
    assert (lundi["jour"], lundi["reservations"], lundi["annulees"]) == ("2030-01-07", 3, 1)
    assert lundi["taux_occupation"] == round(3 / 13, 4)
    assert (mardi["reservations"], mardi["taux_occupation"]) == (1, round(1 / 13, 4))

    [zone] = stats["par_zone"]
    assert zone["id_zone"] == place["id_zone"]
    assert zone["nombre_places"] == 1


def test_statistics_require_admin(client, make_user):
    assert client.get("/admin/statistiques", headers=make_user("personnel")).status_code == 403


def test_statistics_invalid_period(client, make_user):
    response = client.get(
        "/admin/statistiques",
        params={"du": "2030-01-10", "au": "2030-01-01"},
        headers=make_user("administrateur"),
    )
    assert response.status_code == 400

