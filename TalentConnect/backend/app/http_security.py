"""En-têtes de sécurité HTTP pour l'API.

L'API renvoie du JSON et des fichiers : on ajoute des en-têtes qui empêchent le navigateur
de deviner le type d'un fichier, de charger l'API dans un cadre (clickjacking), et qui
imposent HTTPS (HSTS). La politique de contenu (CSP) du SITE est définie côté Vercel,
pas ici : une CSP stricte sur l'API ne protégerait pas le site.
"""
from typing import Dict

HSTS_MAX_AGE = 31_536_000  # un an


def security_headers(hsts: bool = True) -> Dict[str, str]:
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    }
    if hsts:
        headers["Strict-Transport-Security"] = f"max-age={HSTS_MAX_AGE}; includeSubDomains"
    return headers


def apply_security_headers(response_headers, hsts: bool = True) -> None:
    """Ajoute les en-têtes à une réponse et retire ceux qui révèlent le serveur."""
    for name, value in security_headers(hsts).items():
        response_headers[name] = value
    for name in ("server", "x-powered-by"):
        if name in response_headers:
            del response_headers[name]
