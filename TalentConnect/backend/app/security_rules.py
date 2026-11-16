"""Règles pures de détection : tentatives échouées, nouvel appareil, activité suspecte, messages d'alerte."""
import hashlib
import math
from datetime import datetime, timedelta
from typing import Optional

MAX_FAILURES = 5            # tentatives échouées avant verrouillage temporaire
FAILURE_WINDOW_MIN = 15     # fenêtre de comptage ET durée du verrouillage
WARN_AT_FAILURES = 3        # alerte au propriétaire après 3 échecs
SUSPICIOUS_IPS = 3          # 3 adresses différentes en 10 minutes
SUSPICIOUS_WINDOW_MIN = 10


def failures_since_last_success(attempts, now: datetime, window_minutes: int = FAILURE_WINDOW_MIN):
    """attempts : liste (date, succès) triée de la plus ancienne à la plus récente.
    Retourne (nombre d'échecs récents depuis le dernier succès, date du dernier échec)."""
    limit = now - timedelta(minutes=window_minutes)
    failures, last = 0, None
    for when, ok in attempts:
        if when < limit:
            continue
        if ok:
            failures, last = 0, None
        else:
            failures, last = failures + 1, when
    return failures, last


def lock_state(failures: int, last_failure: Optional[datetime], now: datetime,
               max_failures: int = MAX_FAILURES, lock_minutes: int = FAILURE_WINDOW_MIN):
    """(verrouillé, secondes restantes)."""
    if failures < max_failures or last_failure is None:
        return False, 0
    remaining = (last_failure + timedelta(minutes=lock_minutes) - now).total_seconds()
    return (remaining > 0), max(0, math.ceil(remaining))


def device_key(user_agent: str) -> str:
    return hashlib.sha256((user_agent or "").encode()).hexdigest()[:12]


def ip_prefix(ip: str) -> str:
    """Regroupe les adresses voisines (un opérateur change souvent le dernier nombre)."""
    if ":" in (ip or ""):
        return ":".join(ip.split(":")[:4])
    parts = (ip or "").split(".")
    return ".".join(parts[:3]) if len(parts) == 4 else (ip or "")


def is_new_device(previous, ip: str, user_agent: str) -> bool:
    """previous : liste (ip, user_agent) des connexions passées. La toute première connexion ne déclenche pas d'alerte."""
    if not previous:
        return False
    known = {(ip_prefix(i), device_key(u)) for i, u in previous}
    return (ip_prefix(ip), device_key(user_agent)) not in known


def distinct_recent_ips(events, now: datetime, window_minutes: int = SUSPICIOUS_WINDOW_MIN) -> int:
    """events : liste (date, ip). Nombre d'adresses (regroupées) vues dans la fenêtre."""
    limit = now - timedelta(minutes=window_minutes)
    return len({ip_prefix(ip) for when, ip in events if when >= limit and ip})


def is_suspicious(distinct_ips: int) -> bool:
    return distinct_ips >= SUSPICIOUS_IPS


def mask_ip(ip: str) -> str:
    if not ip:
        return "adresse inconnue"
    if ":" in ip:
        return ":".join(ip.split(":")[:3]) + ":…"
    parts = ip.split(".")
    return ".".join(parts[:2]) + ".•.•" if len(parts) == 4 else ip


ALERT_KINDS = {
    "new_device": ("🆕", "Nouvelle connexion"),
    "failed_attempts": ("⚠️", "Tentatives de connexion échouées"),
    "account_locked": ("🔒", "Compte verrouillé temporairement"),
    "suspicious_activity": ("🚨", "Activité suspecte"),
    "session_replaced": ("🔁", "Session fermée"),
    "test": ("🔔", "Alerte de test"),
}


def alert_message(kind: str, ip: str = "", extra: str = "") -> str:
    where = f" depuis {mask_ip(ip)}" if ip else ""
    if kind == "new_device":
        return f"Nouvelle connexion à votre compte TalentConnect{where}, depuis un appareil ou un lieu inhabituel. Si ce n'est pas vous, utilisez la connexion par code puis contactez l'administration."
    if kind == "failed_attempts":
        return f"Plusieurs tentatives de connexion à votre compte ont échoué{where}. Si ce n'est pas vous, ne communiquez jamais vos codes."
    if kind == "account_locked":
        return f"Votre compte est verrouillé pour {FAILURE_WINDOW_MIN} minutes après trop de tentatives échouées{where}. Vous pouvez vous connecter avec un code reçu."
    if kind == "suspicious_activity":
        return f"Activité suspecte : connexions rapprochées depuis plusieurs adresses{where}. Vérifiez votre activité récente."
    if kind == "session_replaced":
        return f"Votre session précédente a été fermée car une nouvelle connexion a été ouverte{where}."
    if kind == "test":
        return "Ceci est une alerte de test : vos notifications de sécurité fonctionnent."
    return extra or "Alerte de sécurité."
