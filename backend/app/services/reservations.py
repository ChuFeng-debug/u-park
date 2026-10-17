"""Règles de gestion des réservations.

Cœur métier du projet. Les routes HTTP ne font qu'appeler ces fonctions : en
isolant les règles ici, elles restent testables sans serveur ni requête, et
sont réutilisables par la validation des demandes visiteurs comme par le
back-office.

Une réservation suit une machine à états simple :

    confirmee ──(annulation)──────▶ annulee
        │
        ├──(scan à l'entrée)─────▶ confirmee + date_passage
        │
        └──(délai dépassé sans passage)──▶ no_show

Les transitions sont irréversibles : on n'annule pas une réservation déjà
honorée, et un no-show ne redevient jamais confirmé.
"""

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import CibleRole, Place, RegleAcces, Reservation, Utilisateur, Zone
from app.services.disponibilites import Creneau, to_utc_naive, zones_indisponibles
from app.services.exceptions import (
    AccessDeniedError,
    ConflictError,
    InvalidRequestError,
    NotFoundError,
)

ADMIN_ROLE = "administrateur"
VISITEUR_ROLE = "visiteur"


def _check_slot_in_opening_hours(zone: Zone, date_debut: datetime, date_fin: datetime) -> date:
    """Vérifie le créneau et renvoie le jour (heure locale) de la réservation."""
    # Les horaires d'une zone sont exprimés en heure locale du campus.
    tz = ZoneInfo(settings.campus_timezone)
    debut_local = date_debut.replace(tzinfo=timezone.utc).astimezone(tz)
    fin_local = date_fin.replace(tzinfo=timezone.utc).astimezone(tz)
    if debut_local.date() != fin_local.date():
        raise InvalidRequestError("Une réservation doit commencer et finir le même jour")
    if debut_local.time() < zone.heure_ouverture or fin_local.time() > zone.heure_fermeture:
        raise InvalidRequestError(
            f"Créneau hors des horaires de la zone "
            f"({zone.heure_ouverture:%H:%M} – {zone.heure_fermeture:%H:%M})"
        )
    return debut_local.date()


def roles_autorises(db: Session, id_zone: int, jour: date) -> set[str] | None:
    """Rôles autorisés par les règles actives de la zone, None si aucune règle."""
    regles = (
        db.query(RegleAcces)
        .filter(
            RegleAcces.id_zone == id_zone,
            RegleAcces.regle_active.is_(True),
            RegleAcces.date_debut_validite <= jour,
            or_(RegleAcces.date_fin_validite.is_(None), RegleAcces.date_fin_validite >= jour),
        )
        .all()
    )
    if not regles:
        return None
    rows = (
        db.query(CibleRole.code_role)
        .filter(CibleRole.id_regle.in_([regle.id_regle for regle in regles]))
        .all()
    )
    return {row.code_role for row in rows}


def _check_access(
    db: Session, user: Utilisateur, user_roles: set[str], zone: Zone, place: Place, jour: date
) -> None:
    if ADMIN_ROLE in user_roles:
        return
    if place.type_place == "pmr" and not user.besoin_pmr:
        raise AccessDeniedError("Place réservée aux personnes à mobilité réduite")
    allowed = roles_autorises(db, zone.id_zone, jour)
    if allowed is not None and not user_roles & allowed:
        raise AccessDeniedError("Votre profil n'a pas accès à cette zone")


def _place_has_overlap(db: Session, id_place: int, date_debut: datetime, date_fin: datetime) -> bool:
    """Cette place est-elle déjà prise sur un créneau recoupant celui demandé ?

    Le test de recouvrement est le couple d'inégalités `debut_A < fin_B` et
    `fin_A > debut_B` : deux intervalles se chevauchent si chacun commence
    avant que l'autre ne se termine. Les inégalités strictes autorisent les
    créneaux adjacents (10h–12h puis 12h–14h sur la même place).
    """
    return (
        db.query(Reservation.id_reservation)
        .filter(
            Reservation.id_place == id_place,
            Reservation.statut_reservation == "confirmee",
            Reservation.date_debut < date_fin,
            Reservation.date_fin > date_debut,
        )
        .first()
        is not None
    )


