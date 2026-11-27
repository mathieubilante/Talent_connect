import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import api, { errorMessage, saveSession } from "../api";
import { t } from "../i18n.js";
import { contactError, passwordError } from "../validate.js";
import Seo from "../components/Seo.jsx";

const HOME_BY_ROLE = { candidate: "/candidate", company: "/company", admin: "/admin" };
const REASON_KEYS = { idle: "msg_session_idle", expired: "msg_session_expired", revoked: "msg_session_other" };

export default function Login() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const next = params.get("next");
  const reasonKey = REASON_KEYS[params.get("reason")];
  const reasonMsg = reasonKey ? t(reasonKey) : "";

  const [mode, setMode] = useState(params.get("mode") === "register" ? "register" : "login");
  const [method, setMethod] = useState("password");
  const [step, setStep] = useState("form");
  const [purpose, setPurpose] = useState("register");
  const [form, setForm] = useState({
    channel: "email", identifier: "", password: "", name: "", website: "",
    role: params.get("role") === "company" ? "company" : "candidate",
  });
  const [otp, setOtp] = useState({ identifier: "", devCode: "", code: "", resendIn: 0 });
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [googleId, setGoogleId] = useState("");
  const googleRef = useRef(null);
  const roleRef = useRef(form.role);
  const isLogin = mode === "login";

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const goAfter = (role) => {
    const safe = next && next.startsWith("/") && !next.startsWith("//");
    navigate(safe ? next : HOME_BY_ROLE[role] || "/offers");
  };

  useEffect(() => { roleRef.current = form.role; }, [form.role]);

  useEffect(() => {
    api.get("/auth/config").then((r) => setGoogleId(r.data.google_client_id || "")).catch(() => {});
  }, []);

  useEffect(() => {
    if (otp.resendIn <= 0) return;
    const timer = setTimeout(() => setOtp((o) => ({ ...o, resendIn: o.resendIn - 1 })), 1000);
    return () => clearTimeout(timer);
  }, [otp.resendIn]);

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
    if (window.google?.accounts?.id) {
      init();
    } else {
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
    setError("");
    setInfo("");
    if (mode === "register") {
      const bad = contactError(form.channel, form.identifier) || passwordError(form.password);
      if (bad) { setError(bad); return; }
    }
    try {
      if (mode === "login" && method === "password") {
        const res = await api.post("/auth/login", new URLSearchParams({ username: form.identifier, password: form.password }));
        saveSession(res.data);
        goAfter(res.data.role);
      } else if (mode === "login") {
        const { data } = await api.post("/auth/otp/request", { identifier: form.identifier });
        goOtp(form.identifier, data.dev_code, data.resend_after_seconds, "login");
        setInfo(t("msg_code_sent"));
      } else {
        const payload = {
          channel: form.channel, password: form.password, role: form.role, name: form.name,
          website: form.website || "",
          email: form.channel === "email" ? form.identifier : null,
          phone: null,
        };
        const { data } = await api.post("/auth/register", payload);
        goOtp(form.identifier, data.dev_code, data.resend_after_seconds, "register");
        setInfo(`${t("msg_code_sent")} ${data.destination_masked}`);
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      if (typeof detail === "string" && detail.startsWith("NOT_VERIFIED")) {
        goOtp(form.identifier, "", 0, "register");
        setInfo(t("msg_not_verified"));
      } else {
        setError(errorMessage(err));
      }
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
    setError("");
    setInfo("");
    try {
      const url = purpose === "login" ? "/auth/otp/request" : "/auth/resend-otp";
      const { data } = await api.post(url, { identifier: otp.identifier });
      setOtp((o) => ({ ...o, devCode: data.dev_code || "", code: "", resendIn: data.resend_after_seconds }));
      setInfo(t("msg_new_code"));
    } catch (err) { setError(errorMessage(err)); }
  };

  if (step === "otp") {
    return (
      <div className="auth">
        <Seo title={t("enter_code")} description="Saisissez le code de vérification reçu." />
        <div className="auth-side"><h2>{t("welcome")}</h2></div>
        <form className="card auth-form" onSubmit={verify}>
          <h2>{t("enter_code")}</h2>
          {info && <p className="info">{info}</p>}
          {otp.devCode && <p className="devcode">{t("demo_code_is")} <b>{otp.devCode}</b></p>}
          <input className="otp-input" inputMode="numeric" maxLength={6} autoFocus placeholder="000000"
                 value={otp.code} onChange={(e) => { const v = e.target.value.replace(/\D/g, ""); setOtp((o) => ({ ...o, code: v })); }} required />
          {error && <p className="error">{error}</p>}
          <button className="btn full" type="submit" disabled={otp.code.length !== 6}>{t("verify")}</button>
          <button type="button" className="link" onClick={resend} disabled={otp.resendIn > 0}>
            {otp.resendIn > 0 ? `${t("resend_code")} (${otp.resendIn} s)` : t("resend_code")}
          </button>
          <button type="button" className="link" onClick={() => { setStep("form"); setError(""); setInfo(""); }}>{t("back")}</button>
        </form>
      </div>
    );
  }

  return (
    <div className="auth">
      <Seo title={isLogin ? t("login_title") : t("register_title")} description="Connectez-vous ou créez votre compte TalentConnect." />
      <div className="auth-side">
        <h2>{t("welcome")}</h2>
        <ul>
          <li>{t("point_login")}</li>
          <li>{t("point_code")}</li>
          <li>{t("point_score")}</li>
          <li>{t("point_ai")}</li>
        </ul>
      </div>
      <form className="card auth-form" onSubmit={submit}>
        <div className="auth-tabs" role="tablist">
          <button type="button" role="tab" aria-selected={isLogin} className={isLogin ? "on" : ""}
                  onClick={() => { setMode("login"); setError(""); setInfo(""); }}>{t("login_tab")}</button>
          <button type="button" role="tab" aria-selected={!isLogin} className={!isLogin ? "on" : ""}
                  onClick={() => { setMode("register"); setError(""); setInfo(""); }}>{t("register_tab")}</button>
        </div>
        <h2 className="auth-title">{isLogin ? t("login_title") : t("register_title")}</h2>
        {reasonMsg && <p className="info">{reasonMsg}</p>}
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
            <label>
              {t("candidate_student")} / {t("company_recruiter")}
              <select value={form.role} onChange={set("role")}>
                <option value="candidate">{t("candidate_student")}</option>
                <option value="company">{t("company_recruiter")}</option>
              </select>
            </label>
            <label>
              {form.role === "company" ? t("company_name_label") : t("full_name")}
              <input value={form.name} onChange={set("name")} required />
            </label>
          </>
        )}
        <label>
          {t("email_addr")}
          <input type="email"
                 value={form.identifier} onChange={set("identifier")} required />
        </label>
        <input type="text" name="website" className="hp-field" tabIndex={-1} autoComplete="off" aria-hidden="true"
               value={form.website} onChange={set("website")} />
        {(!isLogin || method === "password") && (
          <label>
            {t("password_label")} {!isLogin && t("min8")}
            <input type="password" minLength={!isLogin ? 8 : undefined} value={form.password}
                   onChange={set("password")} required />
          </label>
        )}
        {isLogin && method === "password" && (
          <p className="forgot">
            <Link to="/mot-de-passe-oublie" className="link small-link">{t("forgot")}</Link>
          </p>
        )}
        {error && <p className="error">{error}</p>}
        <button className="btn full" type="submit">
          {!isLogin ? t("send_my_code") : method === "code" ? t("send_code") : t("login_btn")}
        </button>
      </form>
    </div>
  );
}
