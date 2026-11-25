import { useEffect } from "react";

const SITE = "TalentConnect";
const BASE = "https://talentconnect-bm.vercel.app";

/* Titre et description de la page (moteurs de recherche et partages). Remis à zéro à chaque page. */
export default function Seo({ title, description, image = "/og-image.png" }) {
  useEffect(() => {
    document.title = title ? `${title} · ${SITE}` : `${SITE} : emplois et stages`;
    const set = (sel, attr, value) => {
      let el = document.head.querySelector(sel);
      if (!el) { el = document.createElement("meta"); const [k, v] = attr; el.setAttribute(k, v); document.head.appendChild(el); }
      el.setAttribute("content", value);
    };
    if (description) set('meta[name="description"]', ["name", "description"], description);
    set('meta[property="og:title"]', ["property", "og:title"], title || SITE);
    set('meta[property="og:description"]', ["property", "og:description"], description || "Emplois et stages : score de compatibilité, candidature en un clic.");
    set('meta[property="og:image"]', ["property", "og:image"], `${BASE}${image}`);
    set('meta[name="twitter:card"]', ["name", "twitter:card"], "summary_large_image");
  }, [title, description, image]);
  return null;
}
