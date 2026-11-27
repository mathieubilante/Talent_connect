import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";
import Avatar from "./Avatar.jsx";

/* En-tête de profil façon réseau professionnel : photo, nom complet, activité, établissement, âge.
   La photo se change directement depuis l'ordinateur ou le téléphone. */
export default function ProfileHeader({ onError }) {
  const [me, setMe] = useState(null);
  const [version, setVersion] = useState(0);
  const [busy, setBusy] = useState(false);
  const [profile, setProfile] = useState(null);

  const load = () => Promise.all([api.get("/profile/me"), api.get("/profile/candidate")])
    .then(([m, p]) => { setMe(m.data); setProfile(p.data); })
    .catch((e) => onError && onError(errorMessage(e)));
  useEffect(() => { load(); }, []);

  const uploadPhoto = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setBusy(true);
    const data = new FormData();
    data.append("file", file);
    try {
      await api.post("/profile/avatar", data);
      setVersion((v) => v + 1);
      await load();
    } catch (err) { onError && onError(errorMessage(err)); }
    setBusy(false);
    e.target.value = "";
  };

  if (!me || !profile) return null;
  const fullName = `${profile.first_name || ""} ${profile.last_name || ""}`.trim() || me.email;
  const subline = [profile.occupation, profile.school].filter(Boolean).join(" · ");

  return (
    <div className="card profile-head">
      <div className="profile-photo">
        <Avatar hasPhoto={!!me.has_avatar} initials={me.initials} size={96} refreshKey={version} />
      </div>
      <div className="profile-info">
        <h1 className="profile-name">{fullName}</h1>
        {subline && <p className="profile-sub">{subline}</p>}
        <p className="muted small">{me.email}{me.age ? ` · ${me.age} ans` : ""}</p>
        {!me.profile_complete && <p className="profile-warn">Profil incomplet : il manque {me.missing.join(", ")}.</p>}
      </div>
    </div>
  );
}
