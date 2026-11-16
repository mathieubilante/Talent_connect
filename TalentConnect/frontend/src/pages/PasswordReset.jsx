import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api, { errorMessage } from "../api";

export default function PasswordReset() {
  const navigate = useNavigate();
  const [step, setStep] = useState("ask");          // ask | reset | done
  const [identifier, setIdentifier] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [devCode, setDevCode] = useState("");
  const [info, setInfo] = useState("");
  const [error, setError] = useState("");

  const ask = async (e) => {
    e.preventDefault(); setError("");
    try {
      const { data } = await api.post("/auth/password/request", { identifier });
      setDevCode(data.dev_code || "");
      setInfo(data.message);
      setStep("reset");
    } catch (err) { setError(errorMessage(err)); }
  };

  const reset = async (e) => {
    e.preventDefault(); setError("");
    try {
      const { data } = await api.post("/auth/password/reset", { identifier, code, new_password: password });
      setInfo(data.message);
      setStep("done");
    } catch (err) { setError(errorMessage(err)); }
  };

  return (
    <div className="auth" style={{ gridTemplateColumns: "1fr" }}>
      <div className="card auth-form" style={{ margin: "0 auto", maxWidth: 440, width: "100%" }}>
        <h2>Mot de passe oublié</h2>
        {step === "ask" && (
          <form onSubmit={ask}>
            <p className="muted">Indiquez votre e-mail ou votre téléphone. Nous vous enverrons un code à 6 chiffres.</p>
            <label>E-mail ou téléphone<input value={identifier} onChange={(e) => setIdentifier(e.target.value)} required /></label>
            {error && <p className="error">{error}</p>}
            <button className="btn full" type="submit">Recevoir le code</button>
          </form>
        )}
        {step === "reset" && (
          <form onSubmit={reset}>
            {info && <p className="info">{info}</p>}
            {devCode && <p className="devcode">Mode démonstration : votre code est <b>{devCode}</b></p>}
            <label>Code à 6 chiffres
              <input className="otp-input" inputMode="numeric" maxLength={6} value={code}
                     onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} required />
            </label>
            <label>Nouveau mot de passe (8 caractères min.)
              <input type="password" minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} required />
            </label>
            {error && <p className="error">{error}</p>}
            <p className="muted small">Toutes vos sessions ouvertes seront fermées après le changement.</p>
            <button className="btn full" type="submit" disabled={code.length !== 6}>Changer le mot de passe</button>
          </form>
        )}
        {step === "done" && (
          <>
            <p className="info">{info}</p>
            <button className="btn full" onClick={() => navigate("/login")}>Aller à la connexion</button>
          </>
        )}
        <p style={{ marginTop: 14 }}><Link to="/login" className="link">← Retour à la connexion</Link></p>
      </div>
    </div>
  );
}
