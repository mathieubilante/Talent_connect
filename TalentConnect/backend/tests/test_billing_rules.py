from datetime import datetime

import pytest

from app.billing_rules import (can_checkout, offer_limit, receipt_number, subscription_end, workspace_slug)
from app.pricing import compute_quote


def test_devis_calcule_cote_serveur():
    q = compute_quote("entreprise_pro", 12)
    assert q["subtotal"] == 180000 and q["discount_percent"] == 20 and q["total"] == 144000
    assert q["discount_amount"] == 36000
    assert compute_quote("candidat_premium", 1)["total"] == 2000


def test_devis_refuse_les_valeurs_invalides():
    with pytest.raises(ValueError):
        compute_quote("offre_inconnue", 1)
    with pytest.raises(ValueError):
        compute_quote("candidat_premium", 5)


def test_fin_d_abonnement():
    assert subscription_end(datetime(2026, 11, 10, 9, 30), 3) == datetime(2027, 2, 10, 9, 30)
    assert subscription_end(datetime(2026, 11, 30, 8, 0), 3) == datetime(2027, 2, 28, 8, 0)   # fin de mois
    assert subscription_end(datetime(2026, 12, 15, 8, 0), 12) == datetime(2027, 12, 15, 8, 0)


def test_souscription_seulement_apres_validation():
    assert can_checkout("validated")[0] and can_checkout("active")[0]
    assert not can_checkout("pending")[0] and "documents" in can_checkout("pending")[1]
    assert not can_checkout("rejected")[0]


def test_limite_d_offres_pendant_l_essai():
    assert offer_limit("pending", "company") == 3 and offer_limit("validated", "company") == 3
    assert offer_limit("active", "company") is None
    assert offer_limit("pending", "candidate") is None


def test_numero_de_recu_et_slug():
    assert receipt_number(2026, 42) == "REC-2026-000042"
    assert workspace_slug("Togo Digital Solutions", 7) == "togo-digital-solutions-7"
    assert workspace_slug("Société Générale d'Étude", 3) == "societe-generale-d-etude-3"
    assert workspace_slug("???", 9) == "espace-9"
