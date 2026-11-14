from tests.helpers import H, admin_token, age_otp_codes, login, login_token, register


def test_alertes_nouvel_appareil_et_session_remplacee(client):
    email, _ = register(client)
    login_token(client, email)
    last = login_token(client, email, ua="Autre navigateur/1.0")
    kinds = {a["kind"] for a in client.get("/security/alerts", headers=H(last)).json()}
    assert "session_replaced" in kinds and "new_device" in kinds


def test_verrouillage_apres_5_echecs_connexion_par_code_et_deblocage(client):
    email, _ = register(client)
    for _ in range(5):
        assert login(client, email, password="mauvais-mot-de-passe").status_code == 401
    locked = login(client, email)
    assert locked.status_code == 429 and "ACCOUNT_LOCKED" in locked.json()["detail"]

    age_otp_codes(email)                                                  # la connexion par code reste possible
    code = client.post("/auth/otp/request", json={"identifier": email}).json()["dev_code"]
    token = client.post("/auth/otp/login", json={"identifier": email, "code": code}).json()["access_token"]
    kinds = {a["kind"] for a in client.get("/security/alerts", headers=H(token)).json()}
    assert "failed_attempts" in kinds and "account_locked" in kinds

    adm = admin_token(client)
    sec = client.get("/admin/security", headers=H(adm)).json()
    assert any(item["identifier"] == email for item in sec["locked"])
    cleared = client.post("/admin/security/unlock", headers=H(adm), json={"identifier": email}).json()["cleared"]
    assert cleared >= 5
    assert login(client, email).status_code == 200


def test_preferences_d_alerte_et_alerte_de_test(client):
    _, token = register(client)
    base = {"notify_email": True, "notify_sms": True, "notify_whatsapp": False, "notify_telegram": False,
            "phone": "", "telegram_chat_id": ""}
    assert client.put("/security/preferences", headers=H(token), json=base).status_code == 422   # SMS sans numéro
    ok = client.put("/security/preferences", headers=H(token), json={**base, "phone": "90 12 34 56"})
    assert ok.status_code == 200 and ok.json()["phone"] == "+22890123456"
    test = client.post("/security/test-alert", headers=H(token)).json()
    assert "sms:console" in test["channels"] and "email:console" in test["channels"]            # mode démonstration


def test_routes_d_administration_reservees(client):
    _, token = register(client)
    for route in ("/admin/stats", "/admin/security", "/admin/kyc", "/admin/billing"):
        assert client.get(route, headers=H(token)).status_code == 403
        assert client.get(route).status_code == 401
    assert client.get("/admin/stats", headers=H(admin_token(client))).status_code == 200
