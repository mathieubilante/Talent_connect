# Mettre TalentConnect en ligne (Vercel + Render)

## Pourquoi « Une erreur est survenue » sur Vercel ?
Vercel héberge seulement le **site** (la partie visible). L'**API** (le cerveau : comptes, offres, codes OTP, base de données) tourne
sur votre PC. Depuis internet, le site ne peut pas la joindre. Il faut donc **mettre l'API en ligne aussi**, puis dire au site où elle se trouve.

Le site affiche maintenant un bandeau rouge tant que cette étape n'est pas faite.

---

## Étape 1 : mettre l'API en ligne sur Render (gratuit)
1. Poussez le projet sur GitHub (`git add .`, `git commit -m "deploiement"`, `git push origin main`).
2. Créez un compte sur https://render.com (connexion avec GitHub).
3. **New +** > **Blueprint** > choisissez votre dépôt GitHub. Render lit le fichier `render.yaml` et crée l'API et la base de données.
4. Render demande les valeurs de :
   - `CORS_ORIGINS` : l'adresse de votre site, par exemple `https://talentconnect-bm.vercel.app` (sans `/` à la fin).
   - `KYC_ENCRYPTION_KEY` : une clé de chiffrement. Pour la générer, dans le terminal de VS Code (venv activé) :
     `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` puis collez le résultat.
   - `ADMIN_PASSWORD` : le mot de passe de l'administrateur (choisissez-en un solide).
   - `GOOGLE_CLIENT_ID` : laissez vide pour l'instant.
5. Attendez la fin du déploiement (quelques minutes). Vous obtenez une adresse du type `https://talentconnect-api.onrender.com`.
6. Ouvrez `https://VOTRE-API.onrender.com/docs` : si la page « TalentConnect API » s'affiche, l'API est en ligne.

## Étape 2 : dire à Vercel où est l'API
1. Vercel > votre projet **TalentConnect** > **Settings** > **Environment Variables**.
2. Ajoutez : nom `VITE_API_URL`, valeur `https://VOTRE-API.onrender.com` (sans `/` à la fin).
3. Vérifiez dans **Settings > General** que **Root Directory** = `frontend`.
4. **Deployments** > les trois points du dernier déploiement > **Redeploy** (obligatoire : la variable n'est prise en compte qu'au redéploiement).

Testez l'inscription sur votre site : le code OTP s'affiche dans un cadre orange (mode démonstration).

## Étape 3 (facultative) : bouton « Continuer avec Google »
1. https://console.cloud.google.com > créez un projet.
2. **APIs et services** > **Écran de consentement OAuth** : type « Externe », nom de l'application, votre e-mail. Enregistrez.
3. **Identifiants** > **Créer des identifiants** > **ID client OAuth** > type **Application Web**.
4. **Origines JavaScript autorisées** : ajoutez `https://talentconnect-bm.vercel.app` et `http://localhost:5173`.
5. Copiez l'**ID client** (il se termine par `.apps.googleusercontent.com`).
6. Render > votre service > **Environment** : renseignez `GOOGLE_CLIENT_ID` avec cet ID, puis enregistrez (l'API redémarre).
7. Pour tester sur votre PC : ajoutez la même variable `GOOGLE_CLIENT_ID` dans l'environnement du backend local.
Le bouton Google apparaît tout seul sur la page de connexion dès que l'ID est configuré.

---

## À savoir (version gratuite)
- **Démarrage lent** : après 15 minutes sans visite, Render met l'API en veille ; la première requête peut prendre environ 50 secondes.
- **Documents d'identité (KYC)** : les fichiers chiffrés sont stockés sur le disque du service, qui est effacé à chaque redéploiement.
  Suffisant pour une démonstration ; en production, il faudra un stockage permanent (disque Render payant ou stockage d'objets).
- **Base de données Render gratuite** : elle expire au bout de 30 jours. Alternatives gratuites : Neon ou Supabase (collez leur adresse dans `DATABASE_URL`).
- **Codes OTP** : tant qu'aucun service de SMS ou d'e-mail n'est branché, `OTP_DEV_MODE=true` affiche le code sur le site. Mettez `false` en production réelle.
- Chaque aperçu Vercel (preview) a une adresse différente : ajoutez-la à `CORS_ORIGINS` (séparée par une virgule) si vous voulez tester dessus.


---

## Installer le site comme une application (PWA)
Une fois le site publié sur Vercel (HTTPS), il est **installable** :
- **Ordinateur (Chrome ou Edge)** : bouton « 📲 Installer l'application » dans la barre du haut, ou l'icône d'installation dans la barre d'adresse.
- **Android (Chrome)** : le même bouton, ou menu ⋮ > « Installer l'application ».
- **iPhone (Safari)** : bouton Partager > « Sur l'écran d'accueil » (le bouton « Installer » du site affiche l'aide).
L'application s'ouvre en plein écran avec son icône. Elle a besoin d'internet pour charger les offres ; hors ligne, une page d'information s'affiche.
Après une mise à jour du site, fermez puis rouvrez l'application pour récupérer la nouvelle version.

## Paiement et sessions (variables du backend)
- `PAYMENT_PROVIDER=simulated` : paiement de démonstration, aucun argent réel. Le branchement d'un vrai moyen de paiement (Mobile Money, carte) viendra plus tard.
- `SESSION_IDLE_MINUTES=30` : déconnexion automatique après 30 minutes d'inactivité (avertissement 60 secondes avant).
- `SESSION_MAX_HOURS=12` : durée maximale d'une session. Une nouvelle connexion ferme la précédente.
Les nouvelles tables (abonnements, paiements, espaces, sessions) se créent toutes seules au démarrage de l'API.


## Alertes de sécurité (étape 7)
Le site prévient l'utilisateur d'une connexion depuis un nouvel appareil, de tentatives échouées, d'une activité suspecte ou d'une session fermée ailleurs.
- **Dans l'application** : toujours actif (page « Sécurité » et notifications).
- **E-mail** : `OTP_DELIVERY=smtp` + `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` (le même réglage que les codes OTP).
- **Telegram** : créez un robot avec @BotFather, copiez son jeton dans `TELEGRAM_BOT_TOKEN` ; chaque utilisateur indique son identifiant Telegram dans « Sécurité ».
- **SMS et WhatsApp** : compte Twilio ; renseignez `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_SMS_FROM` et `TWILIO_WHATSAPP_FROM`.
Sans ces réglages, chaque canal est en « mode démo » : le message est écrit dans les journaux du serveur (Render > Logs).
Après 5 échecs de mot de passe en 15 minutes, le compte est verrouillé 15 minutes (la connexion par code reste possible) ; l'administrateur peut le débloquer.

## Mot de passe de l'administrateur
L'adresse est `admin@talentconnect.tg`. Définissez la variable `ADMIN_PASSWORD` sur Render : le mot de passe est appliqué au prochain démarrage,
même si l'administrateur existe déjà. **Ne gardez jamais le mot de passe par défaut** (il est public dans le code).
