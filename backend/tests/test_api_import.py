import io

from tests.helpers import H, register

GOOD = ("titre,description,type,competences,lieu,date_limite\n"
        "Stage Python,Développement d'API REST avec FastAPI,stage,python;sql,Lomé,2027-02-28\n"
        "Comptable junior,Saisie comptable et rapprochements bancaires,emploi,excel,Kara,\n")


def _up(client, token, text, commit):
    return client.post("/import/offers", headers=H(token), data={"commit": "true" if commit else "false"},
                       files={"file": ("offres.csv", io.BytesIO(text.encode("utf-8")), "text/csv")})


def test_apercu_n_enregistre_rien(client):
    _, comp = register(client, role="company", name="Import Apercu SARL")
    r = _up(client, comp, GOOD, commit=False)
    assert r.status_code == 200 and r.json()["valid"] == 2 and r.json()["imported"] == 0
    assert client.get("/offers/mine", headers=H(comp)).json() == []


def test_import_enregistre_les_offres_valides(client):
    _, comp = register(client, role="company", name="Import Reel SARL")
    r = _up(client, comp, GOOD, commit=True)
    assert r.status_code == 200 and r.json()["imported"] == 2
    titles = {o["title"] for o in client.get("/offers/mine", headers=H(comp)).json()}
    assert titles == {"Stage Python", "Comptable junior"}


def test_erreurs_par_ligne_et_doublons(client):
    _, comp = register(client, role="company", name="Import Erreurs SARL")
    text = GOOD + "X,court,autre,,Lomé,\nStage Python,Développement d'API REST avec FastAPI,stage,python,Lomé,\n"
    r = _up(client, comp, text, commit=True).json()
    assert r["invalid"] == 1 and r["errors"][0]["row"] == 4
    assert len(r["duplicates"]) == 1
    assert r["imported"] == 2


def test_colonnes_manquantes_refusees(client):
    _, comp = register(client, role="company", name="Import Colonnes SARL")
    r = _up(client, comp, "titre,lieu\nStage,Lomé\n", commit=True)
    assert r.status_code == 400 and "description" in r.json()["detail"]


def test_faux_fichier_refuse(client):
    _, comp = register(client, role="company", name="Import Faux SARL")
    r = client.post("/import/offers", headers=H(comp), data={"commit": "true"},
                    files={"file": ("offres.csv", io.BytesIO(b"MZ\x90\x00\x03\x00"), "text/csv")})
    assert r.status_code == 400


def test_candidat_ne_peut_pas_importer(client):
    _, cand = register(client)
    assert _up(client, cand, GOOD, commit=True).status_code == 403


def test_quota_d_essai_respecte(client):
    _, comp = register(client, role="company", name="Import Quota SARL")
    many = "titre,description,type\n" + "".join(
        f"Offre numero {i},Description suffisamment longue de l'offre {i},stage\n" for i in range(5))
    r = _up(client, comp, many, commit=True).json()
    assert r["imported"] == 3 and r["over_quota"] == 2       # 3 offres maximum pendant l'essai
