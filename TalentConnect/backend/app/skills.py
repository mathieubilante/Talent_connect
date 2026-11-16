"""Dictionnaire de compétences et extraction automatique depuis un texte (CV, offre)."""
import re

SKILLS: dict[str, list[str]] = {
    "python": [], "java": [], "javascript": ["js"], "typescript": [], "php": [],
    "c++": ["cpp"], "c#": ["csharp"], "html": [], "css": [], "tailwind": ["tailwindcss"],
    "react": ["reactjs", "react.js"], "angular": [], "vue": ["vue.js", "vuejs"],
    "node.js": ["nodejs"], "fastapi": [], "django": [], "flask": [], "laravel": [],
    "spring boot": ["springboot"], "flutter": [], "dart": [], "react native": [],
    "sql": [], "mysql": [], "postgresql": ["postgres"], "mongodb": [],
    "docker": [], "git": [], "github": [], "linux": [], "aws": [], "azure": [],
    "rest api": ["api rest", "apis rest"], "machine learning": ["apprentissage automatique"],
    "deep learning": [], "nlp": ["traitement du langage naturel"], "pandas": [],
    "data analysis": ["analyse de données", "analyse de donnees"], "power bi": ["powerbi"],
    "excel": [], "figma": [], "ui/ux": ["ux", "ui design"], "photoshop": [],
    "scrum": ["agile"], "gestion de projet": ["project management"],
    "comptabilité": ["comptabilite"], "finance": [], "marketing digital": [],
    "communication": [], "anglais": ["english"], "réseaux": ["reseaux", "networking"],
    "cybersécurité": ["cybersecurite"], "réseaux sociaux": ["reseaux sociaux", "community management"],
}

_ALIAS_TO_CANON: dict[str, str] = {}
for canon, aliases in SKILLS.items():
    _ALIAS_TO_CANON[canon] = canon
    for a in aliases:
        _ALIAS_TO_CANON[a] = canon


def canonical(skill: str) -> str:
    """Ramène une compétence saisie librement à sa forme standard (ex. ReactJS -> react)."""
    s = skill.strip().lower()
    return _ALIAS_TO_CANON.get(s, s)


def split_skills(raw: str) -> list[str]:
    return [canonical(s) for s in re.split(r"[,;\n]", raw or "") if s.strip()]


def _pattern(term: str) -> re.Pattern:
    return re.compile(r"(?<![a-z0-9+#])" + re.escape(term) + r"(?![a-z0-9+#])")


_PATTERNS = {canon: [_pattern(t) for t in [canon, *aliases]] for canon, aliases in SKILLS.items()}


def extract_skills(text: str) -> list[str]:
    """Détecte les compétences connues présentes dans un texte."""
    low = (text or "").lower()
    found = [canon for canon, pats in _PATTERNS.items() if any(p.search(low) for p in pats)]
    return sorted(found)
