import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import api from "../api";

export default function TrialBanner() {
  const [info, setInfo] = useState(null);
  const { pathname } = useLocation();

  useEffect(() => { api.get("/account/me").then((r) => setInfo(r.data)).catch(() => {}); }, [pathname]);
  if (!info || info.status === "active") return null;

  const pct = Math.min(100, Math.round((info.trial_logins_used / info.trial_limit) * 100));
  const level = info.trial_exhausted || info.status === "rejected" ? "danger" : info.alert ? "warn" : "ok";
  return (
    <div className={`trial ${level}`}>
      <div className="row">
        <span><b>{info.status_label}</b> · {info.message}</span>
        <span className="row gap">{info.status === "validated" && <Link to="/billing" className="link">S'abonner</Link>}<Link to="/account" className="link">Détails</Link></span>
      </div>
      <div className="bar"><div className={`fill ${level === "ok" ? "bon" : level === "warn" ? "moyen" : "faible"}`} style={{ width: `${pct}%` }} /></div>
    </div>
  );
}
