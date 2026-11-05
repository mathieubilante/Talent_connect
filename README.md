# TalentConnect

Plateforme web et mobile intelligente de recrutement, d'emploi et de gestion des stages.
**Version 0.1 : base du projet (rapport n°1).**

## Fonctionnalités (version 0.2)
**IA**
- **Matching détaillé** : score 0-100 %, niveau (excellent / bon / moyen / faible), compétences en commun et manquantes, explication en français.
- **Analyse du CV** : le PDF est lu et les compétences détectées sont ajoutées au profil automatiquement.
- **Recommandations** : offres les plus adaptées au candidat ; profils les plus adaptés à chaque offre pour l'entreprise.
- **Assistant IA (chatbot)** : conseils CV, entretien, stage, offres recommandées, compétences à développer, adapté au rôle et au profil.
- **Lettre de motivation générée** automatiquement pour chaque offre au moment de postuler.

**Plateforme**
- Page d'accueil, inscription/connexion JWT avec rôles (candidat, entreprise, administrateur).
- Offres emploi/stage avec recherche, filtres et tri par compatibilité ; favoris.
- Candidatures avec statuts (reçue, présélectionnée, entretien, acceptée, refusée).
- Notifications à chaque événement (nouvelle candidature, changement de statut).
- Espace candidat (profil complété en %, candidatures, favoris, recommandations).
- Espace entreprise (indicateurs, publication, gestion des offres, candidatures classées, talents IA).
- Administration : statistiques, compétences les plus demandées, liste des utilisateurs.

## Comptes et sécurité (versions 0.3 et 0.4)
- Statuts de compte (en attente, validé, actif, refusé) et essai gratuit limité à 30 connexions, historique des connexions.
- Inscription par e-mail ou téléphone avec code OTP (le code s'affiche dans le terminal du backend en mode démonstration).

## Prévu pour la suite
Embeddings Sentence-Transformers, gestion des stages (convention, suivi, évaluation), notifications par e-mail, application mobile.

## Données de démonstration
Pour remplir la plateforme (3 entreprises, 8 offres, 4 candidats) :
```bash
# sans Docker (dans backend/, venv activé)
python -m app.seed
# avec Docker
docker compose exec backend python -m app.seed
```
Mot de passe de tous les comptes démo : `Demo1234!`
Entreprises : `tech@demo.tg`, `agri@demo.tg`, `finance@demo.tg` · Candidats : `kofi@demo.tg`, `ama@demo.tg`, `yao@demo.tg`, `afi@demo.tg`
**Administrateur** (créé automatiquement) : `admin@talentconnect.tg` / `Admin2026!` (à changer via `ADMIN_EMAIL` et `ADMIN_PASSWORD`).

## Structure
```
TalentConnect/
├── backend/        API FastAPI (app/), module IA (app/matching.py), tests
├── frontend/       Application React (Vite)
├── database/       schema.sql (PostgreSQL)
├── docs/           Rapports, maquettes, diagrammes UML
├── docker-compose.yml
└── README.md
```

## Lancer le projet (méthode simple, sans Docker)

### 1. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows : venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # Windows : copy .env.example .env
python -m uvicorn app.main:app --reload
```
API : http://localhost:8000 · Documentation interactive (Swagger) : http://localhost:8000/docs

Pour PostgreSQL, installez aussi : `pip install -r requirements-postgres.txt`.

Par défaut le projet utilise SQLite (aucune installation requise). Les tables sont créées automatiquement.

### 2. Frontend
```bash
cd frontend
npm install
cp .env.example .env              # Windows : copy .env.example .env
npm run dev
```
Application : http://localhost:5173

### 3. Avec Docker (PostgreSQL + API)
```bash
docker compose up --build
```
Puis lancer le frontend comme ci-dessus. Pour utiliser `database/schema.sql` à la main :
`psql -U tc_user -d talentconnect -f database/schema.sql` (à faire avant le premier démarrage de l'API).

## Scénario de démonstration
1. Créer un compte **Entreprise**, publier une offre de stage avec des compétences requises (ex. `python, sql, fastapi`).
2. Créer un compte **Candidat**, renseigner ses compétences et déposer un CV PDF.
3. Consulter la liste des offres : le **score de compatibilité** apparaît, les offres sont triées.
4. Postuler en un clic, puis se reconnecter en entreprise : la candidature apparaît, classée par score, avec changement de statut possible.

## Tests
```bash
cd backend
pytest
```

## Principaux endpoints
| Méthode | Route | Rôle |
|---|---|---|
| POST | /auth/register, /auth/login | public |
| GET/PUT | /profile/candidate | candidat |
| POST | /profile/candidate/cv | candidat |
| GET | /offers | connecté (score si candidat) |
| POST | /offers | entreprise |
| POST | /applications | candidat |
| GET | /applications/received | entreprise |
| PATCH | /applications/{id}/status | entreprise |
