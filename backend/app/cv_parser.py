import pdfplumber


def extract_pdf_result(path: str) -> dict:
    """Texte d'un PDF et diagnostic. Ne masque plus les erreurs : elles sont signalées."""
    try:
        with pdfplumber.open(path) as pdf:
            text = "\n".join((page.extract_text() or "") for page in pdf.pages)
            return {"text": text, "pages": len(pdf.pages), "error": False}
    except Exception:
        return {"text": "", "pages": 0, "error": True}


def extract_pdf_text(path: str) -> str:
    return extract_pdf_result(path)["text"]
