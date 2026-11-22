import pytest

from app.backup_core import make_backup, restore_backup
from app.secure_crypto import generate_key_b64, load_key

KEY = load_key(generate_key_b64())
FILES = {"talentconnect.db": b"base de test", "documents/cin.enc": b"document chiffre"}


def test_sauvegarde_puis_restauration_identique():
    sealed, manifest = make_backup(FILES, KEY)
    assert restore_backup(sealed, manifest, KEY) == FILES


def test_archive_alteree_refusee():
    sealed, manifest = make_backup(FILES, KEY)
    bad = bytearray(sealed)
    bad[40] ^= 0xFF
    with pytest.raises(ValueError):
        restore_backup(bytes(bad), manifest, KEY)


def test_manifeste_modifie_refuse():
    sealed, manifest = make_backup(FILES, KEY)
    manifest["files"]["talentconnect.db"] = "0" * 64
    with pytest.raises(ValueError):
        restore_backup(sealed, manifest, KEY)


def test_mauvaise_cle_refusee():
    sealed, manifest = make_backup(FILES, KEY)
    with pytest.raises(ValueError):
        restore_backup(sealed, manifest, load_key(generate_key_b64()))


def test_fichier_manquant_detecte():
    sealed, manifest = make_backup(FILES, KEY)
    manifest["files"]["fantome.txt"] = "0" * 64
    with pytest.raises(ValueError):
        restore_backup(sealed, manifest, KEY)
