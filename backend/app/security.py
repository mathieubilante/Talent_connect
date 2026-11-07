from datetime import datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import models
from .account_rules import trial_info
from .accounts import account_payload, get_or_create_account
from .config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from .database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "role": role, "exp": expire},
                      SECRET_KEY, algorithm=ALGORITHM)


def get_user_unrestricted(token: str = Depends(oauth2_scheme),
                          db: Session = Depends(get_db)) -> models.User:
    """Utilisateur authentifié, SANS contrôle du statut du compte.
    Réservé à /account/* et aux notifications, pour qu'un essai épuisé puisse voir son état."""
    error = HTTPException(status.HTTP_401_UNAUTHORIZED, "Identifiants invalides",
                          headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = db.get(models.User, int(payload["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise error
    if not user:
        raise error
    return user


def get_current_user(user: models.User = Depends(get_user_unrestricted),
                     db: Session = Depends(get_db)) -> models.User:
    """Utilisateur authentifié ET autorisé (compte actif, ou essai non épuisé)."""
    if user.role == models.Role.admin:
        return user
    acc = get_or_create_account(db, user)
    info = trial_info(acc.status, acc.trial_logins_used, acc.trial_limit)
    info["message"] = account_payload(acc)["message"]
    if not info["access_allowed"]:
        code = "ACCOUNT_REJECTED" if acc.status == "rejected" else "TRIAL_EXPIRED"
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"{code}: {info['message']}")
    now = datetime.utcnow()  # dernière activité (écriture limitée à 1 fois par minute)
    if acc.last_activity_at is None or (now - acc.last_activity_at).total_seconds() > 60:
        acc.last_activity_at = now
        db.commit()
    return user


def require_role(*roles: models.Role):
    def checker(user: models.User = Depends(get_current_user)) -> models.User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès refusé pour ce rôle")
        return user
    return checker
