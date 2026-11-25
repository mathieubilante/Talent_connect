import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { t } from "../i18n.js";
import Seo from "../components/Seo.jsx";
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
      <Seo title="Entreprises qui recrutent" description="Découvrez les entreprises qui recrutent et leurs offres actives." />
      <h2>{t("companies_title")}</h2>
      <div className="card"><input placeholder={t("search_company")}n value={q}
                                   onChange={(e) => setQ(e.target.value)} style={{ margin: 0 }} /></div>
      {error && <p className="error">{error}</p>}
      {shown.length === 0 && !error && <p className="muted">{t("no_company")}</p>}
      <div className="mini-grid">
        {shown.map((c) => (
          <Link key={c.id} to={`/companies/${c.id}`} className="card mini-offer">
            <CompanyLogo name={c.name} size={52} />
            <div>
              <h3>{c.name}</h3>
              <p className="muted small">{c.sector || t("sector_unknown")}{c.city ? ` · ${c.city}` : ""}</p>
              <p className="small"><b>{c.active_offers}</b> offre{c.active_offers > 1 ? "s" : ""} active{c.active_offers > 1 ? "s" : ""}</p>
            </div>
          </Link>
        ))}
      </div>
    </>
  );
}
