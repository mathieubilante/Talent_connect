"""Vérifications au démarrage : avertit des réglages dangereux pour une mise en ligne (règle pure, testable)."""


def collect_warnings(secret_key: str, admin_from_env: bool, kyc_key: str, otp_dev_mode: bool,
                     cors_origins: list, database_url: str, hosted: bool) -> list:
    out = []
    if secret_key == "dev-secret-a-changer":
        out.append("SECRET_KEY par défaut : définissez une valeur longue et secrète.")
    if not admin_from_env:
        out.append("ADMIN_PASSWORD non défini : le mot de passe administrateur par défaut est public.")
    if not kyc_key:
        out.append("KYC_ENCRYPTION_KEY absente : une clé de développement est utilisée pour chiffrer les documents.")
    if otp_dev_mode:
        out.append("OTP_DEV_MODE=true : les codes de vérification s'affichent sur le site (démonstration seulement).")
    if hosted and not database_url.startswith("sqlite") and all("localhost" in o or "127.0.0.1" in o for o in cors_origins):
        out.append("CORS_ORIGINS ne contient que localhost : le site publié ne pourra pas joindre l'API.")
    if hosted and database_url.startswith("sqlite"):
        out.append("SQLite sur un hébergement : les données ne sont pas permanentes. Utilisez PostgreSQL.")
    return out
