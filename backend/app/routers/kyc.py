import os
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from cryptography.fernet import InvalidToken
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import KYC_DIR, MAX_KYC_SIZE
from ..crypto import decrypt_bytes, encrypt_bytes, sha256_hex
from ..database import get_db
from ..kyc_rules import (ALLOWED_MIME, DOC_TYPES, detect_file_type, missing_documents, required_for,
                         rne_expires_on, rne_is_recent)
from ..security import get_user_unrestricted, require_role
from ..services import notify

# Accessibles même si l'essai gratuit est épuisé : c'est justement là qu'on soumet ses documents.
router = APIRouter(prefix="/kyc", tags=["Documents KYC"])
admin_router = APIRouter(prefix="/admin/kyc", tags=["Documents KYC (administration)"])

KYC_PATH = Path(KYC_DIR)


def _ip(request: Request) -> str:
    return (request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or (request.client.host if request.client else ""))[:64]


def _log(db: Session, doc_id, owner_id: int, actor_id: int, action: str, doc_type: str, request: Request):
    db.add(models.KycAccessLog(document_id=doc_id, owner_id=owner_id, actor_id=actor_id, action=action,
                               doc_type=doc_type, ip_address=_ip(request)))


def _doc_out(d: models.KycDocument) -> schemas.KycDocumentOut:
    return schemas.KycDocumentOut(
        id=d.id, doc_type=d.doc_type, label=DOC_TYPES.get(d.doc_type, {}).get("label", d.doc_type),
        original_name=d.original_name, mime_type=d.mime_type, size_bytes=d.size_bytes,
        issue_date=d.issue_date, expires_on=rne_expires_on(d.issue_date) if d.issue_date else None,
        status=d.status, review_note=d.review_note or "", uploaded_at=d.uploaded_at)


def _status(db: Session, user: models.User) -> schemas.KycStatusOut:
    docs = db.query(models.KycDocument).filter_by(user_id=user.id).order_by(models.KycDocument.id).all()
    role = user.role.value
    missing = missing_documents(role, [d.doc_type for d in docs])
    return schemas.KycStatusOut(
        role=role,
        required=[schemas.KycRequirementOut(doc_type=t, label=DOC_TYPES[t]["label"], help=DOC_TYPES[t]["help"],
                                            needs_issue_date=DOC_TYPES[t]["needs_issue_date"])
                  for t in required_for(role)],
        documents=[_doc_out(d) for d in docs], missing=missing, complete=not missing)


def _file_path(storage_name: str) -> Path:
    path = (KYC_PATH / storage_name).resolve()
    if KYC_PATH.resolve() not in path.parents:     # protection contre les chemins détournés
        raise HTTPException(500, "Chemin de stockage invalide")
    return path


@router.get("/me", response_model=schemas.KycStatusOut)
def my_kyc(user: models.User = Depends(get_user_unrestricted), db: Session = Depends(get_db)):
    if user.role == models.Role.admin:
        raise HTTPException(403, "Les administrateurs n'ont pas de dossier KYC")
    return _status(db, user)


