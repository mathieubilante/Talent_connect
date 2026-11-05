from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..account_rules import trial_info
from ..accounts import account_payload, get_or_create_account, record_login
from ..config import DEFAULT_COUNTRY_CODE, OTP_DEV_MODE
from ..database import get_db
from ..otp import check_otp, create_and_send_otp
from ..otp_rules import RESEND_DELAY_SECONDS, mask_contact, normalize_phone, parse_identifier
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentification"])


def _client(request: Request) -> tuple[str, str]:
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or \
         (request.client.host if request.client else "")
    return ip[:64], request.headers.get("user-agent", "")[:255]


def _token(user: models.User, acc) -> schemas.TokenOut:
    return schemas.TokenOut(access_token=create_access_token(user.id, user.role.value),
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
    return _token(user, record_login(db, user, ip, ua))   # compte comme la 1re connexion d'essai


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
    user = _find_user(db, form.username)
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Identifiant ou mot de passe incorrect")
    contact = _contact(db, user)
    if contact is not None and not contact.verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "NOT_VERIFIED: Votre compte n'est pas encore vérifié. Saisissez le code reçu.")
    if user.role != models.Role.admin:
        acc = get_or_create_account(db, user)
        if acc.status == "rejected":
            info = trial_info(acc.status, acc.trial_logins_used, acc.trial_limit)
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"ACCOUNT_REJECTED: {info['message']}")
    ip, ua = _client(request)
    return _token(user, record_login(db, user, ip, ua))
