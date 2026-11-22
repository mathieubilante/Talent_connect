"""Restauration d'une sauvegarde chiffrée, après vérification complète.

Usage : python -m tools.restore sauvegardes/AAAAMMJJ_HHMMSS  [--dest dossier_de_restauration]
La restauration n'écrase JAMAIS la base active : elle écrit dans un dossier séparé pour contrôle.
"""
import json
import os
import sys

from app.backup_core import restore_backup
from app.config import DATA_ENCRYPTION_KEY
from app.secure_crypto import load_key


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage : python -m tools.restore <dossier_de_sauvegarde> [--dest <dossier>]")
        sys.exit(1)
    src = sys.argv[1]
    dest = sys.argv[sys.argv.index("--dest") + 1] if "--dest" in sys.argv else os.path.join(src, "restauration")
    if not DATA_ENCRYPTION_KEY:
        print("Restauration impossible : DATA_ENCRYPTION_KEY n'est pas défini.")
        sys.exit(1)
    with open(os.path.join(src, "sauvegarde.tcbak"), "rb") as f:
        sealed = f.read()
    with open(os.path.join(src, "manifeste.json"), "rb") as f:
        manifest = json.load(f)
    try:
        files = restore_backup(sealed, manifest, load_key(DATA_ENCRYPTION_KEY))
    except ValueError as exc:
        print(f"Sauvegarde REFUSÉE : {exc}")
        sys.exit(2)
    for name, content in files.items():
        target = os.path.join(dest, name)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "wb") as f:
            f.write(content)
    print(f"Sauvegarde vérifiée et restaurée dans : {dest} ({len(files)} fichier(s))")
    print("Vérifiez les fichiers avant de remplacer la base active.")


if __name__ == "__main__":
    main()
