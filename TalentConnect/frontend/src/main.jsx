import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { applyTheme } from "./components/ThemeSwitcher.jsx";
import "./styles.css";

let saved = "emeraude";
try { saved = localStorage.getItem("theme") || "emeraude"; } catch { /* stockage indisponible */ }
applyTheme(saved);   // appliqué avant l'affichage pour éviter un clignotement de couleurs

ReactDOM.createRoot(document.getElementById("root")).render(
  <BrowserRouter>
    <App />
  </BrowserRouter>
);

// Application installable : le service worker n'est enregistré que sur le site publié (pas en développement)
if ("serviceWorker" in navigator && import.meta.env.PROD) {
  window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}));
}
