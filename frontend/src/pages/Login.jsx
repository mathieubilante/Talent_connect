import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import api, { errorMessage, saveSession } from "../api";

const HOME_BY_ROLE = { candidate: "/candidate", company: "/company", admin: "/admin" };

export default function Login() {
  const [params] = useSearchParams();
  const [mode, setMode] = useState(params.get("mode") === "register" ? "register" : "login");
  const [method, setMethod] = useState("password");       // connexion : "password" ou "code" (sans mot de passe)
  const [step, setStep] = useState("form");               // form | otp
  const [purpose, setPurpose] = useState("register");     // à quoi sert le code saisi : register | login
  const [form, setForm] = useState({
    channel: "email", identifier: "", password: "", name: "",
    role: params.get("role") === "company" ? "company" : "candidate",
  });
  const [otp, setOtp] = useState({ identifier: "", devCode: "", code: "", resendIn: 0 });
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [googleId, setGoogleId] = useState("");
  const googleRef = useRef(null);
  const roleRef = useRef(form.role);
  const navigate = useNavigate();
  const next = params.get("next");
  const REASONS = {
    idle: "Vous avez été déconnecté après une période d'inactivité.",
    expired: "Votre session a expiré. Reconnectez-vous.",
    revoked: "Vous avez été déconnecté : une nouvelle connexion a été ouverte sur un autre appareil.",
  };
  const reasonMsg = REASONS[params.get("reason")] || "";
  const goAfter = (role) => navigate(next && next.startsWith("/") && !next.startsWith("//") ? next : HOME_BY_ROLE[role] || "/offers");
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  useEffect(() => { roleRef.current = form.role; }, [form.role]);
  useEffect(() => { api.get("/auth/config").then((r) => setGoogleId(r.data.google_client_id || "")).catch(() => {}); }, []);

  // compte à rebours avant de pouvoir redemander un code
  useEffect(() => {
    if (otp.resendIn <= 0) return;
    const t = setTimeout(() => setOtp((o) => ({ ...o, resendIn: o.resendIn - 1 })), 1000);
    return () => clearTimeout(t);
  }, [otp.resendIn]);

  // bouton « Continuer avec Google » (affiché seulement si un identifiant Google est configuré sur le serveur)
  useEffect(() => {
    if (!googleId || step !== "form") return;
    const onGoogle = async (resp) => {
      setError("");
      try {
        const res = await api.post("/auth/google", { credential: resp.credential, role: roleRef.current });
        saveSession(res.data);
        goAfter(res.data.role);
      } catch (e) { setError(errorMessage(e)); }
    };
    const init = () => {
      if (!googleRef.current || !window.google?.accounts?.id) return;
      window.google.accounts.id.initialize({ client_id: googleId, callback: onGoogle });
      googleRef.current.innerHTML = "";
      window.google.accounts.id.renderButton(googleRef.current, { theme: "outline", size: "large", width: 320, text: "continue_with", locale: "fr" });
    };
    if (window.google?.accounts?.id) init();
    else {
      const s = document.createElement("script");
      s.src = "https://accounts.google.com/gsi/client";
      s.async = true;
      s.onload = init;
      document.head.appendChild(s);
    }
  }, [googleId, step, mode, method]);

  const goOtp = (identifier, devCode, resendIn, why) => {
    setOtp({ identifier, devCode: devCode || "", code: "", resendIn: resendIn || 0 });
    setPurpose(why);
    setStep("otp");
  };

  const submit = async (e) => {
    e.preventDefault();
    setError(""); setInfo("");
    try {
      if (mode === "login" && method === "password") {
        const res = await api.post("/auth/login", new URLSearchParams({ username: form.identifier, password: form.password }));
        saveSession(res.data);
        goAfter(res.data.role);
      } else if (mode === "login") {            // connexion par code, sans mot de passe
        const { data } = await api.post("/auth/otp/request", { identifier: form.identifier });
        goOtp(form.identifier, data.dev_code, data.resend_after_seconds, "login");
        setInfo("Si un compte existe pour cet identifiant, un code à 6 chiffres vient d'être envoyé.");
      } else {                                   // inscription
        const payload = {
          channel: form.channel, password: form.password, role: form.role, name: form.name,
          email: form.channel === "email" ? form.identifier : null,
          phone: form.channel === "phone" ? form.identifier : null,
        };
        const { data } = await api.post("/auth/register", payload);
        goOtp(form.identifier, data.dev_code, data.resend_after_seconds, "register");
        setInfo(`Un code à 6 chiffres a été envoyé à ${data.destination_masked}.`);
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      if (typeof detail === "string" && detail.startsWith("NOT_VERIFIED")) {
        goOtp(form.identifier, "", 0, "register");
        setInfo("Votre compte n'est pas encore vérifié. Demandez un code pour terminer l'inscription.");
      } else setError(errorMessage(err));
    }
  };

  const verify = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const url = purpose === "login" ? "/auth/otp/login" : "/auth/verify-otp";
      const res = await api.post(url, { identifier: otp.identifier, code: otp.code });
      saveSession(res.data);
      goAfter(res.data.role);
    } catch (err) { setError(errorMessage(err)); }
  };

  const resend = async () => {
    setError(""); setInfo("");
    try {
      const url = purpose === "login" ? "/auth/otp/request" : "/auth/resend-otp";
      const { data } = await api.post(url, { identifier: otp.identifier });
      setOtp((o) => ({ ...o, devCode: data.dev_code || "", code: "", resendIn: data.resend_after_seconds }));
      setInfo("Un nouveau code vient d'être envoyé.");
    } catch (err) { setError(errorMessage(err)); }
  };

  const side = (
    <div className="auth-side">
      <h2>Bienvenue</h2>
      <ul>
        <li>🔐 Connexion par e-mail, téléphone ou Google</li>
        <li>🔢 Code de vérification à usage unique</li>
        <li>🎯 Score de compatibilité sur chaque offre</li>
        <li>🤖 TConnect IA : lettre de motivation et conseils</li>
      </ul>
    </div>
  );

  if (step === "otp") {
    return (
      <div className="auth">
        {side}
        <form className="card auth-form" onSubmit={verify}>
          <h2>Saisir le code</h2>
          {info && <p className="info">{info}</p>}
          {otp.devCode && <p className="devcode">Mode démonstration : votre code est <b>{otp.devCode}</b></p>}
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

  const isLogin = mode === "login";
  return (
    <div className="auth">
      {side}
      <form className="card auth-form" onSubmit={submit}>
        <h2>{isLogin ? "Connexion" : "Créer un compte"}</h2>
        {reasonMsg && <p className="info">{reasonMsg}</p>}
        {!isLogin && (
          <label>Je suis
            <select value={form.role} onChange={set("role")}>
              <option value="candidate">Candidat / étudiant</option>
              <option value="company">Entreprise / recruteur</option>
            </select>
          </label>
        )}
        {googleId && (
          <>
            <div ref={googleRef} className="google-btn" />
            <div className="or"><span>ou</span></div>
          </>
        )}
        {isLogin && (
          <div className="tabs small-tabs">
            <button type="button" className={method === "password" ? "on" : ""} onClick={() => setMethod("password")}>🔑 Mot de passe</button>
            <button type="button" className={method === "code" ? "on" : ""} onClick={() => setMethod("code")}>🔢 Code reçu</button>
          </div>
        )}
        {!isLogin && (
          <>
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
          {isLogin ? "E-mail ou numéro de téléphone"
            : form.channel === "email" ? "Adresse e-mail" : "Numéro de téléphone (ex. 90 12 34 56)"}
          <input type={!isLogin && form.channel === "email" ? "email" : "text"}
                 value={form.identifier} onChange={set("identifier")} required />
        </label>
        {(!isLogin || method === "password") && (
          <label>Mot de passe {!isLogin && "(8 caractères min.)"}
            <input type="password" minLength={!isLogin ? 8 : undefined} value={form.password}
                   onChange={set("password")} required />
          </label>
        )}
        {error && <p className="error">{error}</p>}
        <button className="btn full" type="submit">
          {!isLogin ? "Recevoir mon code" : method === "code" ? "Recevoir un code" : "Se connecter"}
        </button>
        <button type="button" className="link" onClick={() => { setMode(isLogin ? "register" : "login"); setError(""); }}>
          {isLogin ? "Pas encore de compte ? S'inscrire" : "Déjà inscrit ? Se connecter"}
        </button>
      </form>
    </div>
  );
}
