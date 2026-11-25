import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { serverLogout } from "../api";
import { t } from "../i18n.js";

/* Affichée quand la période d'utilisation est terminée. « S'abonner » ouvre la page d'abonnement.
   « Non merci » déconnecte automatiquement. */
export default function SubscriptionGate() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const show = () => setOpen(true);
    window.addEventListener("subscription-required", show);
    return () => window.removeEventListener("subscription-required", show);
  }, []);
  if (!open) return null;
  const subscribe = () => { setOpen(false); navigate("/billing"); };
  const decline = async () => {
    setOpen(false);
    await serverLogout();
    navigate("/login?reason=expired");
  };
  return (
    <div className="modal-back">
      <div className="modal welcome" role="dialog" aria-modal="true" aria-labelledby="sub-title">
        <h3 id="sub-title">{t("sub_title")}</h3>
        <p className="muted">{t("sub_text")}</p>
        <button type="button" className="btn full" onClick={subscribe}>{t("sub_yes")}</button>
        <button type="button" className="btn-outline full" onClick={decline}>{t("sub_no")}</button>
      </div>
    </div>
  );
}
