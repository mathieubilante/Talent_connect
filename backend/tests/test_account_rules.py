from app.account_rules import trial_info


def test_pas_de_limite_de_connexions():
    assert trial_info("pending", 1)["access_allowed"]
    assert trial_info("pending", 30)["access_allowed"]
    assert trial_info("pending", 500)["access_allowed"]
    assert not trial_info("pending", 500)["trial_exhausted"]


def test_compte_actif_et_valide_ont_acces():
    assert trial_info("active", 30)["access_allowed"]
    assert trial_info("validated", 30)["access_allowed"]


def test_compte_refuse_bloque():
    assert not trial_info("rejected", 3)["access_allowed"]


def test_fin_de_la_periode_d_utilisation():
    from datetime import datetime, timedelta
    from app.account_rules import subscription_required
    now = datetime(2026, 11, 25)
    assert not subscription_required("pending", now - timedelta(days=13), now)
    assert subscription_required("pending", now - timedelta(days=14), now)
    assert subscription_required("validated", now - timedelta(days=30), now)
    assert not subscription_required("active", now - timedelta(days=400), now)
    assert not subscription_required("rejected", now - timedelta(days=400), now)
