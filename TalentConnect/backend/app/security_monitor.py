"""Surveillance des connexions : verrouillage temporaire, nouvel appareil, activité suspecte."""
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from . import models
from .alerts import raise_alert
from .security_rules import (FAILURE_WINDOW_MIN, MAX_FAILURES, WARN_AT_FAILURES, distinct_recent_ips,
                             failures_since_last_success, is_new_device, is_suspicious, lock_state)


def _failures(db: Session, identifier: str, now: datetime):
    rows = (db.query(models.LoginAttempt)
            .filter(models.LoginAttempt.identifier == identifier,
                    models.LoginAttempt.created_at >= now - timedelta(minutes=FAILURE_WINDOW_MIN))
            .order_by(models.LoginAttempt.created_at.asc()).all())
    return failures_since_last_success([(r.created_at, r.success) for r in rows], now)


def check_not_locked(db: Session, identifier: str) -> None:
    """À appeler AVANT de vérifier le mot de passe : refuse après trop d'échecs récents."""
    now = datetime.utcnow()
    failures, last = _failures(db, identifier, now)
    locked, remaining = lock_state(failures, last, now)
    if locked:
        minutes = max(1, -(-remaining // 60))
        raise HTTPException(429, f"ACCOUNT_LOCKED: Trop de tentatives échouées. Réessayez dans {minutes} minute(s) "
                                 "ou connectez-vous avec un code reçu par e-mail ou téléphone.")


def record_attempt(db: Session, identifier: str, ip: str, success: bool, user: models.User | None) -> None:
    db.add(models.LoginAttempt(identifier=identifier, ip_address=ip, success=success))
    db.commit()
    if success or user is None:
        return                                    # identifiant inconnu : on compte, mais personne à alerter
    failures, _ = _failures(db, identifier, datetime.utcnow())
    if failures >= MAX_FAILURES:
        raise_alert(db, user, "account_locked", ip)
    elif failures >= WARN_AT_FAILURES:
        raise_alert(db, user, "failed_attempts", ip)


def after_login(db: Session, user: models.User, ip: str, ua: str, replaced: bool) -> None:
    """Après une connexion réussie : détecte un nouvel appareil, une activité suspecte, une session remplacée."""
    now = datetime.utcnow()
    history = (db.query(models.LoginHistory).filter_by(user_id=user.id)
               .order_by(models.LoginHistory.logged_at.desc()).limit(30).all())
    current, previous = history[:1], history[1:]                       # la connexion en cours vient d'être enregistrée
    if replaced:
        raise_alert(db, user, "session_replaced", ip, ua)
    if is_new_device([(h.ip_address, h.user_agent) for h in previous], ip, ua):
        raise_alert(db, user, "new_device", ip, ua)
    events = [(h.logged_at, h.ip_address) for h in current + previous if h.logged_at]
    if is_suspicious(distinct_recent_ips(events, now)):
        raise_alert(db, user, "suspicious_activity", ip, ua)
