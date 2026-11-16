"""Vérification d'un jeton « Se connecter avec Google » (Google Identity Services)."""
from fastapi import HTTPException

from .config import GOOGLE_CLIENT_ID


def verify_google_credential(credential: str) -> dict:
    """Retourne les informations du compte Google (email, name...) si le jeton est authentique."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(503, "La connexion Google n'est pas configurée sur ce serveur.")
    try:
        from google.auth.transport import requests as g_requests
        from google.oauth2 import id_token
    except ImportError:
        raise HTTPException(503, "Bibliothèque Google non installée sur le serveur (google-auth).")
    try:
        # Vérifie la signature, l'expiration, l'émetteur ET que le jeton est destiné à CETTE application
        info = id_token.verify_oauth2_token(credential, g_requests.Request(), GOOGLE_CLIENT_ID)
    except ValueError:
        raise HTTPException(401, "Jeton Google invalide ou expiré. Réessayez.")
    except Exception:
        raise HTTPException(502, "Impossible de contacter Google pour le moment.")
    if not info.get("email") or not info.get("email_verified"):
        raise HTTPException(401, "L'adresse e-mail Google n'est pas vérifiée.")
    return info
