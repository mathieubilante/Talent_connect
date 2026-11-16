from datetime import datetime, timedelta

from app.otp_rules import (OTP_LENGTH, generate_code, hash_code, is_expired, mask_contact,
                           normalize_phone, parse_identifier, seconds_until_resend, verify_code)


def test_code_6_chiffres():
    for _ in range(50):
        c = generate_code()
        assert len(c) == OTP_LENGTH and c.isdigit()


def test_code_stocke_hache_et_verifiable():
    h = hash_code("secret", 7, "123456")
    assert "123456" not in h and len(h) == 64
    assert verify_code("secret", 7, "123456", h)
    assert not verify_code("secret", 7, "654321", h)
    assert not verify_code("secret", 8, "123456", h)       # lié à l'utilisateur
    assert not verify_code("autre", 7, "123456", h)        # lié à la clé secrète


def test_expiration():
    now = datetime(2026, 11, 5, 12, 0, 0)
    assert not is_expired(now + timedelta(minutes=1), now)
    assert is_expired(now - timedelta(seconds=1), now)


def test_delai_avant_renvoi():
    now = datetime(2026, 11, 5, 12, 0, 0)
    assert seconds_until_resend(None, now) == 0
    assert seconds_until_resend(now - timedelta(seconds=20), now) == 40
    assert seconds_until_resend(now - timedelta(seconds=90), now) == 0


def test_telephone():
    assert normalize_phone("90 12 34 56") == "+22890123456"        # numéro local togolais
    assert normalize_phone("+228 90-12-34-56") == "+22890123456"
    assert normalize_phone("0022890123456") == "+22890123456"
    assert normalize_phone("abc") is None and normalize_phone("123") is None


def test_identifiant():
    assert parse_identifier("Jean@Mail.COM ") == ("email", "jean@mail.com")
    assert parse_identifier("90123456") == ("phone", "+22890123456")
    assert parse_identifier("???") == (None, None)


def test_masquage():
    assert mask_contact("email", "mathieu@gmail.com") == "m***@gmail.com"
    assert mask_contact("phone", "+22890123456") == "+228****56"
