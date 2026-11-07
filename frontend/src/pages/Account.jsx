import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { errorMessage } from "../api";

export default function Account() {
  const [info, setInfo] = useState(null);
  const [history, setHistory] = useState([]);
  const [kyc, setKyc] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.get("/account/me"), api.get("/account/login-history")])
      .then(([a, h]) => { setInfo(a.data); setHistory(h.data); })
      .catch((e) => setError(errorMessage(e)));
    api.get("/kyc/me").then((r) => setKyc(r.data)).catch(() => {});
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!info) return <p className="muted">Chargement…</p>;
  const docsDone = kyc && kyc.complete;
  const docsApproved = kyc && kyc.required.length > 0 && kyc.documents.filter((d) => d.status === "approved").length >= kyc.required.length;
  const steps = [
    { label: "Compte vérifié (code OTP)", done: true },
    { label: "Documents d'identité envoyés", done: !!docsDone, link: "/kyc" },
    { label: "Validation par l'administration", done: info.status === "validated" || info.status === "active",
      failed: info.status === "rejected", hint: docsApproved ? "documents validés" : "" },
    { label: "Abonnement et paiement", done: info.status === "active", soon: info.status !== "active" },
  ];
  const current = steps.findIndex((st) => !st.done);
  const pct = Math.min(100, Math.round((info.trial_logins_used / info.trial_limit) * 100));

  return (
    <>
      <h2>👤 Mon compte</h2>
      <div className="kpis">
        <div className="card kpi"><b>{info.status_label}</b><span>statut du compte</span></div>
        <div className="card kpi"><b>{info.trial_logins_used}/{info.trial_limit}</b><span>connexions d'essai utilisées</span></div>
        <div className="card kpi"><b>{info.trial_remaining}</b><span>connexions restantes</span></div>
      </div>

      <div className="card">
        <h3>Suivi de mon compte</h3>
        <ol className="stepper">
          {steps.map((st, i) => (
            <li key={st.label} className={st.failed ? "failed" : st.done ? "done" : i === current ? "current" : ""}>
              <span className="dot">{st.failed ? "✖" : st.done ? "✓" : i + 1}</span>
              <span>{st.link && !st.done ? <Link to={st.link} className="link">{st.label}</Link> : st.label}
                {st.hint && !st.done && <span className="muted small"> ({st.hint})</span>}
                {st.soon && <span className="muted small"> (bientôt disponible)</span>}</span>
            </li>))}
        </ol>
        {info.status === "rejected" && <p className="error">{info.message}</p>}
        {info.status === "validated" && <p className="info">Votre compte est validé. Il reste à souscrire un abonnement pour l'activer complètement.</p>}
      </div>

      {info.status !== "active" && info.status !== "rejected" && (
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
