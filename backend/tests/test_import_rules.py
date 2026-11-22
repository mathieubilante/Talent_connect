from datetime import date

from app.import_rules import detect_format, missing_headers, parse_deadline, read_csv, validate_row

TODAY = date(2026, 11, 19)


def test_format_reel_du_fichier():
    assert detect_format(b"titre,type\nA,stage\n") == "csv"
    assert detect_format("titre;type\n".encode("utf-8-sig")) == "csv"
    assert detect_format(b"PK\x03\x04rest") == "xlsx"
    assert detect_format(b"MZ\x90\x00\x03\x00") is None          # exécutable renommé en .csv : refusé
    assert detect_format(b"\xff\xfe\x00\x01") is None


def test_lecture_csv_avec_point_virgule_et_bom():
    headers, rows = read_csv("Titre;Description;Type\nStage Python;Développement d'API REST;stage\n".encode("utf-8-sig"))
    assert headers == ["titre", "description", "type"]
    assert rows[0][0] == 2 and rows[0][1]["titre"] == "Stage Python"
    assert missing_headers(headers) == []
    assert missing_headers(["titre"]) == ["description", "type"]


def test_ligne_valide_normalisee():
    offer, errors = validate_row({"titre": "Stage Python", "description": "Développement d'API REST",
                                  "type": "STAGE", "competences": "python;sql, docker", "lieu": "Lomé",
                                  "date_limite": "2027-01-31"}, TODAY)
    assert errors == [] and offer["offer_type"] == "stage"
    assert offer["required_skills"] == "python, sql, docker" and offer["deadline"] == date(2027, 1, 31)


def test_erreurs_detaillees():
    _, errors = validate_row({"titre": "X", "description": "court", "type": "autre", "date_limite": "2020-01-01"}, TODAY)
    assert len(errors) == 4
    assert any("titre" in e for e in errors) and any("type" in e for e in errors)


def test_dates_acceptees_et_refusees():
    assert parse_deadline("31/01/2027") == date(2027, 1, 31)
    assert parse_deadline("2027-01-31") == date(2027, 1, 31)
    assert parse_deadline("31 janvier") is None


def test_detection_json_et_xml():
    from app.import_rules import detect_format
    assert detect_format(b'[{"titre": "Stage"}]') == "json"
    assert detect_format(b'{"offres": []}') == "json"
    assert detect_format(b"<offres><offre/></offres>") == "xml"
    assert detect_format(b"  \n<?xml version='1.0'?><offres/>") == "xml"


def test_lecture_json():
    from app.import_rules import read_json
    headers, rows = read_json('{"offres": [{"Titre": "Stage Python", "type": "stage", "lieu": null}]}'.encode())
    assert headers == ["titre", "type", "lieu"]
    assert rows[0][1]["titre"] == "Stage Python" and rows[0][1]["lieu"] == ""


def test_lecture_xml():
    from app.import_rules import read_xml
    xml = ("<offres><offre><titre>Stage Python</titre><type>stage</type><lieu>Lomé</lieu></offre>"
           "<offre><titre>Comptable</titre><type>emploi</type></offre></offres>").encode()
    headers, rows = read_xml(xml)
    assert headers == ["titre", "type", "lieu"]
    assert rows[1][1] == {"titre": "Comptable", "type": "emploi"}
