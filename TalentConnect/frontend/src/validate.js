/* Validation des formulaires (côté navigateur). La vérification réelle est toujours refaite par le serveur. */
export const isEmail = (s = "") => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(s.trim());
export const isPhone = (s = "") => {
  const digits = s.replace(/[\s\-.()]/g, "");
  return /^\+?\d{8,15}$/.test(digits);
};
export function passwordError(s = "") {
  if (s.length < 8) return "Le mot de passe doit contenir au moins 8 caractères.";
  if (!/[A-Za-zÀ-ÿ]/.test(s) || !/\d/.test(s)) return "Ajoutez au moins une lettre et un chiffre.";
  return "";
}
export function contactError(channel, value) {
  if (channel === "email") return isEmail(value) ? "" : "Adresse e-mail invalide.";
  return isPhone(value) ? "" : "Numéro de téléphone invalide (ex. 90 12 34 56).";
}
