"""Chiffrement AES-256-GCM (confidentialité + intégrité) et masquage des données sensibles dans les journaux.

Format d'un message chiffré : VERSION (3 octets) + nonce aléatoire (12 octets) + texte chiffré et étiquette GCM.
Le « contexte » (ex. "backup") est lié au chiffrement : un fichier chiffré pour un usage ne peut pas être déchiffré
pour un autre. Toute modification du fichier, ou une mauvaise clé, est détectée et refusée.
"""
import base64
import hashlib
import os
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

VERSION = b"TC1"
NONCE_BYTES = 12
SENSITIVE_WORDS = ("password", "mot_de_passe", "token", "secret", "code", "key", "cle", "iban", "card", "carte", "cin", "otp")


def load_key(b64: str) -> bytes:
    """Clé de 256 bits, fournie en base64 (32 octets une fois décodée)."""
    try:
        raw = base64.urlsafe_b64decode(b64.strip().encode())
    except Exception as exc:
        raise ValueError("Clé de chiffrement invalide (base64 attendu)") from exc
    if len(raw) != 32:
        raise ValueError("La clé doit faire 256 bits (32 octets) une fois décodée")
    return raw


def generate_key_b64() -> str:
    return base64.urlsafe_b64encode(os.urandom(32)).decode()


def encrypt(plaintext: bytes, key: bytes, context: str) -> bytes:
    nonce = os.urandom(NONCE_BYTES)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, context.encode())
    return VERSION + nonce + ciphertext


def decrypt(blob: bytes, key: bytes, context: str) -> bytes:
    if not blob.startswith(VERSION) or len(blob) < len(VERSION) + NONCE_BYTES + 16:
        raise ValueError("Format de données chiffrées non reconnu")
    nonce = blob[len(VERSION):len(VERSION) + NONCE_BYTES]
    body = blob[len(VERSION) + NONCE_BYTES:]
    try:
        return AESGCM(key).decrypt(nonce, body, context.encode())
    except InvalidTag as exc:
        raise ValueError("Données altérées, clé incorrecte ou mauvais contexte") from exc


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def redact(data: Any) -> Any:
    """Copie d'un dictionnaire où les valeurs sensibles sont masquées, pour les journaux."""
    if isinstance(data, dict):
        out = {}
        for k, v in data.items():
            low = str(k).lower()
            out[k] = "***" if any(w in low for w in SENSITIVE_WORDS) else redact(v)
        return out
    if isinstance(data, list):
        return [redact(x) for x in data]
    return data
