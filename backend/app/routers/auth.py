import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..account_rules import trial_info
from ..accounts import account_payload, get_or_create_account, record_login
from ..config import DEFAULT_COUNTRY_CODE, GOOGLE_CLIENT_ID, OTP_DEV_MODE
from ..database import get_db
from ..google_auth import verify_google_credential
from ..otp import check_otp, create_and_send_otp
from ..otp_rules import RESEND_DELAY_SECONDS, mask_contact, normalize_phone, parse_identifier
from ..config import SESSION_IDLE_MINUTES
from ..security import (create_access_token, current_sid, hash_password, oauth2_scheme,
                        verify_password)
from ..security_monitor import after_login, check_not_locked, record_attempt
from ..sessions import end_session, start_session

router = APIRouter(prefix="/auth", tags=["Authentification"])


def _client(request: Request) -> tuple[str, str]:
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or \
         (request.client.host if request.client else "")
    return ip[:64], request.headers.get("user-agent", "")[:255]


def _session_token(db: Session, user: models.User, acc, ip: str, ua: str) -> schemas.TokenOut:
    """Ouvre une session (la précédente est fermée) et retourne le jeton qui lui est lié."""
    sid, replaced = start_session(db, user, ip, ua)
    if user.role != models.Role.admin:
        after_login(db, user, ip, ua, replaced)        # alertes : nouvel appareil, activité suspecte, session remplacée
    return schemas.TokenOut(access_token=create_access_token(user.id, user.role.value, sid),
                            role=user.role,
                            account=schemas.AccountOut(**account_payload(acc)) if acc else None)


def _find_user(db: Session, identifier: str):
    """Retrouve un utilisateur par e-mail ou par numéro de téléphone."""
    kind, value = parse_identifier(identifier, DEFAULT_COUNTRY_CODE)
    if kind == "email":
        return db.query(models.User).filter(func.lower(models.User.email) == value).first()
    if kind == "phone":
        contact = db.query(models.UserContact).filter_by(phone=value).first()
        return db.get(models.User, contact.user_id) if contact else None
    return None


def _contact(db: Session, user: models.User):
    return db.query(models.UserContact).filter_by(user_id=user.id).first()


def _verification_out(channel: str, destination: str, info: dict) -> schemas.VerificationOut:
    return schemas.VerificationOut(channel=channel, destination_masked=mask_contact(channel, destination),
                                   delivery=info["delivery"], expires_in_seconds=info["expires_in_seconds"],
                                   resend_after_seconds=info["resend_after_seconds"], dev_code=info["dev_code"])


@router.post("/register", response_model=schemas.VerificationOut, status_code=201)
def register(data: schemas.RegisterIn, db: Session = Depends(get_db)):
    """Étape 1 de l'inscription : crée le compte (non vérifié) et envoie un code OTP."""
    if data.role == models.Role.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Création d'un admin non autorisée")

    if data.channel == "email":
        destination = data.email.lower()
        email, phone = destination, None
    else:
        phone = normalize_phone(data.phone, DEFAULT_COUNTRY_CODE)
        if not phone:
            raise HTTPException(422, "Numéro de téléphone invalide (ex. +228 90 12 34 56)")
        destination = phone
        email = f"tel{phone[1:]}@phone.invalid"   # e-mail technique : la colonne email est obligatoire

    user = _find_user(db, destination)
    if user:
        contact = _contact(db, user)
        if contact is None or contact.verified:
            raise HTTPException(status.HTTP_409_CONFLICT, "Ce compte existe déjà. Connectez-vous.")
        user.password_hash = hash_password(data.password)   # inscription non terminée : on la reprend
        db.commit()
    else:
        user = models.User(email=email, password_hash=hash_password(data.password), role=data.role)
        db.add(user)
        db.flush()
        if data.role == models.Role.candidate:
            parts = data.name.split(" ", 1)
            db.add(models.Candidate(user_id=user.id, first_name=parts[0],
                                    last_name=parts[1] if len(parts) > 1 else ""))
        else:
            db.add(models.Company(user_id=user.id, name=data.name))
        db.add(models.UserContact(user_id=user.id, phone=phone, channel=data.channel, verified=False))
        db.commit()

    info = create_and_send_otp(db, user, data.channel, destination)
    return _verification_out(data.channel, destination, info)


@router.post("/verify-otp", response_model=schemas.TokenOut)
def verify_otp(data: schemas.VerifyOtpIn, request: Request, db: Session = Depends(get_db)):
    """Étape 2 : vérifie le code ; si correct, le compte est vérifié et la session s'ouvre."""
    user = _find_user(db, data.identifier)
    contact = _contact(db, user) if user else None
    if not user or contact is None:
        raise HTTPException(400, "Code incorrect ou expiré.")
    if contact.verified:
        raise HTTPException(400, "Ce compte est déjà vérifié. Connectez-vous.")
    check_otp(db, user, contact, data.code.strip())
    ip, ua = _client(request)
    return _session_token(db, user, record_login(db, user, ip, ua), ip, ua)   # compte comme la 1re connexion d'essai


