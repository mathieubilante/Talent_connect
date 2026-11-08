import { Link } from "react-router-dom";
import Chips from "./Chips.jsx";
import CompanyLogo from "./CompanyLogo.jsx";
import MatchBar from "./MatchBar.jsx";
import { isNew, splitSkills, timeAgo } from "../utils";

export default function OfferCard({ offer: o, role, applied, onApply, onToggleFav }) {
  const hasMatch = o.match_score !== null && o.match_score !== undefined;
  const next = encodeURIComponent(`/offers/${o.id}`);
  const desc = (o.description || "").length > 200 ? o.description.slice(0, 200) + "…" : o.description;

  return (
    <article className={`card offer ${hasMatch ? "lvl-" + o.match_level : ""}`}>
      <div className="offer-main">
        <Link to={`/companies/${o.company_id}`}><CompanyLogo name={o.company_name} /></Link>
        <div className="offer-body">
          <div className="row">
            <h3 className="offer-title"><Link to={`/offers/${o.id}`}>{o.title}</Link></h3>
            <div className="row gap">
              {isNew(o.created_at) && <span className="badge-new">Nouveau</span>}
              <span className={`tag ${o.offer_type}`}>{o.offer_type}</span>
              {role === "candidate" && (
                <button className={`heart ${o.is_favorite ? "on" : ""}`} onClick={() => onToggleFav && onToggleFav(o.id)}
                        title="Ajouter aux favoris">{o.is_favorite ? "♥" : "♡"}</button>
              )}
            </div>
          </div>
          <p className="muted">
            <Link className="plain" to={`/companies/${o.company_id}`}>{o.company_name}</Link>
            {" · "}📍 {o.location || "Lieu non précisé"}{" · "}🕒 {timeAgo(o.created_at)}
          </p>
          <p className="offer-desc">{desc}</p>
          {hasMatch
            ? <Chips matched={o.matched_skills} missing={o.missing_skills} />
            : <Chips plain={splitSkills(o.required_skills).slice(0, 6)} />}
          {hasMatch && (
            <>
              <MatchBar score={o.match_score} level={o.match_level} />
              <p className="muted small">🤖 {o.match_explanation}</p>
            </>
          )}
          <div className="row end gap">
            <Link className="link" to={`/offers/${o.id}`}>Voir l'offre</Link>
            {role === "candidate" && (applied
              ? <span className="tag done">✓ Déjà postulé</span>
              : <button className="btn" onClick={() => onApply && onApply(o)}>Postuler</button>)}
            {!role && <Link className="btn" to={`/login?next=${next}`}>Postuler</Link>}
          </div>
        </div>
      </div>
    </article>
  );
}
