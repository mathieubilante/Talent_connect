import { Link } from "react-router-dom";
import { t } from "../i18n.js";
import Seo from "../components/Seo.jsx";

/* Accueil des visiteurs : court, clair, avec les deux actions principales dès le premier écran. */
export default function Landing() {
  return (
    <section className="landing">
      <Seo title="Emplois et stages" description="Trouvez votre emploi ou votre stage : score de compatibilité, CV analysé, suivi de vos candidatures." />
      <div className="landing-card">
        <img src="/favicon.svg" alt="" className="landing-logo" />
        <h1>{t("landing_title")}</h1>
        <p className="landing-sub">{t("landing_sub")}</p>
        <div className="landing-actions">
          <Link to="/login?mode=register" className="btn big">{t("btn_signup")}</Link>
          <Link to="/login" className="btn-outline big">{t("btn_login")}</Link>
        </div>
        <Link to="/offers" className="link landing-browse">{t("btn_browse")}</Link>
      </div>
      <ul className="landing-points">
        <li>{t("landing_f1")}</li>
        <li>{t("landing_f2")}</li>
        <li>{t("landing_f3")}</li>
      </ul>
    </section>
  );
}
