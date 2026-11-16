from datetime import date

from app.profile_rules import age_on, birth_date_error, image_type, initials, missing_candidate_fields


def test_champs_obligatoires():
    assert missing_candidate_fields({"first_name": "Kofi", "last_name": "Mensah"}) == [
        "date de naissance", "établissement", "activité"]
    assert missing_candidate_fields({"first_name": "A", "last_name": "B", "birth_date": date(2005, 1, 1),
                                     "school": "ENP", "occupation": "Étudiant"}) == []


def test_age_exact_et_anniversaire():
    assert age_on(date(2005, 11, 17), date(2026, 11, 16)) == 20      # anniversaire pas encore passé
    assert age_on(date(2005, 11, 16), date(2026, 11, 16)) == 21


def test_date_de_naissance_validee():
    today = date(2026, 11, 16)
    assert birth_date_error(None, today) is None
    assert "futur" in birth_date_error(date(2027, 1, 1), today)
    assert "15 ans" in birth_date_error(date(2015, 1, 1), today)
    assert birth_date_error(date(2000, 5, 5), today) is None
    assert "Vérifiez" in birth_date_error(date(1900, 1, 1), today)


def test_type_reel_de_la_photo():
    assert image_type(b"\xff\xd8\xff\xe0abc") == "jpg"
    assert image_type(b"\x89PNG\r\n\x1a\nabc") == "png"
    assert image_type(b"RIFF\x00\x00\x00\x00WEBPVP8 ") == "webp"
    assert image_type(b"<script>alert(1)</script>") is None
    assert image_type(b"GIF89a") is None


def test_initiales():
    assert initials("Kofi", "Mensah") == "KM"
    assert initials("", "", "?") == "?"
    assert initials("marie claire", "d'almeida") == "MC"
