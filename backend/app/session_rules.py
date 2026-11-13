"""Règles pures des sessions (sans base de données)."""
from datetime import datetime, timedelta
from typing import Optional


def session_state(now: datetime, expires_at: datetime, last_seen_at: datetime,
                  revoked_at: Optional[datetime], idle_minutes: int) -> str:
    """'ok', 'revoked' (déconnexion ou nouvelle connexion ailleurs), 'expired' (durée maximale) ou 'idle' (inactivité)."""
    if revoked_at is not None:
        return "revoked"
    if now >= expires_at:
        return "expired"
    if now - last_seen_at > timedelta(minutes=idle_minutes):
        return "idle"
    return "ok"


def session_expiry(now: datetime, max_hours: int) -> datetime:
    return now + timedelta(hours=max_hours)


def should_touch(last_seen_at: datetime, now: datetime, seconds: int = 60) -> bool:
    """Évite une écriture en base à chaque requête : la dernière activité est mise à jour au plus 1 fois par minute."""
    return (now - last_seen_at).total_seconds() >= seconds


SESSION_MESSAGES = {
    "revoked": "Vous avez été déconnecté (nouvelle connexion sur un autre appareil ou déconnexion).",
    "expired": "Votre session a expiré. Reconnectez-vous.",
    "idle": "Vous avez été déconnecté après une période d'inactivité.",
}
