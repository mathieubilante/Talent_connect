from app.http_security import security_headers


def test_en_tetes_de_base():
    h = security_headers(hsts=False)
    assert h["X-Content-Type-Options"] == "nosniff"
    assert h["X-Frame-Options"] == "DENY"
    assert "Strict-Transport-Security" not in h


def test_hsts_active_sur_https():
    assert "max-age=31536000" in security_headers(hsts=True)["Strict-Transport-Security"]


def test_reponses_de_l_api_portent_les_en_tetes(client):
    r = client.get("/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "server" not in r.headers and "x-powered-by" not in r.headers
