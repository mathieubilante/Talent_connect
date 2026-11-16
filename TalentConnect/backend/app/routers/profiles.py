import os
import uuid
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import MAX_CV_SIZE, UPLOAD_DIR
from ..cv_parser import extract_pdf_text
from ..database import get_db
from ..skills import extract_skills, split_skills
from ..profile_rules import (MAX_AVATAR_BYTES, birth_date_error, age_on, image_type, initials,
                             missing_candidate_fields)
from ..security import get_current_user, require_role

router = APIRouter(prefix="/profile", tags=["Profils"])


@router.get("/candidate", response_model=schemas.CandidateOut)
def get_candidate(user: models.User = Depends(require_role(models.Role.candidate))):
    return user.candidate


@router.put("/candidate", response_model=schemas.CandidateOut)
def update_candidate(data: schemas.CandidateUpdate,
                     user: models.User = Depends(require_role(models.Role.candidate)),
                     db: Session = Depends(get_db)):
    values = data.model_dump(exclude_unset=True)
    problem = birth_date_error(values.get("birth_date"), date.today())
    if problem:
        raise HTTPException(422, problem)
    for field, value in values.items():
        setattr(user.candidate, field, value)
    db.commit()
    db.refresh(user.candidate)
    return user.candidate


@router.post("/candidate/cv", response_model=schemas.CandidateOut)
async def upload_cv(file: UploadFile = File(...),
                    user: models.User = Depends(require_role(models.Role.candidate)),
                    db: Session = Depends(get_db)):
    if file.content_type != "application/pdf" or not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "Le CV doit être un fichier PDF")
    content = await file.read()
    if len(content) > MAX_CV_SIZE:
        raise HTTPException(413, "Fichier trop volumineux (5 Mo maximum)")
    if not content.startswith(b"%PDF"):
        raise HTTPException(400, "Fichier PDF invalide")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}.pdf")
    with open(path, "wb") as f:
        f.write(content)

    user.candidate.cv_path = path
    user.candidate.cv_text = extract_pdf_text(path)
    # IA : les compétences détectées dans le CV sont ajoutées au profil
    merged = sorted(set(split_skills(user.candidate.skills)) | set(extract_skills(user.candidate.cv_text)))
    user.candidate.skills = ", ".join(merged)
    db.commit()
    db.refresh(user.candidate)
    return user.candidate


@router.put("/company")
def update_company(data: schemas.CompanyUpdate,
                   user: models.User = Depends(require_role(models.Role.company)),
                   db: Session = Depends(get_db)):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user.company, field, value)
    db.commit()
    return {"message": "Profil entreprise mis à jour"}


def _candidate_values(c) -> dict:
    return {"first_name": c.first_name, "last_name": c.last_name, "birth_date": c.birth_date,
            "school": c.school, "occupation": c.occupation}


@router.get("/me", response_model=schemas.ProfileMeOut)
def my_profile(user: models.User = Depends(get_current_user)):
    """Identité affichée dans le menu (photo, nom complet) et état du profil."""
    if user.role == models.Role.candidate:
        c = user.candidate
        missing = missing_candidate_fields(_candidate_values(c))
        full = f"{c.first_name} {c.last_name}".strip() or user.email
        age = age_on(c.birth_date, date.today()) if c.birth_date else None
        return schemas.ProfileMeOut(role="candidate", email=user.email, full_name=full,
                                    initials=initials(c.first_name, c.last_name, user.email[:1].upper()),
                                    has_avatar=c.has_avatar, profile_complete=not missing, missing=missing, age=age)
    if user.role == models.Role.company:
        name = user.company.name if user.company else ""
        return schemas.ProfileMeOut(role="company", email=user.email, full_name=name or user.email,
                                    initials=initials(name, "", user.email[:1].upper()), has_avatar=False,
                                    profile_complete=bool(name), missing=[] if name else ["nom de l'entreprise"])
    return schemas.ProfileMeOut(role="admin", email=user.email, full_name="Administrateur",
                                initials="AD", has_avatar=False, profile_complete=True, missing=[])


@router.post("/avatar", response_model=schemas.CandidateOut)
async def upload_avatar(file: UploadFile = File(...),
                        user: models.User = Depends(require_role(models.Role.candidate)),
                        db: Session = Depends(get_db)):
    """Photo de profil : JPG, PNG ou WebP, 2 Mo maximum, type vérifié sur le contenu du fichier."""
    content = await file.read(MAX_AVATAR_BYTES + 1)
    if len(content) > MAX_AVATAR_BYTES:
        raise HTTPException(413, "Photo trop volumineuse (2 Mo maximum)")
    kind = image_type(content)
    if kind is None:
        raise HTTPException(400, "Format non accepté : envoyez une photo JPG, PNG ou WebP")
    folder = os.path.join(UPLOAD_DIR, "avatars")
    os.makedirs(folder, exist_ok=True)
    new_path = os.path.join(folder, f"{uuid.uuid4().hex}.{kind}")
    with open(new_path, "wb") as f:
        f.write(content)
    old = user.candidate.avatar_path
    user.candidate.avatar_path = new_path
    db.commit()
    if old and os.path.isfile(old):
        os.remove(old)                       # l'ancienne photo est supprimée
    db.refresh(user.candidate)
    return user.candidate


@router.get("/avatar")
def get_avatar(user: models.User = Depends(require_role(models.Role.candidate))):
    path = user.candidate.avatar_path
    if not path or not os.path.isfile(path):
        raise HTTPException(404, "Pas de photo de profil")
    kind = path.rsplit(".", 1)[-1]
    media = {"jpg": "image/jpeg", "png": "image/png", "webp": "image/webp"}[kind]
    with open(path, "rb") as f:
        return Response(content=f.read(), media_type=media, headers={"Cache-Control": "private, no-store"})
