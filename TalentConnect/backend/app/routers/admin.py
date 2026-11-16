from collections import Counter

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..account_rules import STATUSES, STATUS_LABELS
from ..accounts import get_or_create_account
from ..schemas import StatusChangeIn
from ..security import require_role
from ..services import notify
from ..skills import split_skills

router = APIRouter(tags=["Administration"])


@router.get("/public/stats")
def public_stats(db: Session = Depends(get_db)):
    return {
        "offers": db.query(models.JobOffer).filter_by(is_active=True).count(),
        "companies": db.query(models.Company).count(),
        "candidates": db.query(models.Candidate).count(),
    }


@router.get("/admin/stats")
def admin_stats(user: models.User = Depends(require_role(models.Role.admin)),
                db: Session = Depends(get_db)):
    by_status = {s.value: 0 for s in models.ApplicationStatus}
    for status, n in db.query(models.Application.status, func.count()).group_by(models.Application.status):
        by_status[status.value] = n
    avg = db.query(func.avg(models.Application.match_score)).scalar() or 0
    skills = Counter()
    for (raw,) in db.query(models.JobOffer.required_skills).filter_by(is_active=True):
        skills.update(split_skills(raw))
    return {
        "users": db.query(models.User).count(),
        "candidates": db.query(models.Candidate).count(),
        "companies": db.query(models.Company).count(),
        "offers_active": db.query(models.JobOffer).filter_by(is_active=True).count(),
        "offers_stage": db.query(models.JobOffer).filter_by(is_active=True, offer_type=models.OfferType.stage).count(),
        "offers_emploi": db.query(models.JobOffer).filter_by(is_active=True, offer_type=models.OfferType.emploi).count(),
        "applications": db.query(models.Application).count(),
        "applications_by_status": by_status,
        "average_match_score": round(float(avg), 1),
        "top_skills": [{"skill": s, "count": n} for s, n in skills.most_common(8)],
    }


@router.get("/admin/users")
def admin_users(user: models.User = Depends(require_role(models.Role.admin)),
                db: Session = Depends(get_db)):
    users = db.query(models.User).order_by(models.User.created_at.desc()).limit(200).all()
    return [{"id": u.id, "email": u.email, "role": u.role.value,
             "created_at": u.created_at.isoformat() if u.created_at else None} for u in users]


@router.get("/admin/accounts")
def admin_accounts(user: models.User = Depends(require_role(models.Role.admin)),
                   db: Session = Depends(get_db)):
    rows = (db.query(models.UserAccount, models.User).join(models.User, models.User.id == models.UserAccount.user_id)
            .order_by(models.UserAccount.created_at.desc()).limit(200).all())
    return [{"user_id": u.id, "email": u.email, "role": u.role.value, "status": a.status,
             "status_label": STATUS_LABELS.get(a.status, a.status),
             "trial_logins_used": a.trial_logins_used, "trial_limit": a.trial_limit,
             "last_login_at": a.last_login_at} for a, u in rows]


@router.patch("/admin/accounts/{user_id}/status")
def admin_set_status(user_id: int, data: StatusChangeIn,
                     admin: models.User = Depends(require_role(models.Role.admin)),
                     db: Session = Depends(get_db)):
    """Outil de l'étape 1 : changer le statut d'un compte. Le workflow complet
    (KYC, abonnement, paiement) remplacera ce raccourci aux étapes suivantes."""
    if data.status not in STATUSES:
        raise HTTPException(400, f"Statut invalide. Valeurs possibles : {', '.join(STATUSES)}")
    target = db.get(models.User, user_id)
    if not target or target.role == models.Role.admin:
        raise HTTPException(404, "Utilisateur introuvable")
    acc = get_or_create_account(db, target)
    acc.status = data.status
    acc.rejection_reason = data.reason if data.status == "rejected" else ""
    acc.status_changed_at = datetime.utcnow()
    notify(db, target.id, f"Le statut de votre compte est maintenant : {STATUS_LABELS[data.status]}."
           + (f" Motif : {data.reason}" if data.status == "rejected" and data.reason else ""))
    db.commit()
    return {"user_id": target.id, "status": acc.status}
