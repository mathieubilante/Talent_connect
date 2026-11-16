import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import api, { errorMessage } from "../api";

const fcfa = (n) => `${new Intl.NumberFormat("fr-FR").format(n)} FCFA`;
const day = (iso) => (iso ? new Date(iso + "Z").toLocaleDateString("fr-FR") : "—");

export default function Receipt() {
  const { id } = useParams();
  const [r, setR] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { api.get(`/billing/receipt/${id}`).then((x) => setR(x.data)).catch((e) => setError(errorMessage(e))); }, [id]);

  if (error) return <div className="card empty"><h3>{error}</h3><Link to="/billing" className="link">← Retour</Link></div>;
  if (!r) return <p className="muted">Chargement…</p>;

  return (
    <>
      <p className="info no-print">✅ Paiement réussi. Votre compte est actif et votre espace dédié est prêt.</p>
      <div className="card receipt">
        <div className="row"><h2 style={{ margin: 0 }}>Reçu de paiement</h2><b>{r.number}</b></div>
        <p className="muted">Émis le {day(r.date)} · TalentConnect</p>
        <table><tbody>
          <tr><td>Client</td><td>{r.customer} ({r.email})</td></tr>
          <tr><td>Abonnement</td><td>{r.plan} · {r.months} mois</td></tr>
          <tr><td>Période</td><td>du {day(r.period_start)} au {day(r.period_end)}</td></tr>
          <tr><td>Mode de paiement</td><td>{r.provider === "simulated" ? "Paiement de démonstration" : r.provider}</td></tr>
          <tr><td>Référence</td><td>{r.reference}</td></tr>
          <tr><td><b>Montant payé</b></td><td><b>{fcfa(r.amount)}</b></td></tr>
        </tbody></table>
      </div>
      <div className="row gap no-print">
        <button className="btn" onClick={() => window.print()}>🖨 Imprimer / enregistrer en PDF</button>
        <Link to="/billing" className="link">← Mon abonnement</Link>
      </div>
    </>
  );
}
