import { useEffect, useState } from "react";
import api, { downloadDocument, errorMessage } from "../api";

const STATUS = {
  submitted: ["Envoyé, en attente d'examen", "tag st-preselectionnee"],
  approved: ["Validé", "tag st-acceptee"],
  rejected: ["Refusé", "tag st-refusee"],
};
const size = (b) => (b > 1024 * 1024 ? `${(b / 1024 / 1024).toFixed(1)} Mo` : `${Math.round(b / 1024)} Ko`);

export default function Kyc() {
  const [data, setData] = useState(null);
  const [dates, setDates] = useState({});
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");

  const load = () => api.get("/kyc/me").then((r) => setData(r.data)).catch((e) => setError(errorMessage(e)));
  useEffect(() => { load(); }, []);

  const upload = async (req, file) => {
    if (!file) return;
    setError(""); setMessage(""); setBusy(req.doc_type);
    const form = new FormData();
    form.append("doc_type", req.doc_type);
    form.append("file", file);
    if (req.needs_issue_date) form.append("issue_date", dates[req.doc_type] || "");
    try {
      const res = await api.post("/kyc/documents", form);
      setData(res.data);
      setMessage(res.data.complete
        ? "Dossier complet ✓ Il sera examiné par l'administration."
        : "Document envoyé et stocké de façon chiffrée ✓");
    } catch (e) { setError(errorMessage(e)); }
    setBusy("");
  };

  const remove = async (id) => {
    if (!window.confirm("Supprimer ce document ?")) return;
    try { setData((await api.delete(`/kyc/documents/${id}`)).data); setMessage("Document supprimé"); }
    catch (e) { setError(errorMessage(e)); }
  };

  if (!data) return error ? <p className="error">{error}</p> : <p className="muted">Chargement…</p>;
  const done = data.required.length - data.missing.length;
  const pct = Math.round((done / data.required.length) * 100);

  return (
    <>
      <h2>📁 Mes documents d'identité</h2>
      <div className="card">
        <div className="row"><span><b>{done}/{data.required.length}</b> document(s) fourni(s)</span>
          <span className="muted small">🔒 Vos documents sont chiffrés et visibles uniquement par vous et l'administration.</span></div>
        <div className="bar"><div className={`fill ${data.complete ? "excellent" : "bon"}`} style={{ width: `${pct}%` }} /></div>
      </div>
      {message && <p className="info">{message}</p>}
      {error && <p className="error">{error}</p>}

      {data.required.map((req) => {
        const doc = data.documents.find((d) => d.doc_type === req.doc_type);
        const locked = doc?.status === "approved";
        return (
          <div className="card" key={req.doc_type}>
            <div className="row">
              <div><h3>{req.label}</h3><p className="muted">{req.help}</p></div>
              {doc ? <span className={STATUS[doc.status]?.[1] || "tag"}>{STATUS[doc.status]?.[0] || doc.status}</span>
                   : <span className="tag stage">À fournir</span>}
            </div>
            {doc && (
              <p className="muted small">
                📎 {doc.original_name} · {size(doc.size_bytes)} · envoyé le {new Date(doc.uploaded_at + "Z").toLocaleString("fr-FR")}
                {doc.expires_on && <> · valable jusqu'au {new Date(doc.expires_on).toLocaleDateString("fr-FR")}</>}
              </p>
            )}
            {doc?.review_note && <p className="error">Motif : {doc.review_note}</p>}
            {!locked && (
              <div className="row gap">
                {req.needs_issue_date && (
                  <label style={{ margin: 0 }}>Date d'émission de l'extrait
                    <input type="date" max={new Date().toISOString().slice(0, 10)} value={dates[req.doc_type] || ""}
                           onChange={(e) => setDates({ ...dates, [req.doc_type]: e.target.value })} />
                  </label>
                )}
                <label style={{ margin: 0, flex: 1 }}>{doc ? "Remplacer le fichier" : "Choisir le fichier"} (PDF, JPG ou PNG, 5 Mo max)
                  <input type="file" accept="application/pdf,image/jpeg,image/png" disabled={busy === req.doc_type}
                         onChange={(e) => { upload(req, e.target.files[0]); e.target.value = ""; }} />
                </label>
              </div>
            )}
            {doc && (
              <div className="row end gap">
                <button className="link" onClick={() => downloadDocument(doc.id, doc.original_name).catch((e) => setError(errorMessage(e)))}>Télécharger</button>
                {!locked && <button className="btn-danger" onClick={() => remove(doc.id)}>Supprimer</button>}
              </div>
            )}
          </div>
        );
      })}
    </>
  );
}
