import { useState } from "react";
import { t } from "../i18n.js";

/* Un seul bouton : Auto (thème du téléphone ou de l'ordinateur) → Clair → Sombre → Auto. */
const MODES = ["auto", "light", "dark"];
const ICON = { auto: "📱", light: "☀️", dark: "🌙" };
const LABEL_KEY = { auto: "theme_auto", light: "theme_light", dark: "theme_dark" };

export function getMode() {
  try { const m = localStorage.getItem("themeMode"); if (MODES.includes(m)) return m; } catch { /* ignore */ }
  return "auto";
}

export function applyMode(mode) {
  const valid = MODES.includes(mode) ? mode : "auto";
  const root = document.documentElement;
  root.dataset.theme = "emeraude";                       // couleur unique de la plateforme
  if (valid === "auto") delete root.dataset.mode; else root.dataset.mode = valid;
  const dark = valid === "dark" || (valid === "auto" && window.matchMedia?.("(prefers-color-scheme: dark)").matches);
  document.querySelector('meta[name="theme-color"]')?.setAttribute("content", dark ? "#0b1f1d" : "#0f766e");
  try { localStorage.setItem("themeMode", valid); } catch { /* ignore */ }
  return valid;
}

export default function ThemeToggle() {
  const [mode, setMode] = useState(getMode());
  const next = () => {
    const i = MODES.indexOf(mode);
    const chosen = MODES[(i + 1) % MODES.length];
    setMode(applyMode(chosen));
  };
  return (
    <button type="button" className="theme-btn" onClick={next} title={t(LABEL_KEY[mode])} aria-label={t(LABEL_KEY[mode])}>
      {ICON[mode]} <span className="theme-label">{t(LABEL_KEY[mode])}</span>
    </button>
  );
}
