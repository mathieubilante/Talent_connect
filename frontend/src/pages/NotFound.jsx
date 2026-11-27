import { Link } from "react-router-dom";
import Seo from "../components/Seo.jsx";
import { t } from "../i18n.js";

export default function NotFound() {
  return (
    <section className="notfound">
      <Seo title={t("nf_seo_title")} description={t("nf_seo_desc")} />
      <div className="nf-code">404</div>
      <h1>{t("nf_title")}</h1>
      <p className="muted">{t("nf_help")}</p>
      <div className="landing-actions">
        <Link to="/" className="btn big">{t("nf_home")}</Link>
        <Link to="/offers" className="btn-outline big">{t("nf_offers")}</Link>
      </div>
    </section>
  );
}
