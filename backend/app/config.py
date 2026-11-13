import os

try:  # charge backend/.env s'il existe ; sans lui, les valeurs par défaut suffisent
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./talentconnect.db")
if DATABASE_URL.startswith("postgres://"):      # Render/Heroku donnent postgres:// ; SQLAlchemy veut postgresql://
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-a-changer")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
CORS_ORIGINS = [o.strip().rstrip("/") for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_CV_SIZE = 5 * 1024 * 1024  # 5 Mo

# Compte administrateur créé au premier démarrage (à changer en production)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@talentconnect.tg")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin2026!")
ADMIN_PASSWORD_FROM_ENV = "ADMIN_PASSWORD" in os.environ     # mot de passe choisi explicitement par l'hébergeur

# --- Vérification par code OTP (étape 2) ---
# OTP_DEV_MODE=true : le code est aussi renvoyé par l'API (démonstration). METTRE false en production.
OTP_DEV_MODE = os.getenv("OTP_DEV_MODE", "true").lower() == "true"
# console : le code s'affiche dans le terminal du backend ; smtp : envoi réel par e-mail
OTP_DELIVERY = os.getenv("OTP_DELIVERY", "console").lower()
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "no-reply@talentconnect.tg")
DEFAULT_COUNTRY_CODE = os.getenv("DEFAULT_COUNTRY_CODE", "+228")   # Togo

# --- Documents KYC (étape 3) ---
KYC_DIR = os.getenv("KYC_DIR", "uploads/kyc")
MAX_KYC_SIZE = 5 * 1024 * 1024   # 5 Mo par document
# Clé de chiffrement Fernet (44 caractères). Générer :
#   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Sans clé, une clé de développement est dérivée de SECRET_KEY (à ne pas utiliser en production).
KYC_ENCRYPTION_KEY = os.getenv("KYC_ENCRYPTION_KEY", "")


# --- Connexion avec Google et données de démonstration ---
# Identifiant client OAuth Google (voir DEPLOIEMENT.md). Vide = bouton Google masqué.
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
# SEED_DEMO_DATA=true : crée les comptes et offres de démonstration au démarrage (utile sur un hébergement sans console)
SEED_DEMO_DATA = os.getenv("SEED_DEMO_DATA", "false").lower() == "true"

# --- Paiement (étape 5) et sessions (étape 6) ---
# simulated : paiement de démonstration (aucun argent réel). Un vrai fournisseur (Mobile Money, carte) sera branché plus tard.
PAYMENT_PROVIDER = os.getenv("PAYMENT_PROVIDER", "simulated").lower()
SESSION_IDLE_MINUTES = int(os.getenv("SESSION_IDLE_MINUTES", "30"))   # déconnexion après inactivité
SESSION_MAX_HOURS = int(os.getenv("SESSION_MAX_HOURS", "12"))         # durée maximale d'une session

# --- Alertes de sécurité (étape 7) : tous facultatifs ; sans configuration, les alertes restent dans l'application et dans les journaux ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
TWILIO_SMS_FROM = os.getenv("TWILIO_SMS_FROM", "").strip()                 # numéro ou nom d'expéditeur SMS
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "").strip()       # ex. +14155238886 (sandbox WhatsApp Twilio)
