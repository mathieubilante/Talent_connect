import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import api, { errorMessage, getRole } from "../api";
import ApplyModal from "../components/ApplyModal.jsx";
import OfferCard from "../components/OfferCard.jsx";
import Pagination from "../components/Pagination.jsx";
import SearchBar from "../components/SearchBar.jsx";

const PAGE_SIZE = 8;

export default function Offers() {
  const role = getRole();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const q = params.get("q") || "";
  const location = params.get("location") || "";
  const offerType = params.get("offer_type") || "";
  const sector = params.get("sector") || "";
  const sort = params.get("sort") || (role === "candidate" ? "match" : "recent");
  const page = Math.max(1, Number(params.get("page") || 1));

  const [data, setData] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [meta, setMeta] = useState(null);
  const [appliedIds, setAppliedIds] = useState(new Set());
  const [message, setMessage] = useState("");
  const [applying, setApplying] = useState(null);

  const update = (changes) => {
    const next = new URLSearchParams(params);
    Object.entries({ page: "1", ...changes }).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)));
    setParams(next);
  };

  useEffect(() => { api.get("/public/meta").then((r) => setMeta(r.data)).catch(() => {}); }, []);
  useEffect(() => {
    if (role === "candidate") {
      api.get("/applications/mine").then((r) => setAppliedIds(new Set(r.data.map((a) => a.offer_id)))).catch(() => {});
    }
  }, [role]);

  useEffect(() => {
    setLoading(true);
    const filters = { q, location, offer_type: offerType, sector };
    const clean = Object.fromEntries(Object.entries(filters).filter(([, v]) => v));
    const run = role === "candidate"
      ? api.get("/offers", { params: { ...clean, sort } })
          .then((r) => ({ items: r.data.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE), total: r.data.length }))
      : api.get("/public/offers", { params: { ...clean, page, page_size: PAGE_SIZE } })
          .then((r) => ({ items: r.data.items, total: r.data.total }));
    run.then(setData).catch((e) => setMessage(errorMessage(e))).finally(() => setLoading(false));
  }, [params.toString(), role]);

  const toggleFav = async (id) => {
    await api.post(`/favorites/${id}`);
    setData((d) => ({ ...d, items: d.items.map((o) => (o.id === id ? { ...o, is_favorite: !o.is_favorite } : o)) }));
  };

  const pages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));
  const hasFilters = q || location || offerType || sector;
  const title = offerType === "stage" ? "Offres de stage" : offerType === "emploi" ? "Offres d'emploi" : "Toutes les offres";

  return (
    <>
      <SearchBar key={`${q}|${location}|${offerType}`} initial={{ q, location, offer_type: offerType }}
                 onSearch={(f) => update({ q: f.q, location: f.location, offer_type: f.offer_type })} />
      <div className="board">
        <aside className="card filters-side">
          <h3>Filtres</h3>
          <label>Type de contrat</label>
          <div className="seg">
            {[["", "Tous"], ["emploi", "Emploi"], ["stage", "Stage"]].map(([v, l]) => (
              <button key={v} className={offerType === v ? "on" : ""} onClick={() => update({ offer_type: v })}>{l}</button>
            ))}
          </div>
          <label>Secteur
            <select value={sector} onChange={(e) => update({ sector: e.target.value })}>
              <option value="">Tous les secteurs</option>
              {meta && meta.sectors.map((s) => <option key={s.name} value={s.name}>{s.name} ({s.count})</option>)}
            </select>
          </label>
          {meta && meta.locations.length > 0 && (
            <>
              <label>Lieux fréquents</label>
              <div className="chips">
                {meta.locations.map((l) => (
                  <button key={l.name} className={`chip clickable ${location === l.name ? "ok" : ""}`}
                          onClick={() => update({ location: location === l.name ? "" : l.name })}>{l.name} ({l.count})</button>
                ))}
              </div>
            </>
          )}
          {role === "candidate" && (
            <label>Trier par
              <select value={sort} onChange={(e) => update({ sort: e.target.value })}>
                <option value="match">Meilleure compatibilité</option>
                <option value="recent">Plus récentes</option>
              </select>
            </label>
          )}
          {hasFilters && <button className="link" onClick={() => setParams(new URLSearchParams())}>Effacer les filtres</button>}
        </aside>

        <section>
          <div className="row">
            <h2 style={{ margin: 0 }}>{title}</h2>
            <span className="muted">{loading ? "Chargement…" : `${data.total} offre${data.total > 1 ? "s" : ""} trouvée${data.total > 1 ? "s" : ""}`}</span>
          </div>
          {message && <p className="info">{message}</p>}
          {!loading && data.items.length === 0 && (
            <div className="card empty"><h3>Aucune offre ne correspond à votre recherche</h3>
              <p className="muted">Essayez d'autres mots-clés ou retirez des filtres.</p></div>
          )}
          {data.items.map((o) => (
            <OfferCard key={o.id} offer={o} role={role} applied={appliedIds.has(o.id)}
                       onApply={setApplying} onToggleFav={toggleFav} />
          ))}
          <Pagination page={page} pages={pages} onChange={(n) => { update({ page: String(n) }); window.scrollTo(0, 0); }} />
        </section>
      </div>

      {applying && (
        <ApplyModal offer={applying} onClose={() => setApplying(null)}
                    onDone={(msg) => { setMessage(msg); setAppliedIds(new Set([...appliedIds, applying.id])); setApplying(null); }} />
      )}
    </>
  );
}
