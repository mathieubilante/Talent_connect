import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api, { getRole } from "../api";
import CompanyLogo from "../components/CompanyLogo.jsx";
import SearchBar from "../components/SearchBar.jsx";
import { timeAgo } from "../utils";

const FALLBACK_SECTORS = ["Technologie", "Finance", "Agriculture", "Marketing", "Santé", "Éducation"];
const FEATURES = [
  ["🎯", "Matching intelligent", "Chaque offre reçoit un score de compatibilité avec votre profil, avec les compétences en commun et celles à renforcer."],
  ["📄", "Analyse du CV", "Déposez votre CV PDF : vos compétences sont détectées et ajoutées à votre profil automatiquement."],
  ["🤖", "Assistant IA", "Conseils CV, lettre de motivation générée pour chaque offre, préparation d'entretien."],
  ["🔔", "Suivi en temps réel", "Notifications à chaque étape : candidature reçue, présélection, entretien, décision."],
];

export default function Home() {
  const role = getRole();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [meta, setMeta] = useState(null);
  const [latest, setLatest] = useState([]);
  const [companies, setCompanies] = useState([]);

  useEffect(() => {
    api.get("/public/stats").then((r) => setStats(r.data)).catch(() => {});
    api.get("/public/meta").then((r) => setMeta(r.data)).catch(() => {});
    api.get("/public/offers", { params: { page_size: 6 } }).then((r) => setLatest(r.data.items)).catch(() => {});
    api.get("/public/companies").then((r) => setCompanies(r.data.slice(0, 6))).catch(() => {});
  }, []);

  const search = (f) => {
    const p = new URLSearchParams(Object.entries(f).filter(([, v]) => v));
    navigate(`/offers?${p.toString()}`);
  };
  const sectors = meta && meta.sectors.length ? meta.sectors : FALLBACK_SECTORS.map((name) => ({ name, count: null }));

  return (
    <>
      <section className="hero2">
        <h1>Trouvez l'emploi ou le stage<br />qui vous correspond</h1>
        <p>Des offres d'entreprises, un score de compatibilité calculé par l'IA et un suivi de vos candidatures.</p>
        <SearchBar big onSearch={search} />
        {meta && meta.skills.length > 0 && (
          <div className="popular">
            <span>Recherches populaires :</span>
            {meta.skills.slice(0, 6).map((s) => <Link key={s.name} to={`/offers?q=${encodeURIComponent(s.name)}`}>{s.name}</Link>)}
          </div>
        )}
        {stats && (
          <div className="stats-row">
            <div><b>{stats.offers}</b><span>offres actives</span></div>
            <div><b>{stats.companies}</b><span>entreprises</span></div>
            <div><b>{stats.candidates}</b><span>candidats</span></div>
          </div>
        )}
      </section>

      <h2 className="section-title">Parcourir par secteur</h2>
      <div className="categories">
        {sectors.map((s) => (
          <Link key={s.name} to={`/offers?sector=${encodeURIComponent(s.name)}`} className="category">
            <b>{s.name}</b>{s.count !== null && <span>{s.count} offre{s.count > 1 ? "s" : ""}</span>}
          </Link>
        ))}
      </div>

      <div className="row section-head">
        <h2>Offres récentes</h2>
        <Link to="/offers" className="link">Voir toutes les offres →</Link>
      </div>
      {latest.length === 0 && <p className="muted">Aucune offre pour le moment.</p>}
      <div className="mini-grid">
        {latest.map((o) => (
          <Link key={o.id} to={`/offers/${o.id}`} className="card mini-offer">
            <CompanyLogo name={o.company_name} size={44} />
            <div>
              <h3>{o.title}</h3>
              <p className="muted small">{o.company_name} · 📍 {o.location || "—"}</p>
              <p className="small"><span className={`tag ${o.offer_type}`}>{o.offer_type}</span> <span className="muted">{timeAgo(o.created_at)}</span></p>
            </div>
          </Link>
        ))}
      </div>

      {companies.length > 0 && (
        <>
          <div className="row section-head">
            <h2>Entreprises qui recrutent</h2>
            <Link to="/companies" className="link">Toutes les entreprises →</Link>
          </div>
          <div className="mini-grid">
            {companies.map((c) => (
              <Link key={c.id} to={`/companies/${c.id}`} className="card mini-offer">
                <CompanyLogo name={c.name} size={44} />
                <div>
                  <h3>{c.name}</h3>
                  <p className="muted small">{c.sector || "—"}{c.city ? ` · ${c.city}` : ""}</p>
                  <p className="small"><b>{c.active_offers}</b> offre{c.active_offers > 1 ? "s" : ""} active{c.active_offers > 1 ? "s" : ""}</p>
                </div>
              </Link>
            ))}
          </div>
        </>
      )}

      <h2 className="section-title">Pourquoi TalentConnect</h2>
      <div className="features">
        {FEATURES.map(([icon, title, text]) => (
          <div className="card feature" key={title}><div className="icon">{icon}</div><h3>{title}</h3><p className="muted">{text}</p></div>
        ))}
      </div>

      <h2 className="section-title">Comment ça marche</h2>
      <div className="steps">
        <div className="card"><span className="num">1</span><h3>Créez votre compte</h3><p className="muted">Inscription par e-mail ou téléphone, avec un code de vérification.</p></div>
        <div className="card"><span className="num">2</span><h3>Complétez votre profil</h3><p className="muted">Compétences, CV et documents d'identité pour valider votre compte.</p></div>
        <div className="card"><span className="num">3</span><h3>Postulez et suivez</h3><p className="muted">Candidature en un clic avec lettre générée, notifications à chaque étape.</p></div>
      </div>

      {role !== "company" && (
        <section className="cta-band">
          <div><h2>Vous recrutez ?</h2><p>Publiez vos offres et recevez des candidatures classées par compatibilité.</p></div>
          <Link to="/login?mode=register&role=company" className="btn big">Publier une offre</Link>
        </section>
      )}
    </>
  );
}
