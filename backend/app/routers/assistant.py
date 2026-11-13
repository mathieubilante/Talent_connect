from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..assistant_logic import generate_cover_letter, reply
from ..database import get_db
from ..matching import analyze_match
from ..security import get_current_user, require_role
from ..skills import split_skills

router = APIRouter(prefix="/assistant", tags=["Assistant IA"])


def _context(user: models.User, db: Session) -> dict:
    ctx: dict = {}
    if user.role == models.Role.candidate:
        c = user.candidate
        ctx.update(first_name=c.first_name, skills=split_skills(c.skills),
                   has_cv=bool(c.cv_path), applications_count=len(c.applications))
        offers = db.query(models.JobOffer).filter_by(is_active=True).all()
        scored, gap_count = [], {}
        for o in offers:
            a = analyze_match(c.skills, c.cv_text, o.title, o.description, o.required_skills)
            scored.append({"title": o.title, "company": o.company.name, "score": a["score"]})
            for s in a["missing"]:
                gap_count[s] = gap_count.get(s, 0) + 1
        scored.sort(key=lambda x: x["score"], reverse=True)
        ctx["top_offers"] = scored[:3]
        ctx["skill_gaps"] = sorted(gap_count, key=gap_count.get, reverse=True)
    elif user.role == models.Role.company:
        ctx["pending"] = (db.query(models.Application).join(models.JobOffer)
                          .filter(models.JobOffer.company_id == user.company.id,
                                  models.Application.status == models.ApplicationStatus.recue).count())
    return ctx


@router.post("/chat", response_model=schemas.ChatOut)
def chat(data: schemas.ChatIn, user: models.User = Depends(get_current_user),
         db: Session = Depends(get_db)):
    return reply(data.message[:500], user.role.value, _context(user, db))


@router.post("/cover-letter")
def cover_letter(data: schemas.CoverLetterIn,
                 user: models.User = Depends(require_role(models.Role.candidate)),
                 db: Session = Depends(get_db)):
    offer = db.get(models.JobOffer, data.offer_id)
    if not offer:
        raise HTTPException(404, "Offre introuvable")
    c = user.candidate
    a = analyze_match(c.skills, c.cv_text, offer.title, offer.description, offer.required_skills)
    text = generate_cover_letter(f"{c.first_name} {c.last_name}".strip(), c.education,
                                 offer.title, offer.company.name, a["matched"], a["missing"])
    return {"letter": text}


@router.post("/public-chat", response_model=schemas.ChatOut)
def public_chat(data: schemas.ChatIn, db: Session = Depends(get_db)):
    """TConnect IA pour les visiteurs non connectés : explications générales, aucune donnée personnelle."""
    latest = (db.query(models.JobOffer).filter_by(is_active=True)
              .order_by(models.JobOffer.created_at.desc()).limit(3).all())
    ctx = {"latest_offers": [{"title": o.title, "company": o.company.name} for o in latest]}
    return reply(data.message[:500], "visitor", ctx)
