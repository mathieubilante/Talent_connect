from app.startup_checks import collect_warnings


def test_aucun_avertissement_pour_une_configuration_saine():
    assert collect_warnings("cle-longue-et-secrete", True, "cle-kyc", False, ["https://site.vercel.app"],
                            "postgresql://u:p@h/db", hosted=True) == []


def test_avertissements_de_securite():
    w = " ".join(collect_warnings("dev-secret-a-changer", False, "", True, ["http://localhost:5173"],
                                  "postgresql://u:p@h/db", hosted=True))
    for mot in ("SECRET_KEY", "ADMIN_PASSWORD", "KYC_ENCRYPTION_KEY", "OTP_DEV_MODE", "CORS_ORIGINS"):
        assert mot in w


def test_sqlite_sur_un_hebergement():
    assert any("SQLite" in x for x in collect_warnings("k", True, "k", False, ["https://x"], "sqlite:///a.db", hosted=True))
    assert not any("SQLite" in x for x in collect_warnings("k", True, "k", False, ["https://x"], "sqlite:///a.db", hosted=False))
