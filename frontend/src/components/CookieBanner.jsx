import { useState } from "react";
import { Link } from "react-router-dom";
import { loadAnalytics } from "./Analytics.jsx";

/* Bandeau de consentement. Le site ne fonctionne pas avec les cookies publicitaires : il n'y en a pas.
   Les mesures d'audience ne sont chargées qu'après un accord explicite. */
export default function CookieBanner() {
  const [choice, setChoice] = useState(() => { try { return localStorage.getItem("cookieConsent"); } catch { return null; } });
  if (choice) return null;
  const save = (value) => {
    try { localStorage.setItem("cookieConsent", value); } catch { /* ignore */ }
    setChoice(value);
    if (value === "accepted") loadAnalytics();
  };
  return (
    <div className="cookie-banner" role="dialog" aria-label="Consentement aux cookies">
      <p>Nous utilisons uniquement le stockage nécessaire au fonctionnement du site (connexion, préférences). Avec votre accord, nous mesurons aussi l'audience pour améliorer le service. <Link to="/confidentialite">En savoir plus</Link>.</p>
      <div className="cookie-actions">
        <button type="button" className="btn-outline" onClick={() => save("refused")}>Refuser</button>
        <button type="button" className="btn" onClick={() => save("accepted")}>Accepter</button>
      </div>
    </div>
  );
}
