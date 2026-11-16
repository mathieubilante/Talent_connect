from datetime import datetime, timedelta

from app.session_rules import session_expiry, session_state, should_touch

NOW = datetime(2026, 11, 10, 12, 0, 0)


def _state(**kw):
    base = dict(now=NOW, expires_at=NOW + timedelta(hours=5), last_seen_at=NOW - timedelta(minutes=5),
                revoked_at=None, idle_minutes=30)
    base.update(kw)
    return session_state(**base)


def test_session_valide():
    assert _state() == "ok"


def test_nouvelle_connexion_ailleurs_ferme_la_session():
    assert _state(revoked_at=NOW - timedelta(minutes=1)) == "revoked"


def test_expiration_maximale():
    assert _state(expires_at=NOW - timedelta(seconds=1)) == "expired"


def test_inactivite():
    assert _state(last_seen_at=NOW - timedelta(minutes=31)) == "idle"
    assert _state(last_seen_at=NOW - timedelta(minutes=29)) == "ok"


def test_ecriture_de_derniere_activite_limitee():
    assert not should_touch(NOW - timedelta(seconds=30), NOW)
    assert should_touch(NOW - timedelta(seconds=61), NOW)
    assert session_expiry(NOW, 12) == NOW + timedelta(hours=12)
