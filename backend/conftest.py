"""Configuration des tests : base SQLite temporaire et paramètres de test, définis AVANT l'import de l'application."""
import os
import tempfile

import pytest

_TMP = tempfile.mkdtemp(prefix="tc_tests_")
os.environ.update({
    "DATABASE_URL": f"sqlite:///{_TMP}/test.db",
    "SECRET_KEY": "cle-de-test-uniquement",
    "ADMIN_PASSWORD": "AdminTest2026!",
    "OTP_DEV_MODE": "true",
    "OTP_DELIVERY": "console",
    "PAYMENT_PROVIDER": "simulated",
    "KYC_DIR": os.path.join(_TMP, "kyc"),
    "UPLOAD_DIR": os.path.join(_TMP, "uploads"),
    "SEED_DEMO_DATA": "false",
    "GOOGLE_CLIENT_ID": "",
})


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def kyc_dir():
    return os.environ["KYC_DIR"]
