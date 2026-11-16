import io

from tests.helpers import H, register

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64
COMPLETE = {"birth_date": "2005-03-10", "school": "École Nationale Polytechnique", "occupation": "Étudiant en informatique"}


def test_menu_affiche_le_nom_complet_et_profil_incomplet(client):
    _, token = register(client, name="Ama Adjovi")
    me = client.get("/profile/me", headers=H(token)).json()
    assert me["full_name"] == "Ama Adjovi" and me["initials"] == "AA"
    assert me["profile_complete"] is False and "date de naissance" in me["missing"]
    assert me["has_avatar"] is False


def test_date_de_naissance_trop_jeune_refusee(client):
    _, token = register(client)
    r = client.put("/profile/candidate", headers=H(token), json={"birth_date": "2024-01-01"})
    assert r.status_code == 422


def test_profil_complet_apres_saisie(client):
    _, token = register(client, name="Kofi Mensah")
    assert client.put("/profile/candidate", headers=H(token), json=COMPLETE).status_code == 200
    me = client.get("/profile/me", headers=H(token)).json()
    assert me["profile_complete"] is True and me["missing"] == [] and me["age"] >= 15


def test_photo_de_profil_png_puis_suppression_de_l_ancienne(client, kyc_dir):
    _, token = register(client)
    r = client.post("/profile/avatar", headers=H(token), files={"file": ("moi.png", io.BytesIO(PNG), "image/png")})
    assert r.status_code == 200 and r.json()["has_avatar"] is True
    img = client.get("/profile/avatar", headers=H(token))
    assert img.status_code == 200 and img.headers["content-type"] == "image/png" and img.content == PNG
    assert client.get("/profile/me", headers=H(token)).json()["has_avatar"] is True


def test_photo_refusee_si_ce_n_est_pas_une_image(client):
    _, token = register(client)
    bad = client.post("/profile/avatar", headers=H(token), files={"file": ("x.png", io.BytesIO(b"<script>x</script>"), "image/png")})
    assert bad.status_code == 400


def test_photo_trop_lourde_refusee(client):
    _, token = register(client)
    big = b"\x89PNG\r\n\x1a\n" + b"0" * (2 * 1024 * 1024 + 10)
    r = client.post("/profile/avatar", headers=H(token), files={"file": ("big.png", io.BytesIO(big), "image/png")})
    assert r.status_code == 413


def test_entreprise_sans_photo_et_admin_sans_profil_candidat(client):
    _, comp = register(client, role="company", name="Entreprise Test SARL")
    me = client.get("/profile/me", headers=H(comp)).json()
    assert me["full_name"] == "Entreprise Test SARL" and me["has_avatar"] is False
    assert client.post("/profile/avatar", headers=H(comp), files={"file": ("a.png", io.BytesIO(PNG), "image/png")}).status_code == 403
