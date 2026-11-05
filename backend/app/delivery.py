"""Envoi du code OTP. Modes : console (démonstration) ou e-mail SMTP.
Le SMS n'est pas encore branché : une fonction `send_sms` sera ajoutée quand
l'entreprise aura choisi son fournisseur (Twilio, fournisseur local...)."""
import smtplib
from email.message import EmailMessage

from .config import OTP_DELIVERY, SMTP_FROM, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USER


def _send_email(to: str, code: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = "Votre code de vérification TalentConnect"
    msg["From"], msg["To"] = SMTP_FROM, to
    msg.set_content(f"Votre code de vérification est : {code}\n\n"
                    "Il expire dans 10 minutes. Ne le communiquez à personne.")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
        server.starttls()
        if SMTP_USER:
            server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


def deliver_otp(channel: str, destination: str, code: str) -> str:
    """Retourne le mode d'envoi réellement utilisé : 'email', 'console' ou 'failed'."""
    if channel == "email" and OTP_DELIVERY == "smtp" and SMTP_HOST:
        try:
            _send_email(destination, code)
            return "email"
        except Exception as exc:  # l'utilisateur pourra redemander un code
            print(f"[OTP] échec d'envoi e-mail vers {destination} : {exc}", flush=True)
            return "failed"
    print(f"\n[OTP] canal={channel} destinataire={destination} code={code}\n", flush=True)
    return "console"
