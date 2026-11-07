from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .config import ADMIN_EMAIL, ADMIN_PASSWORD, CORS_ORIGINS
from .database import Base, SessionLocal, engine
from .routers import (account, admin, applications, assistant, auth, favorites, kyc,
                      notifications, offers, profiles, recommendations)
from .security import hash_password

Base.metadata.create_all(bind=engine)


def ensure_admin() -> None:
    db = SessionLocal()
    try:
        if not db.query(models.User).filter_by(role=models.Role.admin).first():
            db.add(models.User(email=ADMIN_EMAIL, password_hash=hash_password(ADMIN_PASSWORD),
                               role=models.Role.admin))
            db.commit()
    finally:
        db.close()


ensure_admin()

app = FastAPI(title="TalentConnect API",
              description="Plateforme intelligente de recrutement, d'emploi et de gestion des stages",
              version="0.5.0")

app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

for r in (auth, account, profiles, offers, applications, favorites, notifications,
          recommendations, assistant, admin, kyc):
    app.include_router(r.router)
app.include_router(kyc.admin_router)


@app.get("/", tags=["Santé"])
def root():
    return {"app": "TalentConnect API", "version": "0.5.0", "status": "ok", "docs": "/docs"}
