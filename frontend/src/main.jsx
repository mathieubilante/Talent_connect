import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { applyMode, getMode } from "./components/ThemeSwitcher.jsx";
import { applyLang, getLang } from "./i18n.js";
import "./styles.css";

applyMode(getMode());   // clair, sombre ou automatique (téléphone / ordinateur)
applyLang(getLang());   // langue et sens d'écriture (RTL pour l'arabe), avant l'affichage

ReactDOM.createRoot(document.getElementById("root")).render(
  <BrowserRouter>
    <App />
  </BrowserRouter>
);

// Application installable : le service worker n'est enregistré que sur le site publié (pas en développement)
if ("serviceWorker" in navigator && import.meta.env.PROD) {
  window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}));
}
