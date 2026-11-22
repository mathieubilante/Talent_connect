"""Règles pures de l'import d'offres (CSV, XLSX) : détection du format, lecture, validation ligne par ligne."""
import csv
import io
import re
from datetime import date, datetime
from typing import Optional

MAX_IMPORT_BYTES = 1 * 1024 * 1024
MAX_ROWS = 500
REQUIRED_COLUMNS = ["titre", "description", "type"]
OPTIONAL_COLUMNS = ["competences", "lieu", "date_limite"]
OFFER_TYPES = {"emploi", "stage"}


def detect_format(content: bytes) -> Optional[str]:
    """Format réel du fichier d'après son contenu (jamais d'après l'extension)."""
    if content.startswith(b"PK\x03\x04"):
        return "xlsx"
    if b"\x00" in content[:1024]:
        return None                      # binaire inconnu (ex. ancien XLS, exécutable renommé)
    try:
        text = content.decode("utf-8-sig").lstrip()
    except UnicodeDecodeError:
        return None
    if text.startswith(("{", "[")):
        return "json"
    if text.startswith("<"):
        return "xml"
    return "csv"


def read_json(content: bytes) -> tuple:
    """JSON : une liste d'objets, ou un objet {"offres": [...]}. Clés et valeurs converties en texte."""
    import json
    data = json.loads(content.decode("utf-8-sig"))
    if isinstance(data, dict):
        data = data.get("offres", data.get("offers", []))
    if not isinstance(data, list):
        raise ValueError("JSON : une liste d'offres est attendue")
    headers, rows = [], []
    for i, obj in enumerate(data, start=1):
        if not isinstance(obj, dict):
            raise ValueError("JSON : chaque offre doit être un objet")
        item = {}
        for k, v in obj.items():
            key = _norm_header(k)
            if key not in headers:
                headers.append(key)
            item[key] = "" if v is None else str(v).strip()
        rows.append((i + 1, item))
    return headers, rows


def read_xml(content: bytes) -> tuple:
    """XML : <offres><offre><titre>…</titre>…</offre></offres>. Balises converties en en-têtes."""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(content)
    headers, rows = [], []
    for i, node in enumerate(list(root), start=1):
        if not len(node):
            continue
        item = {}
        for child in node:
            key = _norm_header(child.tag)
            if key not in headers:
                headers.append(key)
            item[key] = (child.text or "").strip()
        rows.append((i + 1, item))
    return headers, rows


def _norm_header(h) -> str:
    return re.sub(r"\s+", "_", str(h or "").strip().lower())


def read_csv(content: bytes) -> tuple:
    text = content.decode("utf-8-sig")
    sample = text[:2000]
    delimiter = ";" if sample.count(";") > sample.count(",") else ","
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = [r for r in reader if any(c.strip() for c in r)]
    return _to_dicts(rows)


def read_xlsx(content: bytes) -> tuple:
    from openpyxl import load_workbook          # dépendance listée dans requirements.txt
    wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    sheet = wb.worksheets[0]
    rows = [[("" if c is None else str(c)) for c in r] for r in sheet.iter_rows(values_only=True)]
    rows = [r for r in rows if any(c.strip() for c in r)]
    return _to_dicts(rows)


def _to_dicts(rows: list) -> tuple:
    """Retourne (en-têtes normalisés, liste de dictionnaires avec le numéro de ligne Excel/CSV)."""
    if not rows:
        return [], []
    headers = [_norm_header(h) for h in rows[0]]
    data = []
    for line_no, row in enumerate(rows[1:], start=2):
        item = {headers[i]: (row[i].strip() if i < len(row) and row[i] is not None else "")
                for i in range(len(headers)) if headers[i]}
        data.append((line_no, item))
    return headers, data


def missing_headers(headers: list) -> list:
    return [c for c in REQUIRED_COLUMNS if c not in headers]


def parse_deadline(raw: str) -> Optional[date]:
    raw = (raw or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def validate_row(item: dict, today: date) -> tuple:
    """Retourne (offre propre ou None, liste des erreurs)."""
    errors = []
    title = item.get("titre", "")
    desc = item.get("description", "")
    kind = item.get("type", "").lower()
    if not (3 <= len(title) <= 150):
        errors.append("titre : entre 3 et 150 caractères")
    if not (10 <= len(desc) <= 5000):
        errors.append("description : entre 10 et 5000 caractères")
    if kind not in OFFER_TYPES:
        errors.append("type : « emploi » ou « stage » attendu")
    location = item.get("lieu", "")[:150]
    skills = ", ".join(s.strip() for s in re.split(r"[,;]", item.get("competences", "")) if s.strip())[:1000]
    deadline = None
    if item.get("date_limite", ""):
        deadline = parse_deadline(item["date_limite"])
        if deadline is None:
            errors.append("date_limite : format AAAA-MM-JJ ou JJ/MM/AAAA attendu")
        elif deadline < today:
            errors.append("date_limite : déjà passée")
    if errors:
        return None, errors
    return {"title": title, "description": desc, "offer_type": kind, "location": location,
            "required_skills": skills, "deadline": deadline}, []


def duplicate_key(offer: dict) -> tuple:
    return (offer["title"].strip().lower(), offer["location"].strip().lower())
