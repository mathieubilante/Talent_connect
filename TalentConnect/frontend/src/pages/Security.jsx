import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";

const CHANNEL_LABEL = { app: "application", email: "e-mail", sms: "SMS", whatsapp: "WhatsApp", telegram: "Telegram" };
const STATE_LABEL = { sent: "envoyé", console: "mode démo", failed: "échec" };

function Channels({ csv }) {
  return (
    <span className="chips">
      {(csv || "").split(",").filter(Boolean).map((c) => {
        const [name, state] = c.split(":");
        return <span key={c} className={`chip ${state === "failed" ? "miss" : "ok"}`}>{CHANNEL_LABEL[name] || name}{state ? ` · ${STATE_LABEL[state] || state}` : ""}</span>;
      })}
    </span>
  );
}

export default function Security() {
  const [tab, setTab] = useState("alerts");
  const [alerts, setAlerts] = useState([]);
  const [prefs, setPrefs] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const load = () => Promise.all([api.get("/security/alerts"), api.get("/security/preferences")])
    .then(([a, p]) => { setAlerts(a.data); setPrefs(p.data); })
    .catch((e) => setError(errorMessage(e)));
  useEffect(() => { load(); }, []);

  const set = (k) => (e) => setPrefs({ ...prefs, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value });
  const save = async (e) => {
    e.preventDefault(); setError(""); setMessage("");
    try { setPrefs((await api.put("/security/preferences", prefs)).data); setMessage("Préférences enregistrées ✓"); }
    catch (err) { setError(errorMessage(err)); }
  };
  const test = async () => {
    setError(""); setMessage("");
    try { await api.post("/security/test-alert"); setMessage("Alerte de test envoyée ✓"); await load(); setTab("alerts"); }
    catch (err) { setError(errorMessage(err)); }
  };

  if (!prefs) return error ? <p className="error">{error}</p> : <p className="muted">Chargement…</p>;
  const demo = (k) => prefs.providers[k] === "demo" && <span className="tag stage" style={{ marginLeft: 8 }}>mode démo</span>;

  return (
    <>
      <h2>🔐 Sécurité du compte</h2>
      <div className="tabs">
        <button className={tab === "alerts" ? "on" : ""} onClick={() => setTab("alerts")}>Alertes récentes ({alerts.length})</button>
        <button className={tab === "prefs" ? "on" : ""} onClick={() => setTab("prefs")}>Où recevoir mes alertes</button>
      </div>
      {message && <p className="info">{message}</p>}
      {error && <p className="error">{error}</p>}

      {tab === "alerts" && (
        <>
          <p className="muted">Vous êtes prévenu lors d'une connexion depuis un nouvel appareil, de tentatives de connexion échouées, d'une activité suspecte ou de la fermeture de votre session sur un autre appareil.</p>
          {alerts.length === 0 && <div className="card empty"><h3>Aucune alerte</h3><p className="muted">Tout est calme sur votre compte.</p></div>}
          {alerts.map((a) => (
            <div className="card" key={a.id}>
              <div className="row"><h3>{a.icon} {a.title}</h3><span className="muted small">{new Date(a.created_at + "Z").toLocaleString("fr-FR")}</span></div>
              <p>{a.message}</p>
              <p className="muted small">Envoyée sur : <Channels csv={a.channels} /></p>
            </div>
          ))}
        </>
      )}

      {tab === "prefs" && (
        <form className="card" onSubmit={save}>
          <p className="muted">Choisissez les canaux. Tant qu'un service n'est pas configuré sur le serveur (<b>mode démo</b>), l'alerte apparaît dans l'application et dans les journaux du serveur.</p>
          <label className="check"><input type="checkbox" checked={prefs.notify_email} onChange={set("notify_email")} /> ✉️ E-mail {demo("email")}</label>
          <label className="check"><input type="checkbox" checked={prefs.notify_sms} onChange={set("notify_sms")} /> 💬 SMS {demo("sms")}</label>
          <label className="check"><input type="checkbox" checked={prefs.notify_whatsapp} onChange={set("notify_whatsapp")} /> 🟢 WhatsApp {demo("whatsapp")}</label>
          <label>Numéro de téléphone (SMS et WhatsApp)
            <input value={prefs.phone} onChange={set("phone")} placeholder="+228 90 12 34 56" />
          </label>
          <label className="check"><input type="checkbox" checked={prefs.notify_telegram} onChange={set("notify_telegram")} /> ✈️ Telegram {demo("telegram")}</label>
          <label>Identifiant Telegram (chat id)
            <input value={prefs.telegram_chat_id} onChange={set("telegram_chat_id")} placeholder="123456789" />
          </label>
          <p className="muted small">Pour connaître votre identifiant Telegram, écrivez au robot @userinfobot ; puis démarrez une conversation avec le robot de TalentConnect.</p>
          <div className="row gap">
            <button className="btn" type="submit">Enregistrer</button>
            <button className="btn-outline" type="button" onClick={test}>Envoyer une alerte de test</button>
          </div>
        </form>
      )}
    </>
  );
}
