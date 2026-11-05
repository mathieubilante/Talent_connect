import Chips from "./Chips.jsx";
import MatchBar from "./MatchBar.jsx";

const split = (raw) => (raw || "").split(/[,;]/).map((s) => s.trim()).filter(Boolean);

export default function OfferCard({ offer: o, role, applied, onApply, onToggleFav }) {
  const hasMatch = o.match_score !== null && o.match_score !== undefined;
  return (
    <article className="card offer">
      <div className="row">
        <div>
          <h3>{o.title}</h3>
          <p className="muted">🏢 {o.company_name} · 📍 {o.location || "Lieu non précisé"}</p>
        </div>
        <div className="row gap">
          <span className={`tag ${o.offer_type}`}>{o.offer_type}</span>
          {role === "candidate" && (
            <button className={`heart ${o.is_favorite ? "on" : ""}`} onClick={() => onToggleFav(o.id)}
                    title="Ajouter aux favoris">{o.is_favorite ? "♥" : "♡"}</button>
          )}
        </div>
      </div>
      <p>{o.description.length > 230 ? o.description.slice(0, 230) + "…" : o.description}</p>
      {hasMatch
        ? <Chips matched={o.matched_skills} missing={o.missing_skills} />
        : <Chips plain={split(o.required_skills)} />}
      {hasMatch && (
        <>
          <MatchBar score={o.match_score} level={o.match_level} />
          <p className="muted small">🤖 {o.match_explanation}</p>
        </>
      )}
      {role === "candidate" && (
        <div className="row end">
          {applied
            ? <span className="tag done">✓ Déjà postulé</span>
            : <button className="btn" onClick={() => onApply(o)}>Postuler</button>}
        </div>
      )}
    </article>
  );
}
