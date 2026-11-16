import os
from datetime import date, timedelta

from tests.helpers import (H, PDF, admin_token, admin_validate, complete_kyc, create_offer, exhaust_trial,
                           expire_subscriptions, kyc_upload, login_token, pay, register)


def test_document_chiffre_sur_le_disque_et_acces_controle(client, kyc_dir):
    email, token = register(client)
    r = kyc_upload(client, token, "cin")
    assert r.status_code == 201 and r.json()["complete"]
    doc = r.json()["documents"][0]

    files = [os.path.join(kyc_dir, f) for f in os.listdir(kyc_dir)]
    assert files and all(b"CONFIDENTIEL" not in open(f, "rb").read() for f in files)   # rien de lisible sur le disque

    url = f"/kyc/documents/{doc['id']}/download"
    assert client.get(url, headers=H(token)).content == PDF                               # propriétaire
    assert client.get(url, headers=H(admin_token(client))).content == PDF                 # administrateur
    _, other = register(client)
    assert client.get(url, headers=H(other)).status_code == 404                           # un tiers : introuvable


def test_fichier_deguise_et_extrait_rne_trop_ancien_refuses(client):
    _, cand = register(client)
    assert kyc_upload(client, cand, "cin", content=b"MZ\x90\x00 programme.exe", filename="cin.pdf").status_code == 400
    _, comp = register(client, role="company", name="Societe Test")
    vieux = (date.today() - timedelta(days=150)).isoformat()
    assert kyc_upload(client, comp, "extrait_rne", issue_date=vieux).status_code == 422
    assert kyc_upload(client, comp, "extrait_rne").status_code == 422                     # date manquante
    assert kyc_upload(client, comp, "cin").status_code == 400                             # document non demandé aux entreprises


def test_validation_administrative(client):
    email, token = register(client)
    kyc_upload(client, token, "cin")
    adm = admin_token(client)
    row = next(r for r in client.get("/admin/kyc", headers=H(adm)).json() if r["email"] == email)
    doc_id, uid = row["documents"][0]["id"], row["user_id"]

    assert client.post(f"/admin/kyc/documents/{doc_id}/review", headers=H(adm),
                       json={"decision": "rejected", "note": ""}).status_code == 422       # motif obligatoire
    blocked = client.post(f"/admin/kyc/users/{uid}/decision", headers=H(adm), json={"decision": "validate"})
    assert blocked.status_code == 409                                                     # documents pas validés
    assert client.post(f"/admin/kyc/documents/{doc_id}/review", headers=H(adm), json={"decision": "approved"}).status_code == 200
    assert client.post(f"/admin/kyc/documents/{doc_id}/review", headers=H(adm), json={"decision": "approved"}).status_code == 409
    ok = client.post(f"/admin/kyc/users/{uid}/decision", headers=H(adm), json={"decision": "validate"})
    assert ok.status_code == 200 and ok.json()["status"] == "validated"
    assert client.get("/account/me", headers=H(token)).json()["status"] == "validated"


def test_refus_du_compte_bloque_la_connexion(client):
    email, token = register(client)
    kyc_upload(client, token, "cin")
    adm = admin_token(client)
    uid = next(r for r in client.get("/admin/kyc", headers=H(adm)).json() if r["email"] == email)["user_id"]
    assert client.post(f"/admin/kyc/users/{uid}/decision", headers=H(adm), json={"decision": "reject", "reason": ""}).status_code == 422
    assert client.post(f"/admin/kyc/users/{uid}/decision", headers=H(adm),
                       json={"decision": "reject", "reason": "Documents illisibles"}).status_code == 200
    res = client.post("/auth/login", data={"username": email, "password": "MotDePasse123!"})
    assert res.status_code == 403 and "Documents illisibles" in res.json()["detail"]


def test_souscription_impossible_avant_validation(client):
    _, token = register(client)
    plans = client.get("/billing/plans", headers=H(token)).json()
    assert not plans["can_checkout"]
    r = client.post("/billing/checkout", headers=H(token), json={"plan_code": plans["plans"][0]["code"], "months": 3})
    assert r.status_code == 409


