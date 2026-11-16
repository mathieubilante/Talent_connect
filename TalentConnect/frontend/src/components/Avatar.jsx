import { useEffect, useState } from "react";
import api from "../api";

/* Photo de profil ronde. Sans photo, affiche les initiales. La photo est chargée avec le jeton
   (elle n'a pas d'adresse publique). */
export default function Avatar({ hasPhoto, initials = "?", size = 36, refreshKey = 0 }) {
  const [url, setUrl] = useState("");
  useEffect(() => {
    let objectUrl = "";
    let alive = true;
    if (hasPhoto) {
      api.get("/profile/avatar", { responseType: "blob" })
        .then((r) => { if (alive) { objectUrl = URL.createObjectURL(r.data); setUrl(objectUrl); } })
        .catch(() => setUrl(""));
    } else setUrl("");
    return () => { alive = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [hasPhoto, refreshKey]);

  const style = { width: size, height: size, fontSize: Math.round(size * 0.38) };
  return url
    ? <img className="avatar" src={url} alt="" style={style} />
    : <span className="avatar avatar-init" style={style}>{initials}</span>;
}
