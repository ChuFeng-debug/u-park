"""Simulateur de fréquentation : génère un historique de réservations crédible.

Le POC n'a pas de capteurs ni de données réelles ; ce module produit des
réservations fictives sur les parkings du jeu de démonstration pour alimenter
le tableau de bord. Le générateur est déterministe (graine fixe) : deux
exécutions donnent les mêmes chiffres, ce qui permet de vérifier le tableau de
bord contre le jeu de données.

Hypothèses :
- fréquentation selon le jour (forte du lundi au jeudi, plus faible le
  vendredi, quasi nulle le week-end) ;
- arrivées concentrées entre 7 h 30 et 10 h, durées de 3 à 8 h pour les
  étudiants et de 7 à 9 h 30 pour les personnels, parfois une seconde
  réservation l'après-midi sur la même place ;
- environ 8 % d'annulations et 5 % de no-shows sur les créneaux passés.
"""

import random
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import AttributionRole, Place, Reservation, Utilisateur, Zone
from app.services.reservations import roles_autorises

GRAINE = 2026

# Coefficient de fréquentation par jour de la semaine (lundi = 0).
FACTEUR_JOUR = [0.95, 1.0, 0.85, 1.0, 0.75, 0.12, 0.04]
# Taux de remplissage de base selon le public de la zone.
REMPLISSAGE = {"ouverte": 0.85, "personnel": 0.75, "visiteur": 0.4, "pmr": 0.45}
TAUX_ANNULATION = 0.08
TAUX_NO_SHOW = 0.05
PROBA_APRES_MIDI = 0.45

PRENOMS = [
    "Camille", "Lucas", "Inès", "Hugo", "Léa", "Nathan", "Chloé", "Yanis", "Manon", "Adam",
    "Sarah", "Louis", "Emma", "Rayan", "Jade", "Théo", "Lina", "Gabriel", "Zoé", "Mohamed",
    "Clara", "Enzo", "Maëlys", "Noah", "Aya", "Tom", "Anaïs", "Ibrahim", "Julie", "Paul",
]
NOMS = [
    "Martin", "Bernard", "Diallo", "Petit", "Nguyen", "Moreau", "Laurent", "Benali", "Garcia",
    "Roux", "Fontaine", "Traoré", "Mercier", "Lambert", "Bonnet", "Haddad", "Rousseau",
    "Lefèvre", "Da Silva", "Morel", "Fournier", "Mbappé", "Girard", "Chevalier", "Kone",
]


@dataclass
class Population:
    etudiants: list[int]
    etudiants_pmr: list[int]
    personnels: list[int]
    visiteurs: list[int]


def _creer_population(db: Session, mot_de_passe_hash: str, rng: random.Random) -> Population:
    """Comptes fictifs (aucune donnée réelle) qui portent les réservations simulées."""
    effectifs = [
        ("etudiant", 1300, False),
        ("etudiant", 40, True),
        ("personnel", 420, False),
        ("visiteur", 40, False),
    ]
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    groupes: dict[tuple[str, bool], list[int]] = {}
    for role, nombre, pmr in effectifs:
        ids = db.scalars(
            insert(Utilisateur).returning(Utilisateur.id_utilisateur, sort_by_parameter_order=True),
            [
                {
                    "email": f"simu.{role}{'.pmr' if pmr else ''}.{i:04d}@campus.fr",
                    "mot_de_passe_hash": mot_de_passe_hash,
                    "nom_utilisateur": rng.choice(NOMS),
                    "prenom_utilisateur": rng.choice(PRENOMS),
                    "statut_compte": "actif",
                    "besoin_pmr": pmr,
                    "date_creation_compte": now,
                }
                for i in range(nombre)
            ],
        ).all()
        db.execute(
            insert(AttributionRole),
            [
                {"id_utilisateur": id_user, "code_role": role, "date_attribution": now.date()}
                for id_user in ids
            ],
        )
        groupes[(role, pmr)] = list(ids)
    db.flush()
    return Population(
        etudiants=groupes[("etudiant", False)],
        etudiants_pmr=groupes[("etudiant", True)],
        personnels=groupes[("personnel", False)],
        visiteurs=groupes[("visiteur", False)],
    )


def _public(db: Session, zone: Zone, jour: date) -> str:
    roles = roles_autorises(db, zone.id_zone, jour)
    if roles is None:
        return "ouverte"
    if "visiteur" in roles:
        return "visiteur"
    return "personnel"


def _heure_arrivee(rng: random.Random) -> float:
    # Pic d'arrivée vers 8 h 30, quelques arrivées plus tardives.
    return max(7.5, min(rng.gauss(8.75, 0.8), 14.0))


