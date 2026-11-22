"""Sauvegarde chiffrée et restauration vérifiée (fonctions pures : pas de base ni de réseau)."""
import io
import json
import zipfile
from typing import Dict

from .secure_crypto import decrypt, encrypt, sha256_bytes

BACKUP_CONTEXT = "backup-v1"


def make_backup(files: Dict[str, bytes], key: bytes) -> tuple:
    """Retourne (archive chiffrée, manifeste). Le manifeste contient l'empreinte de chaque fichier."""
    buf = io.BytesIO()
    manifest = {"version": 1, "files": {}}
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
            manifest["files"][name] = sha256_bytes(content)
    sealed = encrypt(buf.getvalue(), key, BACKUP_CONTEXT)
    manifest["archive_sha256"] = sha256_bytes(sealed)
    return sealed, manifest


def restore_backup(sealed: bytes, manifest: dict, key: bytes) -> Dict[str, bytes]:
    """Vérifie l'archive puis retourne les fichiers. Lève ValueError si la moindre donnée ne correspond pas."""
    if sha256_bytes(sealed) != manifest.get("archive_sha256"):
        raise ValueError("Sauvegarde altérée : l'empreinte de l'archive ne correspond pas")
    plain = decrypt(sealed, key, BACKUP_CONTEXT)
    files = {}
    with zipfile.ZipFile(io.BytesIO(plain)) as zf:
        for name in zf.namelist():
            content = zf.read(name)
            if sha256_bytes(content) != manifest["files"].get(name):
                raise ValueError(f"Fichier altéré dans la sauvegarde : {name}")
            files[name] = content
    if set(files) != set(manifest["files"]):
        raise ValueError("Sauvegarde incomplète : des fichiers manquent")
    return files


def manifest_to_json(manifest: dict) -> bytes:
    return json.dumps(manifest, indent=2, ensure_ascii=False).encode()