def _user_has_overlap(
    db: Session, id_utilisateur: int, date_debut: datetime, date_fin: datetime
) -> bool:
    """Même test de recouvrement, mais appliqué à l'utilisateur.

    Règle métier distincte de la précédente : elle empêche une personne de
    monopoliser plusieurs places au même moment. Une place peut être libre et
    la réservation malgré tout refusée pour ce motif.
    """
    return (
        db.query(Reservation.id_reservation)
        .filter(
            Reservation.id_utilisateur == id_utilisateur,
            Reservation.statut_reservation == "confirmee",
            Reservation.date_debut < date_fin,
            Reservation.date_fin > date_debut,
        )
        .first()
        is not None
    )


def create_reservation(
    db: Session,
    user: Utilisateur,
    user_roles: set[str],
    id_place: int,
    date_debut: datetime,
    date_fin: datetime,
    *,
    via_demande: bool = False,
    commit: bool = True,
) -> Reservation:
    """Crée une réservation confirmée après contrôle des règles de gestion.

    `via_demande` : réservation créée par la validation d'une demande visiteur.
    `commit=False` : laisse l'appelant valider la transaction. C'est ce qui
    permet à la validation d'une demande d'enregistrer la demande et sa
    réservation en une seule transaction — soit les deux, soit aucune.

    Les contrôles sont volontairement ordonnés du moins au plus coûteux :
    droits et dates d'abord (sans accès à la base), puis existence de la
    place et de la zone, enfin les tests de chevauchement. Inutile
    d'interroger les réservations pour un créneau déjà passé.
    """
    if user_roles == {VISITEUR_ROLE} and not via_demande:
        raise AccessDeniedError("Les visiteurs doivent passer par une demande de place")

    date_debut = to_utc_naive(date_debut)
    date_fin = to_utc_naive(date_fin)
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if date_debut < now:
        raise InvalidRequestError("Impossible de réserver un créneau passé")

    place = db.get(Place, id_place)
    if place is None:
        raise InvalidRequestError("Place inconnue")
    if place.etat_place == "hors_service":
        raise ConflictError("Place hors service")

    zone = db.get(Zone, place.id_zone)
    if zone is None or zones_indisponibles(db, [zone.id_zone], Creneau(date_debut, date_fin)):
        raise ConflictError("Zone bloquée ou inconnue sur ce créneau")

    jour = _check_slot_in_opening_hours(zone, date_debut, date_fin)
    _check_access(db, user, user_roles, zone, place, jour)

    if _user_has_overlap(db, user.id_utilisateur, date_debut, date_fin):
        raise ConflictError("Vous avez déjà une réservation sur ce créneau")
    if _place_has_overlap(db, id_place, date_debut, date_fin):
        raise ConflictError("Place déjà réservée sur ce créneau")

    reservation = Reservation(
        id_utilisateur=user.id_utilisateur,
        id_place=id_place,
        date_debut=date_debut,
        date_fin=date_fin,
        statut_reservation="confirmee",
        date_creation_resa=now,
    )
    db.add(reservation)
    try:
        db.flush()
    except IntegrityError:
        # Filet de sécurité contre les accès concurrents.
        #
        # Les tests de chevauchement ci-dessus laissent une fenêtre : entre
        # leur exécution et l'INSERT, une autre requête peut avoir réservé la
        # même place. Deux utilisateurs cliquant simultanément passeraient
        # donc tous les deux les vérifications.
        #
        # La base tranche : une contrainte EXCLUDE USING gist (voir la
        # migration 5d5d04aa650e) interdit physiquement deux réservations
        # confirmées qui se chevauchent sur une même place. Le perdant reçoit
        # une IntegrityError, qu'on traduit ici en erreur métier lisible.
        db.rollback()
        raise ConflictError("Place déjà réservée sur ce créneau")
    if commit:
        db.commit()
        db.refresh(reservation)
    return reservation


def get_user_reservation(db: Session, user: Utilisateur, id_reservation: int) -> Reservation:
    reservation = db.get(Reservation, id_reservation)
    if reservation is None or reservation.id_utilisateur != user.id_utilisateur:
        raise NotFoundError("Réservation introuvable")
    return reservation


def cancel_reservation(
    db: Session, user: Utilisateur, id_reservation: int, motif: str | None
) -> Reservation:
    reservation = get_user_reservation(db, user, id_reservation)
    return _cancel(db, reservation, motif)


