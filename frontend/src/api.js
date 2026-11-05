import axios from "axios";

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000" });

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
  return Promise.reject(err);
});

export const saveSession = ({ access_token, role }) => {
  localStorage.setItem("token", access_token);
  localStorage.setItem("role", role);
};
export const clearSession = () => localStorage.clear();
export const getRole = () => localStorage.getItem("role");
export const errorMessage = (e) =>
  (e?.response?.data?.detail?.toString?.() || "Une erreur est survenue").replace(/^[A-Z_]+:\s*/, "");

export default api;
