import { useState } from "react";
import api, { errorMessage } from "../api";

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
        <h3>Confirmer ma candidature</h3>
        <p><b>{offer.title}</b><br /><span className="muted">{offer.company_name}</span></p>
        <p className="muted small">Votre profil et votre CV sont transmis au recruteur avec votre candidature.</p>
        <label>Message au recruteur <span className="muted small">(facultatif)</span>
          <textarea rows={5} value={note} placeholder="Ajoutez quelques mots si vous le souhaitez…"
                    onChange={(e) => setNote(e.target.value)} />
        </label>
        <button type="button" className="link" onClick={draft} disabled={drafting}>
          {drafting ? "Rédaction en cours…" : "✨ Proposer un message avec TConnect IA"}
        </button>
        {error && <p className="error">{error}</p>}
        <div className="row end gap" style={{ marginTop: 14 }}>
          <button className="link" onClick={onClose} disabled={sending}>Annuler</button>
          <button className="btn" onClick={send} disabled={sending}>{sending ? "Envoi…" : "Confirmer et postuler"}</button>
        </div>
      </div>
    </div>
  );
}
