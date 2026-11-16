"""Module de matching candidat / offre.

Score = 60 % compétences couvertes + 40 % similarité TF-IDF du texte.
`analyze_match` renvoie aussi les compétences en commun / manquantes et une
explication lisible. Évolution prévue : embeddings Sentence-Transformers
(il suffira de remplacer `_text_similarity`).
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .skills import extract_skills, split_skills


def _text_similarity(a: str, b: str) -> float:
    if not a.strip() or not b.strip():
        return 0.0
    try:
        matrix = TfidfVectorizer(lowercase=True).fit_transform([a, b])
    except ValueError:
        return 0.0
    return float(cosine_similarity(matrix[0], matrix[1])[0][0])


def _level(score: float) -> str:
    if score >= 75:
        return "excellent"
    if score >= 50:
        return "bon"
    if score >= 25:
        return "moyen"
    return "faible"


def analyze_match(candidate_skills: str, candidate_text: str, offer_title: str,
                  offer_description: str, required_skills: str) -> dict:
    declared = set(split_skills(candidate_skills)) | set(extract_skills(candidate_text))
    required = set(split_skills(required_skills))
    if not required:  # offre sans compétences listées : on les détecte dans le texte
        required = set(extract_skills(f"{offer_title} {offer_description}"))

    matched = sorted(required & declared)
    missing = sorted(required - declared)
    coverage = len(matched) / len(required) if required else 0.0
    profile_text = f"{' '.join(sorted(declared))} {candidate_text}"
    similarity = _text_similarity(profile_text, f"{offer_title} {offer_description} {' '.join(sorted(required))}")

    raw = 0.6 * coverage + 0.4 * similarity if required else similarity
    score = round(min(max(raw, 0.0), 1.0) * 100, 1)

    if required:
        explanation = f"{len(matched)} compétence(s) sur {len(required)} requise(s) correspondent à votre profil."
        if missing:
            explanation += f" À renforcer : {', '.join(missing[:3])}."
    else:
        explanation = "Score basé sur la similarité entre le profil et le texte de l'offre."

    return {"score": score, "level": _level(score), "matched": matched,
            "missing": missing, "explanation": explanation}


def compute_match_score(candidate_skills: str, candidate_text: str, offer_title: str,
                        offer_description: str, required_skills: str) -> float:
    return analyze_match(candidate_skills, candidate_text, offer_title,
                         offer_description, required_skills)["score"]
