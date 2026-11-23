import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import api, { errorMessage, saveSession } from "../api";
import { t } from "../i18n.js";
import { contactError, passwordError } from "../validate.js";
import Seo from "../components/Seo.jsx";

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
    idle: t("msg_session_idle"),
    expired: t("msg_session_expired"),
    revoked: t("msg_session_other"),
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
    if (mode === "register") {
      const bad = contactError(form.channel, form.identifier) || passwordError(form.password);
      if (bad) { setError(bad); return; }
    }
    try {
      if (mode === "login" && method === "password") {
        const res = await api.post("/auth/login", new URLSearchParams({ username: form.identifier, password: form.password }));
        saveSession(res.data);
        goAfter(res.data.role);
      } else if (mode === "login") {            // connexion par code, sans mot de passe
        const { data } = await api.post("/auth/otp/request", { identifier: form.identifier });
        goOtp(form.identifier, data.dev_code, data.resend_after_seconds, "login");
        setInfo(t("msg_code_sent"));
      } else {                                   // inscription
        const payload = {
          channel: form.channel, password: form.password, role: form.role, name: form.name, website: form.website || "",
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
        setInfo(t("msg_not_verified"));
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
      setInfo(t("msg_new_code"));
    } catch (err) { setError(errorMessage(err)); }
  };

  const side = (
    <div className="auth-side">
      <h2>{t("welcome")}</h2>
      <ul>
        <li>{t("point_login")}</li>
        <li>{t("point_code")}</li>
        <li>{t("point_score")}</li>
        <li>{t("point_ai")}</li>
      </ul>
    </div>
  );

  if (step === "otp") {
    return (
      <div className="auth">
        {side}
        <form className="card auth-form" onSubmit={verify}>
          <h2>{t("enter_code")}</h2>
          {info && <p className="info">{info}</p>}
          {otp.devCode && <p className="devcode">Mode démonstration : votre code est <b>{otp.devCode}</b></p>}
          <label>Code à 6 chiffres
            <input className="otp-input" inputMode="numeric" maxLength={6} autoFocus value={otp.code}
                   onChange={(e) => setOtp({ ...otp, code: e.target.value.replace(/\D/g, "") })} required />
          </label>
          {error && <p className="error">{error}</p>}
          <button className="btn full" type="submit" disabled={otp.code.length !== 6}>{t("verify")}</button>
          <button type="button" className="link" onClick={resend} disabled={otp.resendIn > 0}>
            {otp.resendIn > 0 ? `Renvoyer le code (${otp.resendIn} s)` : t("resend_code")}
          </button>
          <button type="button" className="link" onClick={() => { setStep("form"); setError(""); setInfo(""); }}>{t("back")}</button>
        </form>
      </div>
    );
  }

  const isLogin = mode === "login";
  return (
    <div className="auth">
      {side}
      <Seo title="Connexion et inscription" description="Connectez-vous ou créez votre compte TalentConnect." />
      <form className="card auth-form" onSubmit={submit}>
        <div className="auth-tabs" role="tablist">
          <button type="button" role="tab" aria-selected={isLogin} className={isLogin ? "on" : ""}
                  onClick={() => { setMode("login"); setError(""); setInfo(""); }}>{t("login_tab")}</button>
          <button type="button" role="tab" aria-selected={!isLogin} className={!isLogin ? "on" : ""}
                  onClick={() => { setMode("register"); setError(""); setInfo(""); }}>{t("register_tab")}</button>
        </div>
        <h2 className="auth-title">{isLogin ? t("login_title") : t("register_title")}</h2>
        {reasonMsg && <p className="info">{reasonMsg}</p>}
        {!isLogin && (
          <label>Je suis
            <select value={form.role} onChange={set("role")}>
              <option value="candidate">{t("candidate_student")}</option>
              <option value="company">{t("company_recruiter")}</option>
            </select>
          </label>
        )}
        {googleId && (
          <>
            <div ref={googleRef} className="google-btn" />
            <div className="or"><span>{t("or")}</span></div>
          </>
        )}
        {isLogin && (
          <div className="tabs small-tabs">
            <button type="button" className={method === "password" ? "on" : ""} onClick={() => setMethod("password")}>{t("by_password")}</button>
            <button type="button" className={method === "code" ? "on" : ""} onClick={() => setMethod("code")}>{t("by_code")}</button>
          </div>
        )}
        {!isLogin && (
          <>
            <label>{form.role === "company" ? t("company_name_label") : t("full_name")}
              <input value={form.name} onChange={set("name")} required />
            </label>
            <div className="tabs small-tabs">
              <button type="button" className={form.channel === "email" ? "on" : ""}
                      onClick={() => setForm({ ...form, channel: "email", identifier: "" })}>{t("email_tab")}</button>
              <button type="button" className={form.channel === "phone" ? "on" : ""}
                      onClick={() => setForm({ ...form, channel: "phone", identifier: "" })}>{t("phone_tab")}</button>
            </div>
          </>
        )}
        <label>
          {isLogin ? "E-mail ou numéro de téléphone"
            : form.channel === "email" ? t("email_addr") : t("phone_example")}
          <input type={!isLogin && form.channel === "email" ? "email" : "text"}
                 value={form.identifier} onChange={set("identifier")} required />
        </label>
        {(!isLogin || method === "password") && (
          <input type="text" name="website" className="hp-field" tabIndex={-1} autoComplete="off" aria-hidden="true" value={form.website || ""} onChange={set("website")} />
        <label>{t("password_label")} {!isLogin && t("min8")}
            <input type="password" minLength={!isLogin ? 8 : undefined} value={form.password}
                   onChange={set("password")} required />
          </label>
        )}
        {isLogin && method === "password" && (
          <p style={{ textAlign: "right", margin: "-6px 0 10px" }}><Link to="/mot-de-passe-oublie" className="link small-link">{t("forgot")}</Link></p>
        )}
        {error && <p className="error">{error}</p>}
        <button className="btn full" type="submit">
          {!isLogin ? t("send_my_code") : method === "code" ? t("send_code") : t("login_btn")}
        </button>

      </form>
    </div>
  );
}
