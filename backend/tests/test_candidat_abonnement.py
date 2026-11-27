from tests.helpers import H, admin_validate, complete_kyc, create_offer, login_token, pay, register


def test_candidat_sans_abonnement_voit_les_offres(client):
    _, comp = register(client, role="company", name="Entreprise Vue SARL")
    create_offer(client, comp, title="Stage Vue Test")
    _, token = register(client)
    assert client.get("/offers", headers=H(token)).status_code == 200


def test_candidat_sans_abonnement_ne_peut_pas_postuler(client):
    _, comp = register(client, role="company", name="Entreprise Postule SARL")
    offer = create_offer(client, comp, title="Stage Postule Test")
    _, token = register(client)
    r = client.post("/applications", headers=H(token), json={"offer_id": offer["id"], "cover_letter": ""})
    assert r.status_code == 403 and r.json()["detail"].startswith("SUBSCRIPTION_REQUIRED_APPLY")


def test_candidat_abonne_peut_postuler(client):
    _, comp = register(client, role="company", name="Entreprise Abonne SARL")
    offer = create_offer(client, comp, title="Stage Abonne Test")
    email, token = register(client)
    complete_kyc(client, token)
    admin_validate(client, email)
    pay(client, token)
    token = login_token(client, email)
    assert client.post("/applications", headers=H(token), json={"offer_id": offer["id"], "cover_letter": ""}).status_code == 201


def test_recruteur_voit_le_nombre_de_vues_une_seule_fois_par_candidat(client):
    _, comp = register(client, role="company", name="Entreprise Vues SARL")
    offer = create_offer(client, comp, title="Stage Vues Test")
    _, cand = register(client)
    client.get(f"/offers/{offer['id']}", headers=H(cand))
    client.get(f"/offers/{offer['id']}", headers=H(cand))
    _, cand2 = register(client)
    client.get(f"/offers/{offer['id']}", headers=H(cand2))
    mine = [o for o in client.get("/offers/mine", headers=H(comp)).json() if o["id"] == offer["id"]][0]
    assert mine["views_count"] == 2
