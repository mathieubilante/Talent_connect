import uuid
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models
from .accounts import get_or_create_account
from .billing_rules import PLAN_QUOTAS, can_checkout, receipt_number, subscription_end, workspace_slug
from .config import PAYMENT_PROVIDER
from .pricing import PLANS, compute_quote
from .services import notify


def start_checkout(db: Session, user: models.User, plan_code: str, months: int):
    acc = get_or_create_account(db, user)
    ok, reason = can_checkout(acc.status)
    if not ok:
        raise HTTPException(409, reason)
    plan = PLANS.get(plan_code)
    if not plan or plan["role"] != user.role.value:
        raise HTTPException(400, "Cette offre d'abonnement n'est pas disponible pour votre profil")
    try:
        quote = compute_quote(plan_code, months)      # le prix est calculé ici, jamais envoyé par le navigateur
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    # une seule tentative en attente à la fois
    db.query(models.Payment).filter_by(user_id=user.id, status="pending").update({"status": "cancelled"})
    db.query(models.Subscription).filter_by(user_id=user.id, status="pending").update({"status": "cancelled"})

    sub = models.Subscription(user_id=user.id, plan_code=plan_code, months=months,
                              amount=quote["total"], currency=quote["currency"])
    db.add(sub)
    db.flush()
    pay = models.Payment(user_id=user.id, subscription_id=sub.id, provider=PAYMENT_PROVIDER,
                         provider_ref=uuid.uuid4().hex, amount=quote["total"], currency=quote["currency"])
    db.add(pay)
    db.commit()
    db.refresh(pay)
    return pay, quote


def _latest_active_end(db: Session, user_id: int, exclude_id: int) -> Optional[datetime]:
    return (db.query(func.max(models.Subscription.ends_at))
            .filter(models.Subscription.user_id == user_id, models.Subscription.status == "active",
                    models.Subscription.id != exclude_id).scalar())


def ensure_workspace(db: Session, user: models.User, plan_code: str) -> models.Workspace:
    quota = PLAN_QUOTAS[plan_code]
    ws = db.query(models.Workspace).filter_by(user_id=user.id).first()
    if ws is None:
        if user.role == models.Role.company and user.company:
            name = user.company.name
        elif user.candidate:
            name = f"{user.candidate.first_name} {user.candidate.last_name}".strip()
        else:
            name = ""
        name = name or user.email
        ws = models.Workspace(user_id=user.id, name=f"Espace {name}", slug=workspace_slug(name, user.id),
                              kind=user.role.value, plan_code=plan_code, storage_mb=quota["storage_mb"],
                              max_active_offers=quota["max_active_offers"])
        db.add(ws)
    else:
        ws.plan_code, ws.storage_mb, ws.max_active_offers = plan_code, quota["storage_mb"], quota["max_active_offers"]
    return ws


def complete_payment(db: Session, user: models.User, payment_id: int, success: bool, reason: str = ""):
    pay = db.get(models.Payment, payment_id)
    if not pay or pay.user_id != user.id:
        raise HTTPException(404, "Paiement introuvable")
    # verrou atomique : un paiement ne peut être traité qu'une seule fois, même en cas de double clic
    claimed = (db.query(models.Payment).filter_by(id=pay.id, status="pending")
               .update({"status": "paid" if success else "failed"}, synchronize_session=False))
    if claimed == 0:
        db.rollback()
        raise HTTPException(409, "Ce paiement a déjà été traité")
    db.refresh(pay)
    sub = db.get(models.Subscription, pay.subscription_id)
    now = datetime.utcnow()

    if not success:
        pay.failure_reason = reason or "Paiement refusé"
        sub.status = "cancelled"
        notify(db, user.id, "Votre paiement a échoué : aucun montant n'a été débité. Vous pouvez réessayer.")
        db.commit()
        return pay

    current_end = _latest_active_end(db, user.id, sub.id)          # renouvellement : on prolonge
    start = current_end if current_end and current_end > now else now
    sub.starts_at, sub.ends_at, sub.status = start, subscription_end(start, sub.months), "active"
    pay.paid_at, pay.receipt_number = now, receipt_number(now.year, pay.id)
    acc = get_or_create_account(db, user)
    acc.status, acc.rejection_reason, acc.status_changed_at = "active", "", now
    ensure_workspace(db, user, sub.plan_code)
    notify(db, user.id, f"Paiement reçu ({pay.amount} {pay.currency}). Votre compte est actif jusqu'au "
                        f"{sub.ends_at.strftime('%d/%m/%Y')} et votre espace dédié est prêt. Reçu {pay.receipt_number}.")
    db.commit()
    return pay


def refresh_subscription(db: Session, user: models.User) -> None:
    """Passe les abonnements échus à « expired » et remet le compte à « validé » s'il n'a plus d'abonnement en cours.
    Un compte activé manuellement (sans abonnement) n'est jamais rétrogradé."""
    now = datetime.utcnow()
    subs = db.query(models.Subscription).filter_by(user_id=user.id).all()
    changed = False
    for s in subs:
        if s.status == "active" and s.ends_at and s.ends_at <= now:
            s.status, changed = "expired", True
    ever_paid = any(s.status in ("active", "expired") for s in subs)
    running = any(s.status == "active" and s.ends_at and s.ends_at > now for s in subs)
    acc = get_or_create_account(db, user)
    if acc.status == "active" and ever_paid and not running:
        acc.status, acc.status_changed_at, changed = "validated", now, True
        notify(db, user.id, "Votre abonnement a expiré. Renouvelez-le pour retrouver l'accès complet.")
    if changed:
        db.commit()
