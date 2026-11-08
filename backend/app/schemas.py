from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from .models import ApplicationStatus, OfferType, Role


class RegisterIn(BaseModel):
    channel: Literal["email", "phone"] = "email"
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str = Field(min_length=8)
    role: Role
    name: str = ""            # nom de l'entreprise ou nom complet du candidat

    @model_validator(mode="after")
    def check_contact(self):
        if self.channel == "email" and not self.email:
            raise ValueError("L'adresse e-mail est obligatoire")
        if self.channel == "phone" and not self.phone:
            raise ValueError("Le numéro de téléphone est obligatoire")
        return self


class VerifyOtpIn(BaseModel):
    identifier: str
    code: str = Field(min_length=4, max_length=10)


class ResendOtpIn(BaseModel):
    identifier: str


class VerificationOut(BaseModel):
    verification_required: bool = True
    channel: str
    destination_masked: str
    delivery: str = "console"
    expires_in_seconds: int
    resend_after_seconds: int
    dev_code: Optional[str] = None


class AccountOut(BaseModel):
    status: str
    status_label: str
    trial_logins_used: int
    trial_limit: int
    trial_remaining: int
    trial_exhausted: bool
    access_allowed: bool
    alert: bool
    message: str
    rejection_reason: str = ""
    last_login_at: Optional[datetime] = None


class StatusChangeIn(BaseModel):
    status: str
    reason: str = ""


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role
    account: Optional[AccountOut] = None


class CandidateUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    education: Optional[str] = None
    skills: Optional[str] = None


class CandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    first_name: str
    last_name: str
    phone: str
    education: str
    skills: str
    cv_path: str


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    sector: Optional[str] = None
    city: Optional[str] = None
    description: Optional[str] = None


class OfferCreate(BaseModel):
    title: str
    description: str
    offer_type: OfferType
    required_skills: str = ""
    location: str = ""
    deadline: Optional[datetime] = None


class OfferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    offer_type: OfferType
    required_skills: str
    location: str
    deadline: Optional[datetime]
    is_active: bool
    company_name: str = ""
    match_score: Optional[float] = None   # rempli pour un candidat connecté
    match_level: str = ""
    match_explanation: str = ""
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    is_favorite: bool = False
    applications_count: int = 0
    company_id: int = 0
    company_sector: str = ""
    company_city: str = ""
    created_at: Optional[datetime] = None


class ApplicationCreate(BaseModel):
    offer_id: int
    cover_letter: str = ""


class StatusUpdate(BaseModel):
    status: ApplicationStatus


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    offer_id: int
    candidate_id: int
    status: ApplicationStatus
    match_score: float
    created_at: datetime
    offer_title: str = ""
    candidate_name: str = ""
    candidate_education: str = ""
    candidate_skills: str = ""
    match_level: str = ""
    matched_skills: list[str] = []
    missing_skills: list[str] = []


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    message: str
    is_read: bool
    created_at: datetime


class CandidateMatchOut(BaseModel):
    candidate_id: int
    name: str
    education: str
    skills: str
    score: float
    level: str
    matched_skills: list[str]
    missing_skills: list[str]


class ChatIn(BaseModel):
    message: str


class ChatOut(BaseModel):
    reply: str
    quick_replies: list[str] = []


class CoverLetterIn(BaseModel):
    offer_id: int


class KycRequirementOut(BaseModel):
    doc_type: str
    label: str
    help: str
    needs_issue_date: bool


class KycDocumentOut(BaseModel):
    id: int
    doc_type: str
    label: str
    original_name: str
    mime_type: str
    size_bytes: int
    issue_date: Optional[date] = None
    expires_on: Optional[date] = None
    status: str
    review_note: str = ""
    uploaded_at: datetime


class KycStatusOut(BaseModel):
    role: str
    required: list[KycRequirementOut]
    documents: list[KycDocumentOut]
    missing: list[str]
    complete: bool


class DocumentReviewIn(BaseModel):
    decision: Literal["approved", "rejected"]
    note: str = ""


class AccountDecisionIn(BaseModel):
    decision: Literal["validate", "reject"]
    reason: str = ""


class OfferPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[OfferOut]


class CompanyPublicOut(BaseModel):
    id: int
    name: str
    sector: str = ""
    city: str = ""
    description: str = ""
    active_offers: int = 0


class CompanyDetailOut(CompanyPublicOut):
    offers: list[OfferOut] = []
