"""Règles pures de la validation administrative (sans base de données)."""
from .kyc_rules import DOC_TYPES

DOC_DECISIONS = ("approved", "rejected")


def can_review_document(doc_status: str) -> bool:
    """Seul un document « envoyé » peut être examiné (pas un document déjà validé ou refusé)."""
    return doc_status == "submitted"


def review_error(decision: str, note: str):
    if decision not in DOC_DECISIONS:
        return "Décision invalide (approved ou rejected)"
    if decision == "rejected" and not (note or "").strip():
        return "Un motif est obligatoire pour refuser un document"
    return None


def validation_blockers(required_types: list, doc_statuses: dict) -> list:
    """Raisons qui empêchent de valider le compte : documents manquants ou pas encore validés."""
    reasons = []
    for t in required_types:
        label = DOC_TYPES.get(t, {}).get("label", t)
        status = doc_statuses.get(t)
        if status is None:
            reasons.append(f"{label} : non fourni")
        elif status != "approved":
            reasons.append(f"{label} : {'refusé' if status == 'rejected' else 'pas encore validé'}")
    return reasons


def account_decision_error(decision: str, reason: str):
    if decision not in ("validate", "reject"):
        return "Décision invalide (validate ou reject)"
    if decision == "reject" and not (reason or "").strip():
        return "Un motif est obligatoire pour refuser un compte"
    return None
