import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { errorMessage } from "../api";

export default function Account() {
  const [info, setInfo] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.get("/account/me"), api.get("/account/login-history")])
      .then(([a, h]) => { setInfo(a.data); setHistory(h.data); })
      .catch((e) => setError(errorMessage(e)));
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!info) return <p className="muted">Chargement…</p>;
  const pct = Math.min(100, Math.round((info.trial_logins_used / info.trial_limit) * 100));

  return (
    <>
      <h2>👤 Mon compte</h2>
      <div className="kpis">
        <div className="card kpi"><b>{info.status_label}</b><span>statut du compte</span></div>
        <div className="card kpi"><b>{info.trial_logins_used}/{info.trial_limit}</b><span>connexions d'essai utilisées</span></div>
        <div className="card kpi"><b>{info.trial_remaining}</b><span>connexions restantes</span></div>
      </div>

      {info.status !== "active" && (
        <div className="card">
          <h3>Essai gratuit</h3>
          <div className="bar"><div className={`fill ${info.trial_exhausted ? "faible" : info.alert ? "moyen" : "bon"}`} style={{ width: `${pct}%` }} /></div>
          <p className={info.trial_exhausted || info.alert ? "error" : "muted"}>{info.message}</p>
          {info.status !== "active" && !info.trial_exhausted && (
            <p className="muted small">📁 Vous pouvez déjà <Link to="/kyc" className="link">déposer vos documents d'identité</Link> pour préparer la validation de votre compte.</p>
          )}
          {info.trial_exhausted && (
            <ol className="muted">
              <li><Link to="/kyc" className="link">Soumettre vos documents d'identité</Link></li>
              <li>Validation de votre compte par l'administration</li>
              <li>Choix d'un abonnement et paiement</li>
              <li>Activation complète, sans perte de vos données</li>
            </ol>
          )}
        </div>
      )}

      <div className="card">
        <h3>Historique des connexions</h3>
        {history.length === 0 ? <p className="muted">Aucune connexion enregistrée.</p> : (
          <div className="scroll"><table>
            <thead><tr><th>Date et heure</th><th>Adresse IP</th><th>Appareil</th><th>Essai</th></tr></thead>
            <tbody>{history.map((h, i) => (
              <tr key={i}><td>{new Date(h.logged_at + "Z").toLocaleString("fr-FR")}</td><td>{h.ip_address || "—"}</td>
                <td>{(h.user_agent || "—").slice(0, 60)}</td><td>{h.counted ? "compté" : "—"}</td></tr>))}</tbody>
          </table></div>
        )}
      </div>
    </>
  );
}
