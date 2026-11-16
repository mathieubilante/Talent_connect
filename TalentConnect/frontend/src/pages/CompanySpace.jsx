import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";
import Chips from "../components/Chips.jsx";
import MatchBar from "../components/MatchBar.jsx";

const STATUSES = [["recue", "Reçue"], ["preselectionnee", "Présélectionnée"], ["entretien", "Entretien"], ["acceptee", "Acceptée"], ["refusee", "Refusée"]];
const EMPTY = { title: "", description: "", offer_type: "stage", required_skills: "", location: "" };

export default function CompanySpace() {
  const [tab, setTab] = useState("apercu");
  const [form, setForm] = useState(EMPTY);
  const [offers, setOffers] = useState([]);
  const [applications, setApplications] = useState([]);
  const [talentOffer, setTalentOffer] = useState("");
  const [talents, setTalents] = useState([]);
  const [message, setMessage] = useState("");

  const load = async () => {
    const [o, a] = await Promise.all([api.get("/offers/mine"), api.get("/applications/received")]);
    setOffers(o.data); setApplications(a.data);
  };
  useEffect(() => { load().catch((e) => setMessage(errorMessage(e))); }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const active = offers.filter((o) => o.is_active);
  const avg = applications.length ? (applications.reduce((s, a) => s + a.match_score, 0) / applications.length).toFixed(1) : 0;
  const pending = applications.filter((a) => a.status === "recue").length;

  const publish = async (e) => {
    e.preventDefault();
    try {
      await api.post("/offers", form);
      setForm(EMPTY); setMessage("Offre publiée ✓"); load(); setTab("offres");
    } catch (err) { setMessage(errorMessage(err)); }
  };
  const changeStatus = async (id, status) => { await api.patch(`/applications/${id}/status`, { status }); load(); };
  const close = async (id) => { await api.delete(`/offers/${id}`); load(); };
  const findTalents = async (id) => {
    setTalentOffer(id);
    if (!id) return setTalents([]);
    try { setTalents((await api.get(`/recommendations/candidates/${id}`)).data); }
    catch (e) { setMessage(errorMessage(e)); }
  };

  const tabs = [["apercu", "📊 Aperçu"], ["publier", "➕ Publier une offre"], ["offres", `📋 Mes offres (${active.length})`], ["talents", "🎯 Talents (IA)"]];

  return (
    <>
      <h2>Espace entreprise</h2>
      <div className="tabs">{tabs.map(([k, l]) => <button key={k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>{l}</button>)}</div>
      {message && <p className="info">{message}</p>}

      {tab === "apercu" && (<>
        <div className="kpis">
          <div className="card kpi"><b>{active.length}</b><span>offres actives</span></div>
          <div className="card kpi"><b>{applications.length}</b><span>candidatures</span></div>
          <div className="card kpi"><b>{pending}</b><span>à traiter</span></div>
          <div className="card kpi"><b>{avg}%</b><span>compatibilité moyenne</span></div>
        </div>
        <h3>Candidatures reçues (classées par compatibilité)</h3>
        {applications.length === 0 && <p className="muted">Aucune candidature pour le moment.</p>}
        {applications.map((a) => (
          <div className="card" key={a.id}>
            <div className="row">
              <div><h3>{a.candidate_name || "Candidat"}</h3>
                <p className="muted">{a.candidate_education || "Formation non précisée"} · pour « {a.offer_title} »</p></div>
              <select value={a.status} onChange={(e) => changeStatus(a.id, e.target.value)}>
                {STATUSES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
            <MatchBar score={a.match_score} level={a.match_level} />
            <Chips matched={a.matched_skills} missing={a.missing_skills} />
          </div>
        ))}
      </>)}

      {tab === "publier" && (
        <form className="card" onSubmit={publish}>
          <label>Titre<input value={form.title} onChange={set("title")} required /></label>
          <label>Description<textarea rows={5} value={form.description} onChange={set("description")} required /></label>
          <div className="grid">
            <label>Type<select value={form.offer_type} onChange={set("offer_type")}><option value="stage">Stage</option><option value="emploi">Emploi</option></select></label>
            <label>Lieu<input value={form.location} onChange={set("location")} /></label>
          </div>
          <label>Compétences requises (virgules) — elles alimentent le matching IA
            <input value={form.required_skills} onChange={set("required_skills")} placeholder="python, sql, docker" /></label>
          <button className="btn" type="submit">Publier l'offre</button>
        </form>
      )}

      {tab === "offres" && (active.length === 0 ? <p className="muted">Aucune offre active.</p> : active.map((o) => (
        <div className="card row" key={o.id}>
          <div><h3>{o.title}</h3><p className="muted">{o.location} · {o.applications_count} candidature(s)</p>
            <Chips plain={(o.required_skills || "").split(",").map((s) => s.trim()).filter(Boolean)} /></div>
          <button className="btn-danger" onClick={() => close(o.id)}>Clôturer</button>
        </div>)))}

      {tab === "talents" && (<>
        <p className="muted">🤖 Choisissez une offre : l'IA classe les profils inscrits par compatibilité.</p>
        <select value={talentOffer} onChange={(e) => findTalents(e.target.value)}>
          <option value="">— Sélectionner une offre —</option>
          {active.map((o) => <option key={o.id} value={o.id}>{o.title}</option>)}
        </select>
        {talents.map((t) => (
          <div className="card" key={t.candidate_id}>
            <div className="row"><div><h3>{t.name}</h3><p className="muted">{t.education || "Formation non précisée"}</p></div></div>
            <MatchBar score={t.score} level={t.level} />
            <Chips matched={t.matched_skills} missing={t.missing_skills} />
          </div>
        ))}
      </>)}
    </>
  );
}
