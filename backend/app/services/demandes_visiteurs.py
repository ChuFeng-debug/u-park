"""Demandes de place temporaire des visiteurs, validées par un administrateur.

Les visiteurs ne réservent pas directement (voir le refus explicite dans
`create_reservation`) : ils déposent une demande qu'un administrateur valide
ou refuse. Ce détour permet de contrôler les entrées extérieures sur le
campus, et d'attribuer la place plutôt que de la laisser choisir.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import (
    AttributionRole,
    DemandeVisiteur,
    Place,
    Reservation,
    Utilisateur,
    Zone,
)
from app.schemas.demande_visiteur import (
    DemandeRefus,
    DemandeValidation,
    DemandeVisiteurCreate,
)
from app.services.disponibilites import Creneau, places_disponibles, to_utc_naive
from app.services.exceptions import (
    ConflictError,
    InvalidRequestError,
    NotFoundError,
    ServiceError,
)
from app.services.reservations import VISITEUR_ROLE, create_reservation, roles_autorises


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_demande(
    db: Session, visiteur: Utilisateur, payload: DemandeVisiteurCreate
) -> DemandeVisiteur:
    debut = to_utc_naive(payload.date_visite_souhaitee)
    if debut < _now():
        raise InvalidRequestError("La visite doit être dans le futur")
    demande = DemandeVisiteur(
        id_demandeur=visiteur.id_utilisateur,
        date_demande=_now(),
        date_visite_souhaitee=debut,
        date_fin_visite_souhaitee=to_utc_naive(payload.date_fin_visite_souhaitee),
        motif_demande=payload.motif_demande,
        statut_demande="en_attente",
    )
    db.add(demande)
    db.commit()
    db.refresh(demande)
    return demande


def get_demande_en_attente(db: Session, id_demande: int) -> DemandeVisiteur:
    demande = db.get(DemandeVisiteur, id_demande)
    if demande is None:
        raise NotFoundError("Demande introuvable")
    if demande.statut_demande != "en_attente":
        raise ConflictError("Demande déjà traitée")
    return demande


def _candidate_places(db: Session, demandeur: Utilisateur, creneau: Creneau) -> list[Place]:
    """Places libres accessibles au visiteur, zones dédiées aux visiteurs d'abord.

    Heuristique d'attribution en deux temps :

    1. Classer les zones par priorité — celles dont une règle d'accès cite
       explicitement le rôle « visiteur », puis celles sans règle (ouvertes à
       tous). Les zones réservées à d'autres profils sont écartées.
    2. Parcourir ces zones dans l'ordre et s'arrêter à la PREMIÈRE qui offre
       au moins une place libre.

    On remplit ainsi les zones visiteurs avant d'entamer les zones communes,
    que l'on préserve pour les étudiants et le personnel.
    """
    zones = db.query(Zone).filter(Zone.zone_active.is_(True)).order_by(Zone.id_zone).all()
    dediees, ouvertes = [], []
    for zone in zones:
        roles = roles_autorises(db, zone.id_zone, creneau.jour)
        if roles is None:
            ouvertes.append(zone)
        elif VISITEUR_ROLE in roles:
            dediees.append(zone)

    candidates: list[Place] = []
    for zone in dediees + ouvertes:
        query = db.query(Place).filter(Place.id_zone == zone.id_zone)
        # Les places PMR ne sont proposées qu'aux personnes concernées, pour
        # ne pas les consommer au détriment de qui en a besoin.
        if not demandeur.besoin_pmr:
            query = query.filter(Place.type_place != "pmr")
        places = query.order_by(Place.numero_place).all()
        libres = places_disponibles(db, places, creneau)
        candidates.extend(place for place in places if place.id_place in libres)
        if candidates:
            break
    return candidates


def valider_demande(
    db: Session, admin: Utilisateur, id_demande: int, payload: DemandeValidation
) -> DemandeVisiteur:
    """Valide une demande : crée la réservation et clôt la demande, en une transaction.

    L'administrateur peut imposer une place précise (`payload.id_place`) ou
    laisser le système choisir parmi les candidates.
    """
    demande = get_demande_en_attente(db, id_demande)
    demandeur = db.get(Utilisateur, demande.id_demandeur)
    roles = {
        row.code_role
        for row in db.query(AttributionRole).filter_by(id_utilisateur=demandeur.id_utilisateur)
    }
    debut, fin = demande.date_visite_souhaitee, demande.date_fin_visite_souhaitee

    if payload.id_place is not None:
        ids_place = [payload.id_place]
    else:
        ids_place = [place.id_place for place in _candidate_places(db, demandeur, Creneau(debut, fin))]
        if not ids_place:
            raise ConflictError("Aucune place disponible pour ce créneau")

    # Essais successifs avec retour arrière : `_candidate_places` s'appuie sur
    # un état lu juste avant, mais `create_reservation` applique des règles
    # supplémentaires (horaires d'ouverture, chevauchements, contrainte
    # d'exclusion en base) et peut refuser une candidate pourtant jugée libre.
    # Plutôt que d'abandonner, on passe à la suivante.
    reservation: Reservation | None = None
    derniere_erreur: ServiceError | None = None
    for id_place in ids_place:
        try:
            # commit=False : la réservation n'est que préparée. Elle ne sera
            # enregistrée qu'avec la mise à jour de la demande, plus bas. Un
            # échec intermédiaire ne laisse donc jamais une réservation
            # orpheline rattachée à une demande restée « en attente ».
            reservation = create_reservation(
                db, demandeur, roles, id_place, debut, fin, via_demande=True, commit=False
            )
            break
        except ServiceError as exc:
            # Mémorisée pour être remontée si AUCUNE candidate n'aboutit :
            # « créneau hors des horaires de la zone » renseigne davantage
            # l'administrateur qu'un générique « aucune place disponible ».
            derniere_erreur = exc
    if reservation is None:
        raise derniere_erreur or ConflictError("Aucune place disponible pour ce créneau")

    demande.statut_demande = "validee"
    demande.id_administrateur = admin.id_utilisateur
    demande.id_reservation = reservation.id_reservation
    demande.date_traitement = _now()
    demande.commentaire_traitement = payload.commentaire_traitement
    db.commit()
    db.refresh(demande)
    return demande


def refuser_demande(
    db: Session, admin: Utilisateur, id_demande: int, payload: DemandeRefus
) -> DemandeVisiteur:
    demande = get_demande_en_attente(db, id_demande)
    demande.statut_demande = "refusee"
    demande.id_administrateur = admin.id_utilisateur
    demande.date_traitement = _now()
    demande.commentaire_traitement = payload.commentaire_traitement
    db.commit()
    db.refresh(demande)
    return demande
