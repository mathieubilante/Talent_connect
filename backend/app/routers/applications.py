from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..matching import analyze_match
from ..security import require_role
from ..services import STATUS_LABELS, notify

router = APIRouter(prefix="/applications", tags=["Candidatures"])


def _to_out(app: models.Application) -> schemas.ApplicationOut:
    out = schemas.ApplicationOut.model_validate(app)
    c, o = app.candidate, app.offer
    out.offer_title = o.title
    out.candidate_name = f"{c.first_name} {c.last_name}".strip()
    out.candidate_education = c.education
    out.candidate_skills = c.skills
    a = analyze_match(c.skills, c.cv_text, o.title, o.description, o.required_skills)
    out.match_level, out.matched_skills, out.missing_skills = a["level"], a["matched"], a["missing"]
    return out


@router.post("", response_model=schemas.ApplicationOut, status_code=201)
def apply(data: schemas.ApplicationCreate,
          user: models.User = Depends(require_role(models.Role.candidate)),
          db: Session = Depends(get_db)):
    offer = db.get(models.JobOffer, data.offer_id)
    if not offer or not offer.is_active:
        raise HTTPException(404, "Offre introuvable ou clôturée")
    if db.query(models.Application).filter_by(candidate_id=user.candidate.id,
                                              offer_id=offer.id).first():
        raise HTTPException(409, "Vous avez déjà postulé à cette offre")

    c = user.candidate
    score = analyze_match(c.skills, c.cv_text, offer.title, offer.description,
                          offer.required_skills)["score"]
    application = models.Application(candidate_id=c.id, offer_id=offer.id,
                                     cover_letter=data.cover_letter, match_score=score)
    db.add(application)
    notify(db, offer.company.user_id,
           f"Nouvelle candidature de {c.first_name} {c.last_name} pour « {offer.title} » (compatibilité {score} %)")
    db.commit()
    db.refresh(application)
    return _to_out(application)


@router.get("/mine", response_model=list[schemas.ApplicationOut])
def my_applications(user: models.User = Depends(require_role(models.Role.candidate))):
    return [_to_out(a) for a in sorted(user.candidate.applications,
                                       key=lambda a: a.created_at, reverse=True)]


@router.get("/received", response_model=list[schemas.ApplicationOut])
def received_applications(user: models.User = Depends(require_role(models.Role.company)),
                          db: Session = Depends(get_db)):
    apps = (db.query(models.Application).join(models.JobOffer)
            .filter(models.JobOffer.company_id == user.company.id)
            .order_by(models.Application.match_score.desc()).all())
    return [_to_out(a) for a in apps]


@router.patch("/{application_id}/status", response_model=schemas.ApplicationOut)
def update_status(application_id: int, data: schemas.StatusUpdate,
                  user: models.User = Depends(require_role(models.Role.company)),
                  db: Session = Depends(get_db)):
    app = db.get(models.Application, application_id)
    if not app or app.offer.company_id != user.company.id:
        raise HTTPException(404, "Candidature introuvable")
    app.status = data.status
    notify(db, app.candidate.user_id,
           f"Votre candidature pour « {app.offer.title} » est {STATUS_LABELS[data.status.value]}.")
    db.commit()
    db.refresh(app)
    return _to_out(app)
