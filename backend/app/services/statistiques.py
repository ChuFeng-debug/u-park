"""Indicateurs du tableau de bord administrateur.

Le taux d'occupation rapporte les heures réservées et honorées (statut
"confirmee") aux heures disponibles : places en service x amplitude
d'ouverture de la zone x nombre de jours. Les zones désactivées ne comptent
pas. Les annulations et no-shows ne consomment pas de capacité.
"""

from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Parking, Place, Reservation, Zone
from app.schemas.statistiques import Indicateurs, StatJour, Statistiques, StatZone
from app.services.exceptions import InvalidRequestError
from app.services.reservations import marquer_no_shows

MAX_JOURS = 366


def _ratio(numerateur: float, denominateur: float) -> float:
    return round(numerateur / denominateur, 4) if denominateur else 0.0


class _Compteur:
    """Accumulateur réutilisé pour les trois axes d'analyse.

    Les mêmes lignes SQL alimentent trois agrégations simultanées : le total
    général, le détail par jour et le détail par zone. Encapsuler le cumul
    ici évite d'écrire trois fois la même logique, et garantit que les trois
    vues restent cohérentes entre elles.
    """

    def __init__(self) -> None:
        self.par_statut: dict[str, int] = defaultdict(int)
        self.heures_honorees = 0.0

    def ajouter(self, statut: str, nombre: int, heures: float) -> None:
        self.par_statut[statut] += nombre
        # Seules les réservations confirmées consomment de la capacité : une
        # place annulée ou laissée vide (no-show) est restée inoccupée, la
        # compter gonflerait artificiellement le taux d'occupation.
        if statut == "confirmee":
            self.heures_honorees += heures

    def indicateurs(self, heures_disponibles: float) -> dict:
        total = sum(self.par_statut.values())
        return {
            "reservations": total,
            "honorees": self.par_statut["confirmee"],
            "annulees": self.par_statut["annulee"],
            "no_show": self.par_statut["no_show"],
            "taux_annulation": _ratio(self.par_statut["annulee"], total),
            "taux_no_show": _ratio(self.par_statut["no_show"], total),
            # Plafonné à 100 % : une réservation peut déborder des horaires
            # d'ouverture théoriques (zone dont les horaires ont changé après
            # coup), et un taux de 103 % serait incompréhensible sur un
            # tableau de bord.
            "taux_occupation": min(1.0, _ratio(self.heures_honorees, heures_disponibles)),
        }


def _heures_ouverture(zone: Zone) -> float:
    debut = datetime.combine(date.min, zone.heure_ouverture)
    fin = datetime.combine(date.min, zone.heure_fermeture)
    return max(0.0, (fin - debut).total_seconds() / 3600)


