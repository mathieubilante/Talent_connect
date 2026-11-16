import { useEffect, useState } from "react";
import api from "../api";

export default function Notifications() {
  const [items, setItems] = useState([]);
  useEffect(() => {
    api.get("/notifications").then(async (r) => {
      setItems(r.data.items);
      if (r.data.unread) await api.post("/notifications/read-all");
    }).catch(() => {});
  }, []);

  return (
    <>
      <h2>🔔 Notifications</h2>
      {items.length === 0 && <p className="muted">Aucune notification pour le moment.</p>}
      {items.map((n) => (
        <div key={n.id} className={`card notif ${n.is_read ? "" : "unread"}`}>
          <p>{n.message}</p>
          <span className="muted small">{new Date(n.created_at).toLocaleString("fr-FR")}</span>
        </div>
      ))}
    </>
  );
}
