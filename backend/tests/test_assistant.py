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
