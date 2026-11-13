import enum
from datetime import datetime

from sqlalchemy import (Column, Date, DateTime, Enum, Float, ForeignKey, Integer,
                        String, Text, Boolean, UniqueConstraint)
from sqlalchemy.orm import relationship

from .database import Base


class Role(str, enum.Enum):
    candidate = "candidate"
    company = "company"
    admin = "admin"


class OfferType(str, enum.Enum):
    emploi = "emploi"
    stage = "stage"


class ApplicationStatus(str, enum.Enum):
    recue = "recue"
    preselectionnee = "preselectionnee"
    entretien = "entretien"
    acceptee = "acceptee"
    refusee = "refusee"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(Role), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="user", uselist=False)
    company = relationship("Company", back_populates="user", uselist=False)


class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    first_name = Column(String(100), default="")
    last_name = Column(String(100), default="")
    phone = Column(String(30), default="")
    education = Column(String(255), default="")
    skills = Column(Text, default="")          # compétences séparées par des virgules
    cv_path = Column(String(500), default="")
    cv_text = Column(Text, default="")          # texte extrait du CV (pour le matching)

    user = relationship("User", back_populates="candidate")
    applications = relationship("Application", back_populates="candidate")


class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String(255), default="")
    sector = Column(String(150), default="")
    city = Column(String(100), default="")
    description = Column(Text, default="")

    user = relationship("User", back_populates="company")
    offers = relationship("JobOffer", back_populates="company")


class JobOffer(Base):
    __tablename__ = "job_offers"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    offer_type = Column(Enum(OfferType), nullable=False)
    required_skills = Column(Text, default="")
    location = Column(String(150), default="")
    deadline = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="offers")
    applications = relationship("Application", back_populates="offer")


class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    offer_id = Column(Integer, ForeignKey("job_offers.id"), nullable=False)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.recue)
    match_score = Column(Float, default=0.0)
    cover_letter = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="applications")
    offer = relationship("JobOffer", back_populates="applications")


class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    offer_id = Column(Integer, ForeignKey("job_offers.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserAccount(Base):
    """Cycle de vie du compte : statut + compteur d'essai (stocké côté serveur)."""
    __tablename__ = "user_accounts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    status = Column(String(20), nullable=False, default="pending")   # pending | validated | active | rejected
    trial_logins_used = Column(Integer, nullable=False, default=0)
    trial_limit = Column(Integer, nullable=False, default=30)
    rejection_reason = Column(Text, default="")
    last_login_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, nullable=True)
    status_changed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class LoginHistory(Base):
    __tablename__ = "login_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    logged_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(64), default="")
    user_agent = Column(String(255), default="")
    counted = Column(Boolean, default=False)   # a consommé une connexion d'essai


class UserContact(Base):
    """Moyen de contact vérifié : e-mail ou téléphone. Pas de ligne = compte historique, considéré vérifié."""
    __tablename__ = "user_contacts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    phone = Column(String(32), unique=True, nullable=True)
    channel = Column(String(10), nullable=False, default="email")   # email | phone
    verified = Column(Boolean, nullable=False, default=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class OtpCode(Base):
    __tablename__ = "otp_codes"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    channel = Column(String(10), nullable=False)
    destination = Column(String(255), nullable=False)
    code_hash = Column(String(64), nullable=False)       # jamais le code en clair
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=5)
    consumed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class KycDocument(Base):
    """Document d'identité d'un utilisateur. Le fichier est stocké chiffré ; ici, seulement ses métadonnées."""
    __tablename__ = "kyc_documents"
    __table_args__ = (UniqueConstraint("user_id", "doc_type", name="uq_kyc_user_doctype"),)
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    doc_type = Column(String(30), nullable=False)          # cin | cin_representant | patente | extrait_rne
    original_name = Column(String(255), default="")
    mime_type = Column(String(50), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False)             # empreinte du fichier d'origine
    storage_name = Column(String(80), nullable=False)       # nom aléatoire du fichier chiffré
    issue_date = Column(Date, nullable=True)                # date d'émission (extrait RNE)
    status = Column(String(20), nullable=False, default="submitted")   # submitted | approved | rejected (étape 4)
    review_note = Column(Text, default="")
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)


class KycAccessLog(Base):
    """Journal d'audit : qui a déposé, consulté ou supprimé quel document."""
    __tablename__ = "kyc_access_log"
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, nullable=True)
    owner_id = Column(Integer, nullable=False)
    actor_id = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)             # upload | replace | view | delete
    doc_type = Column(String(30), default="")
    ip_address = Column(String(64), default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_code = Column(String(40), nullable=False)
    months = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False)                  # montant total en francs CFA
    currency = Column(String(5), nullable=False, default="XOF")
    status = Column(String(20), nullable=False, default="pending")   # pending | active | expired | cancelled
    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    provider = Column(String(20), nullable=False, default="simulated")
    provider_ref = Column(String(64), unique=True, nullable=False)
    amount = Column(Integer, nullable=False)
    currency = Column(String(5), nullable=False, default="XOF")
    status = Column(String(20), nullable=False, default="pending")   # pending | paid | failed | cancelled
    failure_reason = Column(Text, default="")
    receipt_number = Column(String(30), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)


class Workspace(Base):
    """Environnement dédié créé automatiquement à l'activation du compte."""
    __tablename__ = "workspaces"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String(160), nullable=False)
    slug = Column(String(80), unique=True, nullable=False)
    kind = Column(String(20), nullable=False)                 # candidate | company
    plan_code = Column(String(40), nullable=False)
    storage_mb = Column(Integer, nullable=False, default=0)
    max_active_offers = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserSession(Base):
    """Une seule session active par utilisateur : une nouvelle connexion ferme la précédente."""
    __tablename__ = "user_sessions"
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    revoked_reason = Column(String(20), default="")           # new_login | logout
    ip_address = Column(String(64), default="")
    user_agent = Column(String(255), default="")


class LoginAttempt(Base):
    """Tentatives de connexion par mot de passe (réussies ou non), pour le verrouillage temporaire."""
    __tablename__ = "login_attempts"
    id = Column(Integer, primary_key=True)
    identifier = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(64), default="")
    success = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class SecurityAlert(Base):
    __tablename__ = "security_alerts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    kind = Column(String(30), nullable=False)
    message = Column(Text, nullable=False)
    channels = Column(String(255), default="")          # ex. "app,email:console,telegram:sent"
    ip_address = Column(String(64), default="")
    user_agent = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class AlertPreference(Base):
    __tablename__ = "alert_preferences"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    notify_email = Column(Boolean, default=True)
    notify_sms = Column(Boolean, default=False)
    notify_whatsapp = Column(Boolean, default=False)
    notify_telegram = Column(Boolean, default=False)
    phone = Column(String(32), default="")
    telegram_chat_id = Column(String(40), default="")
    updated_at = Column(DateTime, default=datetime.utcnow)
