from app.assistant_logic import generate_cover_letter, reply


def test_salutation_candidat():
    r = reply("Bonjour", "candidate", {"first_name": "Kofi"})
    assert "Kofi" in r["reply"] and r["quick_replies"]


def test_conseils_cv():
    assert "CV" in reply("comment améliorer mon CV ?", "candidate", {})["reply"]


def test_offres_recommandees():
    ctx = {"top_offers": [{"title": "Stage Python", "company": "ACME", "score": 80}]}
    assert "Stage Python" in reply("quelles offres pour moi", "candidate", ctx)["reply"]


def test_lettre_contient_poste():
    txt = generate_cover_letter("Kofi Mensah", "Licence Info", "Stage Python", "ACME", ["python"], ["sql"])
    assert "Stage Python" in txt and "python" in txt and "sql" in txt


def test_visiteur_salutation_et_nom_de_l_assistant():
    r = reply("Bonjour", "visitor", {})
    assert "TConnect IA" in r["reply"] and r["quick_replies"]


def test_visiteur_inscription_mentionne_google_telephone_et_code():
    txt = reply("comment créer un compte ?", "visitor", {})["reply"]
    assert "Google" in txt and "téléphone" in txt and "code" in txt


def test_visiteur_offres_recentes():
    ctx = {"latest_offers": [{"title": "Stage Python", "company": "ACME"}]}
    assert "Stage Python" in reply("je cherche un stage", "visitor", ctx)["reply"]


def test_visiteur_essai_gratuit():
    assert "30 connexions" in reply("c'est gratuit ?", "visitor", {})["reply"]


def test_visiteur_connexions_gratuites_pas_confondu_avec_connexion():
    assert "30 connexions" in reply("Combien de connexions gratuites ?", "visitor", {})["reply"]