def simuler(
    db: Session,
    mot_de_passe_hash: str,
    jours_passes: int = 60,
    jours_futurs: int = 7,
    places_exclues: set[int] | None = None,
) -> int:
    """Génère l'historique (et quelques jours à venir). Renvoie le nombre de réservations."""
    rng = random.Random(GRAINE)
    tz = ZoneInfo(settings.campus_timezone)
    now_local = datetime.now(tz)
    now_utc = now_local.astimezone(timezone.utc).replace(tzinfo=None)
    places_exclues = places_exclues or set()
    population = _creer_population(db, mot_de_passe_hash, rng)

    zones = db.query(Zone).filter(Zone.zone_active.is_(True)).order_by(Zone.id_zone).all()
    places_par_zone = {
        zone.id_zone: [
            place
            for place in db.query(Place)
            .filter(Place.id_zone == zone.id_zone, Place.etat_place != "hors_service")
            .order_by(Place.id_place)
            if place.id_place not in places_exclues
        ]
        for zone in zones
    }

    def _utc(jour: date, heure: float) -> datetime:
        local = datetime.combine(jour, time.min, tzinfo=tz) + timedelta(hours=heure)
        return local.astimezone(timezone.utc).replace(tzinfo=None)

    lignes: list[dict] = []
    debut_periode = now_local.date() - timedelta(days=jours_passes)
    for offset in range(jours_passes + jours_futurs + 1):
        jour = debut_periode + timedelta(days=offset)
        bruit = rng.uniform(0.9, 1.1)
        # Chaque compte n'est utilisé qu'une fois par jour : pas de chevauchement.
        disponibles = {
            "etudiant": rng.sample(population.etudiants, len(population.etudiants)),
            "pmr": rng.sample(population.etudiants_pmr, len(population.etudiants_pmr)),
            "personnel": rng.sample(population.personnels, len(population.personnels)),
            "visiteur": rng.sample(population.visiteurs, len(population.visiteurs)),
        }

        for zone in zones:
            public = _public(db, zone, jour)
            ouverture = zone.heure_ouverture.hour + zone.heure_ouverture.minute / 60
            fermeture = zone.heure_fermeture.hour + zone.heure_fermeture.minute / 60
            for place in places_par_zone[zone.id_zone]:
                cle = "pmr" if place.type_place == "pmr" else public
                proba = REMPLISSAGE[cle] * FACTEUR_JOUR[jour.weekday()] * bruit
                if rng.random() >= proba:
                    continue
                pool = {"pmr": "pmr", "ouverte": "etudiant"}.get(cle, cle)
                if cle == "ouverte" and rng.random() < 0.15:
                    pool = "personnel"  # des personnels se garent aussi en zone ouverte

                creneaux = []
                debut = max(ouverture, _heure_arrivee(rng))
                duree = rng.uniform(7, 9.5) if pool == "personnel" else rng.uniform(3, 8)
                fin = min(fermeture, debut + duree)
                creneaux.append((debut, fin))
                if fin + 0.5 < fermeture - 1.5 and rng.random() < PROBA_APRES_MIDI:
                    debut2 = fin + rng.uniform(0.5, 1.5)
                    creneaux.append((debut2, min(fermeture, debut2 + rng.uniform(1.5, 4))))

                for debut_h, fin_h in creneaux:
                    if not disponibles[pool]:
                        break
                    id_user = disponibles[pool].pop()
                    date_debut, date_fin = _utc(jour, debut_h), _utc(jour, fin_h)
                    lignes.append(
                        _reservation(rng, id_user, place.id_place, date_debut, date_fin, now_utc)
                    )

    for i in range(0, len(lignes), 5000):
        db.execute(Reservation.__table__.insert(), lignes[i : i + 5000])
    db.flush()
    return len(lignes)


def _reservation(
    rng: random.Random,
    id_user: int,
    id_place: int,
    date_debut: datetime,
    date_fin: datetime,
    now: datetime,
) -> dict:
    creation = date_debut - timedelta(hours=rng.uniform(2, 72))
    ligne = {
        "id_utilisateur": id_user,
        "id_place": id_place,
        "date_debut": date_debut,
        "date_fin": date_fin,
        "statut_reservation": "confirmee",
        "date_creation_resa": min(creation, now),
        "date_annulation": None,
        "motif_annulation": None,
        "date_passage": None,
    }
    tirage = rng.random()
    if tirage < TAUX_ANNULATION:
        ligne["statut_reservation"] = "annulee"
        delai = (date_debut - ligne["date_creation_resa"]) * rng.uniform(0.2, 0.95)
        ligne["date_annulation"] = min(ligne["date_creation_resa"] + delai, now)
        ligne["motif_annulation"] = rng.choice(
            ["Changement d'emploi du temps", "Cours annulé", "Covoiturage", None]
        )
    elif date_debut < now - timedelta(minutes=settings.no_show_delai_minutes):
        if tirage < TAUX_ANNULATION + TAUX_NO_SHOW:
            ligne["statut_reservation"] = "no_show"
        else:
            ligne["date_passage"] = date_debut + timedelta(minutes=rng.uniform(-10, 25))
    return ligne
