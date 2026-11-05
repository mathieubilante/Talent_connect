import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { getRole } from "../api";

const FEATURES = [
  ["🎯", "Matching intelligent", "Chaque offre reçoit un score de compatibilité avec votre profil, avec les compétences en commun et celles à renforcer."],
  ["📄", "Analyse automatique du CV", "Déposez votre CV PDF : vos compétences sont détectées et ajoutées à votre profil."],
  ["🤖", "Assistant IA", "Conseils CV, lettre de motivation générée pour chaque offre, préparation d'entretien."],
  ["🏢", "Espace entreprise", "Publiez vos offres, recevez des candidatures classées par pertinence et trouvez les meilleurs talents."],
  ["🔔", "Notifications", "Suivez chaque étape : candidature reçue, présélection, entretien, décision."],
  ["📊", "Tableaux de bord", "Statistiques en temps réel pour les entreprises et l'administration."],
];

export default function Home() {
  const [stats, setStats] = useState(null);
  const role = getRole();
  useEffect(() => { api.get("/public/stats").then((r) => setStats(r.data)).catch(() => {}); }, []);

  return (
    <>
      <section className="hero">
        <h1>Trouvez le bon talent.<br />Trouvez la bonne opportunité.</h1>
        <p>TalentConnect rassemble emplois, stages et candidatures sur une seule plateforme, avec une IA qui rapproche les profils et les offres.</p>
        <div className="row center gap">
          {role
            ? <Link to="/offers" className="btn big">Voir les offres</Link>
            : <><Link to="/login?mode=register" className="btn big">Créer un compte</Link>
                <Link to="/login" className="btn-light big">Se connecter</Link></>}
        </div>
        {stats && (
          <div className="stats-row">
            <div><b>{stats.offers}</b><span>offres actives</span></div>
            <div><b>{stats.companies}</b><span>entreprises</span></div>
            <div><b>{stats.candidates}</b><span>candidats</span></div>
          </div>
        )}
      </section>

      <h2 className="section-title">Tout pour recruter et postuler</h2>
      <div className="features">
        {FEATURES.map(([icon, title, text]) => (
          <div className="card feature" key={title}><div className="icon">{icon}</div><h3>{title}</h3><p className="muted">{text}</p></div>
        ))}
      </div>

      <h2 className="section-title">Comment ça marche</h2>
      <div className="steps">
        <div className="card"><span className="num">1</span><h3>Créez votre profil</h3><p className="muted">Renseignez vos compétences ou déposez votre CV.</p></div>
        <div className="card"><span className="num">2</span><h3>Découvrez vos offres</h3><p className="muted">L'IA classe les offres selon votre compatibilité.</p></div>
        <div className="card"><span className="num">3</span><h3>Postulez et suivez</h3><p className="muted">Candidature en un clic, notifications à chaque étape.</p></div>
      </div>
    </>
  );
}
