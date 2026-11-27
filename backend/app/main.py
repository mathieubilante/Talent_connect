import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .config import (ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_PASSWORD_FROM_ENV, CORS_ORIGINS, DATABASE_URL,
                     KYC_ENCRYPTION_KEY, OTP_DEV_MODE, SECRET_KEY, SEED_DEMO_DATA)
from .database import Base, SessionLocal, engine
from .routers import (account, admin, applications, assistant, auth, billing, favorites, imports, kyc, messages,
                      notifications, offers, profiles, public, recommendations, security_center)
from .security import hash_password, verify_password
from .http_security import apply_security_headers
from .startup_checks import collect_warnings

Base.metadata.create_all(bind=engine)


def ensure_columns() -> None:
    """Ajoute aux bases existantes les colonnes nouvelles (create_all ne modifie jamais une table existante).
    Fonctionne sur SQLite comme sur PostgreSQL. Sans cela, la partie candidat échouerait en ligne."""
    from sqlalchemy import inspect, text
    additions = {"birth_date": "DATE", "school": "VARCHAR(200) DEFAULT ''",
                 "occupation": "VARCHAR(200) DEFAULT ''", "avatar_path": "VARCHAR(500) DEFAULT ''"}
    insp = inspect(engine)
    if not insp.has_table("candidates"):
        return
    existing = {c["name"] for c in insp.get_columns("candidates")}
    with engine.begin() as conn:
        for name, sql_type in additions.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE candidates ADD COLUMN {name} {sql_type}"))
                print(f"[BASE] colonne ajoutée : candidates.{name}", flush=True)


ensure_columns()


def ensure_admin() -> None:
    """Crée l'administrateur au premier démarrage ; si ADMIN_PASSWORD est défini, il devient son mot de passe
    (permet de remplacer le mot de passe par défaut, connu car public)."""
    db = SessionLocal()
    try:
        admin = db.query(models.User).filter_by(role=models.Role.admin, email=ADMIN_EMAIL).first()
        if admin is None:
            if not db.query(models.User).filter_by(role=models.Role.admin).first():
                db.add(models.User(email=ADMIN_EMAIL, password_hash=hash_password(ADMIN_PASSWORD),
                                   role=models.Role.admin))
                db.commit()
        elif ADMIN_PASSWORD_FROM_ENV and not verify_password(ADMIN_PASSWORD, admin.password_hash):
            admin.password_hash = hash_password(ADMIN_PASSWORD)
            db.commit()
            print("[SÉCURITÉ] Mot de passe administrateur mis à jour depuis ADMIN_PASSWORD.", flush=True)
    finally:
        db.close()


ensure_admin()
for _w in collect_warnings(SECRET_KEY, ADMIN_PASSWORD_FROM_ENV, KYC_ENCRYPTION_KEY, OTP_DEV_MODE, CORS_ORIGINS,
                          DATABASE_URL, hosted=bool(os.getenv("RENDER"))):
    print(f"[SÉCURITÉ] {_w}", flush=True)

if SEED_DEMO_DATA:
    from . import seed
    seed.run()

app = FastAPI(title="TalentConnect API",
              description="Plateforme intelligente de recrutement, d'emploi et de gestion des stages",
              version="0.24.0")

app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.middleware("http")
async def _force_https(request, call_next):
    """Sur l'hébergement, toute requête en http est redirigée vers https (308 : la méthode est conservée)."""
    from fastapi.responses import RedirectResponse
    if os.getenv("RENDER") and request.headers.get("x-forwarded-proto", "https") == "http":
        return RedirectResponse(url=str(request.url.replace(scheme="https")), status_code=308)
    return await call_next(request)


@app.middleware("http")
async def _security_headers(request, call_next):
    response = await call_next(request)
    apply_security_headers(response.headers, hsts=request.url.scheme == "https" or bool(os.getenv("RENDER")))
    return response


for r in (auth, account, profiles, offers, applications, messages, favorites, notifications,
          recommendations, assistant, admin, kyc, public, billing, security_center, imports):
    app.include_router(r.router)
app.include_router(kyc.admin_router)
app.include_router(billing.admin_router)
app.include_router(security_center.admin_router)


@app.get("/", tags=["Santé"])
def root():
    return {"app": "TalentConnect API", "version": "0.24.0", "status": "ok", "docs": "/docs"}


@app.get("/health", tags=["Santé"])
def health():
    """Contrôle de santé : l'API répond ET la base de données est joignable."""
    from sqlalchemy import text
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    except Exception:
        raise HTTPException(503, "Base de données injoignable")
    finally:
        db.close()
