import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { t } from "../i18n.js";
import api, { errorMessage, getRole } from "../api";
import ApplyModal from "../components/ApplyModal.jsx";
import Chips from "../components/Chips.jsx";
import CompanyLogo from "../components/CompanyLogo.jsx";
import MatchBar from "../components/MatchBar.jsx";
import { splitSkills, timeAgo, toDate } from "../utils";

export default function OfferDetail() {
  const { id } = useParams();
  const role = getRole();
  const [offer, setOffer] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [error, setError] = useState("");
  const [applied, setApplied] = useState(false);
  const [applying, setApplying] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    setOffer(null); setError(""); setMessage("");
    const url = role === "candidate" ? `/offers/${id}` : `/public/offers/${id}`;
    api.get(url).then((r) => setOffer(r.data)).catch((e) => setError(errorMessage(e)));
    api.get(`/public/offers/${id}/similar`).then((r) => setSimilar(r.data)).catch(() => {});
    if (role === "candidate") {
      api.get("/applications/mine").then((r) => setApplied(r.data.some((a) => a.offer_id === Number(id)))).catch(() => {});
    }
    window.scrollTo(0, 0);
  }, [id, role]);

  const toggleFav = async () => {
    await api.post(`/favorites/${offer.id}`);
    setOffer({ ...offer, is_favorite: !offer.is_favorite });
  };
  const share = async () => {
    try { await navigator.clipboard.writeText(window.location.href); setMessage(t("shared_copied")); }
    catch { setMessage(window.location.href); }
  };

  if (error) return <div className="card empty"><h3>{error}</h3><Link to="/offers" className="link">{t("back_to_offers")}</Link></div>;
  if (!offer) return <p className="muted">{t("loading")}</p>;

  const hasMatch = offer.match_score !== null && offer.match_score !== undefined;
  const deadline = toDate(offer.deadline);
  const next = encodeURIComponent(`/offers/${offer.id}`);

  return (
    <>
      <p className="muted small"><Link to="/offers" className="plain">{t("all_offers_back")}</Link></p>
      <div className="detail">
        <div>
          <div className="card">
            <div className="detail-head">
              <CompanyLogo name={offer.company_name} size={64} />
              <div style={{ flex: 1 }}>
                <h1>{offer.title}</h1>
                <p className="muted"><Link className="plain" to={`/companies/${offer.company_id}`}>{offer.company_name}</Link>
                  {" · "}📍 {offer.location || t("place_unknown")}{" · "}🕒 {timeAgo(offer.created_at)}</p>
                <div className="row gap" style={{ justifyContent: "flex-start" }}>
                  <span className={`tag ${offer.offer_type}`}>{offer.offer_type}</span>
                  {deadline && <span className="tag">Date limite : {deadline.toLocaleDateString("fr-FR")}</span>}
                </div>
              </div>
            </div>
            <div className="row gap detail-actions">
              {role === "candidate" && (applied
                ? <span className="tag done">{t("already_applied")}</span>
                : <button className="btn big" onClick={() => setApplying(true)}>{t("apply_now")}</button>)}
              {!role && <Link className="btn big" to={`/login?next=${next}`}>{t("apply_now")}</Link>}
              {role === "candidate" && (
                <button className={`btn-outline`} onClick={toggleFav}>{offer.is_favorite ? "♥ Dans mes favoris" : "♡ Ajouter aux favoris"}</button>
              )}
              <button className="btn-outline" onClick={share}>{t("share")}</button>
            </div>
            {message && <p className="info">{message}</p>}
          </div>

          {hasMatch && (
            <div className="card">
              <h3>{t("your_match")}</h3>
              <MatchBar score={offer.match_score} level={offer.match_level} />
              <p className="muted">{offer.match_explanation}</p>
              <Chips matched={offer.matched_skills} missing={offer.missing_skills} />
              <p className="muted small">{t("legend_match")}</p>
            </div>
          )}

          <div className="card">
            <h3>{t("job_description")}</h3>
            <p className="prewrap">{offer.description}</p>
            {splitSkills(offer.required_skills).length > 0 && (
              <>
                <h3 style={{ marginTop: 18 }}>{t("required_skills")}</h3>
                <Chips plain={splitSkills(offer.required_skills)} />
              </>
            )}
          </div>
        </div>

        <aside>
          <div className="card">
            <div className="row gap" style={{ justifyContent: "flex-start" }}>
              <CompanyLogo name={offer.company_name} size={48} />
              <div><h3 style={{ margin: 0 }}>{offer.company_name}</h3>
                <p className="muted small" style={{ margin: 0 }}>{offer.company_sector || t("sector_unknown")}{offer.company_city ? ` · ${offer.company_city}` : ""}</p></div>
            </div>
            <p style={{ marginTop: 12 }}><Link to={`/companies/${offer.company_id}`} className="link">{t("see_company_profile")}</Link></p>
          </div>
          {similar.length > 0 && (
            <div className="card">
              <h3>{t("similar_offers")}</h3>
              {similar.map((s) => (
                <Link key={s.id} to={`/offers/${s.id}`} className="similar">
                  <b>{s.title}</b>
                  <span className="muted small">{s.company_name} · {s.location || "—"}</span>
                </Link>
              ))}
            </div>
          )}
        </aside>
      </div>

      {applying && (
        <ApplyModal offer={offer} onClose={() => setApplying(false)}
                    onDone={(msg) => { setMessage(msg); setApplied(true); setApplying(false); }} />
      )}
    </>
  );
}
