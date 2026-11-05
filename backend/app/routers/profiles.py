import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import MAX_CV_SIZE, UPLOAD_DIR
from ..cv_parser import extract_pdf_text
from ..database import get_db
from ..skills import extract_skills, split_skills
from ..security import require_role

router = APIRouter(prefix="/profile", tags=["Profils"])


@router.get("/candidate", response_model=schemas.CandidateOut)
def get_candidate(user: models.User = Depends(require_role(models.Role.candidate))):
    return user.candidate


@router.put("/candidate", response_model=schemas.CandidateOut)
def update_candidate(data: schemas.CandidateUpdate,
                     user: models.User = Depends(require_role(models.Role.candidate)),
                     db: Session = Depends(get_db)):
    for field, value in data.model_dump(exclude_unset=True).items():
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
