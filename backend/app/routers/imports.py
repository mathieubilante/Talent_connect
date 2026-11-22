from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models
from ..accounts import get_or_create_account
from ..billing_rules import offer_limit
from ..database import get_db
from ..import_rules import (MAX_IMPORT_BYTES, MAX_ROWS, detect_format, duplicate_key, missing_headers,
                            read_csv, read_json, read_xlsx, read_xml, validate_row)
from ..security import require_role
from ..services import notify

router = APIRouter(prefix="/import", tags=["Import d'offres"])


@router.post("/offers")
async def import_offers(file: UploadFile = File(...), commit: bool = Form(False),
                        user: models.User = Depends(require_role(models.Role.company)),
                        db: Session = Depends(get_db)):
    """Importe des offres depuis un fichier CSV ou XLSX.
    commit=false : aperçu seulement (rien n'est enregistré). commit=true : enregistre les lignes valides."""
    content = await file.read(MAX_IMPORT_BYTES + 1)
    if len(content) > MAX_IMPORT_BYTES:
        raise HTTPException(413, "Fichier trop volumineux (1 Mo maximum)")
    fmt = detect_format(content)
    if fmt is None:
        raise HTTPException(400, "Format non accepté : CSV, XLSX, JSON ou XML")
    try:
        readers = {"xlsx": read_xlsx, "csv": read_csv, "json": read_json, "xml": read_xml}
        headers, rows = readers[fmt](content)
    except Exception:
        raise HTTPException(400, "Le fichier est illisible ou corrompu")
    missing = missing_headers(headers)
    if missing:
        raise HTTPException(400, "Colonnes obligatoires manquantes : " + ", ".join(missing))
    if len(rows) > MAX_ROWS:
        raise HTTPException(413, f"Trop de lignes ({len(rows)}). Maximum : {MAX_ROWS} par fichier.")

    today = date.today()
    errors, valid, seen = [], [], set()
    existing = {duplicate_key({"title": o.title, "location": o.location or ""})
                for o in user.company.offers if o.is_active}
    duplicates = []
    for line_no, item in rows:
        offer, row_errors = validate_row(item, today)
        if row_errors:
            errors.append({"row": line_no, "messages": row_errors})
            continue
        key = duplicate_key(offer)
        if key in existing or key in seen:
            duplicates.append({"row": line_no, "title": offer["title"], "location": offer["location"]})
            continue
        seen.add(key)
        valid.append(offer)

    limit = offer_limit(get_or_create_account(db, user).status, "company")
    active_now = sum(1 for o in user.company.offers if o.is_active)
    room = None if limit is None else max(0, limit - active_now)
    over_quota = 0
    if room is not None and len(valid) > room:
        over_quota = len(valid) - room
        valid = valid[:room]

    imported = 0
    if commit and valid:
        try:
            for offer in valid:
                db.add(models.JobOffer(company_id=user.company.id, **offer))
                imported += 1
            notify(db, user.id, f"Import terminé : {imported} offre(s) publiée(s).")
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(500, "Import annulé : une erreur est survenue, aucune offre n'a été enregistrée.")

    return {
        "format": fmt, "total_rows": len(rows), "valid": len(valid), "invalid": len(errors),
        "duplicates": duplicates, "over_quota": over_quota, "errors": errors[:200],
        "preview": [{"title": o["title"], "offer_type": o["offer_type"], "location": o["location"],
                     "deadline": o["deadline"].isoformat() if o["deadline"] else None} for o in valid[:10]],
        "imported": imported, "committed": commit,
    }
