import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { errorMessage } from "../api";
import CompanyLogo from "../components/CompanyLogo.jsx";

export default function Companies() {
  const [list, setList] = useState([]);
  const [q, setQ] = useState("");
  const [error, setError] = useState("");
  useEffect(() => { api.get("/public/companies").then((r) => setList(r.data)).catch((e) => setError(errorMessage(e))); }, []);

  const low = q.trim().toLowerCase();
  const shown = list.filter((c) => !low || `${c.name} ${c.sector} ${c.city}`.toLowerCase().includes(low));

  return (
    <>
      <h2>🏢 Entreprises</h2>
      <div className="card"><input placeholder="🔍 Rechercher une entreprise, un secteur, une ville…" value={q}
                                   onChange={(e) => setQ(e.target.value)} style={{ margin: 0 }} /></div>
      {error && <p className="error">{error}</p>}
      {shown.length === 0 && !error && <p className="muted">Aucune entreprise trouvée.</p>}
      <div className="mini-grid">
        {shown.map((c) => (
          <Link key={c.id} to={`/companies/${c.id}`} className="card mini-offer">
            <CompanyLogo name={c.name} size={52} />
            <div>
              <h3>{c.name}</h3>
              <p className="muted small">{c.sector || "Secteur non précisé"}{c.city ? ` · ${c.city}` : ""}</p>
              <p className="small"><b>{c.active_offers}</b> offre{c.active_offers > 1 ? "s" : ""} active{c.active_offers > 1 ? "s" : ""}</p>
            </div>
          </Link>
        ))}
      </div>
    </>
  );
}
