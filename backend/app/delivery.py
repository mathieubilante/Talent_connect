"""Envoi du code OTP. Modes : console (démonstration) ou e-mail SMTP.
Le SMS n'est pas encore branché : une fonction `send_sms` sera ajoutée quand
l'entreprise aura choisi son fournisseur (Twilio, fournisseur local...)."""
import smtplib
from email.message import EmailMessage

import json
import urllib.request

from .config import (BREVO_API_KEY, BREVO_SENDER_EMAIL, BREVO_SENDER_NAME, OTP_DELIVERY, OTP_DEV_MODE, SMTP_FROM,
                     SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USER)


def _send_via_brevo(to: str, subject: str, body: str) -> bool:
    """Envoi par l'API Brevo (HTTPS, port 443 : jamais bloqué, contrairement au SMTP sur Render)."""
    payload = json.dumps({"sender": {"email": BREVO_SENDER_EMAIL, "name": BREVO_SENDER_NAME},
                          "to": [{"email": to}], "subject": subject, "textContent": body}).encode()
    req = urllib.request.Request("https://api.brevo.com/v3/smtp/email", data=payload, method="POST",
                                 headers={"api-key": BREVO_API_KEY, "Content-Type": "application/json",
                                          "accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return 200 <= resp.status < 300
    except Exception as exc:
        print(f"[OTP] échec d'envoi Brevo vers {to} : {exc}", flush=True)
        return False



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
    """Retourne le mode d'envoi réellement utilisé : 'email', 'sms', 'console' ou 'failed'.

    En mode réel (OTP_DELIVERY=smtp), un code n'est JAMAIS seulement affiché dans les journaux :
    s'il ne peut pas partir, on renvoie 'failed' et l'appelant le signale à l'utilisateur."""
    real_mode = OTP_DELIVERY == "smtp"
    if channel == "phone":
        from .alert_channels import TWILIO_ACCOUNT_SID, TWILIO_SMS_FROM, send_sms
        if TWILIO_ACCOUNT_SID and TWILIO_SMS_FROM:
            return "sms" if send_sms(destination, f"TalentConnect : votre code de vérification est {code}. Valable 10 minutes.") == "sent" else "failed"
        if real_mode:
            return "failed"                                    # pas de fournisseur SMS configuré
        print(f"\n[OTP] téléphone={destination} code={code}\n", flush=True)
        return "console"
    if channel == "email" and real_mode and BREVO_API_KEY and BREVO_SENDER_EMAIL:
        body = f"Votre code de vérification TalentConnect est : {code}\n\nIl expire dans 10 minutes. Ne le communiquez à personne."
        return "email" if _send_via_brevo(destination, "Votre code de vérification TalentConnect", body) else "failed"
    if channel == "email" and real_mode and SMTP_HOST:
        try:
            _send_email(destination, code)
            return "email"
        except Exception as exc:  # l'utilisateur pourra redemander un code
            print(f"[OTP] échec d'envoi e-mail vers {destination} : {exc}", flush=True)
            return "failed"
    if real_mode:
        return "failed"                                        # e-mail demandé mais SMTP non configuré
    if OTP_DEV_MODE:                                       # le code n'est écrit dans les journaux qu'en démonstration
        print(f"\n[OTP-DEMO] canal={channel} destinataire={destination} code={code}\n", flush=True)
    else:
        print(f"[OTP] aucun envoi réel configuré (canal={channel}). Vérifiez OTP_DELIVERY et SMTP_*.", flush=True)
    return "console"


def send_email_message(to: str, subject: str, body: str) -> str:
    """E-mail générique (alertes). Retourne 'email', 'console' ou 'failed'."""
    if OTP_DELIVERY == "smtp" and BREVO_API_KEY and BREVO_SENDER_EMAIL:
        return "email" if _send_via_brevo(to, subject, body) else "failed"
    if OTP_DELIVERY == "smtp" and SMTP_HOST:
        try:
            msg = EmailMessage()
            msg["Subject"], msg["From"], msg["To"] = subject, SMTP_FROM, to
            msg.set_content(body)
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
                server.starttls()
                if SMTP_USER:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
            return "email"
        except Exception as exc:
            print(f"[ALERTE] échec d'envoi e-mail vers {to} : {exc}", flush=True)
            return "failed"
    print(f"\n[ALERTE e-mail] {to} : {subject}\n{body}\n", flush=True)
    return "console"
