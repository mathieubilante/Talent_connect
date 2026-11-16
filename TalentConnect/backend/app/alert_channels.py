"""Canaux d'alerte : SMS et WhatsApp (Twilio), Telegram (Bot API). Sans identifiants configurés, le message est
simplement journalisé (mode démonstration) et le statut retourné est « console »."""
import base64
import json
import urllib.parse
import urllib.request

from .config import (TELEGRAM_BOT_TOKEN, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_SMS_FROM,
                     TWILIO_WHATSAPP_FROM)


def _post(url: str, data: bytes, headers: dict) -> bool:
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except Exception as exc:
        print(f"[ALERTE] échec d'envoi : {exc}", flush=True)
        return False


def _twilio(to: str, sender: str, text: str) -> bool:
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    auth = base64.b64encode(f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode()).decode()
    data = urllib.parse.urlencode({"To": to, "From": sender, "Body": text}).encode()
    return _post(url, data, {"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"})


def send_sms(to: str, text: str) -> str:
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_SMS_FROM:
        return "sent" if _twilio(to, TWILIO_SMS_FROM, text) else "failed"
    print(f"[ALERTE SMS] {to} : {text}", flush=True)
    return "console"


def send_whatsapp(to: str, text: str) -> str:
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_WHATSAPP_FROM:
        return "sent" if _twilio(f"whatsapp:{to}", f"whatsapp:{TWILIO_WHATSAPP_FROM}", text) else "failed"
    print(f"[ALERTE WhatsApp] {to} : {text}", flush=True)
    return "console"


def send_telegram(chat_id: str, text: str) -> str:
    if TELEGRAM_BOT_TOKEN:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        ok = _post(url, json.dumps({"chat_id": chat_id, "text": text}).encode(), {"Content-Type": "application/json"})
        return "sent" if ok else "failed"
    print(f"[ALERTE Telegram] {chat_id} : {text}", flush=True)
    return "console"
