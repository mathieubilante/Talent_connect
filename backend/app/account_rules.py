"""Règles métier des comptes : statuts et essai gratuit limité à 30 connexions.

Module volontairement sans dépendance (pas de base de données) pour être testé facilement.
Pour changer la règle (ex. autoriser la 30e session complète), modifier UNIQUEMENT ce fichier.
"""

TRIAL_LIMIT = 30          # connexions d'essai au total (pas une durée)
ALERT_THRESHOLD = 5       # alerte quand il reste 5 connexions ou moins

STATUSES = ("pending", "validated", "active", "rejected")
STATUS_LABELS = {
    "pending": "En attente",
    "validated": "Validé",
    "active": "Actif",
    "rejected": "Refusé",
}


def trial_info(status: str, used: int, limit: int = TRIAL_LIMIT) -> dict:
    remaining = max(limit - used, 0)
    exhausted = status != "active" and used >= limit
    allowed = status == "active" or (status != "rejected" and not exhausted)
    alert = status != "active" and not exhausted and remaining <= ALERT_THRESHOLD

    if status == "active":
        message = "Compte actif : accès complet."
    elif status == "rejected":
        message = "Votre compte a été refusé après vérification. Contactez l'administration."
    elif exhausted:
        message = (f"Vos {limit} connexions d'essai sont épuisées. Validez votre compte "
                   "(documents d'identité) et souscrivez un abonnement pour continuer.")
    elif alert:
        message = f"Attention : il vous reste {remaining} connexion(s) d'essai sur {limit}."
    else:
        message = f"Essai gratuit : {used} connexion(s) utilisée(s), {remaining} restante(s) sur {limit}."

    return {
        "status": status,
        "status_label": STATUS_LABELS.get(status, status),
        "trial_logins_used": used,
        "trial_limit": limit,
        "trial_remaining": remaining,
        "trial_exhausted": exhausted,
        "access_allowed": allowed,
        "alert": alert,
        "message": message,
    }
