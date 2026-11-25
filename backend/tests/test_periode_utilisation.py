from tests.helpers import H, age_account, login_token, register


def test_pendant_la_periode_l_acces_est_ouvert(client):
    email, token = register(client)
    assert client.get("/offers", headers=H(token)).status_code == 200


def test_apres_la_periode_les_fonctions_demandent_l_abonnement(client):
    email, _ = register(client)
    age_account(email, 20)
    token = login_token(client, email)
    r = client.get("/offers", headers=H(token))
    assert r.status_code == 403 and r.json()["detail"].startswith("SUBSCRIPTION_REQUIRED")


def test_apres_la_periode_l_abonnement_reste_accessible(client):
    email, _ = register(client)
    age_account(email, 20)
    token = login_token(client, email)
    assert client.get("/billing/me", headers=H(token)).status_code == 200
    assert client.get("/billing/plans", headers=H(token)).status_code == 200
    assert client.get("/account/me", headers=H(token)).status_code == 200


def test_compte_actif_n_est_jamais_bloque(client):
    from tests.helpers import admin_validate, complete_kyc, pay
    email, token = register(client)
    complete_kyc(client, token)
    admin_validate(client, email)
    pay(client, token)
    age_account(email, 400)
    token = login_token(client, email)
    assert client.get("/offers", headers=H(token)).status_code == 200
