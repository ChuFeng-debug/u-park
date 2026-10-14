from datetime import datetime, timezone
from typing import Annotated

from pydantic import PlainSerializer


def _as_utc_iso(value: datetime) -> str:
    # Les colonnes TIMESTAMP stockent de l'UTC sans fuseau : on l'explicite en
    # sortie pour que les clients convertissent correctement en heure locale.
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


UtcDatetime = Annotated[datetime, PlainSerializer(_as_utc_iso, return_type=str)]
