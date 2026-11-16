from app.matching import analyze_match, compute_match_score
from app.skills import canonical, extract_skills


def test_bon_profil_score_eleve():
    score = compute_match_score("python, fastapi, sql", "Développeur backend Python",
                                "Développeur Python", "API REST avec FastAPI et SQL",
                                "python, fastapi, sql")
    assert score > 60


def test_mauvais_profil_score_faible():
    score = compute_match_score("comptabilité, excel", "Comptable junior",
                                "Développeur Python", "API REST avec FastAPI",
                                "python, fastapi")
    assert score < 20


def test_score_dans_les_bornes():
    assert 0 <= compute_match_score("", "", "", "", "") <= 100


def test_competences_communes_et_manquantes():
    a = analyze_match("python, docker", "", "Dev", "desc", "python, sql, docker")
    assert a["matched"] == ["docker", "python"]
    assert a["missing"] == ["sql"]


def test_alias_reconnus():
    assert canonical("ReactJS") == "react"
    assert "react" in extract_skills("Projet en ReactJS et Node.js")


def test_java_ne_confond_pas_javascript():
    skills = extract_skills("Je connais JavaScript")
    assert "javascript" in skills and "java" not in skills
