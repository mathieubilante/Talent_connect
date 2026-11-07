import pytest
from cryptography.fernet import InvalidToken

from app.crypto import decrypt_bytes, encrypt_bytes, sha256_hex


def test_chiffrement_aller_retour():
    data = b"%PDF-1.7 contenu confidentiel de la CIN"
    enc = encrypt_bytes(data)
    assert enc != data and b"confidentiel" not in enc      # rien de lisible sur le disque
    assert decrypt_bytes(enc) == data


def test_fichier_altere_detecte():
    enc = bytearray(encrypt_bytes(b"document"))
    enc[20] ^= 0x01
    with pytest.raises(InvalidToken):
        decrypt_bytes(bytes(enc))


def test_empreinte():
    assert len(sha256_hex(b"abc")) == 64
