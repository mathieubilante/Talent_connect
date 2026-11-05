import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";
import Chips from "../components/Chips.jsx";
import MatchBar from "../components/MatchBar.jsx";
import OfferCard from "../components/OfferCard.jsx";

const STATUS = { recue: "Reçue", preselectionnee: "Présélectionnée", entretien: "Entretien", acceptee: "Acceptée", refusee: "Refusée" };
const FIELDS = ["first_name", "last_name", "phone", "education", "skills", "cv_path"];

export default function CandidateSpace() {
  const [tab, setTab] = useState("profil");
  const [profile, setProfile] = useState({ first_name: "", last_name: "", phone: "", education: "", skills: "", cv_path: "" });
  const [applications, setApplications] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [reco, setReco] = useState([]);
  const [message, setMessage] = useState("");

  const load = async () => {
    const [p, a, f, r] = await Promise.all([
      api.get("/profile/candidate"), api.get("/applications/mine"),
      api.get("/favorites"), api.get("/recommendations/offers"),
    ]);
    setProfile(p.data); setApplications(a.data); setFavorites(f.data); setReco(r.data);
  };
  useEffect(() => { load().catch((e) => setMessage(errorMessage(e))); }, []);

  const set = (k) => (e) => setProfile({ ...profile, [k]: e.target.value });
  const completeness = Math.round((FIELDS.filter((k) => profile[k]).length / FIELDS.length) * 100);

  const save = async (e) => {
    e.preventDefault();
    try {
      const { first_name, last_name, phone, education, skills } = profile;
      await api.put("/profile/candidate", { first_name, last_name, phone, education, skills });
      setMessage("Profil enregistré ✓");
      load();
    } catch (err) { setMessage(errorMessage(err)); }
  };

  const uploadCv = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const data = new FormData();
    data.append("file", file);
    try {
      const res = await api.post("/profile/candidate/cv", data);
      setProfile(res.data);
      setMessage("CV analysé par l'IA : vos compétences ont été détectées et ajoutées à votre profil ✓");
      load();
    } catch (err) { setMessage(errorMessage(err)); }
  };

  const toggleFav = async (id) => { await api.post(`/favorites/${id}`); load(); };

  const tabs = [["profil", "👤 Profil"], ["candidatures", `📨 Candidatures (${applications.length})`],
                ["favoris", `♥ Favoris (${favorites.length})`], ["reco", "🎯 Recommandations"]];

  return (
    <>
      <h2>Mon espace</h2>
      <div className="tabs">{tabs.map(([k, label]) => (
        <button key={k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>{label}</button>))}</div>
      {message && <p className="info">{message}</p>}

      {tab === "profil" && (
        <form className="card" onSubmit={save}>
          <div className="row">
            <h3>Mon profil</h3>
            <div className="complete"><span>Profil complété à {completeness}%</span>
              <div className="bar"><div className="fill bon" style={{ width: `${completeness}%` }} /></div></div>
          </div>
          <div className="grid">
            <label>Prénom<input value={profile.first_name} onChange={set("first_name")} /></label>
            <label>Nom<input value={profile.last_name} onChange={set("last_name")} /></label>
            <label>Téléphone<input value={profile.phone} onChange={set("phone")} /></label>
            <label>Formation<input value={profile.education} onChange={set("education")} /></label>
          </div>
          <label>Compétences (séparées par des virgules)
            <input value={profile.skills} onChange={set("skills")} placeholder="python, sql, react" />
          </label>
          <label>CV (PDF, 5 Mo max) — l'IA en extrait vos compétences
            <input type="file" accept="application/pdf" onChange={uploadCv} />
          </label>
          {profile.cv_path && <p className="muted small">✓ CV déjà déposé</p>}
          <button className="btn" type="submit">Enregistrer</button>
        </form>
      )}

      {tab === "candidatures" && (applications.length === 0
        ? <p className="muted">Vous n'avez pas encore postulé.</p>
        : applications.map((a) => (
          <div className="card" key={a.id}>
            <div className="row"><h3>{a.offer_title}</h3><span className={`tag st-${a.status}`}>{STATUS[a.status]}</span></div>
            <MatchBar score={a.match_score} level={a.match_level} />
            <Chips matched={a.matched_skills} missing={a.missing_skills} />
          </div>)))}

      {tab === "favoris" && (favorites.length === 0
        ? <p className="muted">Cliquez sur ♡ sur une offre pour la retrouver ici.</p>
        : favorites.map((o) => <OfferCard key={o.id} offer={o} role="candidate" applied={false}
            onApply={() => setMessage("Postulez depuis la page Offres.")} onToggleFav={toggleFav} />))}

      {tab === "reco" && (<>
        <p className="muted">🤖 Les offres les plus compatibles avec votre profil (hors celles déjà postulées).</p>
        {reco.length === 0 && <p className="muted">Complétez vos compétences pour recevoir des recommandations.</p>}
        {reco.map((o) => <OfferCard key={o.id} offer={o} role="candidate" applied={false}
            onApply={() => setMessage("Postulez depuis la page Offres.")} onToggleFav={toggleFav} />)}
      </>)}
    </>
  );
}
