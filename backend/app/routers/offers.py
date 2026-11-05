from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..matching import analyze_match
from ..security import get_current_user, require_role

router = APIRouter(prefix="/offers", tags=["Offres"])


def offer_to_out(offer: models.JobOffer, candidate: Optional[models.Candidate] = None,
                 fav_ids: frozenset = frozenset()) -> schemas.OfferOut:
    out = schemas.OfferOut.model_validate(offer)
    out.company_name = offer.company.name
    out.is_favorite = offer.id in fav_ids
    out.applications_count = len(offer.applications)
    if candidate:
        a = analyze_match(candidate.skills, candidate.cv_text, offer.title,
                          offer.description, offer.required_skills)
        out.match_score, out.match_level = a["score"], a["level"]
        out.match_explanation = a["explanation"]
        out.matched_skills, out.missing_skills = a["matched"], a["missing"]
    return out


def favorite_ids(db: Session, user: models.User) -> frozenset:
    rows = db.query(models.Favorite.offer_id).filter_by(user_id=user.id).all()
    return frozenset(r[0] for r in rows)


@router.get("", response_model=list[schemas.OfferOut])
def list_offers(q: Optional[str] = None, offer_type: Optional[models.OfferType] = None,
                location: Optional[str] = None, sort: str = "recent",
                db: Session = Depends(get_db),
                user: models.User = Depends(get_current_user)):
    query = db.query(models.JobOffer).filter(models.JobOffer.is_active.is_(True))
    if offer_type:
        query = query.filter(models.JobOffer.offer_type == offer_type)
    if location:
        query = query.filter(models.JobOffer.location.ilike(f"%{location}%"))
    if q:
        like = f"%{q}%"
        query = query.filter(models.JobOffer.title.ilike(like) |
                             models.JobOffer.description.ilike(like) |
                             models.JobOffer.required_skills.ilike(like))
    offers = query.order_by(models.JobOffer.created_at.desc()).all()

    candidate = user.candidate if user.role == models.Role.candidate else None
    favs = favorite_ids(db, user)
    result = [offer_to_out(o, candidate, favs) for o in offers]
    if candidate and sort == "match":  # recommandation : meilleurs scores en premier
        result.sort(key=lambda o: o.match_score or 0, reverse=True)
    return result


@router.post("", response_model=schemas.OfferOut, status_code=201)
def create_offer(data: schemas.OfferCreate,
                 user: models.User = Depends(require_role(models.Role.company)),
                 db: Session = Depends(get_db)):
    offer = models.JobOffer(company_id=user.company.id, **data.model_dump())
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer_to_out(offer)


@router.get("/mine", response_model=list[schemas.OfferOut])
def my_offers(user: models.User = Depends(require_role(models.Role.company))):
    return [offer_to_out(o) for o in user.company.offers]


@router.get("/{offer_id}", response_model=schemas.OfferOut)
def get_offer(offer_id: int, db: Session = Depends(get_db),
              user: models.User = Depends(get_current_user)):
    offer = db.get(models.JobOffer, offer_id)
    if not offer:
        raise HTTPException(404, "Offre introuvable")
    candidate = user.candidate if user.role == models.Role.candidate else None
    return offer_to_out(offer, candidate, favorite_ids(db, user))


@router.delete("/{offer_id}", status_code=204)
def close_offer(offer_id: int,
                user: models.User = Depends(require_role(models.Role.company)),
                db: Session = Depends(get_db)):
    offer = db.get(models.JobOffer, offer_id)
    if not offer or offer.company_id != user.company.id:
        raise HTTPException(404, "Offre introuvable")
    offer.is_active = False
    db.commit()
