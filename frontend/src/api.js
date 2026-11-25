import axios from "axios";

export const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/+$/, "");
const isLocal = ["localhost", "127.0.0.1"].includes(window.location.hostname);
// Vrai quand le site est en ligne (Vercel...) mais qu'aucune adresse d'API n'a été configurée
export const apiMisconfigured = !import.meta.env.VITE_API_URL && !isLocal;

// Délai généreux : l'hébergement gratuit peut mettre près d'une minute à redémarrer après une période d'inactivité.
const api = axios.create({ baseURL: API_URL, timeout: 90000 });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use((r) => r, (err) => {
  const d = err?.response?.data?.detail;
  if (err?.response?.status === 403 && typeof d === "string" && d.startsWith("TRIAL_EXPIRED")
      && !window.location.pathname.startsWith("/account")) {
    window.location.href = "/account";
  }
  if (err?.response?.status === 401 && localStorage.getItem("token")) {
    // Jeton périmé, révoqué ou inconnu : on efface la session et on renvoie UNE SEULE FOIS vers la connexion
    // (le drapeau de session évite toute boucle de redirections, notamment sur téléphone).
    const reason = typeof d === "string" && d.startsWith("SESSION_") ? d.slice(8, d.indexOf(":")).toLowerCase() : "expired";
    clearSession();
    if (!sessionStorage.getItem("authRedirect") && !window.location.pathname.startsWith("/login")) {
      sessionStorage.setItem("authRedirect", "1");
      window.location.href = `/login?reason=${reason}`;
    }
  }
  return Promise.reject(err);
});

export const saveSession = ({ access_token, role }) => {
  try { sessionStorage.removeItem("authRedirect"); } catch { /* ignore */ }
  localStorage.setItem("token", access_token);
  localStorage.setItem("role", role);
};
export const clearSession = () => { localStorage.removeItem("token"); localStorage.removeItem("role"); };
export const getRole = () => localStorage.getItem("role");
export const errorMessage = (e) => {
  if (e && !e.response) return "Impossible de joindre le serveur : l'API est hors ligne ou mal configurée.";
  const detail = e?.response?.data?.detail;
  if (Array.isArray(detail)) return "Vérifiez les champs saisis.";
  return (detail?.toString?.() || "Une erreur est survenue").replace(/^[A-Z_]+:\s*/, "");
};

export default api;

// Télécharge un document KYC (le fichier est déchiffré par le serveur, uniquement pour son propriétaire ou l'administrateur)
export async function downloadDocument(id, filename) {
  // Le fichier est demandé avec le jeton (pas de lien public). Sur téléphone, le téléchargement direct
  // d'un blob est souvent bloqué : on ouvre alors le fichier dans un nouvel onglet, où l'utilisateur
  // peut l'enregistrer depuis son navigateur.
  const res = await api.get(`/kyc/documents/${id}/download`, { responseType: "blob" });
  const url = URL.createObjectURL(res.data);
  const mobile = /Android|iPhone|iPad|Mobile/i.test(navigator.userAgent);
  if (mobile) {
    const win = window.open(url, "_blank");
    if (!win) { window.location.href = url; }
  } else {
    const a = document.createElement("a");
    a.href = url;
    a.download = filename || "document";
    document.body.appendChild(a);
    a.click();
    a.remove();
  }
  setTimeout(() => URL.revokeObjectURL(url), 60000);
}

// Déconnexion : ferme aussi la session côté serveur (le jeton devient inutilisable immédiatement)
export async function serverLogout() {
  try { await api.post("/auth/logout"); } catch { /* déjà déconnecté */ }
  clearSession();
}
