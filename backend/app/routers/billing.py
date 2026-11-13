from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..accounts import account_payload, get_or_create_account
from ..billing import complete_payment, refresh_subscription, start_checkout
from ..billing_rules import can_checkout
from ..config import PAYMENT_PROVIDER
from ..database import get_db
from ..pricing import DISCOUNT_PERCENT_BY_MONTHS, PLAN_FEATURES, PLANS, compute_quote
from ..security import get_user_unrestricted, require_role

# Accessible même si l'essai est épuisé : c'est justement là qu'on s'abonne.
router = APIRouter(prefix="/billing", tags=["Abonnement et paiement"])
admin_router = APIRouter(prefix="/admin/billing", tags=["Paiements (administration)"])


def _not_admin(user: models.User) -> None:
    if user.role == models.Role.admin:
        raise HTTPException(403, "Les administrateurs n'ont pas d'abonnement")


def _sub_out(s):
    plan = PLANS.get(s.plan_code, {})
    return {"id": s.id, "plan_code": s.plan_code, "label": plan.get("label", s.plan_code), "months": s.months,
            "amount": s.amount, "currency": s.currency, "status": s.status, "starts_at": s.starts_at, "ends_at": s.ends_at}


def _pay_out(p):
    return {"id": p.id, "amount": p.amount, "currency": p.currency, "status": p.status, "provider": p.provider,
            "receipt_number": p.receipt_number, "created_at": p.created_at, "paid_at": p.paid_at,
            "failure_reason": p.failure_reason or ""}


@router.get("/plans")
def plans(user: models.User = Depends(get_user_unrestricted), db: Session = Depends(get_db)):
    _not_admin(user)
    acc = get_or_create_account(db, user)
    ok, reason = can_checkout(acc.status)
    result = []
    for code, plan in PLANS.items():
        if plan["role"] != user.role.value:
            continue
        result.append({"code": code, "label": plan["label"], "monthly": plan["monthly"],
                       "features": PLAN_FEATURES.get(code, []),
                       "quotes": [compute_quote(code, m) for m in DISCOUNT_PERCENT_BY_MONTHS]})
    return {"plans": result, "account_status": acc.status, "can_checkout": ok, "reason": reason,
            "provider": PAYMENT_PROVIDER}


@router.post("/checkout")
def checkout(data: schemas.CheckoutIn, user: models.User = Depends(get_user_unrestricted), db: Session = Depends(get_db)):
    _not_admin(user)
    pay, quote = start_checkout(db, user, data.plan_code, data.months)
    return {"payment_id": pay.id, "provider": pay.provider, "provider_ref": pay.provider_ref,
            "amount": pay.amount, "currency": pay.currency, "quote": quote}


@router.post("/payments/{payment_id}/simulate")
def simulate(payment_id: int, data: schemas.SimulatePaymentIn,
             user: models.User = Depends(get_user_unrestricted), db: Session = Depends(get_db)):
    """Paiement de démonstration : n'existe que tant que PAYMENT_PROVIDER=simulated."""
    _not_admin(user)
    if PAYMENT_PROVIDER != "simulated":
        raise HTTPException(404, "Le paiement simulé est désactivé")
    pay = complete_payment(db, user, payment_id, data.outcome == "success", data.reason)
    return {"payment": _pay_out(pay), "account": account_payload(get_or_create_account(db, user))}


@router.get("/me")
def my_billing(user: models.User = Depends(get_user_unrestricted), db: Session = Depends(get_db)):
    _not_admin(user)
    refresh_subscription(db, user)
    acc = get_or_create_account(db, user)
    subs = db.query(models.Subscription).filter_by(user_id=user.id).order_by(models.Subscription.id.desc()).all()
    current = next((s for s in subs if s.status == "active"), None)
    pays = (db.query(models.Payment).filter_by(user_id=user.id).order_by(models.Payment.id.desc()).limit(30).all())
    ws = db.query(models.Workspace).filter_by(user_id=user.id).first()
    return {"account": account_payload(acc),
            "subscription": _sub_out(current) if current else None,
            "payments": [_pay_out(p) for p in pays],
            "workspace": ({"name": ws.name, "slug": ws.slug, "kind": ws.kind, "plan_code": ws.plan_code,
                           "storage_mb": ws.storage_mb, "max_active_offers": ws.max_active_offers,
                           "created_at": ws.created_at} if ws else None)}


@router.get("/receipt/{payment_id}")
def receipt(payment_id: int, user: models.User = Depends(get_user_unrestricted), db: Session = Depends(get_db)):
    pay = db.get(models.Payment, payment_id)
    if not pay or (pay.user_id != user.id and user.role != models.Role.admin) or pay.status != "paid":
        raise HTTPException(404, "Reçu introuvable")
    sub = db.get(models.Subscription, pay.subscription_id)
    owner = db.get(models.User, pay.user_id)
    name = (owner.company.name if owner.company else
            f"{owner.candidate.first_name} {owner.candidate.last_name}".strip() if owner.candidate else owner.email)
    return {"number": pay.receipt_number, "date": pay.paid_at, "customer": name or owner.email, "email": owner.email,
            "plan": PLANS.get(sub.plan_code, {}).get("label", sub.plan_code), "months": sub.months,
            "period_start": sub.starts_at, "period_end": sub.ends_at, "amount": pay.amount,
            "currency": pay.currency, "provider": pay.provider, "reference": pay.provider_ref}


@admin_router.get("")
def admin_billing(admin: models.User = Depends(require_role(models.Role.admin)), db: Session = Depends(get_db)):
    paid = db.query(models.Payment).filter_by(status="paid")
    total = db.query(func.coalesce(func.sum(models.Payment.amount), 0)).filter_by(status="paid").scalar()
    by_plan = {}
    for code, amount in (db.query(models.Subscription.plan_code, models.Payment.amount)
                         .join(models.Payment, models.Payment.subscription_id == models.Subscription.id)
                         .filter(models.Payment.status == "paid")):
        row = by_plan.setdefault(code, {"plan": PLANS.get(code, {}).get("label", code), "count": 0, "amount": 0})
        row["count"] += 1
        row["amount"] += amount
    last = (db.query(models.Payment, models.User).join(models.User, models.User.id == models.Payment.user_id)
            .order_by(models.Payment.id.desc()).limit(30).all())
    now = datetime.utcnow()
    return {"total_paid": int(total or 0), "paid_count": paid.count(), "currency": "XOF",
            "active_subscriptions": db.query(models.Subscription).filter(models.Subscription.status == "active",
                                                                         models.Subscription.ends_at > now).count(),
            "by_plan": list(by_plan.values()),
            "payments": [{**_pay_out(p), "email": u.email} for p, u in last]}
