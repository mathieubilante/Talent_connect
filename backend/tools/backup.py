"""Sauvegarde CHIFFRÉE (AES-256-GCM) : base de données + documents.

Usage (dossier backend, environnement activé) : python -m tools.backup
Prérequis : DATA_ENCRYPTION_KEY défini (voir config.py). Sans clé, la sauvegarde est refusée.
"""
import datetime
import json
import os
import sys

from app.backup_core import make_backup, manifest_to_json
from app.config import DATA_ENCRYPTION_KEY, DATABASE_URL, KYC_DIR
from app.secure_crypto import load_key


def _read_tree(root: str, prefix: str) -> dict:
    out = {}
    if os.path.isdir(root):
        for dirpath, _, names in os.walk(root):
            for n in names:
                full = os.path.join(dirpath, n)
                rel = os.path.relpath(full, root).replace("\\", "/")
                with open(full, "rb") as f:
                    out[f"{prefix}/{rel}"] = f.read()
    return out


def main() -> None:
    if not DATA_ENCRYPTION_KEY:
        print("Sauvegarde refusée : DATA_ENCRYPTION_KEY n'est pas défini. Une sauvegarde non chiffrée n'est pas autorisée.")
        sys.exit(1)
    key = load_key(DATA_ENCRYPTION_KEY)
    files = {}
    if DATABASE_URL.startswith("sqlite:///") and os.path.isfile(DATABASE_URL[len("sqlite:///"):]):
        with open(DATABASE_URL[len("sqlite:///"):], "rb") as f:
            files["database/talentconnect.db"] = f.read()
    else:
        print("Base non SQLite : utilisez pg_dump puis chiffrez le fichier, ou la sauvegarde de votre hébergeur.")
    files.update(_read_tree(KYC_DIR, "documents"))
    if not files:
        print("Rien à sauvegarder.")
        return
    sealed, manifest = make_backup(files, key)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join("sauvegardes", stamp)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "sauvegarde.tcbak"), "wb") as f:
        f.write(sealed)
    with open(os.path.join(out, "manifeste.json"), "wb") as f:
        f.write(manifest_to_json(manifest))
    print(f"Sauvegarde chiffrée créée : {out} ({len(files)} fichier(s))")
    print("IMPORTANT : conservez la clé DATA_ENCRYPTION_KEY dans un coffre séparé. Sans elle, la sauvegarde est illisible.")


if __name__ == "__main__":
    main()
