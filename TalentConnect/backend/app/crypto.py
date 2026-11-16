"""Chiffrement des documents KYC (Fernet : AES + authentification HMAC).
Les fichiers ne sont JAMAIS stockés en clair sur le disque."""
import base64
import hashlib

from cryptography.fernet import Fernet

from .config import KYC_ENCRYPTION_KEY, SECRET_KEY


def _fernet() -> Fernet:
    if KYC_ENCRYPTION_KEY:
        return Fernet(KYC_ENCRYPTION_KEY.encode())
    # Clé de développement dérivée de SECRET_KEY (changer SECRET_KEY changerait la clé !)
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(("kyc:" + SECRET_KEY).encode()).digest()))


def encrypt_bytes(data: bytes) -> bytes:
    return _fernet().encrypt(data)


def decrypt_bytes(token: bytes) -> bytes:
    return _fernet().decrypt(token)   # lève InvalidToken si le fichier a été altéré


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