@router.post("/documents", response_model=schemas.KycStatusOut, status_code=201)
async def upload_document(request: Request,
                          doc_type: str = Form(...),
                          issue_date: Optional[str] = Form(None),
                          file: UploadFile = File(...),
                          user: models.User = Depends(get_user_unrestricted),
                          db: Session = Depends(get_db)):
    if user.role == models.Role.admin:
        raise HTTPException(403, "Les administrateurs n'ont pas de dossier KYC")
    if doc_type not in required_for(user.role.value):
        raise HTTPException(400, "Ce type de document n'est pas demandé pour votre profil")

    parsed_date = None
    if DOC_TYPES[doc_type]["needs_issue_date"]:
        try:
            parsed_date = date.fromisoformat(issue_date or "")
        except ValueError:
            raise HTTPException(422, "Indiquez la date d'émission de l'extrait (format AAAA-MM-JJ)")
        if not rne_is_recent(parsed_date, date.today()):
            raise HTTPException(422, "L'extrait RNE doit dater de moins de 3 mois et ne peut pas être daté du futur")

    content = await file.read(MAX_KYC_SIZE + 1)
    if len(content) > MAX_KYC_SIZE:
        raise HTTPException(413, "Fichier trop volumineux (5 Mo maximum)")
    if not content:
        raise HTTPException(400, "Fichier vide")
    mime = detect_file_type(content)
    if mime not in ALLOWED_MIME:
        raise HTTPException(400, "Format non accepté : envoyez un PDF, un JPG ou un PNG")

    was_missing = missing_documents(user.role.value,
                                    [d.doc_type for d in db.query(models.KycDocument).filter_by(user_id=user.id)])

    KYC_PATH.mkdir(parents=True, exist_ok=True)
    storage_name = f"{uuid.uuid4().hex}.enc"
    _file_path(storage_name).write_bytes(encrypt_bytes(content))      # chiffré avant d'être écrit sur le disque

    safe_name = os.path.basename(file.filename or "document")[:200]
    existing = db.query(models.KycDocument).filter_by(user_id=user.id, doc_type=doc_type).first()
    if existing:
        if existing.status == "approved":
            _file_path(storage_name).unlink(missing_ok=True)
            raise HTTPException(409, "Ce document a déjà été validé et ne peut plus être remplacé")
        old_name = existing.storage_name
        existing.original_name, existing.mime_type, existing.size_bytes = safe_name, mime, len(content)
        existing.sha256, existing.storage_name, existing.issue_date = sha256_hex(content), storage_name, parsed_date
        existing.status, existing.review_note, existing.uploaded_at = "submitted", "", datetime.utcnow()
        doc, action = existing, "replace"
        _file_path(old_name).unlink(missing_ok=True)                  # l'ancienne version est supprimée
    else:
        doc = models.KycDocument(user_id=user.id, doc_type=doc_type, original_name=safe_name, mime_type=mime,
                                 size_bytes=len(content), sha256=sha256_hex(content), storage_name=storage_name,
                                 issue_date=parsed_date)
        db.add(doc)
        action = "upload"
    db.flush()
    _log(db, doc.id, user.id, user.id, action, doc_type, request)

    still_missing = [t for t in was_missing if t != doc_type]
    if was_missing and not still_missing:                              # le dossier vient d'être complété
        notify(db, user.id, "Votre dossier de documents est complet. Il sera examiné par l'administration.")
        for admin in db.query(models.User).filter_by(role=models.Role.admin):
            notify(db, admin.id, f"Dossier KYC complet à examiner : {user.email}")
    db.commit()
    return _status(db, user)


@router.get("/documents/{doc_id}/download")
def download_document(doc_id: int, request: Request,
                      user: models.User = Depends(get_user_unrestricted), db: Session = Depends(get_db)):
    doc = db.get(models.KycDocument, doc_id)
    # Le propriétaire et l'administrateur sont les seuls à pouvoir lire un document ; 404 pour les autres
    if not doc or (doc.user_id != user.id and user.role != models.Role.admin):
        raise HTTPException(404, "Document introuvable")
    try:
        data = decrypt_bytes(_file_path(doc.storage_name).read_bytes())
    except (InvalidToken, FileNotFoundError):
        raise HTTPException(500, "Document illisible ou altéré")
    _log(db, doc.id, doc.user_id, user.id, "view", doc.doc_type, request)
    db.commit()
    ext = ALLOWED_MIME.get(doc.mime_type, "bin")
    return Response(content=data, media_type=doc.mime_type,
                    headers={"Content-Disposition": f'attachment; filename="{doc.doc_type}.{ext}"',
                             "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})


@router.delete("/documents/{doc_id}", response_model=schemas.KycStatusOut)
def delete_document(doc_id: int, request: Request,
                    user: models.User = Depends(get_user_unrestricted), db: Session = Depends(get_db)):
    doc = db.get(models.KycDocument, doc_id)
    if not doc or doc.user_id != user.id:
        raise HTTPException(404, "Document introuvable")
    if doc.status == "approved":
        raise HTTPException(409, "Un document validé ne peut pas être supprimé")
    _file_path(doc.storage_name).unlink(missing_ok=True)
    _log(db, doc.id, user.id, user.id, "delete", doc.doc_type, request)
    db.delete(doc)
    db.commit()
    return _status(db, user)


@admin_router.get("")
def admin_list(admin: models.User = Depends(require_role(models.Role.admin)), db: Session = Depends(get_db)):
    rows = []
    for u in db.query(models.User).filter(models.User.role != models.Role.admin).order_by(models.User.id.desc()).all():
        docs = db.query(models.KycDocument).filter_by(user_id=u.id).order_by(models.KycDocument.id).all()
        if not docs:
            continue
        role = u.role.value
        rows.append({"user_id": u.id, "email": u.email, "role": role,
                     "required_count": len(required_for(role)), "uploaded_count": len(docs),
                     "complete": not missing_documents(role, [d.doc_type for d in docs]),
                     "documents": [{"id": d.id, "doc_type": d.doc_type,
                                    "label": DOC_TYPES.get(d.doc_type, {}).get("label", d.doc_type),
                                    "original_name": d.original_name, "status": d.status,
                                    "uploaded_at": d.uploaded_at} for d in docs]})
    return rows
