"""Routes publiques (sans connexion) : parcourir les offres et les entreprises comme sur un site d'emploi."""
from collections import Counter
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..search_rules import similar_score
from ..skills import split_skills
from .offers import offer_to_out

router = APIRouter(prefix="/public", tags=["Public"])


def _active_offers(db: Session):
    return (db.query(models.JobOffer).join(models.Company)
            .filter(models.JobOffer.is_active.is_(True),
                    or_(models.JobOffer.deadline.is_(None), models.JobOffer.deadline >= datetime.utcnow())))


def _public(offer: models.JobOffer) -> schemas.OfferOut:
    out = offer_to_out(offer)
    out.applications_count = 0          # information réservée à l'entreprise
    return out


@router.get("/offers", response_model=schemas.OfferPage)
def public_offers(q: Optional[str] = None, offer_type: Optional[models.OfferType] = None,
                  location: Optional[str] = None, sector: Optional[str] = None,
                  page: int = Query(1, ge=1), page_size: int = Query(8, ge=1, le=50),
                  db: Session = Depends(get_db)):
    query = _active_offers(db)
    if offer_type:
        query = query.filter(models.JobOffer.offer_type == offer_type)
    if location:
        query = query.filter(models.JobOffer.location.ilike(f"%{location}%"))
    if sector:
        query = query.filter(models.Company.sector.ilike(f"%{sector}%"))
    if q:
        like = f"%{q}%"
        query = query.filter(models.JobOffer.title.ilike(like) | models.JobOffer.description.ilike(like) |
                             models.JobOffer.required_skills.ilike(like) | models.Company.name.ilike(like))
    total = query.count()
    items = (query.order_by(models.JobOffer.created_at.desc(), models.JobOffer.id.desc())
             .offset((page - 1) * page_size).limit(page_size).all())
    return schemas.OfferPage(total=total, page=page, page_size=page_size, items=[_public(o) for o in items])


@router.get("/offers/{offer_id}", response_model=schemas.OfferOut)
def public_offer(offer_id: int, db: Session = Depends(get_db)):
    offer = db.get(models.JobOffer, offer_id)
    if not offer or not offer.is_active:
        raise HTTPException(404, "Offre introuvable ou clôturée")
    return _public(offer)


@router.get("/offers/{offer_id}/similar", response_model=list[schemas.OfferOut])
def similar_offers(offer_id: int, db: Session = Depends(get_db)):
    base = db.get(models.JobOffer, offer_id)
    if not base:
        raise HTTPException(404, "Offre introuvable")
    base_skills = set(split_skills(base.required_skills))
    scored = []
    for o in _active_offers(db).filter(models.JobOffer.id != offer_id).all():
        score = similar_score(base_skills, set(split_skills(o.required_skills)), o.offer_type == base.offer_type,
                              bool(o.location) and o.location == base.location)
        scored.append((score, o))
    scored.sort(key=lambda x: (-x[0], -x[1].id))
    return [_public(o) for _, o in scored[:3]]


def _company_out(company: models.Company, count: int) -> dict:
    return dict(id=company.id, name=company.name, sector=company.sector or "", city=company.city or "",
                description=company.description or "", active_offers=count)


@router.get("/companies", response_model=list[schemas.CompanyPublicOut])
def public_companies(db: Session = Depends(get_db)):
    rows = (db.query(models.Company, func.count(models.JobOffer.id))
            .outerjoin(models.JobOffer, and_(models.JobOffer.company_id == models.Company.id,
                                             models.JobOffer.is_active.is_(True)))
            .group_by(models.Company.id).all())
    result = [schemas.CompanyPublicOut(**_company_out(c, n)) for c, n in rows if (c.name or "").strip()]
    result.sort(key=lambda c: (-c.active_offers, c.name.lower()))
    return result


@router.get("/companies/{company_id}", response_model=schemas.CompanyDetailOut)
def public_company(company_id: int, db: Session = Depends(get_db)):
    company = db.get(models.Company, company_id)
    if not company or not (company.name or "").strip():
        raise HTTPException(404, "Entreprise introuvable")
    offers = [o for o in company.offers if o.is_active and (o.deadline is None or o.deadline >= datetime.utcnow())]
    offers.sort(key=lambda o: o.created_at or datetime.min, reverse=True)
    return schemas.CompanyDetailOut(**_company_out(company, len(offers)), offers=[_public(o) for o in offers])


@router.get("/meta")
def public_meta(db: Session = Depends(get_db)):
    """Lieux, secteurs et compétences les plus présents : alimente les filtres et les recherches populaires."""
    locations, sectors, skills, types = Counter(), Counter(), Counter(), Counter()
    for o in _active_offers(db).all():
        if (o.location or "").strip():
            locations[o.location.strip()] += 1
        if (o.company.sector or "").strip():
            sectors[o.company.sector.strip()] += 1
        skills.update(split_skills(o.required_skills))
        types[o.offer_type.value] += 1
    pack = lambda c, n: [{"name": k, "count": v} for k, v in c.most_common(n)]
    return {"locations": pack(locations, 8), "sectors": pack(sectors, 8), "skills": pack(skills, 10),
            "types": {"emploi": types["emploi"], "stage": types["stage"]}}
