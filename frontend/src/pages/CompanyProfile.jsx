import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import api, { errorMessage, getRole } from "../api";
import CompanyLogo from "../components/CompanyLogo.jsx";
import OfferCard from "../components/OfferCard.jsx";

export default function CompanyProfile() {
  const { id } = useParams();
  const role = getRole();
  const navigate = useNavigate();
  const [company, setCompany] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setCompany(null); setError("");
    api.get(`/public/companies/${id}`).then((r) => setCompany(r.data)).catch((e) => setError(errorMessage(e)));
    window.scrollTo(0, 0);
  }, [id]);

  const toggleFav = async (offerId) => {
    await api.post(`/favorites/${offerId}`);
    setCompany((c) => ({ ...c, offers: c.offers.map((o) => (o.id === offerId ? { ...o, is_favorite: !o.is_favorite } : o)) }));
  };

  if (error) return <div className="card empty"><h3>{error}</h3><Link to="/companies" className="link">← Retour aux entreprises</Link></div>;
  if (!company) return <p className="muted">Chargement…</p>;

  return (
    <>
      <p className="muted small"><Link to="/companies" className="plain">← Toutes les entreprises</Link></p>
      <div className="card detail-head">
        <CompanyLogo name={company.name} size={72} />
        <div>
          <h1>{company.name}</h1>
          <p className="muted">{company.sector || "Secteur non précisé"}{company.city ? ` · 📍 ${company.city}` : ""}</p>
          <p><b>{company.active_offers}</b> offre{company.active_offers > 1 ? "s" : ""} active{company.active_offers > 1 ? "s" : ""}</p>
        </div>
      </div>
      {company.description && <div className="card"><h3>À propos</h3><p className="prewrap">{company.description}</p></div>}
      <h2>Offres de {company.name}</h2>
      {company.offers.length === 0 && <p className="muted">Cette entreprise n'a aucune offre active pour le moment.</p>}
      {company.offers.map((o) => (
        <OfferCard key={o.id} offer={o} role={role} applied={false}
                   onApply={(offer) => navigate(`/offers/${offer.id}`)} onToggleFav={toggleFav} />
      ))}
    </>
  );
}
