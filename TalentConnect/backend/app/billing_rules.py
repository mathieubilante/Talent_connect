"""Règles pures de l'abonnement (sans base de données, donc faciles à tester)."""
import re
import unicodedata
from datetime import datetime
from typing import Optional

from .kyc_rules import add_months

TRIAL_MAX_OFFERS = 3     # une entreprise en essai peut publier 3 offres actives ; l'abonnement lève la limite

PLAN_QUOTAS = {
    "candidat_premium": {"storage_mb": 200, "max_active_offers": None},
    "entreprise_pro": {"storage_mb": 2000, "max_active_offers": 50},
}


def subscription_end(start: datetime, months: int) -> datetime:
    d = add_months(start.date(), months)
    return datetime.combine(d, start.time())


def can_checkout(account_status: str):
    """(autorisé, raison). L'abonnement se souscrit une fois le compte validé ; un compte actif peut renouveler."""
    if account_status in ("validated", "active"):
        return True, ""
    if account_status == "rejected":
        return False, "Votre compte a été refusé : l'abonnement n'est pas disponible."
    return False, "Votre compte doit d'abord être validé : envoyez vos documents d'identité."


def offer_limit(account_status: str, role: str) -> Optional[int]:
    """Nombre maximum d'offres actives, ou None si illimité."""
    if role == "company" and account_status != "active":
        return TRIAL_MAX_OFFERS
    return None


def receipt_number(year: int, payment_id: int) -> str:
    return f"REC-{year}-{payment_id:06d}"


def workspace_slug(name: str, user_id: int) -> str:
    base = unicodedata.normalize("NFD", name.lower())
    base = "".join(c for c in base if unicodedata.category(c) != "Mn")
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")[:40] or "espace"
    return f"{base}-{user_id}"
