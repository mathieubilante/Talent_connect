from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..matching import analyze_match
from ..security import require_role
from .offers import favorite_ids, offer_to_out

router = APIRouter(prefix="/recommendations", tags=["Recommandations IA"])


@router.get("/offers", response_model=list[schemas.OfferOut])
def recommended_offers(user: models.User = Depends(require_role(models.Role.candidate)),
                       db: Session = Depends(get_db)):
    """Top 6 des offres les plus compatibles avec le profil, hors offres déjà postulées."""
    c = user.candidate
    applied = {a.offer_id for a in c.applications}
    offers = db.query(models.JobOffer).filter(models.JobOffer.is_active.is_(True)).all()
    favs = favorite_ids(db, user)
    scored = [offer_to_out(o, c, favs) for o in offers if o.id not in applied]
    scored.sort(key=lambda o: o.match_score or 0, reverse=True)
    return scored[:6]


@router.get("/candidates/{offer_id}", response_model=list[schemas.CandidateMatchOut])
def recommended_candidates(offer_id: int,
                           user: models.User = Depends(require_role(models.Role.company)),
                           db: Session = Depends(get_db)):
    """Top 8 des profils les plus compatibles avec une offre de l'entreprise."""
    offer = db.get(models.JobOffer, offer_id)
    if not offer or offer.company_id != user.company.id:
        raise HTTPException(404, "Offre introuvable")
    result = []
    for c in db.query(models.Candidate).limit(500).all():
        a = analyze_match(c.skills, c.cv_text, offer.title, offer.description, offer.required_skills)
        result.append(schemas.CandidateMatchOut(
            candidate_id=c.id, name=f"{c.first_name} {c.last_name}".strip() or "Candidat",
            education=c.education, skills=c.skills, score=a["score"], level=a["level"],
            matched_skills=a["matched"], missing_skills=a["missing"]))
    result.sort(key=lambda r: r.score, reverse=True)
    return result[:8]
