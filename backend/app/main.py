from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .config import ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_PASSWORD_FROM_ENV, CORS_ORIGINS, SEED_DEMO_DATA
from .database import Base, SessionLocal, engine
from .routers import (account, admin, applications, assistant, auth, billing, favorites, kyc,
                      notifications, offers, profiles, public, recommendations, security_center)
from .security import hash_password, verify_password

Base.metadata.create_all(bind=engine)


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
        if not ADMIN_PASSWORD_FROM_ENV:
            print("[SÉCURITÉ] ATTENTION : ADMIN_PASSWORD n'est pas défini, le mot de passe par défaut (public) est utilisé. "
                  "Définissez ADMIN_PASSWORD sur l'hébergeur.", flush=True)
    finally:
        db.close()


ensure_admin()

if SEED_DEMO_DATA:
    from . import seed
    seed.run()

app = FastAPI(title="TalentConnect API",
              description="Plateforme intelligente de recrutement, d'emploi et de gestion des stages",
              version="0.10.0")

app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

for r in (auth, account, profiles, offers, applications, favorites, notifications,
          recommendations, assistant, admin, kyc, public, billing, security_center):
    app.include_router(r.router)
app.include_router(kyc.admin_router)
app.include_router(billing.admin_router)
app.include_router(security_center.admin_router)


@app.get("/", tags=["Santé"])
def root():
    return {"app": "TalentConnect API", "version": "0.10.0", "status": "ok", "docs": "/docs"}
