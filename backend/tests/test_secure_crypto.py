import pytest

from app.secure_crypto import decrypt, encrypt, generate_key_b64, load_key, redact


def test_aller_retour_et_texte_illisible():
    key = load_key(generate_key_b64())
    blob = encrypt(b"CONFIDENTIEL 123", key, "kyc")
    assert b"CONFIDENTIEL" not in blob
    assert decrypt(blob, key, "kyc") == b"CONFIDENTIEL 123"


def test_nonce_aleatoire_chaque_chiffrement():
    key = load_key(generate_key_b64())
    assert encrypt(b"meme texte", key, "x") != encrypt(b"meme texte", key, "x")


def test_modification_detectee():
    key = load_key(generate_key_b64())
    blob = bytearray(encrypt(b"donnees", key, "x"))
    blob[-1] ^= 1
    with pytest.raises(ValueError):
        decrypt(bytes(blob), key, "x")


def test_mauvaise_cle_ou_mauvais_contexte_refuses():
    k1, k2 = load_key(generate_key_b64()), load_key(generate_key_b64())
    blob = encrypt(b"donnees", k1, "backup")
    with pytest.raises(ValueError):
        decrypt(blob, k2, "backup")
    with pytest.raises(ValueError):
        decrypt(blob, k1, "kyc")          # un chiffré pour un usage ne sert pas pour un autre


def test_cle_de_taille_incorrecte_refusee():
    import base64
    with pytest.raises(ValueError):
        load_key(base64.urlsafe_b64encode(b"court").decode())
    with pytest.raises(ValueError):
        load_key("pas du base64 !!")


def test_masquage_pour_les_journaux():
    out = redact({"email": "a@b.tg", "password": "secret1", "otp_code": "123456",
                  "nested": {"auth_token": "abc"}, "nom": "Kofi"})
    assert out == {"email": "a@b.tg", "password": "***", "otp_code": "***",
                   "nested": {"auth_token": "***"}, "nom": "Kofi"}
