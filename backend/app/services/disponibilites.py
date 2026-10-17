"""Calcul des disponibilités des places sur un créneau.

Principe : une place est libre sur un créneau si elle n'est ni hors service,
ni déjà réservée sur un intervalle qui chevauche ce créneau, et si sa zone
n'est ni désactivée ni bloquée à ce moment-là.

Tous ces tests sont traduits en conditions SQL plutôt qu'évalués en Python :
sur un parking de plusieurs centaines de places, charger toutes les
réservations pour les filtrer en mémoire serait bien plus coûteux que de
laisser PostgreSQL répondre avec ses index.
"""

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import and_, exists, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Blocage, Place, Reservation, Zone
from app.services.exceptions import InvalidRequestError


class Creneau:
    """Créneau [debut, fin[ en UTC sans fuseau. Sans bornes : l'instant présent.

    L'intervalle est semi-ouvert : la borne de fin est exclue. C'est ce qui
    permet à une réservation de 10 h à 12 h et une autre de 12 h à 14 h de
    coexister sur la même place sans être considérées comme un conflit.

    Deux modes cohabitent dans la même classe :
      - créneau explicite (debut et fin fournis) : « la place sera-t-elle
        libre demain de 14 h à 16 h ? » ;
      - instant présent (aucune borne) : « la place est-elle libre là,
        maintenant ? », où debut et fin valent tous deux l'heure courante.
    Le second cas a un intervalle de durée nulle, d'où le test de chevauchement
    distinct dans `_chevauche`.
    """

    def __init__(self, debut: datetime | None = None, fin: datetime | None = None) -> None:
        # Un créneau à moitié renseigné traduit une erreur d'appel : mieux vaut
        # le refuser que de deviner la borne manquante.
        if (debut is None) != (fin is None):
            raise InvalidRequestError("Indiquer à la fois debut et fin, ou aucun des deux")
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        self.maintenant = debut is None
        self.debut = to_utc_naive(debut) if debut else now
        self.fin = to_utc_naive(fin) if fin else now
        if not self.maintenant and self.fin <= self.debut:
            raise InvalidRequestError("fin doit être postérieure à debut")

    @property
    def jour(self) -> date:
        """Jour du début du créneau, en heure locale du campus.

        La conversion est indispensable pour comparer aux horaires d'ouverture
        des zones, qui sont exprimés en heure locale. Une réservation stockée
        à 23 h 30 UTC un lundi correspond au mardi 1 h 30 à Paris : lire la
        date brute en UTC désignerait le mauvais jour d'ouverture.
        """
        local = self.debut.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(settings.campus_timezone))
        return local.date()


def to_utc_naive(value: datetime) -> datetime:
    """Les colonnes TIMESTAMP sont sans fuseau : on y stocke de l'UTC.

    Convention du projet : la base ne contient que de l'UTC, et la conversion
    vers l'heure locale n'a lieu qu'à l'affichage. Comparer une date « naïve »
    à une date porteuse d'un fuseau lèverait un TypeError en Python, d'où ce
    passage obligé avant toute comparaison.
    """
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _chevauche(debut_col, fin_col, creneau: Creneau):
    """Condition SQL : l'intervalle de la table recoupe-t-il le créneau ?

    Test classique de recouvrement de deux intervalles — ils se chevauchent
    si chacun commence avant que l'autre ne finisse :

        debut_A < fin_B  ET  fin_A > debut_B

    Les inégalités sont strictes, conformément à l'intervalle semi-ouvert
    [debut, fin[ : deux créneaux qui se touchent bout à bout (10h–12h puis
    12h–14h) ne se chevauchent pas.

    Cas particulier de l'instant présent : debut == fin, et l'intervalle est
    donc vide. Avec des inégalités strictes, il ne chevaucherait jamais rien.
    On teste alors l'appartenance du point à l'intervalle, avec un `<=` pour
    inclure la borne de début.
    """
    if creneau.maintenant:
        return and_(debut_col <= creneau.debut, fin_col > creneau.debut)
    return and_(debut_col < creneau.fin, fin_col > creneau.debut)


