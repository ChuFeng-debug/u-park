import os
import uuid

os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5433")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def make_user(client):
    """Crée un compte directement en base (utile pour les rôles non
    accessibles à l'inscription) et renvoie ses en-têtes d'authentification."""
    from datetime import datetime, timezone

    from app.core.security import hash_password
    from app.db.session import SessionLocal
    from app.models import AttributionRole, Utilisateur

    def _make(role: str = "etudiant", besoin_pmr: bool = False) -> dict[str, str]:
        email = f"test-{uuid.uuid4().hex[:10]}@campus.fr"
        now = datetime.now(timezone.utc)
        with SessionLocal() as db:
            user = Utilisateur(
                email=email,
                mot_de_passe_hash=hash_password("motdepasse123"),
                nom_utilisateur="Test",
                prenom_utilisateur="User",
                statut_compte="actif",
                besoin_pmr=besoin_pmr,
                date_creation_compte=now,
            )
            db.add(user)
            db.flush()
            db.add(
                AttributionRole(
                    id_utilisateur=user.id_utilisateur, code_role=role, date_attribution=now.date()
                )
            )
            db.commit()
        login = client.post("/auth/login", data={"username": email, "password": "motdepasse123"})
        return {"Authorization": f"Bearer {login.json()['access_token']}"}

    return _make
