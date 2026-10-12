"""Génère un jeu de données de démonstration pour le POC U-Park.

Usage : python -m app.seed.seed_data
Réinitialise les tables métier (hors `role`, déjà peuplée par Alembic)
et recrée un jeu de données cohérent pour une démonstration de bout en
bout sur les profils étudiant, personnel, visiteur et administrateur.
"""

import math
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import (
    AttributionRole,
    CibleRole,
    DemandeVisiteur,
    Incident,
    Parking,
    Place,
    RegleAcces,
    Reservation,
    Utilisateur,
    Zone,
)

DEMO_PASSWORD = "motdepasse123"

TABLES_TO_RESET = [
    "demande_visiteur",
    "incident",
    "blocage",
    "reservation",
    "cible_role",
    "place",
    "regle_acces",
    "zone",
    "parking",
    "attribution_role",
    "trace",
    "utilisateur",
]


def _reset(db: Session) -> None:
    db.execute(text(f"TRUNCATE TABLE {', '.join(TABLES_TO_RESET)} RESTART IDENTITY CASCADE"))
    db.commit()


def _create_user(
    db: Session,
    *,
    email: str,
    prenom: str,
    nom: str,
    role_code: str,
    besoin_pmr: bool = False,
) -> Utilisateur:
    now = datetime.now(timezone.utc)
    user = Utilisateur(
        email=email,
        mot_de_passe_hash=hash_password(DEMO_PASSWORD),
        nom_utilisateur=nom,
        prenom_utilisateur=prenom,
        statut_compte="actif",
        besoin_pmr=besoin_pmr,
        date_creation_compte=now,
    )
    db.add(user)
    db.flush()
    db.add(
        AttributionRole(
            id_utilisateur=user.id_utilisateur, code_role=role_code, date_attribution=now.date()
        )
    )
    return user

# Parkings réels du campus de Marne-la-Vallée (Cité Descartes).
# Source : https://www.univ-gustave-eiffel.fr/menu-footer/acces-aux-batiments-campus-de-marne-la-vallee
# (capacités et publics consultés le 2026-10-12). Hypothèses du POC, faute
# de données publiques : horaires 7h-20h, 2 % de places PMR par zone,
# 20 places du parking aérien Copernic réservées aux visiteurs, zone IUT
# à accès contrôlé bloquée pour la démonstration.
SOURCE = "Source : univ-gustave-eiffel.fr, accès aux bâtiments (Cité Descartes)"
OUVERTURE, FERMETURE = time(7, 0), time(20, 0)
PART_PMR = 0.02

# (clé, nom de zone, code de place, capacité, rôles autorisés ou None = tous, active)
CAMPUS = [
    {
        "nom": "Parking Copernic",
        "localisation": "5 boulevard Descartes, 77420 Champs-sur-Marne",
        "zones": [
            ("copernic_souterrain", "Souterrain (personnels)", "CS", 96, ["personnel"], True),
            ("copernic_aerien", "Aérien", "CA", 236, None, True),
            ("copernic_visiteurs", "Aérien - visiteurs", "CV", 20, ["visiteur"], True),
        ],
    },
    {
        "nom": "Parking Lavoisier",
        "localisation": "Rue Galilée, 77420 Champs-sur-Marne",
        "zones": [("lavoisier", "Souterrain", "LS", 168, None, True)],
    },
    {
        "nom": "Parking Clément Ader",
        "localisation": "Boulevard Descartes, 77420 Champs-sur-Marne",
        "zones": [("clement_ader", "Aérien", "CD", 105, None, True)],
    },
    {
        "nom": "Parking Bibliothèque François Rabelais",
        "localisation": "Boulevard Descartes, 77420 Champs-sur-Marne",
        "zones": [("rabelais", "Personnels", "BR", 114, ["personnel"], True)],
    },
    {
        "nom": "Parking IUT de Champs-sur-Marne",
        "localisation": "2 rue Albert Einstein, 77420 Champs-sur-Marne",
        "zones": [
            ("iut_souterrain", "Souterrain", "IS", 124, None, True),
            ("iut_aerien", "Aérien", "IA", 80, None, True),
            ("iut_controle", "Aérien - accès contrôlé", "IC", 15, ["personnel"], False),
        ],
    },
    {
        "nom": "Parking Alexandra David-Néel",
        "localisation": "2 allée du Promontoire, 93160 Noisy-le-Grand",
        "zones": [
            ("david_neel_aerien", "Aérien", "DA", 55, None, True),
            ("david_neel_souterrain", "Souterrain (personnels)", "DS", 40, ["personnel"], True),
        ],
    },
]


