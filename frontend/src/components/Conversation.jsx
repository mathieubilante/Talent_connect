import { useEffect, useRef, useState } from "react";
import api, { errorMessage } from "../api";
import { t } from "../i18n.js";

/* Conversation liée à une candidature : candidat et recruteur uniquement. */
export default function Conversation({ applicationId }) {
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [sending, setSending] = useState(false);
  const endRef = useRef(null);

  const load = () =>
    api.get(`/messages/application/${applicationId}`)
      .then((r) => setMessages(r.data))
      .catch((e) => setError(errorMessage(e)));

  // Rafraîchissement automatique toutes les 20 secondes, tant que la conversation est ouverte
  useEffect(() => {
    load();
    const timer = setInterval(load, 20000);
    return () => clearInterval(timer);
  }, [applicationId]);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [messages.length]);

  const send = async (e) => {
    e.preventDefault();
    const body = text.trim();
    if (!body) return;
    setSending(true); setError("");
    try {
      await api.post(`/messages/application/${applicationId}`, { body });
      setText("");
      await load();
    } catch (err) { setError(errorMessage(err)); }
    setSending(false);
  };

  return (
    <div className="conversation">
      <div className="conv-list">
        {messages.length === 0 && <p className="muted small">{t("msg_empty")}</p>}
        {messages.map((m) => (
          <div key={m.id} className={`bubble ${m.mine ? "mine" : "theirs"}`}>
            <span>{m.body}</span>
            <small>{m.mine ? t("msg_you") : ""}</small>
          </div>
        ))}
        <div ref={endRef} />
      </div>
      <form className="conv-form" onSubmit={send}>
        <textarea rows={2} maxLength={2000} value={text} placeholder={t("msg_placeholder")}
                  onChange={(e) => setText(e.target.value)} />
        <button className="btn" type="submit" disabled={sending || !text.trim()}>{t("msg_send")}</button>
      </form>
      {error && <p className="error small">{error}</p>}
    </div>
  );
}
