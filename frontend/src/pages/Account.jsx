import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { errorMessage, getRole } from "../api";
import PersonalInfoForm from "../components/PersonalInfoForm.jsx";
import { t } from "../i18n.js";

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
  if (!info) return <p className="muted">{t("ac_loading")}</p>;
  const docsDone = kyc && kyc.complete;
  const docsApproved = kyc && kyc.required.length > 0 && kyc.documents.filter((d) => d.status === "approved").length >= kyc.required.length;
  const steps = [
    { label: t("ac_otp"), done: true },
    { label: t("ac_docs"), done: !!docsDone, link: "/kyc" },
    { label: t("ac_admin"), done: info.status === "validated" || info.status === "active",
      failed: info.status === "rejected", hint: docsApproved ? "documents validés" : "" },
    { label: t("ac_subscription"), done: info.status === "active", link: info.status === "validated" ? "/billing" : null },
  ];
  const current = steps.findIndex((st) => !st.done);
  const pct = Math.min(100, Math.round((info.trial_logins_used / info.trial_limit) * 100));

  return (
    <>
      <h2>👤 Mon compte</h2>
      {getRole() === "candidate" && (
        <div className="card" style={{ marginBottom: 14 }}>
          <h3>{t("ac_personal")}</h3>
          <p className="muted small">Ces informations servent à votre profil et à vos candidatures. Elles se modifient uniquement ici.</p>
          <PersonalInfoForm />
        </div>
      )}
      <div className="kpis">
        <div className="card kpi"><b>{info.status_label}</b><span>{t("ac_status")}</span></div>
      </div>

      <div className="card">
        <h3>{t("ac_follow")}</h3>
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
        {info.status === "validated" && <p className="info">Votre compte est validé. Il reste à souscrire un abonnement pour l'activer complètement. <Link to="/billing" className="link">{t("ac_choose_plan")}</Link></p>}
      </div>

      <div className="card">
        <h3>{t("ac_history")}</h3>
        {history.length === 0 ? <p className="muted">{t("ac_no_login")}</p> : (
          <div className="scroll"><table>
            <thead><tr><th>{t("ac_datetime")}</th><th>{t("ac_ip")}</th><th>{t("ac_device")}</th><th>{t("ac_trial")}</th></tr></thead>
            <tbody>{history.map((h, i) => (
              <tr key={i}><td>{new Date(h.logged_at + "Z").toLocaleString("fr-FR")}</td><td>{h.ip_address || "—"}</td>
                <td>{(h.user_agent || "—").slice(0, 60)}</td><td>{h.counted ? "compté" : "—"}</td></tr>))}</tbody>
          </table></div>
        )}
      </div>
    </>
  );
}
