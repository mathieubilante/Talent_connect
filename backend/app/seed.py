"""Données de démonstration : python -m app.seed  (idempotent)."""
from . import models
from .database import Base, SessionLocal, engine
from .accounts import get_or_create_account
from .security import hash_password

PASSWORD = "Demo1234!"

COMPANIES = [
    ("tech@demo.tg", "Togo Digital Solutions", "Technologie", "Lomé"),
    ("agri@demo.tg", "AgriTech Togo", "Agriculture", "Kara"),
    ("finance@demo.tg", "Lomé Finance Conseil", "Finance", "Lomé"),
]

OFFERS = {
    "tech@demo.tg": [
        ("Stage développeur backend Python", "stage", "python, fastapi, sql, docker", "Lomé",
         "Participez au développement d'API REST pour nos clients. Encadrement par un développeur senior."),
        ("Développeur web React", "emploi", "react, javascript, css, git", "Lomé",
         "Conception d'interfaces web modernes et responsives pour des applications métier."),
        ("Stage UI/UX Designer", "stage", "figma, ui/ux, html, css", "Lomé",
         "Création de maquettes et prototypes pour une plateforme mobile."),
    ],
    "agri@demo.tg": [
        ("Stage analyste de données", "stage", "python, pandas, excel, sql", "Kara",
         "Analyse des données de production agricole et création de tableaux de bord."),
        ("Responsable marketing digital", "emploi", "marketing digital, communication, réseaux sociaux", "Kara",
         "Pilotage de la communication en ligne et des campagnes sur les réseaux sociaux."),
    ],
    "finance@demo.tg": [
        ("Stage assistant comptable", "stage", "comptabilité, excel, finance", "Lomé",
         "Saisie comptable, rapprochements bancaires et reporting mensuel."),
        ("Analyste financier junior", "emploi", "finance, excel, power bi, anglais", "Lomé",
         "Analyse de la performance financière et production de rapports pour la direction."),
        ("Stage développeur mobile Flutter", "stage", "flutter, dart, rest api", "Lomé",
         "Développement de l'application mobile de suivi client."),
    ],
}

CANDIDATES = [
    ("kofi@demo.tg", "Kofi", "Mensah", "Licence Informatique - ENP", "python, sql, fastapi, docker, git",
     "Étudiant en informatique passionné par le développement backend et les API."),
    ("ama@demo.tg", "Ama", "Adjovi", "Licence Design numérique", "react, javascript, css, figma, html",
     "Développeuse front-end et designer d'interfaces, projets web et maquettes."),
    ("yao@demo.tg", "Yao", "Agbeko", "Master Comptabilité et Finance", "comptabilité, excel, power bi, finance, anglais",
     "Étudiant en comptabilité, analyse financière et reporting."),
    ("afi@demo.tg", "Afi", "Dossou", "Licence Communication", "marketing digital, communication, réseaux sociaux",
     "Community manager, gestion de campagnes et création de contenus."),
]


def run() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for email, name, sector, city in COMPANIES:
            if db.query(models.User).filter_by(email=email).first():
                continue
            u = models.User(email=email, password_hash=hash_password(PASSWORD), role=models.Role.company)
            db.add(u); db.flush()
            comp = models.Company(user_id=u.id, name=name, sector=sector, city=city,
                                  description=f"{name}, entreprise du secteur {sector}.")
            db.add(comp); db.flush()
            for title, kind, skills, loc, desc in OFFERS[email]:
                db.add(models.JobOffer(company_id=comp.id, title=title, offer_type=models.OfferType(kind),
                                       required_skills=skills, location=loc, description=desc))
        for email, first, last, edu, skills, text in CANDIDATES:
            if db.query(models.User).filter_by(email=email).first():
                continue
            u = models.User(email=email, password_hash=hash_password(PASSWORD), role=models.Role.candidate)
            db.add(u); db.flush()
            db.add(models.Candidate(user_id=u.id, first_name=first, last_name=last, education=edu,
                                    skills=skills, cv_text=text))
        db.commit()
        for u in db.query(models.User).filter(models.User.email.like("%@demo.tg")).all():
            acc = get_or_create_account(db, u)
            if acc.status == "pending" and acc.trial_logins_used == 0:
                acc.status = "active"
        # compte d'essai pour la démonstration : 27 connexions déjà utilisées sur 30
        if not db.query(models.User).filter_by(email="essai@demo.tg").first():
            u = models.User(email="essai@demo.tg", password_hash=hash_password(PASSWORD), role=models.Role.candidate)
            db.add(u); db.flush()
            db.add(models.Candidate(user_id=u.id, first_name="Essai", last_name="Gratuit",
                                    education="Licence Informatique", skills="python, sql"))
            db.flush()
            acc = get_or_create_account(db, u)
            acc.trial_logins_used = 27
        db.commit()
        print(f"Données de démonstration créées. Mot de passe de tous les comptes : {PASSWORD}")
        print("Entreprises : tech@demo.tg, agri@demo.tg, finance@demo.tg")
        print("Candidats   : kofi@demo.tg, ama@demo.tg, yao@demo.tg, afi@demo.tg (comptes actifs)")
        print("Essai gratuit : essai@demo.tg (27 connexions utilisées sur 30, pour la démonstration)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
