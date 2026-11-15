"""Headers de sécurité HTTP pour l'API TalentConnect.

Ces réponses protègent à la fois l'API (HSTS, X-Content-Type-Options, X-Frame-Options)
et le site front (CSP, Referrer-Policy). Règle pure, testable sans base de données.
"""
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# CSP : par défaut, on n'autorise que le même origine (le site) + les connexions à l'API.
# Les scripts, styles et images viennent de soi-même ; les connexions AJAX/WS vers l'API.
# Aucune ressource externe (CDN, analytics) n'est chargée sans être explicitement listée.
_DEFAULT_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob:; "
    "font-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "object-src 'none'; "
    "upgrade-in-requests"
)


def security_headers_middleware(app: FastAPI, *, csp: str = _DEFAULT_CSP,
                                hsts_max_age: int = 31_536_000, hsts_include_subdomains: bool = True,
                                enabled: bool = True) -> None:
    """Ajoute les headers de sécurité à chaque réponse HTTP."""

    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            if not enabled:
                return await call_next(request)
            response: Response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Cache-Control"] = "no-store"
            response.headers["Permissions-Policy"] = (
                "camera=(), microphone=(), geolocation=(), interest-cohort=()"
            )
            response.headers["Content-Security-Policy"] = csp
            response.headers["Strict-Transport-Security"] = (
                f"max-age={hsts_max_age}"
                + ("; includeSubDomains" if hsts_include_subdomains else "")
            )
            # On masque les informations qui aident les attaquants à fingerprinter le serveur.
            response.headers.pop("Server", None)
            response.headers.pop("X-Powered-By", None)
            return response

    app.add_middleware(SecurityHeadersMiddleware)
    return app


def build_csp(allowed_connect_origins: list[str] | None = None) -> str:
    """Construit une CSP personnalisée. Par défaut, 'self' uniquement."""
    if not allowed_connect_origins:
        return _DEFAULT_CSP
    connect = "self " + " ".join(allowed_connect_origins)
    return _DEFAULT_CSP.replace("connect-src 'self';", f"connect-src {connect};")