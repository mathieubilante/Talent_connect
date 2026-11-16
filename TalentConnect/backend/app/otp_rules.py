"""Règles pures du code OTP (sans base de données, donc faciles à tester)."""
import hashlib
import hmac
import math
import re
import secrets
from datetime import datetime
from typing import Optional

OTP_LENGTH = 6
OTP_TTL_SECONDS = 600          # le code expire après 10 minutes
MAX_ATTEMPTS = 5               # essais de saisie par code
RESEND_DELAY_SECONDS = 60      # délai minimum entre deux envois
MAX_SENDS_PER_HOUR = 5         # envois maximum par heure et par compte


def generate_code() -> str:
    return "".join(str(secrets.randbelow(10)) for _ in range(OTP_LENGTH))


def hash_code(secret: str, user_id: int, code: str) -> str:
    """Le code n'est jamais stocké en clair : seulement son empreinte HMAC-SHA256."""
    return hmac.new(secret.encode(), f"{user_id}:{code}".encode(), hashlib.sha256).hexdigest()


def verify_code(secret: str, user_id: int, code: str, code_hash: str) -> bool:
    return hmac.compare_digest(hash_code(secret, user_id, code), code_hash)


def is_expired(expires_at: datetime, now: datetime) -> bool:
    return now >= expires_at


def seconds_until_resend(last_created: Optional[datetime], now: datetime,
                         delay: int = RESEND_DELAY_SECONDS) -> int:
    if last_created is None:
        return 0
    return max(0, math.ceil(delay - (now - last_created).total_seconds()))


def normalize_phone(raw: str, default_country_code: str = "+228") -> Optional[str]:
    s = re.sub(r"[\s\-\.\(\)]", "", raw or "")
    if s.startswith("00"):
        s = "+" + s[2:]
    if not s.startswith("+"):
        if not s.isdigit():
            return None
        s = default_country_code + s if len(s) == 8 else "+" + s
    return s if re.fullmatch(r"\+\d{8,15}", s) else None


def parse_identifier(raw: str, default_country_code: str = "+228"):
    """Retourne ('email', valeur) ou ('phone', valeur normalisée), ou (None, None)."""
    raw = (raw or "").strip()
    if "@" in raw:
        return "email", raw.lower()
    phone = normalize_phone(raw, default_country_code)
    return ("phone", phone) if phone else (None, None)


def mask_contact(channel: str, destination: str) -> str:
    if channel == "email" and "@" in destination:
        name, domain = destination.split("@", 1)
        return f"{name[:1]}***@{domain}"
    return f"{destination[:4]}****{destination[-2:]}"
