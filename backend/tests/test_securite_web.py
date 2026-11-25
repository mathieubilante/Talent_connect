from tests.helpers import new_email, PASSWORD


def test_robot_rempli_le_champ_piege_est_refuse(client):
    r = client.post("/auth/register", json={"channel": "email", "email": new_email(), "password": PASSWORD,
                                            "role": "candidate", "name": "Robot", "website": "http://spam.example"})
    assert r.status_code == 400 and r.json()["detail"] == "Requête refusée."


def test_inscription_normale_sans_champ_piege(client):
    r = client.post("/auth/register", json={"channel": "email", "email": new_email(), "password": PASSWORD,
                                            "role": "candidate", "name": "Humain", "website": ""})
    assert r.status_code == 201


def test_page_inconnue_renvoie_404(client):
    assert client.get("/route-qui-nexiste-pas-du-tout").status_code == 404
