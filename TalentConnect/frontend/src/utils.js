export function toDate(iso) {
  if (!iso) return null;
  return new Date(/(Z|[+-]\d{2}:?\d{2})$/i.test(iso) ? iso : iso + "Z");
}

export function timeAgo(iso) {
  const d = toDate(iso);
  if (!d) return "";
  const s = Math.max(0, (Date.now() - d.getTime()) / 1000);
  if (s < 60) return "à l'instant";
  const m = Math.floor(s / 60);
  if (m < 60) return `il y a ${m} min`;
  const h = Math.floor(m / 60);
  if (h < 24) return `il y a ${h} h`;
  const j = Math.floor(h / 24);
  if (j < 7) return j === 1 ? "hier" : `il y a ${j} jours`;
  if (j < 30) { const w = Math.floor(j / 7); return `il y a ${w} semaine${w > 1 ? "s" : ""}`; }
  return `il y a ${Math.floor(j / 30)} mois`;
}

export const isNew = (iso) => { const d = toDate(iso); return !!d && Date.now() - d.getTime() < 3 * 86400000; };

export const initials = (name = "") =>
  name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0].toUpperCase()).join("") || "?";

export function colorFor(name = "") {
  let h = 0;
  for (const c of name) h = (h * 31 + c.charCodeAt(0)) % 360;
  return `hsl(${h} 55% 42%)`;
}

export const splitSkills = (raw) => (raw || "").split(/[,;]/).map((s) => s.trim()).filter(Boolean);
