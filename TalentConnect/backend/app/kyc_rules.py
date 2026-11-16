"""Règles pures des documents KYC (sans base de données, donc faciles à tester)."""
from datetime import date
from typing import Optional

DOC_TYPES = {
    "cin": {"label": "Carte d'identité nationale (CIN)", "needs_issue_date": False,
            "help": "Recto-verso lisible, en cours de validité."},
    "cin_representant": {"label": "CIN du représentant légal", "needs_issue_date": False,
                         "help": "CIN du dirigeant ou du représentant de l'entreprise."},
    "patente": {"label": "Patente", "needs_issue_date": False,
                "help": "Patente de l'entreprise en cours de validité."},
    "extrait_rne": {"label": "Extrait du RNE (moins de 3 mois)", "needs_issue_date": True,
                    "help": "Registre national des entreprises : l'extrait doit dater de moins de 3 mois."},
}

REQUIRED_BY_ROLE = {
    "candidate": ["cin"],                                       # particuliers
    "company": ["cin_representant", "patente", "extrait_rne"],  # entreprises
}

ALLOWED_MIME = {"application/pdf": "pdf", "image/jpeg": "jpg", "image/png": "png"}
RNE_MAX_AGE_MONTHS = 3


def detect_file_type(content: bytes) -> Optional[str]:
    """Type réel du fichier d'après ses premiers octets (et non d'après son nom)."""
    if content.startswith(b"%PDF"):
        return "application/pdf"
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    return None


def add_months(d: date, months: int) -> date:
    y, m = divmod(d.month - 1 + months, 12)
    year, month = d.year + y, m + 1
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    last = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
    return date(year, month, min(d.day, last))


def rne_expires_on(issue_date: date) -> date:
    """Date limite de validité d'un extrait RNE : 3 mois après son émission."""
    return add_months(issue_date, RNE_MAX_AGE_MONTHS)


def rne_is_recent(issue_date: date, today: date) -> bool:
    return issue_date <= today <= rne_expires_on(issue_date)


def required_for(role: str) -> list[str]:
    return list(REQUIRED_BY_ROLE.get(role, []))


def missing_documents(role: str, uploaded_types) -> list[str]:
    have = set(uploaded_types)
    return [t for t in required_for(role) if t not in have]