def calculer(
    db: Session, du: date | None = None, au: date | None = None, id_parking: int | None = None
) -> Statistiques:
    tz = ZoneInfo(settings.campus_timezone)
    today = datetime.now(tz).date()
    au = au or today
    du = du or au - timedelta(days=29)
    if au < du:
        raise InvalidRequestError("au doit être postérieur ou égal à du")
    nb_jours = (au - du).days + 1
    if nb_jours > MAX_JOURS:
        raise InvalidRequestError(f"Période limitée à {MAX_JOURS} jours")

    # Les statistiques reflètent les no-shows dès que le délai est dépassé.
    marquer_no_shows(db)

    zones_query = (
        db.query(Zone, Parking).join(Parking, Parking.id_parking == Zone.id_parking)
    )
    if id_parking is not None:
        zones_query = zones_query.filter(Zone.id_parking == id_parking)
    zones = zones_query.order_by(Parking.nom_parking, Zone.nom_zone).all()
    ids_zone = [zone.id_zone for zone, _ in zones]

    places_en_service = dict(
        db.execute(
            select(Place.id_zone, func.count(Place.id_place))
            .where(Place.id_zone.in_(ids_zone), Place.etat_place != "hors_service")
            .group_by(Place.id_zone)
        ).all()
    )
    # Dénominateur du taux d'occupation : « places-heures » offertes par jour.
    # Une zone de 50 places ouverte 10 h offre 500 places-heures ; 250 heures
    # réservées correspondent donc à 50 % d'occupation. Une zone désactivée
    # n'offre rien et sort du calcul (capacité nulle), au lieu d'être comptée
    # comme une zone vide qui tirerait la moyenne vers le bas.
    capacite_jour = {
        zone.id_zone: places_en_service.get(zone.id_zone, 0) * _heures_ouverture(zone)
        if zone.zone_active
        else 0.0
        for zone, _ in zones
    }

    debut_utc = datetime.combine(du, time.min, tzinfo=tz).astimezone(timezone.utc)
    fin_utc = datetime.combine(au + timedelta(days=1), time.min, tzinfo=tz).astimezone(
        timezone.utc
    )
    # Jour local du début de réservation (colonnes stockées en UTC sans fuseau).
    #
    # Le double appel à timezone() n'est pas une redondance. En PostgreSQL,
    # l'opérateur AT TIME ZONE change de sens selon le type reçu :
    #   timezone('UTC', colonne_sans_fuseau) → déclare que cette date EST en
    #     UTC, et produit une date horodatée ;
    #   timezone('Europe/Paris', date_horodatée) → la CONVERTIT vers Paris.
    # Il faut donc les deux : déclarer, puis convertir.
    #
    # Ce regroupement est fait par la base plutôt qu'en Python car c'est le
    # GROUP BY lui-même qui en dépend — regrouper sur le jour UTC placerait
    # les réservations nocturnes dans la mauvaise journée.
    jour_local = func.date(
        func.timezone(settings.campus_timezone, func.timezone("UTC", Reservation.date_debut))
    )
    heures = func.sum(func.extract("epoch", Reservation.date_fin - Reservation.date_debut) / 3600)
    rows = db.execute(
        select(
            jour_local,
            Place.id_zone,
            Reservation.statut_reservation,
            func.count(Reservation.id_reservation),
            heures,
        )
        .join(Place, Place.id_place == Reservation.id_place)
        .where(
            Place.id_zone.in_(ids_zone),
            Reservation.date_debut >= debut_utc.replace(tzinfo=None),
            Reservation.date_debut < fin_utc.replace(tzinfo=None),
        )
        .group_by(jour_local, Place.id_zone, Reservation.statut_reservation)
    ).all()

    # Une seule requête, agrégée sur trois dimensions (jour × zone × statut),
    # puis ventilée en mémoire sur les trois axes du tableau de bord. Trois
    # requêtes distinctes auraient coûté trois parcours de la même table.
    total, par_jour, par_zone = _Compteur(), defaultdict(_Compteur), defaultdict(_Compteur)
    for jour, id_zone, statut, nombre, nb_heures in rows:
        nb_heures = float(nb_heures or 0)
        total.ajouter(statut, nombre, nb_heures)
        par_jour[jour].ajouter(statut, nombre, nb_heures)
        par_zone[id_zone].ajouter(statut, nombre, nb_heures)

    capacite_totale_jour = sum(capacite_jour.values())
    # La liste des jours est générée, pas déduite des résultats : un jour sans
    # aucune réservation est absent du GROUP BY, mais doit apparaître à zéro
    # dans le graphique. Le `defaultdict` fournit alors un compteur vide.
    jours = [du + timedelta(days=i) for i in range(nb_jours)]
    return Statistiques(
        du=du,
        au=au,
        totaux=Indicateurs(**total.indicateurs(capacite_totale_jour * nb_jours)),
        par_jour=[
            StatJour(jour=jour, **par_jour[jour].indicateurs(capacite_totale_jour))
            for jour in jours
        ],
        par_zone=[
            StatZone(
                id_zone=zone.id_zone,
                nom_zone=zone.nom_zone,
                id_parking=parking.id_parking,
                nom_parking=parking.nom_parking,
                nombre_places=places_en_service.get(zone.id_zone, 0),
                **par_zone[zone.id_zone].indicateurs(capacite_jour[zone.id_zone] * nb_jours),
            )
            for zone, parking in zones
        ],
    )
