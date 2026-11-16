import { Link } from "react-router-dom";

export default function SiteFooter() {
  return (
    <footer className="sitefooter">
      <div className="footer-grid">
        <div>
          <div className="brand light"><img src="/favicon.svg" alt="" /> Talent<span>Connect</span></div>
          <p>Plateforme intelligente de recrutement, d'emploi et de gestion des stages.</p>
        </div>
        <div>
          <h4>Candidats</h4>
          <Link to="/offers?offer_type=emploi">Offres d'emploi</Link>
          <Link to="/offers?offer_type=stage">Offres de stage</Link>
          <Link to="/companies">Entreprises</Link>
          <Link to="/login?mode=register">Créer un compte</Link>
        </div>
        <div>
          <h4>Recruteurs</h4>
          <Link to="/login?mode=register&role=company">Publier une offre</Link>
          <Link to="/company">Espace entreprise</Link>
        </div>
        <div>
          <h4>Intelligence artificielle</h4>
          <span>Score de compatibilité</span>
          <span>Analyse automatique du CV</span>
          <span>Assistant et lettre de motivation</span>
        </div>
      </div>
      <div className="footer-bottom">© 2026 TalentConnect · Tous droits réservés</div>
    </footer>
  );
}
