import enum
from datetime import datetime

from sqlalchemy import (Column, DateTime, Enum, Float, ForeignKey, Integer,
                        String, Text, Boolean)
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
