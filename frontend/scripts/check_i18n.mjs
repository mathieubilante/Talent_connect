// Contrôle des traductions :
// 1) chaque clé du français existe en anglais et en arabe (et inversement) ;
// 2) chaque clé utilisée dans le code (t("...")) existe dans le dictionnaire ;
// 3) aucune valeur vide.
// Usage : node scripts/check_i18n.mjs   (code de sortie 1 si un problème est trouvé)
import fs from "node:fs";
import path from "node:path";
import { DICT } from "../src/i18n.js";

const fr = new Set(Object.keys(DICT.fr));
let problems = 0;
for (const lang of ["en", "ar"]) {
  const keys = new Set(Object.keys(DICT[lang]));
  for (const k of fr) if (!keys.has(k)) { console.log(`${lang} : clé manquante -> ${k}`); problems++; }
  for (const k of keys) if (!fr.has(k)) { console.log(`${lang} : clé en trop -> ${k}`); problems++; }
  for (const k of fr) if (DICT[lang][k] === "") { console.log(`${lang} : valeur vide -> ${k}`); problems++; }
}
function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) walk(full, out);
    else if (/\.(jsx?|mjs)$/.test(e.name)) out.push(full);
  }
  return out;
}
const used = new Set();
for (const file of walk(path.resolve("src"))) {
  const src = fs.readFileSync(file, "utf8");
  for (const m of src.matchAll(/\bt\(\s*"([a-z0-9_]+)"\s*\)/g)) used.add(m[1]);
}
for (const k of used) if (!fr.has(k)) { console.log(`clé utilisée dans le code mais absente du dictionnaire -> ${k}`); problems++; }
console.log(problems === 0
  ? `Traductions cohérentes : ${fr.size} clés, ${used.size} usages vérifiés dans le code, 3 langues.`
  : `${problems} problème(s) à corriger.`);
process.exit(problems === 0 ? 0 : 1);
