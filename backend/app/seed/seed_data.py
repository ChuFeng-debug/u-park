"""Génère un jeu de données de démonstration pour le POC U-Park.

Usage : python -m app.seed.seed_data
Réinitialise les tables métier (hors `role`, déjà peuplée par Alembic)
et recrée un jeu de données cohérent pour une démonstration de bout en
bout sur les profils étudiant, personnel, visiteur et administrateur.
"""

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import (
    AttributionRole,
    CibleRole,
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

        parking_nord = Parking(
            nom_parking="Parking Nord",
            localisation_parking="Entrée Nord du campus",
            description_parking="Proche des amphithéâtres",
        )
        parking_sud = Parking(
            nom_parking="Parking Sud",
            localisation_parking="Entrée Sud du campus",
            description_parking="Proche de la bibliothèque",
        )
        db.add_all([parking_nord, parking_sud])
        db.flush()

        zone_standard = Zone(
            id_parking=parking_nord.id_parking,
            nom_zone="Zone A - Standard",
            capacite_theorique=4,
            heure_ouverture=time(7, 0),
            heure_fermeture=time(20, 0),
            zone_active=True,
        )
        zone_pmr = Zone(
            id_parking=parking_nord.id_parking,
            nom_zone="Zone PMR",
            capacite_theorique=2,
            heure_ouverture=time(7, 0),
            heure_fermeture=time(20, 0),
            zone_active=True,
        )
        zone_visiteurs = Zone(
            id_parking=parking_sud.id_parking,
            nom_zone="Zone Visiteurs",
            capacite_theorique=3,
            heure_ouverture=time(8, 0),
            heure_fermeture=time(18, 0),
            zone_active=True,
        )
        zone_bloquee = Zone(
            id_parking=parking_sud.id_parking,
            nom_zone="Zone Travaux",
            capacite_theorique=2,
            heure_ouverture=time(7, 0),
            heure_fermeture=time(20, 0),
            zone_active=False,
        )
        db.add_all([zone_standard, zone_pmr, zone_visiteurs, zone_bloquee])
        db.flush()

        places = [
            Place(id_zone=zone_standard.id_zone, numero_place="A1", type_place="standard", etat_place="libre"),
            Place(id_zone=zone_standard.id_zone, numero_place="A2", type_place="standard", etat_place="libre"),
            Place(id_zone=zone_standard.id_zone, numero_place="A3", type_place="electrique", etat_place="libre"),
            Place(id_zone=zone_standard.id_zone, numero_place="A4", type_place="standard", etat_place="hors_service"),
            Place(id_zone=zone_pmr.id_zone, numero_place="P1", type_place="pmr", etat_place="libre"),
            Place(id_zone=zone_pmr.id_zone, numero_place="P2", type_place="pmr", etat_place="libre"),
            Place(id_zone=zone_visiteurs.id_zone, numero_place="V1", type_place="standard", etat_place="libre"),
            Place(id_zone=zone_visiteurs.id_zone, numero_place="V2", type_place="standard", etat_place="occupee"),
            Place(id_zone=zone_visiteurs.id_zone, numero_place="V3", type_place="moto", etat_place="libre"),
            Place(id_zone=zone_bloquee.id_zone, numero_place="T1", type_place="standard", etat_place="libre"),
            Place(id_zone=zone_bloquee.id_zone, numero_place="T2", type_place="standard", etat_place="libre"),
        ]
        db.add_all(places)
        db.flush()

        today = date.today()
        regle_pmr = RegleAcces(
            id_zone=zone_pmr.id_zone,
            libelle_regle="Priorité PMR",
            niveau_priorite=1,
            date_debut_validite=today,
            regle_active=True,
        )
        regle_personnel = RegleAcces(
            id_zone=zone_standard.id_zone,
            libelle_regle="Priorité personnel",
            niveau_priorite=2,
            date_debut_validite=today,
            regle_active=True,
        )
        regle_visiteurs = RegleAcces(
            id_zone=zone_visiteurs.id_zone,
            libelle_regle="Réservé visiteurs",
            niveau_priorite=3,
            date_debut_validite=today,
            regle_active=True,
        )
        db.add_all([regle_pmr, regle_personnel, regle_visiteurs])
        db.flush()
        db.add_all(
            [
                CibleRole(id_regle=regle_pmr.id_regle, code_role="etudiant"),
                CibleRole(id_regle=regle_pmr.id_regle, code_role="personnel"),
                CibleRole(id_regle=regle_personnel.id_regle, code_role="personnel"),
                CibleRole(id_regle=regle_visiteurs.id_regle, code_role="visiteur"),
            ]
        )

        now = datetime.now(timezone.utc)
        db.add_all(
            [
                Reservation(
                    id_utilisateur=etudiant.id_utilisateur,
                    id_place=places[0].id_place,
                    date_debut=now + timedelta(hours=1),
                    date_fin=now + timedelta(hours=4),
                    statut_reservation="confirmee",
                    date_creation_resa=now,
                ),
                Reservation(
                    id_utilisateur=pmr_etudiant.id_utilisateur,
                    id_place=places[4].id_place,
                    date_debut=now + timedelta(hours=2),
                    date_fin=now + timedelta(hours=6),
                    statut_reservation="confirmee",
                    date_creation_resa=now,
                ),
                Reservation(
                    id_utilisateur=visiteur.id_utilisateur,
                    id_place=places[6].id_place,
                    date_debut=now - timedelta(days=1, hours=3),
                    date_fin=now - timedelta(days=1),
                    statut_reservation="annulee",
                    date_creation_resa=now - timedelta(days=1, hours=4),
                    date_annulation=now - timedelta(days=1, hours=1),
                    motif_annulation="Changement de programme",
                ),
            ]
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
