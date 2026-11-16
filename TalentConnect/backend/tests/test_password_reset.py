from tests.helpers import H, PASSWORD, age_otp_codes, login, new_email, register


def _request(client, email):
    age_otp_codes(email)
    r = client.post("/auth/password/request", json={"identifier": email})
    assert r.status_code == 200
    return r.json()


def test_reinitialisation_complete_et_sessions_fermees(client):
    email, old_token = register(client)
    code = _request(client, email)["dev_code"]
    assert code
    ok = client.post("/auth/password/reset", json={"identifier": email, "code": code, "new_password": "NouveauMotDePasse9!"})
    assert ok.status_code == 200
    assert login(client, email, password=PASSWORD).status_code == 401              # ancien mot de passe refusé
    assert login(client, email, password="NouveauMotDePasse9!").status_code == 200  # nouveau accepté
    assert client.get("/account/me", headers=H(old_token)).status_code == 401       # anciennes sessions fermées


def test_code_incorrect_ne_change_pas_le_mot_de_passe(client):
    email, _ = register(client)
    code = _request(client, email)["dev_code"]
    wrong = "111111" if code != "111111" else "222222"
    r = client.post("/auth/password/reset", json={"identifier": email, "code": wrong, "new_password": "Autre12345!"})
    assert r.status_code == 400
    assert login(client, email, password=PASSWORD).status_code == 200


def test_reponse_neutre_pour_un_compte_inconnu(client):
    r = client.post("/auth/password/request", json={"identifier": new_email()})
    assert r.status_code == 200 and r.json()["dev_code"] is None


def test_mot_de_passe_trop_court_refuse(client):
    email, _ = register(client)
    code = _request(client, email)["dev_code"]
    r = client.post("/auth/password/reset", json={"identifier": email, "code": code, "new_password": "court"})
    assert r.status_code == 422


def test_envoi_en_echec_est_signale(client, monkeypatch):
    from app import otp
    monkeypatch.setattr(otp, "deliver_otp", lambda *a, **k: "failed")
    email = new_email()
    r = client.post("/auth/register", json={"channel": "email", "email": email, "password": PASSWORD,
                                            "role": "candidate", "name": "Echec Envoi"})
    assert r.status_code == 503 and "pas pu envoyer" in r.json()["detail"]


def test_sans_envoi_reel_on_ne_pretend_pas_avoir_envoye(client, monkeypatch):
    from app import otp
    monkeypatch.setattr(otp, "deliver_otp", lambda *a, **k: "console")
    monkeypatch.setattr(otp, "OTP_DEV_MODE", False)
    r = client.post("/auth/register", json={"channel": "email", "email": new_email(), "password": PASSWORD,
                                            "role": "candidate", "name": "Sans Envoi"})
    assert r.status_code == 503
