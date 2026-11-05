from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.orm import Session

from . import models
from .config import OTP_DEV_MODE, SECRET_KEY
from .delivery import deliver_otp
from .otp_rules import (MAX_ATTEMPTS, MAX_SENDS_PER_HOUR, OTP_TTL_SECONDS, RESEND_DELAY_SECONDS,
                        generate_code, hash_code, is_expired, seconds_until_resend, verify_code)


def create_and_send_otp(db: Session, user: models.User, channel: str, destination: str) -> dict:
    now = datetime.utcnow()
    last = (db.query(models.OtpCode).filter_by(user_id=user.id)
            .order_by(models.OtpCode.created_at.desc()).first())
    wait = seconds_until_resend(last.created_at if last else None, now)
    if wait > 0:
        raise HTTPException(429, f"Veuillez patienter {wait} seconde(s) avant de demander un nouveau code.")
    sent_last_hour = (db.query(models.OtpCode)
                      .filter(models.OtpCode.user_id == user.id,
                              models.OtpCode.created_at >= now - timedelta(hours=1)).count())
    if sent_last_hour >= MAX_SENDS_PER_HOUR:
        raise HTTPException(429, "Trop de demandes de code. Réessayez dans une heure.")

    db.query(models.OtpCode).filter_by(user_id=user.id, consumed=False).update({"consumed": True})
    code = generate_code()
    db.add(models.OtpCode(user_id=user.id, channel=channel, destination=destination,
                          code_hash=hash_code(SECRET_KEY, user.id, code),
                          expires_at=now + timedelta(seconds=OTP_TTL_SECONDS),
                          max_attempts=MAX_ATTEMPTS))
    db.commit()
    delivery = deliver_otp(channel, destination, code)
    return {"delivery": delivery, "expires_in_seconds": OTP_TTL_SECONDS,
            "resend_after_seconds": RESEND_DELAY_SECONDS,
            "dev_code": code if OTP_DEV_MODE else None}


def check_otp(db: Session, user: models.User, contact: models.UserContact, code: str) -> None:
    """Vérifie le code ; lève une erreur HTTP sinon. Marque le contact comme vérifié si correct."""
    otp = (db.query(models.OtpCode).filter_by(user_id=user.id, consumed=False)
           .order_by(models.OtpCode.created_at.desc()).first())
    now = datetime.utcnow()
    if not otp:
        raise HTTPException(400, "Aucun code actif. Demandez un nouveau code.")
    if is_expired(otp.expires_at, now):
        raise HTTPException(400, "Ce code a expiré. Demandez un nouveau code.")
    if otp.attempts >= otp.max_attempts:
        raise HTTPException(429, "Trop d'essais incorrects. Demandez un nouveau code.")

    if not verify_code(SECRET_KEY, user.id, code, otp.code_hash):
        db.execute(update(models.OtpCode).where(models.OtpCode.id == otp.id)
                   .values(attempts=models.OtpCode.attempts + 1)
                   .execution_options(synchronize_session=False))
        db.commit()
        remaining = max(otp.max_attempts - otp.attempts - 1, 0)
        raise HTTPException(400, f"Code incorrect. Il reste {remaining} essai(s).")

    otp.consumed = True
    contact.verified = True
    contact.verified_at = now
    db.commit()
