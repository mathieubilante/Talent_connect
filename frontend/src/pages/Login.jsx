import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import api, { errorMessage, saveSession } from "../api";

const HOME_BY_ROLE = { candidate: "/candidate", company: "/company", admin: "/admin" };

export default function Login() {
  const [params] = useSearchParams();
  const [mode, setMode] = useState(params.get("mode") === "register" ? "register" : "login");
  const [step, setStep] = useState("form");            // form | otp
  const [form, setForm] = useState({ channel: "email", identifier: "", password: "", role: params.get("role") === "company" ? "company" : "candidate", name: "" });
  const [otp, setOtp] = useState({ identifier: "", masked: "", devCode: "", code: "", resendIn: 0 });
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const navigate = useNavigate();
  const next = params.get("next");
  const goAfter = (role) => navigate(next && next.startsWith("/") && !next.startsWith("//") ? next : HOME_BY_ROLE[role] || "/offers");
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  // compte à rebours avant de pouvoir redemander un code
  useEffect(() => {
    if (otp.resendIn <= 0) return;
    const t = setTimeout(() => setOtp((o) => ({ ...o, resendIn: o.resendIn - 1 })), 1000);
    return () => clearTimeout(t);
  }, [otp.resendIn]);

  const goOtp = (identifier, masked, devCode, resendIn) => {
    setOtp({ identifier, masked, devCode: devCode || "", code: "", resendIn });
    setStep("otp");
  };

  const submit = async (e) => {
    e.preventDefault();
    setError(""); setInfo("");
    try {
      if (mode === "login") {
        const res = await api.post("/auth/login", new URLSearchParams({ username: form.identifier, password: form.password }));
        saveSession(res.data);
        goAfter(res.data.role);
      } else {
        const payload = {
          channel: form.channel, password: form.password, role: form.role, name: form.name,
          email: form.channel === "email" ? form.identifier : null,
          phone: form.channel === "phone" ? form.identifier : null,
        };
        const { data } = await api.post("/auth/register", payload);
        goOtp(form.identifier, data.destination_masked, data.dev_code, data.resend_after_seconds);
        setInfo(`Un code à 6 chiffres a été envoyé à ${data.destination_masked}.`);
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      if (typeof detail === "string" && detail.startsWith("NOT_VERIFIED")) {
        goOtp(form.identifier, "", "", 0);
        setInfo("Votre compte n'est pas encore vérifié. Demandez un code pour terminer l'inscription.");
      } else {
        setError(Array.isArray(detail) ? "Vérifiez les champs saisis." : errorMessage(err));
      }
    }
  };

  const verify = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const res = await api.post("/auth/verify-otp", { identifier: otp.identifier, code: otp.code });
      saveSession(res.data);
      goAfter(res.data.role);
    } catch (err) { setError(errorMessage(err)); }
  };

  const resend = async () => {
    setError(""); setInfo("");
    try {
      const { data } = await api.post("/auth/resend-otp", { identifier: otp.identifier });
      setOtp((o) => ({ ...o, devCode: data.dev_code || "", code: "", resendIn: data.resend_after_seconds }));
      setInfo("Un nouveau code vient d'être envoyé.");
    } catch (err) { setError(errorMessage(err)); }
  };

  const side = (
    <div className="auth-side">
      <h2>Bienvenue sur TalentConnect</h2>
      <ul>
        <li>🎯 Score de compatibilité sur chaque offre</li>
        <li>📄 Compétences détectées dans votre CV</li>
        <li>🤖 Assistant et lettre de motivation automatique</li>
        <li>🔐 Inscription sécurisée par code de vérification</li>
      </ul>
    </div>
  );

  if (step === "otp") {
    return (
      <div className="auth">
        {side}
        <form className="card auth-form" onSubmit={verify}>
          <h2>Vérification</h2>
          {info && <p className="info">{info}</p>}
          {otp.devCode && (
            <p className="devcode">Mode démonstration : votre code est <b>{otp.devCode}</b></p>
          )}
          <label>Code à 6 chiffres
            <input className="otp-input" inputMode="numeric" maxLength={6} autoFocus value={otp.code}
                   onChange={(e) => setOtp({ ...otp, code: e.target.value.replace(/\D/g, "") })} required />
          </label>
          {error && <p className="error">{error}</p>}
          <button className="btn full" type="submit" disabled={otp.code.length !== 6}>Vérifier</button>
          <button type="button" className="link" onClick={resend} disabled={otp.resendIn > 0}>
            {otp.resendIn > 0 ? `Renvoyer le code (${otp.resendIn} s)` : "Renvoyer le code"}
          </button>
          <button type="button" className="link" onClick={() => { setStep("form"); setError(""); setInfo(""); }}>← Retour</button>
        </form>
      </div>
    );
  }

  return (
    <div className="auth">
      {side}
      <form className="card auth-form" onSubmit={submit}>
        <h2>{mode === "login" ? "Connexion" : "Créer un compte"}</h2>
        {mode === "register" && (
          <>
            <label>Je suis
              <select value={form.role} onChange={set("role")}>
                <option value="candidate">Candidat / étudiant</option>
                <option value="company">Entreprise / recruteur</option>
              </select>
            </label>
            <label>{form.role === "company" ? "Nom de l'entreprise" : "Nom complet"}
              <input value={form.name} onChange={set("name")} required />
            </label>
            <div className="tabs small-tabs">
              <button type="button" className={form.channel === "email" ? "on" : ""}
                      onClick={() => setForm({ ...form, channel: "email", identifier: "" })}>✉️ E-mail</button>
              <button type="button" className={form.channel === "phone" ? "on" : ""}
                      onClick={() => setForm({ ...form, channel: "phone", identifier: "" })}>📱 Téléphone</button>
            </div>
          </>
        )}
        <label>
          {mode === "login" ? "E-mail ou numéro de téléphone"
            : form.channel === "email" ? "Adresse e-mail" : "Numéro de téléphone (ex. 90 12 34 56)"}
          <input type={mode === "register" && form.channel === "email" ? "email" : "text"}
                 value={form.identifier} onChange={set("identifier")} required />
        </label>
        <label>Mot de passe {mode === "register" && "(8 caractères min.)"}
          <input type="password" minLength={mode === "register" ? 8 : undefined} value={form.password}
                 onChange={set("password")} required />
        </label>
        {error && <p className="error">{error}</p>}
        <button className="btn full" type="submit">{mode === "login" ? "Se connecter" : "Recevoir mon code"}</button>
        <button type="button" className="link" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}>
          {mode === "login" ? "Pas encore de compte ? S'inscrire" : "Déjà inscrit ? Se connecter"}
        </button>
      </form>
    </div>
  );
}
