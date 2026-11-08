"""Règles pures de recherche et de recommandation d'offres similaires (testables sans base)."""
import math


def similar_score(base_skills: set, other_skills: set, same_type: bool, same_location: bool) -> int:
    """Plus le score est élevé, plus l'offre ressemble à l'offre de départ."""
    return 2 * len(base_skills & other_skills) + (1 if same_type else 0) + (1 if same_location else 0)


def page_count(total: int, page_size: int) -> int:
    return max(1, math.ceil(total / page_size)) if page_size > 0 else 1
