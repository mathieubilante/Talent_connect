from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import require_role
from .offers import favorite_ids, offer_to_out

router = APIRouter(prefix="/favorites", tags=["Favoris"])


@router.get("", response_model=list[schemas.OfferOut])
def list_favorites(user: models.User = Depends(require_role(models.Role.candidate)),
                   db: Session = Depends(get_db)):
    favs = favorite_ids(db, user)
    offers = db.query(models.JobOffer).filter(models.JobOffer.id.in_(favs)).all() if favs else []
    return [offer_to_out(o, user.candidate, favs) for o in offers]


@router.post("/{offer_id}")
def toggle_favorite(offer_id: int,
                    user: models.User = Depends(require_role(models.Role.candidate)),
                    db: Session = Depends(get_db)):
    if not db.get(models.JobOffer, offer_id):
        raise HTTPException(404, "Offre introuvable")
    existing = db.query(models.Favorite).filter_by(user_id=user.id, offer_id=offer_id).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"is_favorite": False}
    db.add(models.Favorite(user_id=user.id, offer_id=offer_id))
    db.commit()
    return {"is_favorite": True}
