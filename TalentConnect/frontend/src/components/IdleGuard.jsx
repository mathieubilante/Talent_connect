import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { getRole, serverLogout } from "../api";

/* Déconnexion automatique après inactivité : avertissement 60 s avant, et signal d'activité régulier
   vers le serveur pour que sa propre minuterie d'inactivité reste synchronisée. */
export default function IdleGuard() {
  const role = getRole();
  const navigate = useNavigate();
  const [idleMin, setIdleMin] = useState(30);
  const [warning, setWarning] = useState(false);
  const [left, setLeft] = useState(60);
  const last = useRef(Date.now());
  const lastPing = useRef(Date.now());
  const warnRef = useRef(false);

  useEffect(() => { api.get("/auth/config").then((r) => setIdleMin(r.data.session_idle_minutes || 30)).catch(() => {}); }, []);

  useEffect(() => {
    if (!role) return;
    const mark = () => { if (!warnRef.current) last.current = Date.now(); };
    const events = ["mousemove", "mousedown", "keydown", "scroll", "touchstart", "click"];
    events.forEach((e) => window.addEventListener(e, mark, { passive: true }));

    const limit = idleMin * 60000;
    const warnAt = Math.max(limit - 60000, limit / 2);
    const timer = setInterval(async () => {
      const idle = Date.now() - last.current;
      if (idle >= limit) {
        clearInterval(timer);
        warnRef.current = false;
        await serverLogout();
        navigate("/login?reason=idle");
        return;
      }
      if (idle >= warnAt) { warnRef.current = true; setWarning(true); setLeft(Math.ceil((limit - idle) / 1000)); }
      else if (idle < 240000 && Date.now() - lastPing.current > 240000) {
        lastPing.current = Date.now();                       // l'utilisateur est actif : on prévient le serveur
        api.get("/account/me").catch(() => {});
      }
    }, 1000);

    return () => { events.forEach((e) => window.removeEventListener(e, mark)); clearInterval(timer); };
  }, [role, idleMin]);

  const stay = () => {
    last.current = Date.now();
    warnRef.current = false;
    setWarning(false);
    api.get("/account/me").catch(() => {});
  };

  if (!role || !warning) return null;
  return (
    <div className="modal-back">
      <div className="modal" style={{ maxWidth: 420, textAlign: "center" }}>
        <h3>⏱ Toujours là ?</h3>
        <p>Pour votre sécurité, vous serez déconnecté dans <b>{left} s</b> en raison de votre inactivité.</p>
        <button className="btn full" onClick={stay}>Rester connecté</button>
      </div>
    </div>
  );
}
