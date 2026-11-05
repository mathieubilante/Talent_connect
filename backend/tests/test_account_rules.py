from app.account_rules import trial_info


def test_debut_essai():
    i = trial_info("pending", 1)
    assert i["trial_remaining"] == 29 and i["access_allowed"] and not i["alert"]


def test_alerte_a_5_restantes():
    i = trial_info("pending", 25)
    assert i["trial_remaining"] == 5 and i["alert"] and i["access_allowed"]


def test_30e_connexion_suspend_l_essai():
    i = trial_info("pending", 30)
    assert i["trial_exhausted"] and not i["access_allowed"] and "épuisées" in i["message"]


def test_compteur_jamais_negatif():
    assert trial_info("pending", 45)["trial_remaining"] == 0


def test_compte_actif_sans_limite():
    i = trial_info("active", 30)
    assert i["access_allowed"] and not i["trial_exhausted"] and not i["alert"]


def test_compte_refuse_bloque():
    assert not trial_info("refused" if False else "rejected", 3)["access_allowed"]


def test_valide_reste_limite_par_l_essai():
    assert not trial_info("validated", 30)["access_allowed"]
