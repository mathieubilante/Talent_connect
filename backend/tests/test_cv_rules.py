from app.cv_rules import is_readable, unreadable_message


def test_cv_avec_texte_lisible():
    assert is_readable("Développeur backend : Python, FastAPI, SQL. " * 3)


def test_scan_ou_texte_vide_signale():
    assert not is_readable("")
    assert not is_readable("   \n  ")
    assert not is_readable("CV")


def test_message_explicite():
    assert "scan" in unreadable_message() and "numérique" in unreadable_message()
