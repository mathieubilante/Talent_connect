import { Link } from "react-router-dom";
import { t } from "../i18n.js";

export default function SiteFooter() {
  return (
    <footer className="sitefooter">
      <div className="footer-grid">
        <div>
          <div className="brand light"><img src="/favicon.svg" alt="" /> Talent<span>Connect</span></div>
          <p>{t("ft_desc")}</p>
        </div>
        <div>
          <h4>{t("ft_candidates")}</h4>
          <Link to="/offers?offer_type=emploi">{t("ft_jobs")}</Link>
          <Link to="/offers?offer_type=stage">{t("ft_internships")}</Link>
          <Link to="/companies">{t("ft_companies")}</Link>
          <Link to="/login?mode=register">{t("ft_signup")}</Link>
        </div>
        <div>
          <h4>{t("ft_recruiters")}</h4>
          <Link to="/login?mode=register&role=company">{t("ft_publish")}</Link>
          <Link to="/company">{t("ft_company_space")}</Link>
        </div>
        <div>
          <h4>{t("ft_ai")}</h4>
          <span>{t("ft_score")}</span>
          <span>{t("ft_cv")}</span>
          <span>{t("ft_assistant")}</span>
        </div>
      </div>
      <div className="footer-bottom">
        <Link to="/confidentialite">{t("ft_privacy")}</Link> · <Link to="/conditions">{t("ft_terms")}</Link> · © 2026 TalentConnect · Tous droits réservés
      </div>
    </footer>
  );
}
