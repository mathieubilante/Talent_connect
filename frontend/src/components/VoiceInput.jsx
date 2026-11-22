import { useState } from "react";
import { getLang } from "../i18n.js";

/* Dictée vocale (Speech-to-Text du navigateur). Fonctionne sur Chrome, Edge et Android ;
   non disponible sur certains navigateurs : le bouton n'apparaît pas.
   Remarque : la ponctuation automatique dépend du navigateur ; l'utilisateur la vérifie toujours. */
const LANG_CODE = { fr: "fr-FR", en: "en-US", ar: "ar-SA" };

export default function VoiceInput({ value, onChange }) {
  const [listening, setListening] = useState(false);
  const [error, setError] = useState("");
  const Recognition = typeof window !== "undefined" && (window.SpeechRecognition || window.webkitSpeechRecognition);
  if (!Recognition) return null;

  const start = () => {
    setError("");
    const r = new Recognition();
    r.lang = LANG_CODE[getLang()] || "fr-FR";
    r.interimResults = false;
    r.maxAlternatives = 1;
    r.onresult = (e) => {
      const text = e.results[0][0].transcript.trim();
      onChange(value ? `${value} ${text}` : text);
    };
    r.onerror = (e) => { setError(e.error === "not-allowed" ? "Autorisez le microphone dans le navigateur." : "Dictée impossible."); setListening(false); };
    r.onend = () => setListening(false);
    setListening(true);
    r.start();
  };

  return (
    <span className="voice">
      <button type="button" className={`mic ${listening ? "on" : ""}`} onClick={start} disabled={listening}
              aria-label="Dictée vocale" title="Dicter le texte">{listening ? "● Écoute…" : "🎤 Dicter"}</button>
      {error && <span className="error small"> {error}</span>}
    </span>
  );
}
