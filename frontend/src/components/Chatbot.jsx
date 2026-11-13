import { useEffect, useRef, useState } from "react";
import api, { getRole } from "../api";

export default function Chatbot() {
  const role = getRole();
  const endpoint = role === "candidate" || role === "company" ? "/assistant/chat" : "/assistant/public-chat";
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [quick, setQuick] = useState([]);
  const [busy, setBusy] = useState(false);
  const end = useRef(null);

  const send = async (text) => {
    const msg = (text ?? input).trim();
    if (!msg || busy) return;
    setInput("");
    setQuick([]);
    setMessages((m) => [...m, { from: "me", text: msg }]);
    setBusy(true);
    try {
      const { data } = await api.post(endpoint, { message: msg });
      setMessages((m) => [...m, { from: "bot", text: data.reply }]);
      setQuick(data.quick_replies || []);
    } catch {
      setMessages((m) => [...m, { from: "bot", text: "Je ne parviens pas à joindre le serveur pour le moment. Réessayez dans un instant." }]);
    }
    setBusy(false);
  };

  // changement de rôle (connexion / déconnexion) : on repart d'une conversation neuve
  useEffect(() => { setMessages([]); setQuick([]); }, [role]);
  useEffect(() => { if (open && messages.length === 0) send("Bonjour"); }, [open, messages.length]);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, quick]);

  return (
    <>
      {!open && <button className="chat-fab" onClick={() => setOpen(true)} title="Discuter avec TConnect IA">🤖 <span>TConnect IA</span></button>}
      {open && (
        <div className="chat">
          <div className="chat-head">
            <strong>🤖 TConnect IA <small>bêta</small></strong>
            <button className="chat-close" onClick={() => setOpen(false)}>✕</button>
          </div>
          <div className="chat-body">
            {messages.map((m, i) => <div key={i} className={`bubble ${m.from}`}>{m.text}</div>)}
            {busy && <div className="bubble bot">…</div>}
            <div className="qr">
              {quick.map((q) => <button key={q} onClick={() => send(q)}>{q}</button>)}
            </div>
            <div ref={end} />
          </div>
          <form className="chat-input" onSubmit={(e) => { e.preventDefault(); send(); }}>
            <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Posez votre question…" />
            <button className="btn" type="submit">Envoyer</button>
          </form>
        </div>
      )}
    </>
  );
}
