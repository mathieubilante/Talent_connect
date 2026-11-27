import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { serverLogout } from "../api";
import { t } from "../i18n.js";

/* Deux cas :
   - « apply » : le candidat veut postuler sans abonnement. Il peut fermer la fenêtre, sans déconnexion.
   - « period » : la période d'utilisation est terminée. Refuser déconnecte automatiquement. */
export default function SubscriptionGate() {
  const navigate = useNavigate();
  const [reason, setReason] = useState(null);
  useEffect(() => {
    const show = (e) => setReason(e.detail?.reason || "period");
    window.addEventListener("subscription-required", show);
    return () => window.removeEventListener("subscription-required", show);
  }, []);
  if (!reason) return null;
  const subscribe = () => { setReason(null); navigate("/billing"); };
  const later = () => setReason(null);
  const decline = async () => {
    setReason(null);
    await serverLogout();
    navigate("/login?reason=expired");
  };
  const isApply = reason === "apply";
  return (
    <div className="modal-back">
      <div className="modal welcome" role="dialog" aria-modal="true" aria-labelledby="sub-title">
        <h3 id="sub-title">{isApply ? t("sub_apply_title") : t("sub_title")}</h3>
        <p className="muted">{isApply ? t("sub_apply_text") : t("sub_text")}</p>
        <button type="button" className="btn full" onClick={subscribe}>{t("sub_yes")}</button>
        {isApply
          ? <button type="button" className="btn-outline full" onClick={later}>{t("sub_later")}</button>
          : <button type="button" className="btn-outline full" onClick={decline}>{t("sub_no")}</button>}
      </div>
    </div>
  );
}
