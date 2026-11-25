import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getRole } from "../api";
import { t } from "../i18n.js";

/* Affiché une seule fois à la première visite d'un visiteur non connecté. */
export default function WelcomeModal() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  useEffect(() => {
    try {
      if (!getRole() && !localStorage.getItem("welcomeSeen")) setOpen(true);
    } catch { /* stockage indisponible */ }
  }, []);
  if (!open) return null;
  const close = (to) => {
    try { localStorage.setItem("welcomeSeen", "1"); } catch { /* ignore */ }
    setOpen(false);
    if (to) navigate(to);
  };
  return (
    <div className="modal-back" onClick={() => close(null)}>
      <div className="modal welcome" onClick={(e) => e.stopPropagation()}>
        <h3>{t("welcome_title")}</h3>
        <p className="muted">{t("welcome_text")}</p>
        <button type="button" className="btn full" onClick={() => close("/login?mode=register")}>{t("btn_signup")}</button>
        <button type="button" className="btn-outline full" onClick={() => close("/login")}>{t("btn_login")}</button>
        <button type="button" className="link" onClick={() => close(null)}>{t("welcome_continue")}</button>
      </div>
    </div>
  );
}
