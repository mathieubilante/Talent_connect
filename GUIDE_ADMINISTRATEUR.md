# Guide de l'administrateur

## Se connecter
- Adresse : `admin@talentconnect.tg`
- Mot de passe : celui de la variable `ADMIN_PASSWORD` (sur Render > Environment). En local sans réglage : `Admin2026!`.
- Page de connexion du site > saisir ces deux informations > le site ouvre la page **Administration**
  (aussi accessible par le menu « Mon espace » > Administration).
L'administrateur se connecte uniquement par mot de passe (pas de Google ni de code).

## Ce que vous voyez dans la page Administration
1. **Chiffres clés** : utilisateurs, offres, candidatures, compatibilité moyenne, compétences les plus demandées.
2. **Comptes et essais gratuits** : chaque compte avec ses connexions d'essai et son statut (outil de support).
3. **Examen des dossiers (KYC)** : les dossiers à examiner apparaissent en premier.
4. **Abonnements et paiements** : montants encaissés, abonnements en cours, liste des paiements.
5. **Sécurité** : comptes verrouillés (bouton Débloquer), tentatives échouées, dernières alertes.

## Valider un compte, pas à pas
1. L'utilisateur s'inscrit (code OTP) puis envoie ses documents (page « Mes documents »). Vous recevez une notification quand le dossier est complet.
2. Page Administration > **Examen des dossiers** : repérez le dossier (étiquette « à examiner »).
3. Cliquez sur **Télécharger** pour ouvrir chaque document (il est déchiffré uniquement pour vous).
4. Pour chaque document : **Valider**, ou **Refuser** avec un motif obligatoire (l'utilisateur pourra en renvoyer un autre).
5. Quand tous les documents sont validés, le bouton **✔ Valider le compte** devient actif : cliquez dessus. Le compte passe à « Validé ».
   (**✖ Refuser le compte** bloque la connexion et affiche le motif.)
6. L'utilisateur est notifié, peut choisir un abonnement et payer : son compte devient « Actif ».
