import { useEffect, useRef, useState } from "react";
import api from "../api";

export default function Chatbot() {
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
      const { data } = await api.post("/assistant/chat", { message: msg });
      setMessages((m) => [...m, { from: "bot", text: data.reply }]);
      setQuick(data.quick_replies || []);
    } catch {
      setMessages((m) => [...m, { from: "bot", text: "Désolé, l'assistant est indisponible pour le moment." }]);
    }
    setBusy(false);
  };

  useEffect(() => { if (open && messages.length === 0) send("Bonjour"); }, [open]);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, quick]);

  return (
    <>
      {!open && <button className="chat-fab" onClick={() => setOpen(true)} title="Assistant IA">🤖</button>}
      {open && (
        <div className="chat">
          <div className="chat-head">
            <strong>🤖 Assistant TalentConnect</strong>
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