def zones_indisponibles(db: Session, ids_zone: list[int], creneau: Creneau) -> set[int]:
    """Zones désactivées ou couvertes par un blocage pendant le créneau."""
    if not ids_zone:
        return set()
    inactives = db.scalars(
        select(Zone.id_zone).where(Zone.id_zone.in_(ids_zone), Zone.zone_active.is_(False))
    ).all()
    bloquees = db.scalars(
        select(Blocage.id_zone).where(
            Blocage.id_zone.in_(ids_zone),
            _chevauche(Blocage.date_debut_blocage, Blocage.date_fin_blocage, creneau),
        )
    ).all()
    return set(inactives) | set(bloquees)


def _condition_place_libre(creneau: Creneau):
    """Condition SQL réutilisable : « cette place est réservable sur le créneau ».

    Le cœur est un EXISTS corrélé — la sous-requête référence `Place.id_place`
    de la requête englobante. PostgreSQL peut l'interrompre dès la première
    réservation conflictuelle trouvée, sans compter ni matérialiser les
    suivantes ; c'est moins coûteux qu'une jointure suivie d'un regroupement.
    """
    reservee = exists().where(
        Reservation.id_place == Place.id_place,
        # Seules les réservations confirmées bloquent : les annulées et les
        # no-show restent en base pour l'historique et les statistiques.
        Reservation.statut_reservation == "confirmee",
        _chevauche(Reservation.date_debut, Reservation.date_fin, creneau),
    )
    # "occupee" décrit l'état physique actuel (simulé) : il ne compte que pour
    # l'instant présent, pas pour un créneau futur.
    etats_exclus = ["hors_service", "occupee"] if creneau.maintenant else ["hors_service"]
    return and_(Place.etat_place.not_in(etats_exclus), ~reservee)


def compter_places(db: Session, ids_zone: list[int], creneau: Creneau) -> dict[int, tuple[int, int]]:
    """Pour chaque zone : (nombre de places, nombre de places libres sur le créneau).

    Deux agrégats groupés plutôt qu'une requête par zone : le catalogue affiche
    toutes les zones d'un coup, et une boucle de requêtes produirait ici le
    classique problème N+1.
    """
    if not ids_zone:
        return {}
    totaux = dict(
        db.execute(
            select(Place.id_zone, func.count(Place.id_place))
            .where(Place.id_zone.in_(ids_zone))
            .group_by(Place.id_zone)
        ).all()
    )
    libres = dict(
        db.execute(
            select(Place.id_zone, func.count(Place.id_place))
            .where(Place.id_zone.in_(ids_zone), _condition_place_libre(creneau))
            .group_by(Place.id_zone)
        ).all()
    )
    # Une zone fermée est annoncée à 0 place libre quand bien même ses places
    # ne sont pas réservées : la capacité totale reste affichée, mais rien n'y
    # est réservable. Le `.get(..., 0)` couvre les zones sans aucune place,
    # absentes du résultat d'un GROUP BY.
    fermees = zones_indisponibles(db, ids_zone, creneau)
    return {
        id_zone: (totaux.get(id_zone, 0), 0 if id_zone in fermees else libres.get(id_zone, 0))
        for id_zone in ids_zone
    }


def places_disponibles(db: Session, places: list[Place], creneau: Creneau) -> set[int]:
    """Identifiants des places réservables sur le créneau parmi `places`."""
    if not places:
        return set()
    fermees = zones_indisponibles(db, list({place.id_zone for place in places}), creneau)
    candidates = [place.id_place for place in places if place.id_zone not in fermees]
    if not candidates:
        return set()
    return set(
        db.scalars(
            select(Place.id_place).where(
                Place.id_place.in_(candidates), _condition_place_libre(creneau)
            )
        ).all()
    )
