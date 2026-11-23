/* Mesure d'audience. Aucun script n'est chargé sans accord (voir CookieBanner) et sans adresse configurée.
   Configuration : VITE_ANALYTICS_SRC = adresse du script fourni par le service choisi (ex. Plausible, Matomo).
   Le choix du service doit être fait avec l'entreprise. */
export function loadAnalytics() {
  let consent = null;
  try { consent = localStorage.getItem("cookieConsent"); } catch { /* ignore */ }
  const src = import.meta.env.VITE_ANALYTICS_SRC;
  if (consent !== "accepted" || !src || document.querySelector(`script[data-analytics]`)) return;
  const s = document.createElement("script");
  s.src = src;
  s.defer = true;
  s.setAttribute("data-analytics", "1");
  s.setAttribute("data-domain", window.location.hostname);
  document.head.appendChild(s);
}
export default function Analytics() {
  loadAnalytics();
  return null;
}
