from app.review_rules import (account_decision_error, can_review_document, review_error,
                              validation_blockers)


def test_seul_un_document_envoye_peut_etre_examine():
    assert can_review_document("submitted")
    assert not can_review_document("approved")
    assert not can_review_document("rejected")


def test_refus_exige_un_motif():
    assert review_error("rejected", "") is not None
    assert review_error("rejected", "   ") is not None
    assert review_error("rejected", "Photo floue") is None
    assert review_error("approved", "") is None
    assert review_error("peut-etre", "x") is not None


def test_validation_du_compte_exige_tous_les_documents_valides():
    required = ["cin_representant", "patente", "extrait_rne"]
    assert validation_blockers(required, {"cin_representant": "approved", "patente": "approved",
                                          "extrait_rne": "approved"}) == []
    blockers = validation_blockers(required, {"cin_representant": "approved", "patente": "submitted"})
    assert len(blockers) == 2
    assert any("Patente" in b and "pas encore validé" in b for b in blockers)
    assert any("RNE" in b and "non fourni" in b for b in blockers)
    assert "refusé" in validation_blockers(["cin"], {"cin": "rejected"})[0]


def test_particulier_une_seule_cin():
    assert validation_blockers(["cin"], {"cin": "approved"}) == []


def test_decision_sur_le_compte():
    assert account_decision_error("validate", "") is None
    assert account_decision_error("reject", "") is not None
    assert account_decision_error("reject", "Documents falsifiés") is None
    assert account_decision_error("autre", "x") is not None
