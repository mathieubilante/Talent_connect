# TalentConnect : contexte du projet (à coller au début d'une conversation avec l'IA)

**Stage de 3 mois (12 semaines)** : plateforme web et mobile intelligente de recrutement, d'emploi et de gestion des stages.
Stagiaire : Mathieu OUKPIL BILANTE. Rapport journalier obligatoire chaque jour : fichier Word + code source zippé + vidéo de démonstration + version complète du projet.

## Lancement (Windows)
1_INSTALLER.bat (une fois) puis 2_LANCER.bat ; 3_REINITIALISER_DONNEES.bat pour tout remettre à zéro. Voir LISEZ-MOI.txt. SQLite par défaut, Docker facultatif.

## Stack
Backend : Python, FastAPI, SQLAlchemy 2, JWT (PyJWT) + bcrypt, PostgreSQL (SQLite en dev), Docker Compose.
IA : scikit-learn (TF-IDF), pdfplumber. Frontend : React (Vite), axios, react-router. Mobile : Flutter (plus tard).

## Structure
- backend/app : main.py, config.py, database.py, models.py, schemas.py, security.py, services.py
  - account_rules.py (règles pures : statuts, essai 30 connexions) · accounts.py (accès base des comptes)
  - kyc_rules.py (règles pures KYC) · crypto.py (chiffrement Fernet) · routers/kyc.py
  - search_rules.py (offres similaires, pagination) · routers/public.py (API publique sans connexion)
  - otp_rules.py (règles pures OTP) · otp.py (création/vérification des codes) · delivery.py (envoi : console ou SMTP)
  - matching.py, skills.py, cv_parser.py, assistant_logic.py, seed.py
  - routers/ : auth, account, profiles, offers, applications, favorites, notifications, recommendations, assistant, admin
- backend/tests : tests unitaires (matching, assistant, règles de compte)
- frontend/src : App.jsx, api.js, components/ (OfferCard, MatchBar, Chips, Chatbot, TrialBanner), pages/ (Home, Login, Offers, CandidateSpace, CompanySpace, Notifications, Admin, Account)
- database/schema.sql : schéma PostgreSQL. ATTENTION : SQLAlchemy create_all ne modifie jamais une table existante ; toute modification de colonne = script SQL ou migration.