@router.post("/resend-otp")
def resend_otp(data: schemas.ResendOtpIn, db: Session = Depends(get_db)):
    """Renvoie un code (délai de 60 s entre deux envois, 5 par heure). Réponse neutre pour
    ne pas révéler si un compte existe."""
    user = _find_user(db, data.identifier)
    contact = _contact(db, user) if user else None
    result = {"message": "Si un compte en attente existe, un nouveau code vient d'être envoyé.",
              "resend_after_seconds": RESEND_DELAY_SECONDS, "dev_code": None}
    if user and contact and not contact.verified:
        destination = contact.phone if contact.channel == "phone" else user.email
        info = create_and_send_otp(db, user, contact.channel, destination)
        result["dev_code"] = info["dev_code"] if OTP_DEV_MODE else None
    return result


@router.post("/login", response_model=schemas.TokenOut)
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(),
          db: Session = Depends(get_db)):
    ip, ua = _client(request)
    ident = (form.username or "").strip().lower()
    check_not_locked(db, ident)                      # trop d'échecs récents : 429
    user = _find_user(db, form.username)
    if not user or not verify_password(form.password, user.password_hash):
        record_attempt(db, ident, ip, False, user)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Identifiant ou mot de passe incorrect")
    record_attempt(db, ident, ip, True, user)
    contact = _contact(db, user)
    if contact is not None and not contact.verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "NOT_VERIFIED: Votre compte n'est pas encore vérifié. Saisissez le code reçu.")
    if user.role != models.Role.admin:
        acc = get_or_create_account(db, user)
        if acc.status == "rejected":
            msg = account_payload(acc)["message"]
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"ACCOUNT_REJECTED: {msg}")
    return _session_token(db, user, record_login(db, user, ip, ua), ip, ua)


def _ensure_not_rejected(db: Session, user: models.User) -> None:
    if user.role != models.Role.admin:
        acc = get_or_create_account(db, user)
        if acc.status == "rejected":
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"ACCOUNT_REJECTED: {account_payload(acc)['message']}")


@router.get("/config")
def public_config():
    """Réglages publics utiles au site (identifiant Google pour afficher le bouton)."""
    return {"google_client_id": GOOGLE_CLIENT_ID or "", "session_idle_minutes": SESSION_IDLE_MINUTES}


@router.post("/google", response_model=schemas.TokenOut)
def google_login(data: schemas.GoogleLoginIn, request: Request, db: Session = Depends(get_db)):
    """Connexion ou inscription avec Google. L'adresse Google étant vérifiée par Google, aucun code OTP n'est demandé."""
    info = verify_google_credential(data.credential)
    email = info["email"].lower()
    user = db.query(models.User).filter(func.lower(models.User.email) == email).first()
    now = datetime.utcnow()
    if user and user.role == models.Role.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Les administrateurs se connectent avec leur mot de passe.")
    if not user:
        user = models.User(email=email, password_hash=hash_password(secrets.token_urlsafe(32)),
                           role=models.Role(data.role))
        db.add(user)
        db.flush()
        name = info.get("name") or email.split("@")[0]
        if data.role == "candidate":
            parts = name.split(" ", 1)
            db.add(models.Candidate(user_id=user.id, first_name=parts[0],
                                    last_name=parts[1] if len(parts) > 1 else ""))
        else:
            db.add(models.Company(user_id=user.id, name=name))
        db.add(models.UserContact(user_id=user.id, channel="email", verified=True, verified_at=now))
    else:
        contact = _contact(db, user)
        if contact is None:
            db.add(models.UserContact(user_id=user.id, channel="email", verified=True, verified_at=now))
        elif not contact.verified:
            contact.verified, contact.verified_at = True, now
    db.commit()
    _ensure_not_rejected(db, user)
    ip, ua = _client(request)
    return _session_token(db, user, record_login(db, user, ip, ua), ip, ua)


@router.post("/otp/request")
def otp_login_request(data: schemas.OtpRequestIn, db: Session = Depends(get_db)):
    """Connexion sans mot de passe, étape 1 : envoie un code à l'e-mail ou au téléphone d'un compte existant."""
    result = {"message": "Si un compte existe pour cet identifiant, un code vient d'être envoyé.",
              "resend_after_seconds": RESEND_DELAY_SECONDS, "dev_code": None}
    kind, value = parse_identifier(data.identifier, DEFAULT_COUNTRY_CODE)
    user = _find_user(db, data.identifier)
    if user and kind and user.role != models.Role.admin:
        if _contact(db, user) is None:   # compte historique : son e-mail est considéré vérifié
            db.add(models.UserContact(user_id=user.id, channel="email", verified=True,
                                      verified_at=datetime.utcnow()))
            db.commit()
        info = create_and_send_otp(db, user, kind, value)
        result["dev_code"] = info["dev_code"] if OTP_DEV_MODE else None
    return result


@router.post("/otp/login", response_model=schemas.TokenOut)
def otp_login(data: schemas.OtpLoginIn, request: Request, db: Session = Depends(get_db)):
    """Connexion sans mot de passe, étape 2 : vérifie le code reçu et ouvre la session."""
    user = _find_user(db, data.identifier)
    contact = _contact(db, user) if user else None
    if not user or contact is None or user.role == models.Role.admin:
        raise HTTPException(400, "Code incorrect ou expiré.")
    check_otp(db, user, contact, data.code.strip())
    _ensure_not_rejected(db, user)
    ip, ua = _client(request)
    return _session_token(db, user, record_login(db, user, ip, ua), ip, ua)


@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Ferme la session : le jeton devient inutilisable immédiatement."""
    sid = current_sid(token)
    if sid:
        end_session(db, sid, "logout")
    return {"ok": True}
