import { useEffect, useState } from "react";

export const THEMES = [
  ["emeraude", "Émeraude", "#0f766e"],
  ["ocean", "Océan", "#1d4f91"],
  ["violet", "Violet", "#5b21b6"],
  ["rose", "Rose", "#be123c"],
];

export function applyTheme(name) {
  const valid = THEMES.some(([k]) => k === name) ? name : "emeraude";
  document.documentElement.dataset.theme = valid;
  const color = (THEMES.find(([k]) => k === valid) || THEMES[0])[2];
  document.querySelector('meta[name="theme-color"]')?.setAttribute("content", color);
  try { localStorage.setItem("theme", valid); } catch { /* stockage indisponible */ }
  return valid;
}

export default function ThemeSwitcher() {
  const [open, setOpen] = useState(false);
  const [theme, setTheme] = useState(document.documentElement.dataset.theme || "emeraude");
  useEffect(() => { setTheme(document.documentElement.dataset.theme || "emeraude"); }, []);

  const choose = (name) => { setTheme(applyTheme(name)); setOpen(false); };
  return (
    <div className="usermenu">
      <button className="theme-btn" onClick={() => setOpen(!open)} title="Changer les couleurs" aria-label="Changer les couleurs">🎨</button>
      {open && (
        <>
          <div className="menu-back" onClick={() => setOpen(false)} />
          <div className="dropdown themes">
            <span className="muted small" style={{ padding: "4px 12px" }}>Couleurs du site</span>
            {THEMES.map(([key, label, color]) => (
              <button key={key} className={theme === key ? "on" : ""} onClick={() => choose(key)}>
                <i className="swatch" style={{ background: color }} /> {label}{theme === key ? " ✓" : ""}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
