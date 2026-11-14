import uuid

from tests.helpers import H, create_offer, register


def test_parcours_visiteur_sans_connexion(client):
    name = f"Societe{uuid.uuid4().hex[:6]}"
    _, comp = register(client, role="company", name=name)
    mot = f"Zebre{uuid.uuid4().hex[:6]}"
    offer = create_offer(client, comp, title=f"Stage {mot}")

    res = client.get("/public/offers", params={"q": mot}).json()
    assert res["total"] == 1 and res["items"][0]["id"] == offer["id"] and res["items"][0]["applications_count"] == 0
    assert client.get(f"/public/offers/{offer['id']}").status_code == 200
    assert isinstance(client.get(f"/public/offers/{offer['id']}/similar").json(), list)
    assert any(c["name"] == name for c in client.get("/public/companies").json())
    assert {"locations", "sectors", "skills", "types"} <= set(client.get("/public/meta").json())
    assert client.get("/public/stats").status_code == 200
    assert client.get("/offers").status_code == 401                         # la liste personnalisée exige une connexion


def test_offre_cloturee_invisible_pour_les_visiteurs(client):
    _, comp = register(client, role="company", name="Societe Cloture")
    offer = create_offer(client, comp)
    assert client.delete(f"/offers/{offer['id']}", headers=H(comp)).status_code == 204
    assert client.get(f"/public/offers/{offer['id']}").status_code == 404


def test_assistant_public_et_sante(client):
    r = client.post("/assistant/public-chat", json={"message": "Bonjour"}).json()
    assert "TConnect IA" in r["reply"] and r["quick_replies"]
    assert client.get("/").json()["status"] == "ok"
    assert client.get("/health").json() == {"status": "ok", "database": "ok"}
