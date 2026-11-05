from datetime import datetime

from sqlalchemy import update
from sqlalchemy.orm import Session

from . import models
from .account_rules import ALERT_THRESHOLD, TRIAL_LIMIT, trial_info
from .services import notify


def get_or_create_account(db: Session, user: models.User) -> models.UserAccount:
    acc = db.query(models.UserAccount).filter_by(user_id=user.id).first()
    if not acc:
        acc = models.UserAccount(user_id=user.id, status="pending", trial_limit=TRIAL_LIMIT)
        db.add(acc)
        db.commit()
        db.refresh(acc)
    return acc


def account_payload(acc: models.UserAccount) -> dict:
    data = trial_info(acc.status, acc.trial_logins_used, acc.trial_limit)
    data["last_login_at"] = acc.last_login_at
    return data


def record_login(db: Session, user: models.User, ip: str, user_agent: str):
    """Enregistre une connexion réussie et consomme une connexion d'essai si nécessaire.

    Le compteur est incrémenté par un UPDATE atomique côté base (avec condition
    « compteur < limite ») : impossible à contourner par déconnexion, changement
    d'appareil ou de navigateur, même avec des connexions simultanées.
    """
    now = datetime.utcnow()
    if user.role == models.Role.admin:
        db.add(models.LoginHistory(user_id=user.id, ip_address=ip, user_agent=user_agent, counted=False))
        db.commit()
        return None

    acc = get_or_create_account(db, user)
    counted = False
    if acc.status != "active":
        result = db.execute(
            update(models.UserAccount)
            .where(models.UserAccount.id == acc.id,
                   models.UserAccount.trial_logins_used < models.UserAccount.trial_limit)
            .values(trial_logins_used=models.UserAccount.trial_logins_used + 1)
            .execution_options(synchronize_session=False))
        counted = result.rowcount == 1

    db.add(models.LoginHistory(user_id=user.id, ip_address=ip, user_agent=user_agent, counted=counted))
    db.commit()
    db.refresh(acc)
    acc.last_login_at = now
    acc.last_activity_at = now

    if counted:
        remaining = acc.trial_limit - acc.trial_logins_used
        if remaining == 0:
            notify(db, user.id, f"Vos {acc.trial_limit} connexions d'essai sont épuisées. "
                                "Validez votre compte et souscrivez un abonnement pour continuer.")
        elif remaining <= ALERT_THRESHOLD:
            notify(db, user.id, f"Il vous reste {remaining} connexion(s) d'essai gratuit.")
    db.commit()
    db.refresh(acc)
    return acc
