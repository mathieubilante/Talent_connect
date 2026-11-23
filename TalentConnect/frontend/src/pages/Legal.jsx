import { Link } from "react-router-dom";
import Seo from "../components/Seo.jsx";

/* Textes juridiques. Les crochets [ ] doivent être remplacés par les informations réelles de l'entreprise,
   et les textes doivent être relus par un juriste avant publication. */

export function PrivacyPage() {
  return (
    <article className="legal">
      <Seo title="Politique de confidentialité" description="Comment TalentConnect collecte, utilise et protège vos données personnelles." />
      <h1>Politique de confidentialité</h1>
      <p className="muted">Dernière mise à jour : [date]</p>
      <h2>1. Qui est responsable de vos données ?</h2>
      <p>TalentConnect, [nom légal de l'entreprise], [adresse], contact : [adresse e-mail de contact].</p>
      <h2>2. Quelles données collectons-nous ?</h2>
      <ul>
        <li><b>Compte</b> : adresse e-mail ou numéro de téléphone, mot de passe (stocké sous forme chiffrée, jamais en clair).</li>
        <li><b>Profil</b> : nom, prénom, date de naissance, établissement, activité, photo de profil, CV (PDF), compétences.</li>
        <li><b>Documents d'identité</b> (candidats et entreprises) : pièces demandées pour valider le compte, stockées chiffrées.</li>
        <li><b>Candidatures et favoris</b> : offres consultées, candidatures envoyées, statuts.</li>
        <li><b>Sécurité</b> : date et adresse réseau des connexions, tentatives échouées, pour protéger votre compte.</li>
        <li><b>Paiements</b> : historique des abonnements et reçus (les coordonnées bancaires ne sont pas stockées sur nos serveurs).</li>
      </ul>
      <h2>3. Pourquoi les utilisons-nous ?</h2>
      <ul>
        <li>Créer et sécuriser votre compte ; vérifier votre identité et votre adresse de contact.</li>
        <li>Calculer la compatibilité entre votre profil et les offres, et transmettre votre candidature aux recruteurs.</li>
        <li>Gérer les abonnements, les paiements et les reçus.</li>
        <li>Mesurer l'audience du site, uniquement si vous l'acceptez.</li>
      </ul>
      <h2>4. Qui peut voir vos données ?</h2>
      <p>Vos données ne sont pas vendues. Les recruteurs ne voient que les informations de votre profil et de votre candidature. Les documents d'identité ne sont consultables que par l'administration de la plateforme. Des prestataires techniques (hébergement, envoi de codes par e-mail ou SMS) reçoivent uniquement les informations nécessaires à leur service.</p>
      <h2>5. Combien de temps les conservons-nous ?</h2>
      <p>Pendant la durée de votre compte, puis [durée à définir] après sa suppression. Les documents d'identité sont supprimés [durée à définir] après la décision sur votre compte, sauf obligation légale.</p>
      <h2>6. Vos droits</h2>
      <p>Vous pouvez demander l'accès, la rectification, la suppression de vos données ou leur transfert. Vous pouvez aussi retirer votre consentement aux mesures d'audience à tout moment. Écrivez à [adresse e-mail de contact].</p>
      <h2>7. Sécurité</h2>
      <p>Connexion chiffrée (HTTPS), mots de passe protégés, documents chiffrés, sessions limitées dans le temps, journal des accès aux documents.</p>
      <h2>8. Cookies et stockage local</h2>
      <p>Le site n'utilise que le stockage nécessaire à son fonctionnement (session de connexion, préférences d'affichage, choix de langue). Les mesures d'audience ne sont activées qu'avec votre accord. Voir le bandeau cookies.</p>
      <p><Link to="/">← Retour à l'accueil</Link></p>
    </article>
  );
}

export function TermsPage() {
  return (
    <article className="legal">
      <Seo title="Conditions générales d'utilisation" description="Conditions d'utilisation de la plateforme TalentConnect." />
      <h1>Conditions générales d'utilisation</h1>
      <p className="muted">Dernière mise à jour : [date]</p>
      <h2>1. Objet</h2>
      <p>Ces conditions encadrent l'utilisation de TalentConnect, plateforme de mise en relation entre candidats (emploi et stage) et entreprises.</p>
      <h2>2. Inscription</h2>
      <p>L'inscription nécessite une adresse e-mail ou un téléphone vérifié. Vous êtes responsable de la confidentialité de vos identifiants. Les informations fournies doivent être exactes.</p>
      <h2>3. Validation du compte</h2>
      <p>Certaines fonctions nécessitent la validation de votre compte par l'administration, à partir de documents d'identité. La validation peut être refusée, avec un motif.</p>
      <h2>4. Essai gratuit et abonnements</h2>
      <p>L'essai gratuit est limité à 30 connexions. Les abonnements donnent accès à des fonctions supplémentaires pour une durée choisie. Les tarifs affichés sont indiqués toutes taxes comprises [à confirmer]. Les conditions de remboursement sont [à définir].</p>
      <h2>5. Candidatures et offres</h2>
      <p>TalentConnect facilite la mise en relation mais ne garantit ni l'embauche ni l'exactitude des offres publiées. Les recruteurs sont responsables du contenu de leurs annonces. Toute offre trompeuse ou discriminatoire peut être retirée.</p>
      <h2>6. Comportements interdits</h2>
      <p>Usurpation d'identité, fausses informations, spam, tentative d'accès non autorisé, collecte de données d'autres utilisateurs, contournement de l'essai gratuit.</p>
      <h2>7. Responsabilité</h2>
      <p>TalentConnect met en œuvre les moyens raisonnables pour assurer la disponibilité du service, sans garantie d'un fonctionnement ininterrompu.</p>
      <h2>8. Données personnelles</h2>
      <p>Le traitement des données est décrit dans la <Link to="/confidentialite">politique de confidentialité</Link>.</p>
      <h2>9. Droit applicable</h2>
      <p>[Droit applicable et juridiction à définir].</p>
      <p><Link to="/">← Retour à l'accueil</Link></p>
    </article>
  );
}
