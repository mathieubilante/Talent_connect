# Journal de bord TalentConnect

| Jour | Date | Travail réalisé | Fichiers principaux | Problèmes / solutions |
|---|---|---|---|---|
| 1 | 1 nov. 2026 | Rapport de lancement : nom, logo, cahier des charges, technologies, architecture, planning | Rapport n°1, logo | — |
| 2 | 2 nov. 2026 | Version 0.1 : API (auth JWT, profils, offres, candidatures), matching TF-IDF, frontend React, schema.sql, Docker | backend/, frontend/, database/ | pip échouait : requirements assouplis ; Docker installé |
| 3 | 3 nov. 2026 | Version 0.2 : matching détaillé, analyse de CV, recommandations, assistant IA, lettre auto, favoris, notifications, administration, seed | matching.py, skills.py, assistant_logic.py, routers/* | table favorites ajoutée au schéma |
| 4 | 4 nov. 2026 | Version 0.3 (étape 1) : statuts de compte, essai limité à 30 connexions (compteur atomique), historique des connexions, bannière d'essai, page Mon compte, gestion des statuts côté admin | account_rules.py, accounts.py, security.py, routers/account.py, auth.py, admin.py, models.py | nouvelles tables user_accounts et login_history (SQL fourni) |
| 5 | 5 nov. 2026 | Version 0.4 (étape 2) : inscription par e-mail ou téléphone avec code OTP (6 chiffres, expiration 10 min, 5 essais, renvoi limité, codes hachés), connexion par e-mail ou téléphone, page de saisie du code | otp_rules.py, otp.py, delivery.py, routers/auth.py, models.py, schemas.py, config.py, frontend Login.jsx | colonne email obligatoire : e-mail technique pour les inscriptions par téléphone ; SMS non branché (mode console) |
| 6 | 7 nov. 2026 | Version 0.5 (étape 3) : documents KYC (CIN ; CIN représentant, patente, extrait RNE < 3 mois), stockage chiffré Fernet, vérification du vrai type de fichier, journal d'audit, page Mes documents, vue administrateur | kyc_rules.py, crypto.py, routers/kyc.py, models.py, schemas.py, frontend Kyc.jsx | clé de chiffrement de dev dérivée de SECRET_KEY (clé dédiée obligatoire en prod) |
