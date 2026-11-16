"""Fonctions utilitaires des tests d'intégration."""
import uuid
from datetime import date, datetime, timedelta

PASSWORD = "MotDePasse123!"
ADMIN_EMAIL, ADMIN_PASSWORD = "admin@talentconnect.tg", "AdminTest2026!"
PDF = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\nCONTENU CONFIDENTIEL DE TEST\n%%EOF"


def H(token):
    return {"Authorization": f"Bearer {token}"}


def new_email():
    return f"{uuid.uuid4().hex[:10]}@test.tg"


def register(client, role="candidate", name="Utilisateur Test", email=None):
    """Inscription complète (e-mail + code OTP). Retourne (email, jeton)."""
    email = email or new_email()
    r = client.post("/auth/register", json={"channel": "email", "email": email, "password": PASSWORD,
                                            "role": role, "name": name})
    assert r.status_code == 201, r.text
    v = client.post("/auth/verify-otp", json={"identifier": email, "code": r.json()["dev_code"]})
    assert v.status_code == 200, v.text
    return email, v.json()["access_token"]


def login(client, email, password=PASSWORD, ua="pytest-navigateur"):
    return client.post("/auth/login", data={"username": email, "password": password}, headers={"User-Agent": ua})


def login_token(client, email, **kw):
    r = login(client, email, **kw)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def admin_token(client):
    return login_token(client, ADMIN_EMAIL, password=ADMIN_PASSWORD)


def exhaust_trial(client, email):
    """Atteint les 30 connexions d'essai (l'inscription compte pour 1). Retourne le dernier jeton."""
    token = None
    for _ in range(29):
        token = login_token(client, email)
    return token


def kyc_upload(client, token, doc_type, content=PDF, issue_date=None, filename="document.pdf"):
    data = {"doc_type": doc_type}
    if issue_date:
        data["issue_date"] = issue_date
    return client.post("/kyc/documents", headers=H(token), data=data,
                       files={"file": (filename, content, "application/pdf")})


def complete_kyc(client, token, role="candidate"):
    if role == "candidate":
        assert kyc_upload(client, token, "cin").status_code == 201
    else:
        for t in ("cin_representant", "patente"):
            assert kyc_upload(client, token, t).status_code == 201
        assert kyc_upload(client, token, "extrait_rne", issue_date=date.today().isoformat()).status_code == 201


def admin_validate(client, email):
    """L'administrateur valide tous les documents puis le compte."""
    adm = admin_token(client)
    row = next(r for r in client.get("/admin/kyc", headers=H(adm)).json() if r["email"] == email)
    for d in row["documents"]:
        r = client.post(f"/admin/kyc/documents/{d['id']}/review", headers=H(adm), json={"decision": "approved"})
        assert r.status_code == 200, r.text
    r = client.post(f"/admin/kyc/users/{row['user_id']}/decision", headers=H(adm), json={"decision": "validate"})
    assert r.status_code == 200, r.text
    return adm


def pay(client, token, months=3, outcome="success"):
    plans = client.get("/billing/plans", headers=H(token)).json()
    code = plans["plans"][0]["code"]
    co = client.post("/billing/checkout", headers=H(token), json={"plan_code": code, "months": months})
    assert co.status_code == 200, co.text
    res = client.post(f"/billing/payments/{co.json()['payment_id']}/simulate", headers=H(token), json={"outcome": outcome})
    return co.json(), res


def create_offer(client, company_token, title="Stage Python", skills="python, sql"):
    r = client.post("/offers", headers=H(company_token), json={
        "title": title, "description": "Description de l'offre de test.", "offer_type": "stage",
        "required_skills": skills, "location": "Lomé"})
    assert r.status_code == 201, r.text
    return r.json()


def _db():
    from app.database import SessionLocal
    return SessionLocal()


def age_otp_codes(email, minutes=5):
    """Vieillit les codes OTP pour passer le délai de 60 s avant renvoi."""
    from app import models
    db = _db()
    try:
        user = db.query(models.User).filter(models.User.email == email).first()
        db.query(models.OtpCode).filter_by(user_id=user.id).update({"created_at": datetime.utcnow() - timedelta(minutes=minutes)})
        db.commit()
    finally:
        db.close()


def expire_subscriptions(email):
    """Fait échoir les abonnements de l'utilisateur (hier)."""
    from app import models
    db = _db()
    try:
        user = db.query(models.User).filter(models.User.email == email).first()
        db.query(models.Subscription).filter_by(user_id=user.id, status="active").update(
            {"ends_at": datetime.utcnow() - timedelta(days=1)})
        db.commit()
    finally:
        db.close()
