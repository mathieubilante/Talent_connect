import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";
import { t } from "../i18n.js";
import Chips from "../components/Chips.jsx";
import MatchBar from "../components/MatchBar.jsx";
import OfferCard from "../components/OfferCard.jsx";
import ProfileHeader from "../components/ProfileHeader.jsx";

const STATUS_KEY = { recue: "status_new", preselectionnee: "status_pre", entretien: "status_interview", acceptee: "status_accepted", refusee: "status_refused" };
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
      setMessage(t("profile_saved"));
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

  const tabs = [["profil", t("tab_profile")], ["candidatures", `📨 Candidatures (${applications.length})`],
                ["favoris", `♥ Favoris (${favorites.length})`], ["reco", t("tab_reco")]];

  return (
    <>
      <ProfileHeader onError={setMessage} />
      <h2>{t("my_space")}</h2>
      <div className="tabs">{tabs.map(([k, label]) => (
        <button key={k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>{label}</button>))}</div>
      {message && <p className="info">{message}</p>}

      {tab === "profil" && (
        <form className="card" onSubmit={save}>
          <div className="row">
            <h3>{t("my_profile")}</h3>
            <div className="complete"><span>Profil complété à {completeness}%</span>
              <div className="bar"><div className="fill bon" style={{ width: `${completeness}%` }} /></div></div>
          </div>
          <div className="grid">
            <label>{t("first_name")}<input value={profile.first_name} onChange={set("first_name")} /></label>
            <label>{t("last_name")}<input value={profile.last_name} onChange={set("last_name")} /></label>
            <label>{t("phone")}<input value={profile.phone} onChange={set("phone")} /></label>
            <label>{t("education")}<input value={profile.education} onChange={set("education")} /></label>
          </div>
          <label>Compétences (séparées par des virgules)
            <input value={profile.skills} onChange={set("skills")} placeholder="python, sql, react" />
          </label>
          <label>CV (PDF, 5 Mo max) — l'IA en extrait vos compétences
            <input type="file" accept="application/pdf" onChange={uploadCv} />
          </label>
          {profile.cv_path && profile.cv_readable && <p className="muted small">✓ CV déposé et lisible</p>}
          {profile.cv_path && !profile.cv_readable && (
            <p className="profile-warn">⚠️ Votre CV ne contient pas de texte lisible (scan ou photo). Les compétences n'ont pas pu être détectées : déposez une version numérique du CV.</p>
          )}
          <button className="btn" type="submit">{t("save")}</button>
        </form>
      )}

      {tab === "candidatures" && (applications.length === 0
        ? <p className="muted">{t("not_applied_yet")}</p>
        : applications.map((a) => (
          <div className="card" key={a.id}>
            <div className="row"><h3>{a.offer_title}</h3><span className={`tag st-${a.status}`}>{t(STATUS_KEY[a.status])}</span></div>
            <MatchBar score={a.match_score} level={a.match_level} />
            <Chips matched={a.matched_skills} missing={a.missing_skills} />
          </div>)))}

      {tab === "favoris" && (favorites.length === 0
        ? <p className="muted">{t("fav_hint")}</p>
        : favorites.map((o) => <OfferCard key={o.id} offer={o} role="candidate" applied={false}
            onApply={() => setMessage(t("apply_from_offers"))} onToggleFav={toggleFav} />))}

      {tab === "reco" && (<>
        <p className="muted">🤖 Les offres les plus compatibles avec votre profil (hors celles déjà postulées).</p>
        {reco.length === 0 && <p className="muted">{t("reco_hint")}</p>}
        {reco.map((o) => <OfferCard key={o.id} offer={o} role="candidate" applied={false}
            onApply={() => setMessage(t("apply_from_offers"))} onToggleFav={toggleFav} />)}
      </>)}
    </>
  );
}
