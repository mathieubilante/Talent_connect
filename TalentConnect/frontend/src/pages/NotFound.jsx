import { Link } from "react-router-dom";
import Seo from "../components/Seo.jsx";

export default function NotFound() {
  return (
    <section className="notfound">
      <Seo title="Page introuvable" description="Cette page n'existe pas ou a été déplacée." />
      <div className="nf-code">404</div>
      <h1>Cette page n'existe pas</h1>
      <p className="muted">Le lien est peut-être ancien, ou la page a été déplacée. Essayez plutôt de rechercher une offre.</p>
      <div className="landing-actions">
        <Link to="/" className="btn big">Retour à l'accueil</Link>
        <Link to="/offers" className="btn-outline big">Voir les offres</Link>
      </div>
    </section>
  );
}
