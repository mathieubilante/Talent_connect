import { useEffect, useState } from "react";
import api, { errorMessage, getRole } from "../api";
import OfferCard from "../components/OfferCard.jsx";

export default function Offers() {
  const role = getRole();
  const [offers, setOffers] = useState([]);
  const [appliedIds, setAppliedIds] = useState(new Set());
  const [filters, setFilters] = useState({ q: "", offer_type: "", location: "", sort: role === "candidate" ? "match" : "recent" });
  const [message, setMessage] = useState("");
  const [applying, setApplying] = useState(null);   // offre en cours de candidature
  const [letter, setLetter] = useState("");

  const load = async () => {
    const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v));
    const { data } = await api.get("/offers", { params });
    setOffers(data);
    if (role === "candidate") {
      const apps = await api.get("/applications/mine");
      setAppliedIds(new Set(apps.data.map((a) => a.offer_id)));
    }
  };
  useEffect(() => { load().catch((e) => setMessage(errorMessage(e))); }, []);

  const toggleFav = async (id) => {
    await api.post(`/favorites/${id}`);
    setOffers((list) => list.map((o) => (o.id === id ? { ...o, is_favorite: !o.is_favorite } : o)));
  };

  const startApply = async (offer) => {
    setApplying(offer);
    setLetter("Génération de la lettre de motivation…");
    try {
      const { data } = await api.post("/assistant/cover-letter", { offer_id: offer.id });
      setLetter(data.letter);
    } catch { setLetter(""); }
  };

  const sendApplication = async () => {
    try {
      await api.post("/applications", { offer_id: applying.id, cover_letter: letter });
      setMessage(`Candidature envoyée pour « ${applying.title} » !`);
      setAppliedIds(new Set([...appliedIds, applying.id]));
      setApplying(null);
    } catch (e) { setMessage(errorMessage(e)); setApplying(null); }
  };

  const f = (k) => (e) => setFilters({ ...filters, [k]: e.target.value });

  return (
    <>
      <h2>Offres d'emploi et de stage</h2>
      <div className="card filters">
        <input placeholder="🔍 Mot-clé, compétence…" value={filters.q} onChange={f("q")} />
        <input placeholder="📍 Lieu" value={filters.location} onChange={f("location")} />
        <select value={filters.offer_type} onChange={f("offer_type")}>
          <option value="">Emploi et stage</option>
          <option value="emploi">Emploi</option>
          <option value="stage">Stage</option>
        </select>
        {role === "candidate" && (
          <select value={filters.sort} onChange={f("sort")}>
            <option value="match">Trier : meilleure compatibilité</option>
            <option value="recent">Trier : plus récentes</option>
          </select>
        )}
        <button className="btn" onClick={() => load().catch((e) => setMessage(errorMessage(e)))}>Rechercher</button>
      </div>
      {message && <p className="info">{message}</p>}
      {offers.length === 0 && <p className="muted">Aucune offre ne correspond à votre recherche.</p>}
      {offers.map((o) => (
        <OfferCard key={o.id} offer={o} role={role} applied={appliedIds.has(o.id)}
                   onApply={startApply} onToggleFav={toggleFav} />
      ))}

      {applying && (
        <div className="modal-back" onClick={() => setApplying(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Postuler : {applying.title}</h3>
            <p className="muted small">🤖 Brouillon de lettre généré selon votre profil. Vous pouvez le modifier.</p>
            <textarea rows={12} value={letter} onChange={(e) => setLetter(e.target.value)} />
            <div className="row end gap">
              <button className="link" onClick={() => setApplying(null)}>Annuler</button>
              <button className="btn" onClick={sendApplication}>Envoyer ma candidature</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
