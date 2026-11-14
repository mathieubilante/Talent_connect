"""Sauvegarde des données : base de données + documents chiffrés.

Utilisation (depuis le dossier backend, environnement Python activé) :   python -m tools.backup
- SQLite : copie du fichier de base de données.
- PostgreSQL : export avec pg_dump (doit être installé ; sur Render, utilisez aussi les sauvegardes du service de base de données).
Le dossier créé (sauvegardes/AAAAMMJJ_HHMMSS) contient des données sensibles : ne le publiez jamais sur GitHub.
"""
import datetime
import os
import shutil
import subprocess

from app.config import DATABASE_URL, KYC_DIR, UPLOAD_DIR


def main() -> None:
    out = os.path.join("sauvegardes", datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(out, exist_ok=True)

    if DATABASE_URL.startswith("sqlite:///"):
        path = DATABASE_URL[len("sqlite:///"):]
        if os.path.isfile(path):
            shutil.copy2(path, os.path.join(out, "talentconnect.db"))
            print("Base SQLite copiée.")
        else:
            print(f"Fichier de base introuvable : {path}")
    elif shutil.which("pg_dump"):
        subprocess.run(["pg_dump", "--no-owner", "-f", os.path.join(out, "talentconnect.sql"), DATABASE_URL], check=True)
        print("Base PostgreSQL exportée.")
    else:
        print("pg_dump est introuvable : installez les outils PostgreSQL ou utilisez les sauvegardes de votre hébergeur.")

    for source, name in ((KYC_DIR, "documents_chiffres"), (UPLOAD_DIR, "cv")):
        if os.path.isdir(source):
            shutil.copytree(source, os.path.join(out, name), dirs_exist_ok=True)
            print(f"Dossier copié : {name}")

    print(f"\nSauvegarde créée dans : {out}")
    print("IMPORTANT : sauvegardez séparément la clé KYC_ENCRYPTION_KEY (sans elle, les documents chiffrés sont illisibles).")


if __name__ == "__main__":
    main()
