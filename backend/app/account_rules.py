"""Règles du compte.

Période d'utilisation : chaque compte peut utiliser la plateforme pendant TRIAL_DAYS jours à partir de sa création.
Passé ce délai, sans abonnement actif, les fonctions sont suspendues et l'application propose l'abonnement.
La durée est réglable par la variable TRIAL_DAYS (par défaut 14).

Statuts : pending (en attente de validation des documents), validated (validé), active (abonné), rejected (refusé).
Un compte refusé n'a pas accès. Les autres comptes ont accès ; les fonctions réservées sont gérées par leur propre règle
(validation des documents pour l'abonnement, limite d'offres pour les entreprises non abonnées).
"""

import os
from datetime import datetime, timedelta

TRIAL_DAYS = int(os.getenv("TRIAL_DAYS", "14"))
TRIAL_LIMIT = 30          # conservé pour compatibilité de la base ; n'est plus appliqué
ALERT_THRESHOLD = 5       # conservé pour compatibilité ; n'est plus utilisé

STATUSES = ("pending", "validated", "active", "rejected")
STATUS_LABELS = {
    "pending": "En attente",
    "validated": "Validé",
    "active": "Actif",
    "rejected": "Refusé",
}


def trial_info(status: str, used: int, limit: int = TRIAL_LIMIT) -> dict:
    allowed = status != "rejected"
    if status == "active":
        message = "Compte actif."
    elif status == "validated":
        message = "Compte validé. Vous pouvez souscrire un abonnement."
    elif status == "rejected":
        message = "Votre compte a été refusé après vérification. Contactez l'administration."
    else:
        message = "Compte en attente de validation : envoyez vos documents d'identité."
    return {
        "status": status,
        "status_label": STATUS_LABELS.get(status, status),
        "trial_logins_used": used,
        "trial_limit": limit,
        "trial_remaining": 0,
        "trial_exhausted": False,
        "access_allowed": allowed,
        "alert": False,
        "message": message,
    }


def trial_ends_at(created_at: datetime) -> datetime:
    return created_at + timedelta(days=TRIAL_DAYS)


def subscription_required(status: str, created_at, now: datetime) -> bool:
    """True si la période d'utilisation est terminée et que le compte n'est pas abonné."""
    if status == "active" or status == "rejected" or created_at is None:
        return False
    return now >= trial_ends_at(created_at)
