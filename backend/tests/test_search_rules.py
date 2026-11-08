from app.search_rules import page_count, similar_score


def test_offres_similaires():
    base = {"python", "sql"}
    assert similar_score(base, {"python", "sql"}, True, True) == 6
    assert similar_score(base, {"python"}, False, False) == 2
    assert similar_score(base, {"excel"}, True, False) == 1
    assert similar_score(base, set(), False, False) == 0


def test_nombre_de_pages():
    assert page_count(0, 8) == 1
    assert page_count(8, 8) == 1
    assert page_count(9, 8) == 2
    assert page_count(25, 10) == 3
