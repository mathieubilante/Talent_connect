from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..account_rules import trial_info
from ..accounts import account_payload, get_or_create_account
from ..database import get_db
from ..security import get_user_unrestricted

router = APIRouter(prefix="/account", tags=["Compte"])


@router.get("/me", response_model=schemas.AccountOut)
def my_account(user: models.User = Depends(get_user_unrestricted), db: Session = Depends(get_db)):
    if user.role == models.Role.admin:
        return schemas.AccountOut(**trial_info("active", 0, 0), last_login_at=None)
    return schemas.AccountOut(**account_payload(get_or_create_account(db, user)))


@router.get("/login-history")
def login_history(user: models.User = Depends(get_user_unrestricted), db: Session = Depends(get_db)):
    rows = (db.query(models.LoginHistory).filter_by(user_id=user.id)
            .order_by(models.LoginHistory.logged_at.desc()).limit(20).all())
    return [{"logged_at": r.logged_at, "ip_address": r.ip_address,
             "user_agent": r.user_agent, "counted": r.counted} for r in rows]
