// Tests des règles de validation (exécutables sans navigateur).
import { isEmail, isPhone, passwordError, contactError } from "../src/validate.js";
const checks = [
  [isEmail("kofi@mail.tg") === true, "e-mail valide"],
  [isEmail("kofi@mail") === false, "e-mail sans domaine complet refusé"],
  [isEmail("kofi mensah@mail.tg") === false, "espace dans l'e-mail refusé"],
  [isPhone("90 12 34 56") === true, "téléphone local valide"],
  [isPhone("+228 90-12-34-56") === true, "téléphone international valide"],
  [isPhone("12") === false, "téléphone trop court refusé"],
  [passwordError("motdepasse1") === "", "mot de passe valide"],
  [passwordError("abc") !== "", "mot de passe court refusé"],
  [passwordError("motdepasse") !== "", "mot de passe sans chiffre refusé"],
  [contactError("email", "x") !== "", "contact e-mail invalide signalé"],
];
let fail = 0;
for (const [ok, label] of checks) { if (!ok) { console.log("ÉCHEC :", label); fail++; } }
console.log(fail === 0 ? `Validation : ${checks.length} règles vérifiées, toutes conformes.` : `${fail} échec(s).`);
process.exit(fail === 0 ? 0 : 1);
