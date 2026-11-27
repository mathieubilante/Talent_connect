"""Messagerie candidat-recruteur, par candidature.

Règles :
- seuls le candidat concerné et le recruteur de l'offre voient la conversation ;
- un message : texte seulement, 1 à 2000 caractères ;
- l'autre partie reçoit une notification à chaque nouveau message.
Un utilisateur qui n'est pas concerné reçoit 404 (la candidature n'est pas révélée).
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..security import get_current_user
from ..services import notify

router = APIRouter(prefix="/messages", tags=["Messagerie"])


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


def _application_for(db: Session, user: models.User, app_id: int) -> models.Application:
    app = db.get(models.Application, app_id)
    if not app:
        raise HTTPException(404, "Conversation introuvable")
    if user.role == models.Role.candidate and app.candidate.user_id == user.id:
        return app
    if user.role == models.Role.company and app.offer.company.user_id == user.id:
        return app
    raise HTTPException(404, "Conversation introuvable")


def _other_party_user_id(app: models.Application, user: models.User) -> int:
    return app.offer.company.user_id if user.role == models.Role.candidate else app.candidate.user_id


@router.get("/application/{app_id}")
def list_messages(app_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    app = _application_for(db, user, app_id)
    rows = (db.query(models.ApplicationMessage).filter_by(application_id=app.id)
            .order_by(models.ApplicationMessage.created_at, models.ApplicationMessage.id).all())
    return [{"id": m.id, "body": m.body, "mine": m.sender_user_id == user.id,
             "created_at": m.created_at.isoformat() if m.created_at else ""} for m in rows]


@router.post("/application/{app_id}", status_code=201)
def send_message(app_id: int, data: MessageIn, db: Session = Depends(get_db),
                 user: models.User = Depends(get_current_user)):
    app = _application_for(db, user, app_id)
    body = data.body.strip()
    if not body:
        raise HTTPException(422, "Le message est vide")
    msg = models.ApplicationMessage(application_id=app.id, sender_user_id=user.id, body=body, created_at=datetime.utcnow())
    db.add(msg)
    notify(db, _other_party_user_id(app, user), f"Nouveau message concernant « {app.offer.title} ».")
    db.commit()
    db.refresh(msg)
    return {"id": msg.id, "body": msg.body, "mine": True, "created_at": msg.created_at.isoformat()}
