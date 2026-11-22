import { useState } from "react";
import { t } from "../i18n.js";
import api, { errorMessage } from "../api";
import VoiceInput from "./VoiceInput.jsx";

/* Candidature en deux clics : on confirme, le message au recruteur est facultatif.
   Le brouillon de lettre n'est généré que si l'utilisateur le demande. */
export default function ApplyModal({ offer, onClose, onDone }) {
  const [note, setNote] = useState("");
  const [drafting, setDrafting] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");

  const draft = async () => {
    setDrafting(true); setError("");
    try {
      const { data } = await api.post("/assistant/cover-letter", { offer_id: offer.id });
      setNote(data.letter);
    } catch (e) { setError(errorMessage(e)); }
    setDrafting(false);
  };

  const send = async () => {
    setSending(true); setError("");
    try {
      await api.post("/applications", { offer_id: offer.id, cover_letter: note });
      onDone(`Candidature envoyée pour « ${offer.title} ».`);
    } catch (e) { setError(errorMessage(e)); setSending(false); }
  };

  return (
    <div className="modal-back" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>{t("confirm_apply_title")}</h3>
        <p><b>{offer.title}</b><br /><span className="muted">{offer.company_name}</span></p>
        <p className="muted small">{t("profile_cv_sent")}</p>
        <div className="row"><span className="muted small">{t("recruiter_msg")}</span><VoiceInput value={note} onChange={setNote} /></div>
        <label style={{ marginTop: 0 }}>
          <textarea rows={5} value={note} placeholder={t("add_words")}
                    onChange={(e) => setNote(e.target.value)} />
        </label>
        <button type="button" className="link" onClick={draft} disabled={drafting}>
          {drafting ? t("drafting") : t("ai_draft")}
        </button>
        {error && <p className="error">{error}</p>}
        <div className="row end gap" style={{ marginTop: 14 }}>
          <button className="link" onClick={onClose} disabled={sending}>{t("cancel")}</button>
          <button className="btn" onClick={send} disabled={sending}>{sending ? t("sending") : t("confirm_send")}</button>
        </div>
      </div>
    </div>
  );
}
