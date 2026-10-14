"""Journal des actions importantes (traçabilité).

On n'y écrit que des identifiants techniques et des informations
fonctionnelles courtes : jamais d'email, de nom, de mot de passe ni de
contenu libre saisi par l'utilisateur.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Trace


def journaliser(
    db: Session,
    id_utilisateur: int,
    type_action: str,
    entite_cible: str,
    identifiant_cible: int,
    detail: str | None = None,
) -> None:
    db.add(
        Trace(
            id_utilisateur=id_utilisateur,
            horodatage=datetime.now(timezone.utc).replace(tzinfo=None),
            type_action=type_action,
            entite_cible=entite_cible,
            identifiant_cible=identifiant_cible,
            detail_action=detail[:255] if detail else None,
        )
    )
    db.commit()


def champs_modifies(changes: dict) -> str:
    """Résumé d'une modification : noms des champs seulement, pas les valeurs."""
    return "champs : " + ", ".join(sorted(changes)) if changes else "aucun champ"
