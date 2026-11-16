from datetime import datetime, timedelta

from app.security_rules import (alert_message, device_key, distinct_recent_ips, failures_since_last_success, ip_prefix,
                                is_new_device, is_suspicious, lock_state, mask_ip)

NOW = datetime(2026, 11, 12, 10, 0, 0)


def _fails(n, start_min_ago=10):
    return [(NOW - timedelta(minutes=start_min_ago - i), False) for i in range(n)]


def test_verrouillage_apres_5_echecs():
    failures, last = failures_since_last_success(_fails(5), NOW)
    assert failures == 5
    locked, remaining = lock_state(failures, last, NOW)
    assert locked and 0 < remaining <= 15 * 60


def test_pas_de_verrouillage_avant_5_echecs():
    failures, last = failures_since_last_success(_fails(4), NOW)
    assert failures == 4 and lock_state(failures, last, NOW) == (False, 0)


def test_un_succes_remet_le_compteur_a_zero():
    attempts = _fails(4) + [(NOW - timedelta(minutes=2), True)]
    assert failures_since_last_success(attempts, NOW)[0] == 0


def test_les_anciens_echecs_sont_ignores():
    old = [(NOW - timedelta(minutes=40 + i), False) for i in range(6)]
    assert failures_since_last_success(old, NOW)[0] == 0


def test_le_verrouillage_se_termine():
    failures, last = failures_since_last_success(_fails(5, start_min_ago=14), NOW)
    assert lock_state(failures, last, NOW + timedelta(minutes=20)) == (False, 0)


def test_nouvel_appareil():
    prev = [("41.207.10.5", "Chrome/120 Windows")]
    assert not is_new_device([], "1.2.3.4", "X")                                   # première connexion
    assert not is_new_device(prev, "41.207.10.99", "Chrome/120 Windows")           # même réseau, même navigateur
    assert is_new_device(prev, "41.207.10.5", "Safari iPhone")                     # autre appareil
    assert is_new_device(prev, "102.64.1.1", "Chrome/120 Windows")                 # autre réseau


def test_activite_suspecte_plusieurs_adresses():
    events = [(NOW - timedelta(minutes=m), ip) for m, ip in ((1, "1.1.1.1"), (3, "2.2.2.2"), (5, "3.3.3.3"), (40, "4.4.4.4"))]
    assert distinct_recent_ips(events, NOW) == 3 and is_suspicious(3) and not is_suspicious(2)


def test_ip_masquee_et_prefixe():
    assert mask_ip("41.207.10.5") == "41.207.•.•" and mask_ip("") == "adresse inconnue"
    assert ip_prefix("41.207.10.5") == "41.207.10" and device_key("a") == device_key("a") != device_key("b")


def test_messages_d_alerte():
    assert "nouvelle connexion" in alert_message("new_device", "41.207.10.5").lower()
    assert "15 minutes" in alert_message("account_locked")
    assert "test" in alert_message("test").lower()
