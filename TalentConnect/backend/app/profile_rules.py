"""Règles pures du profil : champs obligatoires, âge, validation de la date de naissance et des photos."""
from datetime import date
from typing import Optional

MIN_AGE = 15
MAX_AGE = 100
MAX_AVATAR_BYTES = 2 * 1024 * 1024
REQUIRED_CANDIDATE_FIELDS = {
    "first_name": "prénom",
    "last_name": "nom",
    "birth_date": "date de naissance",
    "school": "établissement",
    "occupation": "activité",
}


def missing_candidate_fields(values: dict) -> list:
    """Liste des libellés des champs obligatoires qui sont vides."""
    return [label for key, label in REQUIRED_CANDIDATE_FIELDS.items() if not values.get(key)]


def age_on(birth: date, today: date) -> int:
    years = today.year - birth.year
    if (today.month, today.day) < (birth.month, birth.day):
        years -= 1
    return years


def birth_date_error(birth: Optional[date], today: date) -> Optional[str]:
    if birth is None:
        return None
    if birth > today:
        return "La date de naissance ne peut pas être dans le futur."
    age = age_on(birth, today)
    if age < MIN_AGE:
        return f"Vous devez avoir au moins {MIN_AGE} ans pour créer un compte."
    if age > MAX_AGE:
        return "Vérifiez la date de naissance saisie."
    return None


def image_type(content: bytes) -> Optional[str]:
    """Type réel de l'image d'après ses premiers octets (jamais d'après le nom du fichier)."""
    if content.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "webp"
    return None


def initials(first: str, last: str, fallback: str = "?") -> str:
    letters = [w[0].upper() for w in f"{first or ''} {last or ''}".split() if w][:2]
    return "".join(letters) or fallback
