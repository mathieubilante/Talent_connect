import pdfplumber


def extract_pdf_text(path: str) -> str:
    """Extrait le texte d'un CV au format PDF."""
    try:
        with pdfplumber.open(path) as pdf:
            return "\n".join((page.extract_text() or "") for page in pdf.pages)
    except Exception:
        return ""
