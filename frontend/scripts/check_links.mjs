// Contrôle des liens internes : chaque lien interne du code doit correspondre à une route déclarée.
// Usage : node scripts/check_links.mjs   (code de sortie 1 si un lien est cassé)
import fs from "node:fs";
import path from "node:path";
function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const f = path.join(dir, e.name);
    if (e.isDirectory()) walk(f, out); else if (/\.jsx?$/.test(e.name)) out.push(f);
  }
  return out;
}
const files = walk(path.resolve("src"));
const app = fs.readFileSync(path.resolve("src/App.jsx"), "utf8");
const routes = [...app.matchAll(/path="([^"]+)"/g)].map((m) => m[1]).filter((p) => p !== "*");
const matches = (target) => routes.some((r) => {
  const re = new RegExp("^" + r.replace(/:[a-zA-Z]+/g, "[^/]+") + "$");
  return re.test(target);
});
let broken = 0, checked = 0;
for (const f of files) {
  const src = fs.readFileSync(f, "utf8");
  for (const m of src.matchAll(/(?:to|href)=\{?"(\/[^"]*)"/g)) {
    const target = m[1].split("?")[0].split("#")[0];
    if (!target || target.startsWith("//")) continue;
    checked++;
    if (!matches(target)) { console.log(`lien cassé : ${target}  (dans ${path.relative(process.cwd(), f)})`); broken++; }
  }
}
console.log(broken === 0 ? `Liens internes : ${checked} vérifiés, aucun lien cassé.` : `${broken} lien(s) cassé(s).`);
process.exit(broken === 0 ? 0 : 1);
