"""Création et envoi des alertes de sécurité sur les canaux choisis par l'utilisateur."""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from . import models
from .alert_channels import send_sms, send_telegram, send_whatsapp
from .delivery import send_email_message
from .security_rules import ALERT_KINDS, alert_message
from .services import notify

DEDUPE_MINUTES = {"failed_attempts": 15, "account_locked": 15, "new_device": 60, "suspicious_activity": 30}


def get_preferences(db: Session, user: models.User) -> models.AlertPreference:
    prefs = db.query(models.AlertPreference).filter_by(user_id=user.id).first()
    if prefs is None:
        prefs = models.AlertPreference(user_id=user.id)       # par défaut : e-mail seulement
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


def raise_alert(db: Session, user: models.User, kind: str, ip: str = "", user_agent: str = "") -> models.SecurityAlert | None:
    since = datetime.utcnow() - timedelta(minutes=DEDUPE_MINUTES.get(kind, 0))
    if kind in DEDUPE_MINUTES and db.query(models.SecurityAlert).filter(
            models.SecurityAlert.user_id == user.id, models.SecurityAlert.kind == kind,
            models.SecurityAlert.created_at >= since).first():
        return None                                           # évite de multiplier les alertes identiques

    message = alert_message(kind, ip=ip)
    title = ALERT_KINDS.get(kind, ("🔐", "Alerte de sécurité"))[1]
    prefs = get_preferences(db, user)
    sent = ["app"]
    notify(db, user.id, f"🔐 {message}")
    if prefs.notify_email and user.email and not user.email.endswith("@phone.invalid"):
        sent.append(f"email:{send_email_message(user.email, f'TalentConnect – {title}', message)}")
    text = f"TalentConnect – {message}"
    if prefs.notify_sms and prefs.phone:
        sent.append(f"sms:{send_sms(prefs.phone, text)}")
    if prefs.notify_whatsapp and prefs.phone:
        sent.append(f"whatsapp:{send_whatsapp(prefs.phone, text)}")
    if prefs.notify_telegram and prefs.telegram_chat_id:
        sent.append(f"telegram:{send_telegram(prefs.telegram_chat_id, text)}")
    alert = models.SecurityAlert(user_id=user.id, kind=kind, message=message, channels=",".join(sent),
                                 ip_address=ip, user_agent=user_agent)
    db.add(alert)
    db.commit()
    return alert
