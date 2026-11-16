import re
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..alerts import get_preferences, raise_alert
from ..config import (DEFAULT_COUNTRY_CODE, OTP_DELIVERY, SMTP_HOST, TELEGRAM_BOT_TOKEN, TWILIO_ACCOUNT_SID,
                      TWILIO_AUTH_TOKEN, TWILIO_SMS_FROM, TWILIO_WHATSAPP_FROM)
from ..database import get_db
from ..otp_rules import normalize_phone
from ..security import get_user_unrestricted, require_role
from ..security_rules import ALERT_KINDS, FAILURE_WINDOW_MIN, failures_since_last_success, lock_state

# Accessible même si l'essai est épuisé : la sécurité du compte ne doit jamais être bloquée.
router = APIRouter(prefix="/security", tags=["Sécurité du compte"])
admin_router = APIRouter(prefix="/admin/security", tags=["Sécurité (administration)"])


def _providers() -> dict:
    twilio = bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN)
    return {"email": "smtp" if (OTP_DELIVERY == "smtp" and SMTP_HOST) else "demo",
            "sms": "configured" if (twilio and TWILIO_SMS_FROM) else "demo",
            "whatsapp": "configured" if (twilio and TWILIO_WHATSAPP_FROM) else "demo",
            "telegram": "configured" if TELEGRAM_BOT_TOKEN else "demo"}


def _prefs_out(p: models.AlertPreference) -> dict:
    return {"notify_email": p.notify_email, "notify_sms": p.notify_sms, "notify_whatsapp": p.notify_whatsapp,
            "notify_telegram": p.notify_telegram, "phone": p.phone or "", "telegram_chat_id": p.telegram_chat_id or "",
            "providers": _providers()}


def _alert_out(a: models.SecurityAlert) -> dict:
    icon, title = ALERT_KINDS.get(a.kind, ("🔐", "Alerte"))
    return {"id": a.id, "kind": a.kind, "icon": icon, "title": title, "message": a.message, "channels": a.channels,
            "ip_address": a.ip_address, "created_at": a.created_at}


@router.get("/alerts")
def my_alerts(user: models.User = Depends(get_user_unrestricted), db: Session = Depends(get_db)):
    rows = (db.query(models.SecurityAlert).filter_by(user_id=user.id)
            .order_by(models.SecurityAlert.id.desc()).limit(30).all())
    return [_alert_out(a) for a in rows]


@router.get("/preferences")
def get_prefs(user: models.User = Depends(get_user_unrestricted), db: Session = Depends(get_db)):
    return _prefs_out(get_preferences(db, user))


@router.put("/preferences")
def set_prefs(data: schemas.AlertPrefsIn, user: models.User = Depends(get_user_unrestricted), db: Session = Depends(get_db)):
    phone = ""
    if data.phone.strip():
        phone = normalize_phone(data.phone, DEFAULT_COUNTRY_CODE)
        if not phone:
            raise HTTPException(422, "Numéro de téléphone invalide (ex. +228 90 12 34 56)")
    chat = data.telegram_chat_id.strip()
    if chat and not re.fullmatch(r"-?\d{5,20}", chat):
        raise HTTPException(422, "Identifiant Telegram invalide : il ne contient que des chiffres")
    if (data.notify_sms or data.notify_whatsapp) and not phone:
        raise HTTPException(422, "Indiquez votre numéro de téléphone pour recevoir les alertes par SMS ou WhatsApp")
    if data.notify_telegram and not chat:
        raise HTTPException(422, "Indiquez votre identifiant Telegram pour recevoir les alertes sur Telegram")
    p = get_preferences(db, user)
    p.notify_email, p.notify_sms, p.notify_whatsapp, p.notify_telegram = (
        data.notify_email, data.notify_sms, data.notify_whatsapp, data.notify_telegram)
    p.phone, p.telegram_chat_id, p.updated_at = phone, chat, datetime.utcnow()
    db.commit()
    return _prefs_out(p)


@router.post("/test-alert")
def test_alert(user: models.User = Depends(get_user_unrestricted), db: Session = Depends(get_db)):
    """Envoie une alerte de test sur les canaux activés."""
    alert = raise_alert(db, user, "test")
    return _alert_out(alert)


@admin_router.get("")
def admin_security(admin: models.User = Depends(require_role(models.Role.admin)), db: Session = Depends(get_db)):
    now = datetime.utcnow()
    recent = (db.query(models.LoginAttempt).filter(models.LoginAttempt.created_at >= now - timedelta(minutes=FAILURE_WINDOW_MIN))
              .order_by(models.LoginAttempt.created_at.asc()).all())
    by_ident = {}
    for r in recent:
        by_ident.setdefault(r.identifier, []).append((r.created_at, r.success))
    locked = []
    for ident, attempts in by_ident.items():
        failures, last = failures_since_last_success(attempts, now)
        is_locked, remaining = lock_state(failures, last, now)
        if is_locked:
            locked.append({"identifier": ident, "failures": failures, "remaining_seconds": remaining})
    alerts = (db.query(models.SecurityAlert, models.User).join(models.User, models.User.id == models.SecurityAlert.user_id)
              .order_by(models.SecurityAlert.id.desc()).limit(40).all())
    failed_24h = (db.query(models.LoginAttempt).filter(models.LoginAttempt.success.is_(False),
                                                       models.LoginAttempt.created_at >= now - timedelta(hours=24)).count())
    return {"locked": locked, "failed_last_24h": failed_24h, "providers": _providers(),
            "alerts": [{**_alert_out(a), "email": u.email} for a, u in alerts]}


@admin_router.post("/unlock")
def unlock(data: schemas.UnlockIn, admin: models.User = Depends(require_role(models.Role.admin)),
           db: Session = Depends(get_db)):
    """Débloque un identifiant verrouillé (efface ses tentatives récentes)."""
    ident = data.identifier.strip().lower()
    n = (db.query(models.LoginAttempt).filter(models.LoginAttempt.identifier == ident,
                                              models.LoginAttempt.created_at >= datetime.utcnow() - timedelta(minutes=FAILURE_WINDOW_MIN))
         .delete(synchronize_session=False))
    db.commit()
    return {"identifier": ident, "cleared": n}
