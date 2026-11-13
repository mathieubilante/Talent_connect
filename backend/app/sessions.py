"""Sessions : une seule session active par utilisateur, expiration, inactivité, déconnexion."""
import uuid
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import models
from .config import SESSION_IDLE_MINUTES, SESSION_MAX_HOURS
from .session_rules import SESSION_MESSAGES, session_expiry, session_state, should_touch


def start_session(db: Session, user: models.User, ip: str, user_agent: str):
    now = datetime.utcnow()
    # la connexion depuis un nouvel appareil ferme automatiquement la session précédente
    replaced = (db.query(models.UserSession).filter(models.UserSession.user_id == user.id,
                                                    models.UserSession.revoked_at.is_(None),
                                                    models.UserSession.expires_at > now)
                .update({"revoked_at": now, "revoked_reason": "new_login"}, synchronize_session=False))
    sid = str(uuid.uuid4())
    db.add(models.UserSession(id=sid, user_id=user.id, created_at=now, last_seen_at=now,
                              expires_at=session_expiry(now, SESSION_MAX_HOURS), ip_address=ip, user_agent=user_agent))
    db.commit()
    return sid, replaced > 0          # (identifiant de la nouvelle session, une session précédente a-t-elle été fermée ?)


def end_session(db: Session, sid: str, reason: str = "logout") -> None:
    db.query(models.UserSession).filter_by(id=sid, revoked_at=None).update(
        {"revoked_at": datetime.utcnow(), "revoked_reason": reason}, synchronize_session=False)
    db.commit()


def validate_session(db: Session, sid: str, user_id: int) -> None:
    """Lève une erreur 401 « SESSION_xxx » si la session est fermée, expirée ou inactive depuis trop longtemps."""
    s = db.get(models.UserSession, sid)
    if not s or s.user_id != user_id:
        raise HTTPException(401, "SESSION_REVOKED: " + SESSION_MESSAGES["revoked"])
    now = datetime.utcnow()
    state = session_state(now, s.expires_at, s.last_seen_at, s.revoked_at, SESSION_IDLE_MINUTES)
    if state != "ok":
        raise HTTPException(401, f"SESSION_{state.upper()}: {SESSION_MESSAGES[state]}")
    if should_touch(s.last_seen_at, now):
        s.last_seen_at = now
        db.commit()
