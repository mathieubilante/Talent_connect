import { Link } from "react-router-dom";
import { t } from "../i18n.js";

export default function SiteFooter() {
  return (
    <footer className="sitefooter">
      <div className="footer-grid">
        <div>
          <div className="brand light"><img src="/favicon.svg" alt="" /> Talent<span>Connect</span></div>
          <p>{t("footer_desc")}</p>
        </div>
        <div>
          <h4>{t("footer_candidates")}</h4>
          <Link to="/offers?offer_type=emploi">{t("footer_jobs")}</Link>
          <Link to="/offers?offer_type=stage">{t("footer_internships")}</Link>
          <Link to="/companies">{t("footer_companies")}</Link>
          <Link to="/login?mode=register">{t("footer_register")}</Link>
        </div>
        <div>
          <h4>{t("footer_recruiters")}</h4>
          <Link to="/login?mode=register&role=company">{t("footer_publish")}</Link>
          <Link to="/company">{t("footer_space")}</Link>
        </div>
        <div>
          <h4>{t("footer_ai")}</h4>
          <span>{t("footer_score")}</span>
          <span>{t("footer_cv")}</span>
          <span>{t("footer_assistant")}</span>
        </div>
      </div>
      <div className="footer-bottom">{t("footer_rights")}</div>
    </footer>
  );
}