def test_prix_et_offre_non_falsifiables(client):
    email, token = register(client)
    complete_kyc(client, token)
    admin_validate(client, email)
    plans = client.get("/billing/plans", headers=H(token)).json()
    code = plans["plans"][0]["code"]
    assert client.post("/billing/checkout", headers=H(token), json={"plan_code": code, "months": 5}).status_code == 400
    assert client.post("/billing/checkout", headers=H(token), json={"plan_code": "entreprise_pro", "months": 3}).status_code == 400
    co = client.post("/billing/checkout", headers=H(token), json={"plan_code": code, "months": 3, "amount": 1}).json()
    assert co["amount"] == plans["plans"][0]["quotes"][1]["total"]                        # le prix vient toujours du serveur


def test_paiement_active_le_compte_et_cree_l_espace(client):
    email, token = register(client)
    complete_kyc(client, token)
    admin_validate(client, email)
    co, res = pay(client, token)
    assert res.status_code == 200 and res.json()["account"]["status"] == "active"
    pid = co["payment_id"]
    again = client.post(f"/billing/payments/{pid}/simulate", headers=H(token), json={"outcome": "success"})
    assert again.status_code == 409                                                       # jamais traité deux fois
    me = client.get("/billing/me", headers=H(token)).json()
    assert me["subscription"]["status"] == "active" and me["workspace"]["slug"]
    rec = client.get(f"/billing/receipt/{pid}", headers=H(token)).json()
    assert rec["number"].startswith("REC-") and rec["amount"] == co["amount"]


def test_echec_de_paiement_ne_change_pas_le_compte(client):
    email, token = register(client)
    complete_kyc(client, token)
    admin_validate(client, email)
    _, res = pay(client, token, outcome="failure")
    assert res.status_code == 200 and res.json()["payment"]["status"] == "failed"
    assert client.get("/account/me", headers=H(token)).json()["status"] == "validated"


def test_abonnement_expire_puis_renouvellement(client):
    email, token = register(client)
    complete_kyc(client, token)
    admin_validate(client, email)
    pay(client, token)
    expire_subscriptions(email)
    assert client.get("/billing/me", headers=H(token)).json()["account"]["status"] == "validated"
    pay(client, token)
    assert client.get("/account/me", headers=H(token)).json()["status"] == "active"


def test_limite_de_3_offres_pendant_l_essai(client):
    _, token = register(client, role="company", name="Entreprise Limite")
    for i in range(3):
        create_offer(client, token, title=f"Offre {i}")
    r = client.post("/offers", headers=H(token), json={"title": "Offre 4", "description": "x", "offer_type": "stage"})
    assert r.status_code == 403 and "OFFER_LIMIT" in r.json()["detail"]


def test_passage_de_l_essai_au_compte_actif_sans_perte_de_donnees(client):
    _, comp = register(client, role="company", name="Entreprise Transition")
    offer = create_offer(client, comp, title="Stage Transition")

    email, token = register(client, name="Marie Transition")
    assert client.put("/profile/candidate", headers=H(token),
                      json={"skills": "python, sql", "education": "Licence Informatique"}).status_code == 200
    app_r = client.post("/applications", headers=H(token), json={"offer_id": offer["id"], "cover_letter": "Bonjour"})
    assert app_r.status_code == 201
    app_id, score = app_r.json()["id"], app_r.json()["match_score"]
    assert client.post(f"/favorites/{offer['id']}", headers=H(token)).status_code == 200

    last = exhaust_trial(client, email)                                                   # essai épuisé : accès bloqué
    assert client.get("/offers", headers=H(last)).status_code == 403
    assert kyc_upload(client, last, "cin").status_code == 201
    admin_validate(client, email)
    _, res = pay(client, last)
    assert res.json()["account"]["status"] == "active"

    # accès rendu, et toutes les données sont retrouvées
    assert client.get("/offers", headers=H(last)).status_code == 200
    apps = client.get("/applications/mine", headers=H(last)).json()
    assert any(a["id"] == app_id and a["match_score"] == score for a in apps)
    assert any(o["id"] == offer["id"] for o in client.get("/favorites", headers=H(last)).json())
    profile = client.get("/profile/candidate", headers=H(last)).json()
    assert "python" in profile["skills"] and profile["education"] == "Licence Informatique"
    acc = client.get("/account/me", headers=H(last)).json()
    assert acc["status"] == "active" and acc["access_allowed"]
    assert client.get("/billing/me", headers=H(last)).json()["workspace"] is not None
