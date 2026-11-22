"""Règles pures de lisibilité du CV (sans dépendance)."""
MIN_READABLE_CHARS = 50


def is_readable(text: str) -> bool:
    """Un CV est lisible s'il contient assez de texte. Un scan (image) donne un texte vide ou presque."""
    return len((text or "").strip()) >= MIN_READABLE_CHARS


def unreadable_message() -> str:
    return ("Votre CV ne contient pas de texte lisible : il s'agit probablement d'un scan ou d'une photo. "
            "Les compétences n'ont pas pu être détectées. Déposez une version numérique du CV (exportée depuis "
            "Word ou Google Docs) pour que le matching fonctionne.")
