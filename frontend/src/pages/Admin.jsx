import { useEffect, useState } from "react";
import api, { downloadDocument, errorMessage } from "../api";

const LABELS = { recue: "Reçues", preselectionnee: "Présélectionnées", entretien: "Entretiens", acceptee: "Acceptées", refusee: "Refusées" };

export default function Admin() {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [kyc, setKyc] = useState([]);
  const [error, setError] = useState("");
  useEffect(() => {
    Promise.all([api.get("/admin/stats"), api.get("/admin/users"), api.get("/admin/accounts"), api.get("/admin/kyc")])
      .then(([s, u, a, k]) => { setStats(s.data); setUsers(u.data); setAccounts(a.data); setKyc(k.data); })
      .catch((e) => setError(errorMessage(e)));
  }, []);

  const changeStatus = async (id, status) => {
    const reason = status === "rejected" ? window.prompt("Motif du refus :") || "" : "";
    await api.patch(`/admin/accounts/${id}/status`, { status, reason });
    setAccounts((await api.get("/admin/accounts")).data);
  };

  if (error) return <p className="error">{error}</p>;
  if (!stats) return <p className="muted">Chargement…</p>;
  const maxStatus = Math.max(1, ...Object.values(stats.applications_by_status));
  const maxSkill = Math.max(1, ...stats.top_skills.map((s) => s.count));

  return (
    <>
      <h2>📊 Administration</h2>
      <div className="kpis">
        <div className="card kpi"><b>{stats.users}</b><span>utilisateurs</span></div>
        <div className="card kpi"><b>{stats.offers_active}</b><span>offres actives</span></div>
        <div className="card kpi"><b>{stats.applications}</b><span>candidatures</span></div>
        <div className="card kpi"><b>{stats.average_match_score}%</b><span>compatibilité moyenne</span></div>
      </div>
      <div className="grid2">
        <div className="card"><h3>Candidatures par statut</h3>
          {Object.entries(stats.applications_by_status).map(([k, n]) => (
            <div className="hbar" key={k}><span>{LABELS[k]}</span>
              <div className="bar"><div className="fill bon" style={{ width: `${(n / maxStatus) * 100}%` }} /></div><b>{n}</b></div>))}
        </div>
        <div className="card"><h3>Compétences les plus demandées</h3>
          {stats.top_skills.length === 0 && <p className="muted">Pas encore de données.</p>}
          {stats.top_skills.map((s) => (
            <div className="hbar" key={s.skill}><span>{s.skill}</span>
              <div className="bar"><div className="fill excellent" style={{ width: `${(s.count / maxSkill) * 100}%` }} /></div><b>{s.count}</b></div>))}
        </div>
      </div>
      <div className="card"><h3>Répartition</h3>
        <p>👤 {stats.candidates} candidats · 🏢 {stats.companies} entreprises · 🎓 {stats.offers_stage} offres de stage · 💼 {stats.offers_emploi} offres d'emploi</p></div>
      <div className="card"><h3>Comptes et essais gratuits</h3>
        <div className="scroll"><table><thead><tr><th>E-mail</th><th>Rôle</th><th>Essai</th><th>Statut</th></tr></thead>
          <tbody>{accounts.map((a) => <tr key={a.user_id}><td>{a.email}</td><td>{a.role}</td>
            <td>{a.trial_logins_used}/{a.trial_limit}</td>
            <td><select value={a.status} onChange={(e) => changeStatus(a.user_id, e.target.value)}>
              <option value="pending">En attente</option><option value="validated">Validé</option>
              <option value="active">Actif</option><option value="rejected">Refusé</option></select></td></tr>)}</tbody></table></div></div>
      <div className="card"><h3>Dossiers de documents (KYC)</h3>
        {kyc.length === 0 && <p className="muted">Aucun document déposé pour le moment.</p>}
        {kyc.map((k) => (
          <div key={k.user_id} style={{ borderTop: "1px solid #edf1f5", padding: "10px 0" }}>
            <div className="row"><b>{k.email}</b>
              <span className={k.complete ? "tag st-acceptee" : "tag stage"}>{k.uploaded_count}/{k.required_count} {k.complete ? "· complet" : "· incomplet"}</span></div>
            <div className="chips">{k.documents.map((d) => (
              <button key={d.id} className="chip ok" style={{ border: 0, cursor: "pointer" }}
                      onClick={() => downloadDocument(d.id, d.original_name)} title="Télécharger (déchiffré)">⬇ {d.label}</button>))}</div>
          </div>))}
      </div>
      <div className="card"><h3>Utilisateurs récents</h3>
        <div className="scroll"><table><thead><tr><th>ID</th><th>E-mail</th><th>Rôle</th><th>Inscription</th></tr></thead>
          <tbody>{users.map((u) => <tr key={u.id}><td>{u.id}</td><td>{u.email}</td><td>{u.role}</td>
            <td>{u.created_at ? new Date(u.created_at).toLocaleDateString("fr-FR") : ""}</td></tr>)}</tbody></table></div></div>
    </>
  );
}