def _create_campus(db: Session, today: date) -> dict[str, Zone]:
    zones: dict[str, Zone] = {}
    for site in CAMPUS:
        parking = Parking(
            nom_parking=site["nom"],
            localisation_parking=site["localisation"],
            description_parking=SOURCE,
        )
        db.add(parking)
        db.flush()
        for key, nom_zone, code, capacite, roles, active in site["zones"]:
            zone = Zone(
                id_parking=parking.id_parking,
                nom_zone=nom_zone,
                capacite_theorique=capacite,
                heure_ouverture=OUVERTURE,
                heure_fermeture=FERMETURE,
                zone_active=active,
            )
            db.add(zone)
            db.flush()
            zones[key] = zone

            nb_pmr = math.ceil(capacite * PART_PMR)
            db.add_all(
                Place(
                    id_zone=zone.id_zone,
                    numero_place=f"{code}-{numero:03d}",
                    type_place="pmr" if numero <= nb_pmr else "standard",
                    etat_place="libre",
                )
                for numero in range(1, capacite + 1)
            )

            if roles:
                regle = RegleAcces(
                    id_zone=zone.id_zone,
                    libelle_regle=f"Réservé : {', '.join(roles)}",
                    niveau_priorite=1,
                    date_debut_validite=today,
                    regle_active=True,
                )
                db.add(regle)
                db.flush()
                db.add_all(CibleRole(id_regle=regle.id_regle, code_role=role) for role in roles)
    db.flush()
    return zones


def seed() -> None:
    db = SessionLocal()
    try:
        _reset(db)

        etudiant = _create_user(
            db, email="alice.etudiante@campus.fr", prenom="Alice", nom="Durand", role_code="etudiant"
        )
        pmr_etudiant = _create_user(
            db,
            email="karim.pmr@campus.fr",
            prenom="Karim",
            nom="Haddad",
            role_code="etudiant",
            besoin_pmr=True,
        )
        personnel = _create_user(
            db, email="marc.personnel@campus.fr", prenom="Marc", nom="Lefevre", role_code="personnel"
        )
        visiteur = _create_user(
            db, email="julie.visiteuse@campus.fr", prenom="Julie", nom="Petit", role_code="visiteur"
        )
        admin = _create_user(
            db, email="admin@campus.fr", prenom="Sofia", nom="Admin", role_code="administrateur"
        )
        db.flush()

        today = date.today()
        zones = _create_campus(db, today)

        # Une place libre d'une zone donnée (hors PMR sauf demande).
        def _place(zone_key: str, type_place: str = "standard") -> Place:
            return (
                db.query(Place)
                .filter_by(id_zone=zones[zone_key].id_zone, type_place=type_place)
                .order_by(Place.id_place)
                .first()
            )

        tz = ZoneInfo(settings.campus_timezone)
        demain = today + timedelta(days=1)
        hier = today - timedelta(days=1)

        def _utc(jour: date, heure: int) -> datetime:
            local = datetime.combine(jour, time(heure), tzinfo=tz)
            return local.astimezone(timezone.utc).replace(tzinfo=None)

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        db.add_all(
            [
                Reservation(
                    id_utilisateur=etudiant.id_utilisateur,
                    id_place=_place("copernic_aerien").id_place,
                    date_debut=_utc(demain, 8),
                    date_fin=_utc(demain, 12),
                    statut_reservation="confirmee",
                    date_creation_resa=now,
                ),
                Reservation(
                    id_utilisateur=pmr_etudiant.id_utilisateur,
                    id_place=_place("lavoisier", "pmr").id_place,
                    date_debut=_utc(demain, 9),
                    date_fin=_utc(demain, 17),
                    statut_reservation="confirmee",
                    date_creation_resa=now,
                ),
                Reservation(
                    id_utilisateur=personnel.id_utilisateur,
                    id_place=_place("copernic_souterrain").id_place,
                    date_debut=_utc(demain, 8),
                    date_fin=_utc(demain, 18),
                    statut_reservation="confirmee",
                    date_creation_resa=now,
                ),
                Reservation(
                    id_utilisateur=visiteur.id_utilisateur,
                    id_place=_place("copernic_visiteurs").id_place,
                    date_debut=_utc(hier, 14),
                    date_fin=_utc(hier, 17),
                    statut_reservation="annulee",
                    date_creation_resa=_utc(hier, 9),
                    date_annulation=_utc(hier, 11),
                    motif_annulation="Changement de programme",
                ),
            ]
        )

        db.add(
            DemandeVisiteur(
                id_demandeur=visiteur.id_utilisateur,
                date_demande=now,
                date_visite_souhaitee=_utc(demain, 14),
                date_fin_visite_souhaitee=_utc(demain, 17),
                motif_demande="Intervention en jury de soutenance",
                statut_demande="en_attente",
            )
        )
        db.add(
            Incident(
                id_zone=zones["lavoisier"].id_zone,
                id_utilisateur_signalement=etudiant.id_utilisateur,
                description_incident="Éclairage en panne au niveau -1, côté rampe d'accès",
                priorite_incident="moyenne",
                statut_incident="ouvert",
                date_signalement=now,
            )
        )

        db.commit()

        print("Jeu de données de démonstration créé.")
        print(f"Comptes de démo (mot de passe : {DEMO_PASSWORD}) :")
        print(f"  - étudiant       : {etudiant.email}")
        print(f"  - étudiant PMR   : {pmr_etudiant.email}")
        print(f"  - personnel      : {personnel.email}")
        print(f"  - visiteur       : {visiteur.email}")
        print(f"  - administrateur : {admin.email}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