def admin_cancel_reservation(db: Session, id_reservation: int, motif: str | None) -> Reservation:
    reservation = db.get(Reservation, id_reservation)
    if reservation is None:
        raise NotFoundError("Réservation introuvable")
    return _cancel(db, reservation, motif)


def _cancel(db: Session, reservation: Reservation, motif: str | None) -> Reservation:
    """Transition vers « annulee », avec les gardes de la machine à états.

    Les trois refus ci-dessous couvrent les transitions interdites : annuler
    deux fois, annuler un no-show déjà constaté, et annuler après l'entrée du
    véhicule — à ce stade la place a effectivement été occupée, l'annuler
    fausserait les statistiques d'occupation.
    """
    if reservation.statut_reservation == "annulee":
        raise ConflictError("Réservation déjà annulée")
    if reservation.statut_reservation == "no_show":
        raise ConflictError("Réservation non honorée, elle ne peut plus être annulée")
    if reservation.date_passage is not None:
        raise ConflictError("Véhicule déjà entré, la réservation ne peut plus être annulée")

    reservation.statut_reservation = "annulee"
    reservation.date_annulation = datetime.now(timezone.utc).replace(tzinfo=None)
    reservation.motif_annulation = motif
    db.commit()
    db.refresh(reservation)
    return reservation


def cancel_reservations_in_zone(
    db: Session, id_zone: int, date_debut: datetime, date_fin: datetime, motif: str
) -> int:
    """Annule (sans valider la transaction) les réservations confirmées de la
    zone qui chevauchent la période. Renvoie le nombre d'annulations."""
    reservations = (
        db.query(Reservation)
        .join(Place, Place.id_place == Reservation.id_place)
        .filter(
            Place.id_zone == id_zone,
            Reservation.statut_reservation == "confirmee",
            Reservation.date_debut < date_fin,
            Reservation.date_fin > date_debut,
        )
        .all()
    )
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for reservation in reservations:
        reservation.statut_reservation = "annulee"
        reservation.date_annulation = now
        reservation.motif_annulation = motif
    return len(reservations)


def enregistrer_passage(db: Session, user: Utilisateur, id_reservation: int) -> Reservation:
    """Simule le scan du QR code à l'entrée du parking."""
    reservation = get_user_reservation(db, user, id_reservation)
    if reservation.statut_reservation != "confirmee":
        raise ConflictError("Seule une réservation confirmée peut être présentée à l'entrée")
    if reservation.date_passage is not None:
        raise ConflictError("Passage déjà enregistré")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    # Tolérance d'avance : on accepte le véhicule un peu avant l'heure, sans
    # quoi un conducteur arrivé cinq minutes en avance serait refusé.
    ouverture = reservation.date_debut - timedelta(minutes=settings.passage_avance_minutes)
    if not ouverture <= now < reservation.date_fin:
        raise InvalidRequestError(
            f"Le passage est possible de {settings.passage_avance_minutes} min avant "
            "le début jusqu'à la fin du créneau"
        )
    reservation.date_passage = now
    db.commit()
    db.refresh(reservation)
    return reservation


def marquer_no_shows(db: Session, now: datetime | None = None) -> int:
    """Passe en "no_show" les réservations confirmées sans passage une fois le
    délai de grâce écoulé. Renvoie le nombre de réservations marquées.

    Faute d'ordonnanceur (cron, Celery) dans ce projet, le balayage est
    déclenché à la demande, notamment avant le calcul des statistiques, pour
    que celles-ci portent sur des statuts à jour. Le paramètre `now`
    injectable rend la fonction testable sans attendre le délai réel.
    """
    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    limite = now - timedelta(minutes=settings.no_show_delai_minutes)
    # UPDATE ... WHERE en un seul ordre SQL plutôt qu'une boucle Python.
    # `synchronize_session=False` dispense SQLAlchemy de répercuter la
    # modification sur les objets déjà chargés en session : ils ne sont pas
    # réutilisés ensuite, et le faire imposerait une requête de relecture.
    marquees = (
        db.query(Reservation)
        .filter(
            Reservation.statut_reservation == "confirmee",
            Reservation.date_passage.is_(None),
            Reservation.date_debut < limite,
        )
        .update({Reservation.statut_reservation: "no_show"}, synchronize_session=False)
    )
    db.commit()
    return marquees
