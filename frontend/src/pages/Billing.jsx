import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api, { errorMessage } from "../api";

const fcfa = (n) => `${new Intl.NumberFormat("fr-FR").format(n)} FCFA`;
const STATUS = { paid: ["Payé", "tag st-acceptee"], failed: ["Échoué", "tag st-refusee"], pending: ["En attente", "tag st-preselectionnee"], cancelled: ["Annulé", "tag"] };

export default function Billing() {
  const navigate = useNavigate();
  const [me, setMe] = useState(null);
  const [plans, setPlans] = useState(null);
  const [months, setMonths] = useState(3);
  const [checkout, setCheckout] = useState(null);
  const [method, setMethod] = useState("mobile");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = () => Promise.all([api.get("/billing/me"), api.get("/billing/plans")])
    .then(([m, p]) => { setMe(m.data); setPlans(p.data); })
    .catch((e) => setError(errorMessage(e)));
  useEffect(() => { load(); }, []);

  const choose = async (plan) => {
    setError(""); setBusy(true);
    try { setCheckout((await api.post("/billing/checkout", { plan_code: plan.code, months })).data); }
    catch (e) { setError(errorMessage(e)); }
    setBusy(false);
  };

  const pay = async (success) => {
    setBusy(true); setError("");
    try {
      await api.post(`/billing/payments/${checkout.payment_id}/simulate`, { outcome: success ? "success" : "failure", reason: success ? "" : "Paiement refusé (simulation)" });
      const id = checkout.payment_id;
      setCheckout(null);
      if (success) navigate(`/billing/receipt/${id}`);
      else { setError("Le paiement a échoué (simulation). Aucun montant n'a été débité. Vous pouvez réessayer."); load(); }
    } catch (e) { setError(errorMessage(e)); }
    setBusy(false);
  };

  if (!me || !plans) return error ? <p className="error">{error}</p> : <p className="muted">Chargement…</p>;
  const sub = me.subscription;
  const ws = me.workspace;

  return (
    <>
      <h2>💳 Abonnement</h2>
      {error && <p className="error">{error}</p>}

      {sub && (
        <div className="card">
          <div className="row"><h3>{sub.label}</h3><span className="tag st-acceptee">Actif</span></div>
          <p className="muted">Valable du {new Date(sub.starts_at + "Z").toLocaleDateString("fr-FR")} au <b>{new Date(sub.ends_at + "Z").toLocaleDateString("fr-FR")}</b></p>
        </div>
      )}
      {ws && (
        <div className="card">
          <h3>🏠 {ws.name}</h3>
          <p className="muted">Votre espace dédié est prêt : stockage de {ws.storage_mb} Mo{ws.max_active_offers ? `, jusqu'à ${ws.max_active_offers} offres actives` : ""}.</p>
        </div>
      )}

      {!plans.can_checkout && (
        <div className="card">
          <h3>Abonnement indisponible pour le moment</h3>
          <p className="muted">{plans.reason}</p>
          {plans.account_status === "pending" && <Link to="/kyc" className="btn">Envoyer mes documents</Link>}
        </div>
      )}

      {plans.can_checkout && (
        <>
          <p className="muted">{sub ? "Renouvelez ou prolongez votre abonnement :" : "Choisissez votre durée puis votre offre. Plus la durée est longue, plus la remise est importante."}</p>
          <div className="tabs">
            {[1, 3, 6, 12].map((m) => {
              const d = plans.plans[0]?.quotes.find((q) => q.months === m)?.discount_percent;
              return <button key={m} className={months === m ? "on" : ""} onClick={() => setMonths(m)}>{m} mois{d ? ` (−${d} %)` : ""}</button>;
            })}
          </div>
          <div className="plans">
            {plans.plans.map((plan) => {
              const q = plan.quotes.find((x) => x.months === months);
              return (
                <div className="card plan" key={plan.code}>
                  <h3>{plan.label}</h3>
                  <p className="price">{fcfa(q.total)} <small>pour {months} mois</small></p>
                  {q.discount_percent > 0 && <p className="muted small"><s>{fcfa(q.subtotal)}</s> · vous économisez {fcfa(q.discount_amount)}</p>}
                  <p className="muted small">soit {fcfa(plan.monthly)} par mois avant remise</p>
                  <ul className="plan-list">{plan.features.map((f) => <li key={f}>{f}</li>)}</ul>
                  <button className="btn full" disabled={busy} onClick={() => choose(plan)}>{sub ? "Renouveler" : "Choisir cette offre"}</button>
                </div>
              );
            })}
          </div>
          <p className="muted small">Tarifs de démonstration, à confirmer avec l'entreprise. Le prix est toujours calculé par le serveur.</p>
        </>
      )}

      <div className="card">
        <h3>Historique des paiements</h3>
        {me.payments.length === 0 ? <p className="muted">Aucun paiement pour le moment.</p> : (
          <div className="scroll"><table>
            <thead><tr><th>Date</th><th>Montant</th><th>Statut</th><th>Reçu</th></tr></thead>
            <tbody>{me.payments.map((p) => (
              <tr key={p.id}><td>{new Date(p.created_at + "Z").toLocaleString("fr-FR")}</td><td>{fcfa(p.amount)}</td>
                <td><span className={STATUS[p.status]?.[1] || "tag"}>{STATUS[p.status]?.[0] || p.status}</span></td>
                <td>{p.status === "paid" ? <Link to={`/billing/receipt/${p.id}`} className="link">{p.receipt_number}</Link> : "—"}</td></tr>
            ))}</tbody>
          </table></div>
        )}
      </div>

      {checkout && (
        <div className="modal-back" onClick={() => !busy && setCheckout(null)}>
          <div className="modal" style={{ maxWidth: 440 }} onClick={(e) => e.stopPropagation()}>
            <h3>Paiement</h3>
            <p className="devcode">Mode démonstration : aucun argent réel n'est débité.</p>
            <p><b>{checkout.quote.label}</b> · {checkout.quote.months} mois<br />
              Montant à payer : <b>{fcfa(checkout.amount)}</b><br /><span className="muted small">Référence : {checkout.provider_ref.slice(0, 12)}…</span></p>
            <div className="seg" style={{ marginBottom: 14 }}>
              <button className={method === "mobile" ? "on" : ""} onClick={() => setMethod("mobile")}>📱 Mobile Money</button>
              <button className={method === "card" ? "on" : ""} onClick={() => setMethod("card")}>💳 Carte</button>
            </div>
            <button className="btn full" disabled={busy} onClick={() => pay(true)}>{busy ? "Traitement…" : `Payer ${fcfa(checkout.amount)}`}</button>
            <div className="row" style={{ marginTop: 8 }}>
              <button className="link" disabled={busy} onClick={() => pay(false)}>Simuler un échec</button>
              <button className="link" disabled={busy} onClick={() => setCheckout(null)}>Annuler</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
