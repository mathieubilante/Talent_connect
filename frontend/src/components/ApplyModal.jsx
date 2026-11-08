import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";

export default function ApplyModal({ offer, onClose, onDone }) {
  const [letter, setLetter] = useState("Génération de la lettre de motivation…");
  const [error, setError] = useState("");

  useEffect(() => {
    api.post("/assistant/cover-letter", { offer_id: offer.id })
      .then((r) => setLetter(r.data.letter))
      .catch(() => setLetter(""));
  }, [offer.id]);

  const send = async () => {
    try {
      await api.post("/applications", { offer_id: offer.id, cover_letter: letter });
      onDone(`Candidature envoyée pour « ${offer.title} » !`);
    } catch (e) { setError(errorMessage(e)); }
  };

  return (
    <div className="modal-back" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>Postuler : {offer.title}</h3>
        <p className="muted small">🤖 Brouillon de lettre généré selon votre profil. Vous pouvez le modifier avant l'envoi.</p>
        <textarea rows={12} value={letter} onChange={(e) => setLetter(e.target.value)} />
        {error && <p className="error">{error}</p>}
        <div className="row end gap">
          <button className="link" onClick={onClose}>Annuler</button>
          <button className="btn" onClick={send}>Envoyer ma candidature</button>
        </div>
      </div>
    </div>
  );
}
