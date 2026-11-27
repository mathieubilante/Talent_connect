import uuid

from tests.helpers import (H, PASSWORD, age_otp_codes, exhaust_trial, login, login_token, new_email, register)


def test_inscription_par_code_otp(client):
    email, token = register(client)
    data = client.get("/account/me", headers=H(token)).json()
    assert data["status"] == "pending" and data["trial_logins_used"] == 1 and data["access_allowed"]


def test_connexion_refusee_tant_que_le_code_n_est_pas_saisi(client):
    email = new_email()
    r = client.post("/auth/register", json={"channel": "email", "email": email, "password": PASSWORD,
                                            "role": "candidate", "name": "Sans Code"})
    assert r.status_code == 201
    res = login(client, email)
    assert res.status_code == 403 and res.json()["detail"].startswith("NOT_VERIFIED")


def test_mauvais_code_puis_bon_code(client):
    email = new_email()
    r = client.post("/auth/register", json={"channel": "email", "email": email, "password": PASSWORD,
                                            "role": "candidate", "name": "Code Test"})
    code = r.json()["dev_code"]
    wrong = "111111" if code != "111111" else "222222"
    bad = client.post("/auth/verify-otp", json={"identifier": email, "code": wrong})
    assert bad.status_code == 400 and "essai" in bad.json()["detail"]
    good = client.post("/auth/verify-otp", json={"identifier": email, "code": code})
    assert good.status_code == 200 and good.json()["role"] == "candidate"


def test_trop_d_essais_incorrects_bloquent_le_code(client):
    email = new_email()
    r = client.post("/auth/register", json={"channel": "email", "email": email, "password": PASSWORD,
                                            "role": "candidate", "name": "Essais Test"})
    code = r.json()["dev_code"]
    wrong = "111111" if code != "111111" else "222222"
    for _ in range(5):
        assert client.post("/auth/verify-otp", json={"identifier": email, "code": wrong}).status_code == 400
    blocked = client.post("/auth/verify-otp", json={"identifier": email, "code": code})
    assert blocked.status_code == 429


def test_inscription_par_telephone(client):
    phone = "+2289" + str(uuid.uuid4().int)[:7]
    r = client.post("/auth/register", json={"channel": "phone", "phone": phone, "password": PASSWORD,
                                            "role": "candidate", "name": "Tel Test"})
    assert r.status_code == 201 and r.json()["channel"] == "phone"
    v = client.post("/auth/verify-otp", json={"identifier": phone, "code": r.json()["dev_code"]})
    assert v.status_code == 200


def test_connexion_par_code_sans_mot_de_passe(client):
    email, _ = register(client)
    age_otp_codes(email)
    req = client.post("/auth/otp/request", json={"identifier": email})
    assert req.status_code == 200 and req.json()["dev_code"]
    res = client.post("/auth/otp/login", json={"identifier": email, "code": req.json()["dev_code"]})
    assert res.status_code == 200 and res.json()["access_token"]


def test_mot_de_passe_incorrect(client):
    email, _ = register(client)
    assert login(client, email, password="mauvais-mot-de-passe").status_code == 401


def test_connexions_illimitees_sans_blocage(client):
    email, _ = register(client)
    last = exhaust_trial(client, email)
    acc = client.get("/account/me", headers=H(last)).json()
    assert acc["access_allowed"] and not acc["trial_exhausted"]
    assert client.get("/offers", headers=H(last)).status_code == 200
    assert client.get("/kyc/me", headers=H(last)).status_code == 200

def test_session_unique_et_deconnexion(client):
    email, first = register(client)
    second = login_token(client, email)
    old = client.get("/account/me", headers=H(first))
    assert old.status_code == 401 and old.json()["detail"].startswith("SESSION_REVOKED")
    assert client.get("/account/me", headers=H(second)).status_code == 200
    assert client.post("/auth/logout", headers=H(second)).status_code == 200
    assert client.get("/account/me", headers=H(second)).status_code == 401


def test_google_non_configure(client):
    cfg = client.get("/auth/config").json()
    assert cfg["google_client_id"] == "" and cfg["session_idle_minutes"] == 30
    assert client.post("/auth/google", json={"credential": "faux", "role": "candidate"}).status_code == 503