## Tables
users, candidates, companies, job_offers, applications, favorites, notifications, internships*, evaluations* (*pas encore utilisées),
**user_accounts** (statut + compteur d'essai), **login_history** (historique des connexions),
**user_contacts** (téléphone, canal, compte vérifié ou non), **otp_codes** (codes OTP hachés),
**kyc_documents** (métadonnées des documents), **kyc_access_log** (journal d'audit : dépôt, consultation, suppression).

## Cahier des charges "cycle de vie du compte" (réalisé par étapes)
1. Statuts (pending, validated, active, rejected) + essai gratuit limité à **30 connexions au total** (pas une durée) + historique des connexions : **FAIT (étape 1)**
2. Inscription e-mail/téléphone + code OTP : **FAIT (étape 2)**
3. Documents KYC (CIN ; entreprises : CIN représentant, patente, extrait RNE < 3 mois), stockage chiffré : **FAIT (étape 3)**
4. Validation/refus administrateur : **FAIT (étape 4)**
5. Abonnement, paiement, activation, création de l'environnement : **FAIT (étape 5, paiement simulé)**
6. Une seule session active, déconnexion après inactivité, gestion sécurisée des jetons : **FAIT (étape 6)** ; reste « comportements suspects » (étape 7)
7. Alertes de sécurité (e-mail, SMS, WhatsApp, Telegram), détection de comportements suspects : **FAIT (étape 7)**
8. Passage essai -> actif sans perte de données, tests, déploiement : à faire

## Règles de l'étape 1 (implémentées)
- Compteur `trial_logins_used` dans `user_accounts`, incrémenté par un UPDATE atomique côté base (condition `< trial_limit`) : non contournable par déconnexion, autre appareil ou autre navigateur.
- L'inscription compte comme la 1re connexion. Les administrateurs sont exclus. Les comptes `active` ne consomment rien.
- À la 30e connexion : essai suspendu (accès refusé `403 TRIAL_EXPIRED` sur les routes métier), notification envoyée. /account/me, /account/login-history et /notifications restent accessibles.
- Alerte quand il reste 5 connexions ou moins. Compte `rejected` : connexion refusée.
- Pour changer la règle (ex. autoriser la 30e session complète) : modifier uniquement `account_rules.py`.
- Dernière activité mise à jour au plus 1 fois par minute (security.get_current_user).

## Règles de l'étape 2 (OTP, implémentées)
- Inscription par **e-mail ou téléphone** (numéro normalisé, indicatif par défaut +228). Un compte créé est **non vérifié** : connexion refusée (`403 NOT_VERIFIED`) tant que le code n'est pas validé.
- Flux : `POST /auth/register` (crée le compte + envoie le code) → `POST /auth/verify-otp` (vérifie, ouvre la session, compte comme la 1re connexion d'essai) ; `POST /auth/resend-otp` pour redemander un code.
- Code à 6 chiffres, valable 10 min, 5 essais par code, 60 s entre deux envois, 5 envois par heure. Le code est stocké **haché** (HMAC-SHA256), jamais en clair.
- Connexion possible avec e-mail OU téléphone. Les comptes historiques (sans ligne dans `user_contacts`) sont considérés comme vérifiés.
- Pour un compte inscrit par téléphone, `users.email` contient un e-mail technique `tel<numéro>@phone.invalid` (la colonne est obligatoire).
- Envoi : mode `console` (code affiché dans le terminal du backend) par défaut ; `OTP_DELIVERY=smtp` pour un vrai e-mail. **SMS : pas encore branché** (fournisseur à choisir). `OTP_DEV_MODE=true` renvoie aussi le code dans la réponse de l'API pour la démonstration : **à mettre à false en production**.
- Tout changement de règle OTP : `otp_rules.py`.

## Règles de l'étape 3 (documents KYC, implémentées)
- Particuliers (candidats) : **CIN**. Entreprises : **CIN du représentant**, **patente**, **extrait RNE de moins de 3 mois** (date d'émission saisie et contrôlée : refus si > 3 mois ou dans le futur).
- Formats PDF, JPG, PNG, 5 Mo max ; le type est vérifié sur le **contenu réel** du fichier (octets d'en-tête), pas sur l'extension.
- Stockage : chaque fichier est **chiffré (Fernet, AES + HMAC)** avant d'être écrit dans `uploads/kyc/<nom aléatoire>.enc` ; jamais servi statiquement. Clé : `KYC_ENCRYPTION_KEY` (en dev, dérivée de SECRET_KEY ; **obligatoire en production**). Toute altération d'un fichier est détectée au déchiffrement.
- Accès : seul le propriétaire ou un administrateur peut télécharger (404 pour les autres). Un document `approved` ne peut plus être remplacé/supprimé. Remplacer un document supprime l'ancien fichier.
- Journal d'audit `kyc_access_log` (qui, quoi, quand, IP). Notification aux administrateurs quand un dossier devient complet.
- Les routes /kyc/* restent accessibles quand l'essai est épuisé (c'est là qu'on soumet ses documents).
- La validation/refus par l'administrateur (statuts `approved`/`rejected`, motif) arrive à l'étape 4 ; les colonnes existent déjà.

## Règles de l'étape 4 (validation administrative, implémentées)
- L'administrateur examine chaque document (`POST /admin/kyc/documents/{id}/review`) : **valider** ou **refuser avec motif obligatoire**. Un document n'est examiné qu'une fois (état `submitted` uniquement). Un document refusé peut être remplacé par l'utilisateur (il repasse à `submitted`, motif effacé) ; un document validé est verrouillé.
- Décision sur le compte (`POST /admin/kyc/users/{id}/decision`) : **valider** (impossible tant que tous les documents requis ne sont pas fournis ET validés : l'API liste les raisons) → statut `validated` ; **refuser** (motif obligatoire) → statut `rejected` : la connexion est bloquée et le motif est affiché à l'utilisateur.
- Un compte déjà `validated` ou `active` ne peut plus être re-décidé. L'ancien `PATCH /admin/accounts/{id}/status` reste comme outil de support/démo.
- Notification à l'utilisateur à chaque décision ; journal d'audit étendu (`approve`, `reject`, `account_validated`, `account_rejected` dans `kyc_access_log`). Aucune nouvelle table : colonnes déjà prévues à l'étape 3.
- Interface : l'administrateur voit les dossiers à examiner en premier ; « Mon compte » affiche un suivi des étapes (OTP, documents, validation, abonnement).
- Règles dans `review_rules.py`. `validated` reste soumis à la limite des 30 connexions tant que l'abonnement n'est pas payé (étape 5).

## Site d'emploi public (version 0.7)
- Un visiteur NON connecté peut parcourir le site comme un site d'emploi : accueil avec recherche (mot-clé, lieu, type), recherches populaires, secteurs, offres récentes, entreprises ; liste d'offres avec filtres (type, secteur, lieu) et pagination ; détail d'une offre avec offres similaires ; annuaire et profil des entreprises.
- API publique (`/public/*`) : `offers` (filtres + pagination serveur), `offers/{id}`, `offers/{id}/similar`, `companies`, `companies/{id}`, `meta` (lieux, secteurs, compétences), `stats`. Elle masque les données privées (nombre de candidatures = 0, pas d'e-mails) et les offres clôturées ou expirées.
- Candidat connecté : mêmes pages avec score de compatibilité, favoris, lettre de motivation générée ; pagination côté client (le tri par score est calculé à la volée). « Postuler » pour un visiteur renvoie vers la connexion puis revient à l'offre (`?next=`).
- Frontend : utils.js (dates relatives, logos à initiales), components Navbar/SiteFooter/SearchBar/Pagination/OfferCard/ApplyModal/CompanyLogo ; pages Home, Offers, OfferDetail, Companies, CompanyProfile. Les pages privées gardent leurs routes.
- Pas de salaire ni de durée dans les offres (nécessiterait de modifier la table job_offers : à faire avec Alembic).

## Version 0.8 : connexions multiples, TConnect IA, thèmes, mise en ligne
- Méthodes de connexion : e-mail ou téléphone + mot de passe ; **code OTP sans mot de passe** (`POST /auth/otp/request` puis `/auth/otp/login`) ; **Google** (`POST /auth/google`, jeton vérifié par `google-auth` : signature, expiration, audience = GOOGLE_CLIENT_ID, e-mail vérifié). `GET /auth/config` renvoie l'identifiant Google : le bouton n'apparaît que s'il est configuré. Les admins ne peuvent pas se connecter par Google ni par code. Compte Google inconnu : création du compte avec le rôle choisi, e-mail marqué vérifié.
- **TConnect IA** (nom du chatbot, bêta) : visible pour TOUS sauf admin. Connecté → `/assistant/chat` (contextuel) ; visiteur → `/assistant/public-chat` (explications générales : inscription, score, essai gratuit, documents, recruteurs). Règles dans `assistant_logic.py` (`_reply_visitor`).
- Design : 4 thèmes (émeraude par défaut, océan, violet, rose) via variables CSS + sélecteur 🎨 (mémorisé dans localStorage) ; illustrations SVG animées (`Illustrations.jsx`) ; contenu concret à la place du texte marketing ; photo d'accueil facultative `frontend/public/images/hero.jpg`.
- **Mise en ligne** : site sur Vercel (Root Directory = frontend, variable `VITE_API_URL`), API sur Render via `render.yaml` (Docker, PostgreSQL). Voir `DEPLOIEMENT.md`. Sans `VITE_API_URL` en ligne, le site affiche un bandeau rouge (cause de l'erreur « Une erreur est survenue » à l'inscription). `vercel.json` réécrit toutes les routes vers index.html. Config backend : `CORS_ORIGINS` (liste), `DATABASE_URL` (postgres:// converti), `GOOGLE_CLIENT_ID`, `SEED_DEMO_DATA`, `OTP_DEV_MODE`, `KYC_ENCRYPTION_KEY`, `ADMIN_PASSWORD`, `PORT`.
- Limites connues sur hébergement gratuit : veille de l'API (premier appel lent), documents KYC sur disque éphémère, base Render gratuite limitée à 30 jours, SMS non branchés (OTP affiché si OTP_DEV_MODE=true).

## Étapes 5 et 6 + application installable (version 0.9)
- **Abonnement et paiement** : `pricing.py` (offres `candidat_premium` 2 000 FCFA/mois et `entreprise_pro` 15 000 FCFA/mois, remises 5/10/20 % sur 3/6/12 mois : tarifs de démonstration à confirmer), `billing_rules.py` (règles pures), `billing.py` (devis, paiement, activation, expiration), `routers/billing.py`. Flux : compte `validated` → `POST /billing/checkout` (prix calculé par le serveur, jamais par le navigateur) → paiement **simulé** `POST /billing/payments/{id}/simulate` → compte `active`, abonnement avec dates, **espace dédié** (`workspaces`), reçu `REC-AAAA-NNNNNN`, notification. Un paiement ne peut être traité qu'une fois (verrou atomique). Renouvellement : la nouvelle période prolonge la précédente. Un abonnement échu remet le compte à `validated` (jamais pour un compte activé manuellement sans abonnement).
- **Restriction levée à l'activation** : en essai/validé, une entreprise ne peut avoir que 3 offres actives (`OFFER_LIMIT`) ; l'abonnement Pro autorise 50 offres. Fin des 30 connexions d'essai.
- **Sessions** : table `user_sessions` ; le jeton JWT contient `sid`. Une nouvelle connexion ferme la précédente (`SESSION_REVOKED`), inactivité de 30 min (`SESSION_IDLE`), durée max 12 h (`SESSION_EXPIRED`), `POST /auth/logout` ferme la session côté serveur. Côté site : `IdleGuard` (avertissement 60 s avant, signal d'activité toutes les 4 min), message sur la page de connexion. Règles dans `session_rules.py` ; paramètres `SESSION_IDLE_MINUTES`, `SESSION_MAX_HOURS`.
- **PWA** : `manifest.webmanifest`, `sw.js` (cache de la coquille, jamais l'API), `offline.html`, icônes, bouton d'installation (`PwaTools.jsx`), bandeau hors ligne. Service worker enregistré en production seulement.
- Pas encore fait : vrai fournisseur de paiement, alertes de sécurité (e-mail/SMS/WhatsApp/Telegram), détection de comportements suspects, limitation des tentatives de connexion (étape 7), stockage permanent des documents.
- Comptes de démonstration prêts à s'abonner : `valide@demo.tg` (candidat), `pro@demo.tg` (entreprise).

## Étape 7 : alertes de sécurité (version 0.10)
- `security_rules.py` (règles pures) : verrouillage après 5 échecs de mot de passe en 15 min (par identifiant, 15 min, la connexion par code reste possible), alerte au propriétaire dès 3 échecs, détection de **nouvel appareil** (réseau + navigateur inconnus ; la 1re connexion ne déclenche rien), **activité suspecte** (3 réseaux différents en 10 min), **session remplacée**. Messages d'alerte en français, IP masquée.
- `security_monitor.py` (accès base) branché dans `routers/auth.py` (`check_not_locked`, `record_attempt`, `after_login`) ; `alerts.py` envoie sur les canaux choisis ; anti-spam (même alerte au plus 1 fois / 15-60 min) ; `alert_channels.py` : SMS et WhatsApp via Twilio, Telegram via Bot API (HTTP, sans bibliothèque) ; e-mail via `delivery.send_email_message`. **Sans identifiants : mode démo** (message dans l'application et les journaux).
- Tables : `login_attempts`, `security_alerts`, `alert_preferences`. Routes : `/security/alerts`, `/security/preferences`, `/security/test-alert`, `/admin/security` (+ `/unlock`). Page « Sécurité » côté utilisateur ; carte « Sécurité » côté administrateur.
- Limites : les identifiants SMS/WhatsApp/Telegram ne sont pas testés avec de vrais comptes ; l'adresse IP vient de l'en-tête X-Forwarded-For (indicative, falsifiable) donc le verrouillage repose sur l'identifiant et non sur l'IP ; l'administrateur peut aussi être verrouillé (pas de connexion par code pour lui).
- `ADMIN_PASSWORD` défini = devient le mot de passe de l'administrateur au démarrage (rotation possible). Voir GUIDE_ADMINISTRATEUR.md.

## Comptes de démonstration (python -m app.seed, mot de passe Demo1234!)
Entreprises : tech@demo.tg, agri@demo.tg, finance@demo.tg · Candidats actifs : kofi@, ama@, yao@, afi@demo.tg
Essai : essai@demo.tg (27/30 connexions) · Admin : admin@talentconnect.tg / Admin2026!

## Règles de travail avec l'IA
Expliquer chaque modification simplement en français, ne pas casser les routes existantes, donner le code complet des fichiers modifiés, indiquer comment tester, mettre à jour JOURNAL.md et ce fichier.
