"""Tarifs et devis calculés UNIQUEMENT côté serveur : le navigateur n'envoie jamais un prix, seulement un code d'offre
et une durée. (Valeurs de démonstration à confirmer avec l'entreprise.)"""

CURRENCY = "XOF"   # franc CFA : pas de centimes, montants entiers
PLANS = {
    "candidat_premium": {"label": "Candidat Premium", "role": "candidate", "monthly": 2000},
    "entreprise_pro": {"label": "Entreprise Pro", "role": "company", "monthly": 15000},
}
DISCOUNT_PERCENT_BY_MONTHS = {1: 0, 3: 5, 6: 10, 12: 20}


def compute_quote(plan_code: str, months: int) -> dict:
    if plan_code not in PLANS:
        raise ValueError("Offre d'abonnement inconnue")
    if months not in DISCOUNT_PERCENT_BY_MONTHS:
        raise ValueError("Durée invalide (1, 3, 6 ou 12 mois)")
    unit = PLANS[plan_code]["monthly"]
    discount = DISCOUNT_PERCENT_BY_MONTHS[months]
    subtotal = unit * months
    total = subtotal * (100 - discount) // 100
    return {"plan": plan_code, "label": PLANS[plan_code]["label"], "months": months, "currency": CURRENCY,
            "unit_price": unit, "subtotal": subtotal, "discount_percent": discount,
            "discount_amount": subtotal - total, "total": total}


PLAN_FEATURES = {
    "candidat_premium": ["Candidatures illimitées", "Lettre de motivation générée par TConnect IA", "Alertes sur les nouvelles offres",
                         "Stockage de 200 Mo pour vos documents"],
    "entreprise_pro": ["Jusqu'à 50 offres actives", "Talents recommandés par l'IA pour chaque offre", "Statistiques de candidatures",
                       "Stockage de 2 000 Mo"],
}
