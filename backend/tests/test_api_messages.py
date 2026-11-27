from tests.helpers import H, admin_validate, complete_kyc, create_offer, login_token, pay, register


def _candidate_subscribed(client, name):
    email, token = register(client, name=name)
    complete_kyc(client, token)
    admin_validate(client, email)
    pay(client, token)
    return login_token(client, email)


def test_conversation_entre_candidat_et_recruteur(client):
    _, comp = register(client, role="company", name="Entreprise Chat SARL")
    offer = create_offer(client, comp, title="Stage Chat Test")
    cand = _candidate_subscribed(client, "Candidat Chat")
    app = client.post("/applications", headers=H(cand), json={"offer_id": offer["id"], "cover_letter": ""}).json()
    assert client.post(f"/messages/application/{app['id']}", headers=H(cand), json={"body": "Bonjour"}).status_code == 201
    assert client.post(f"/messages/application/{app['id']}", headers=H(comp), json={"body": "Bonjour, merci"}).status_code == 201
    msgs = client.get(f"/messages/application/{app['id']}", headers=H(comp)).json()
    assert [m["body"] for m in msgs] == ["Bonjour", "Bonjour, merci"]
    assert msgs[1]["mine"] is True and msgs[0]["mine"] is False


def test_tiers_ne_voit_pas_la_conversation(client):
    _, comp = register(client, role="company", name="Entreprise Privee SARL")
    offer = create_offer(client, comp, title="Stage Prive Test")
    cand = _candidate_subscribed(client, "Candidat Prive")
    app = client.post("/applications", headers=H(cand), json={"offer_id": offer["id"], "cover_letter": ""}).json()
    _, autre = register(client)
    assert client.get(f"/messages/application/{app['id']}", headers=H(autre)).status_code == 404
    assert client.post(f"/messages/application/{app['id']}", headers=H(autre), json={"body": "x"}).status_code == 404


def test_message_vide_ou_trop_long_refuse(client):
    _, comp = register(client, role="company", name="Entreprise Longue SARL")
    offer = create_offer(client, comp, title="Stage Longueur Test")
    cand = _candidate_subscribed(client, "Candidat Longueur")
    app = client.post("/applications", headers=H(cand), json={"offer_id": offer["id"], "cover_letter": ""}).json()
    assert client.post(f"/messages/application/{app['id']}", headers=H(cand), json={"body": ""}).status_code == 422
    assert client.post(f"/messages/application/{app['id']}", headers=H(cand), json={"body": "x" * 2001}).status_code == 422


def test_notification_envoyee_au_destinataire(client):
    _, comp = register(client, role="company", name="Entreprise Notif SARL")
    offer = create_offer(client, comp, title="Stage Notif Test")
    cand = _candidate_subscribed(client, "Candidat Notif")
    app = client.post("/applications", headers=H(cand), json={"offer_id": offer["id"], "cover_letter": ""}).json()
    client.post(f"/messages/application/{app['id']}", headers=H(cand), json={"body": "Bonjour"})
    notes = client.get("/notifications", headers=H(comp)).json()
    items = notes["items"] if isinstance(notes, dict) and "items" in notes else notes
    assert any("nouveau message" in n["message"].lower() for n in items)
