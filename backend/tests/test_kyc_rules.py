from datetime import date

from app.kyc_rules import (add_months, detect_file_type, missing_documents, required_for,
                           rne_expires_on, rne_is_recent)


def test_documents_requis_par_profil():
    assert required_for("candidate") == ["cin"]
    assert required_for("company") == ["cin_representant", "patente", "extrait_rne"]
    assert required_for("admin") == []


def test_documents_manquants():
    assert missing_documents("company", ["patente"]) == ["cin_representant", "extrait_rne"]
    assert missing_documents("candidate", ["cin"]) == []


def test_type_reel_du_fichier():
    assert detect_file_type(b"%PDF-1.7 ...") == "application/pdf"
    assert detect_file_type(b"\xff\xd8\xff\xe0abc") == "image/jpeg"
    assert detect_file_type(b"\x89PNG\r\n\x1a\nabc") == "image/png"
    assert detect_file_type(b"MZ\x90\x00 programme.exe") is None       # un .exe renommé en .pdf est refusé
    assert detect_file_type(b"") is None


def test_extrait_rne_moins_de_3_mois():
    today = date(2026, 11, 7)
    assert rne_is_recent(date(2026, 10, 1), today)
    assert rne_is_recent(date(2026, 8, 7), today)          # exactement 3 mois : encore valable
    assert not rne_is_recent(date(2026, 8, 6), today)      # 3 mois et 1 jour : refusé
    assert not rne_is_recent(date(2026, 11, 8), today)     # daté du futur : refusé


def test_calcul_des_mois():
    assert add_months(date(2026, 11, 30), 3) == date(2027, 2, 28)
    assert add_months(date(2026, 12, 15), 1) == date(2027, 1, 15)
    assert rne_expires_on(date(2026, 8, 31)) == date(2026, 11, 30)
