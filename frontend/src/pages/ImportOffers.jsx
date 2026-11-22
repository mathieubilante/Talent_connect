import { useState } from "react";
import api, { errorMessage } from "../api";
import { t } from "../i18n.js";

const TEMPLATE = "titre,description,type,competences,lieu,date_limite\n" +
  "Stage développeur Python,Participer au développement d'API REST pour nos clients,stage,python;sql;docker,Lomé,2027-03-31\n";

export default function ImportOffers() {
  const [file, setFile] = useState(null);
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const send = async (commit) => {
    if (!file) return;
    setBusy(true); setError("");
    const data = new FormData();
    data.append("file", file);
    data.append("commit", commit ? "true" : "false");
    try { setReport((await api.post("/import/offers", data)).data); }
    catch (e) { setError(errorMessage(e)); }
    setBusy(false);
  };

  const downloadTemplate = () => {
    const url = URL.createObjectURL(new Blob(["\uFEFF" + TEMPLATE], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url; a.download = "modele_offres.csv"; a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="card" style={{ maxWidth: 760, margin: "20px auto" }}>
      <h2>{t("import_title")}</h2>
      <p className="muted">{t("import_help")}</p>
      <button type="button" className="link" onClick={downloadTemplate}>{t("import_template")}</button>
      <label style={{ marginTop: 12 }}>Fichier
        <input type="file" accept=".csv,.xlsx,text/csv" onChange={(e) => { setFile(e.target.files[0] || null); setReport(null); }} />
      </label>
      <div className="row gap" style={{ justifyContent: "flex-start" }}>
        <button className="btn-outline" disabled={!file || busy} onClick={() => send(false)}>{t("import_check")}</button>
        <button className="btn" disabled={!file || busy || !report || report.valid === 0} onClick={() => send(true)}>{t("import_go")}</button>
      </div>
      {error && <p className="error">{error}</p>}
      {report && (
        <div style={{ marginTop: 16 }}>
          <p><b>{report.total_rows}</b> ligne(s) lue(s) · <b className="ok-text">{report.valid}</b> valide(s) · <b className="err-text">{report.invalid}</b> erreur(s) · {report.duplicates.length} doublon(s)
            {report.over_quota > 0 && <> · <b>{report.over_quota}</b> non importée(s) : limite de votre offre d'essai</>}</p>
          {report.committed && <p className="info">{report.imported} offre(s) publiée(s) ✓</p>}
          {report.errors.length > 0 && (
            <div className="scroll"><table><thead><tr><th>Ligne</th><th>Erreur</th></tr></thead>
              <tbody>{report.errors.map((e) => <tr key={e.row}><td>{e.row}</td><td>{e.messages.join(" ; ")}</td></tr>)}</tbody></table></div>
          )}
          {report.duplicates.length > 0 && <p className="muted small">Doublons ignorés (même titre et même lieu que une offre existante) : lignes {report.duplicates.map((d) => d.row).join(", ")}.</p>}
          {!report.committed && report.preview.length > 0 && (
            <>
              <h3 style={{ marginTop: 12 }}>Aperçu des offres valides</h3>
              {report.preview.map((o, i) => <p key={i} className="small">• {o.title} ({o.offer_type}{o.location ? `, ${o.location}` : ""})</p>)}
            </>
          )}
        </div>
      )}
    </div>
  );
}
