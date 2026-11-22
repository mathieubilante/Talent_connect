import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { errorMessage } from "../api";
import Avatar from "../components/Avatar.jsx";

const ageOf = (iso) => {
  if (!iso) return null;
  const b = new Date(iso), t = new Date();
  let a = t.getFullYear() - b.getFullYear();
  if (t.getMonth() < b.getMonth() || (t.getMonth() === b.getMonth() && t.getDate() < b.getDate())) a--;
  return a;
};

export default function CompleteProfile() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ first_name: "", last_name: "", birth_date: "", school: "", occupation: "", phone: "" });
  const [photoVersion, setPhotoVersion] = useState(0);
  const [hasPhoto, setHasPhoto] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const age = ageOf(form.birth_date);
  const today = new Date().toISOString().slice(0, 10);

  useEffect(() => {
    api.get("/profile/candidate").then((r) => {
      const c = r.data;
      setForm({ first_name: c.first_name || "", last_name: c.last_name || "", birth_date: c.birth_date || "",
                school: c.school || "", occupation: c.occupation || "", phone: c.phone || "" });
      setHasPhoto(c.has_avatar);
    }).catch((e) => setError(errorMessage(e)));
  }, []);

  const save = async (e) => {
    e.preventDefault(); setError(""); setBusy(true);
    try {
      await api.put("/profile/candidate", { ...form, birth_date: form.birth_date || null });
      navigate("/candidate");
    } catch (err) { setError(errorMessage(err)); }
    setBusy(false);
  };

  const uploadPhoto = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setError("");
    const data = new FormData();
    data.append("file", file);
    try {
      await api.post("/profile/avatar", data);
      setHasPhoto(true);
      setPhotoVersion((v) => v + 1);
    } catch (err) { setError(errorMessage(err)); }
    e.target.value = "";
  };

  return (
    <div className="card" style={{ maxWidth: 640, margin: "20px auto" }}>
      <h2>Complétez votre profil</h2>
      <p className="muted">Ces informations sont nécessaires pour postuler. Elles restent visibles uniquement pour les recruteurs auprès de qui vous postulez.</p>
      <div className="row gap" style={{ justifyContent: "flex-start", marginBottom: 16 }}>
        <Avatar hasPhoto={hasPhoto} initials={(form.first_name[0] || "?").toUpperCase()} size={84} refreshKey={photoVersion} />
        <label style={{ margin: 0 }}>Photo de profil (JPG, PNG ou WebP, 2 Mo max)
          <input type="file" accept="image/jpeg,image/png,image/webp" onChange={uploadPhoto} />
        </label>
      </div>
      <form onSubmit={save}>
        <div className="grid">
          <label>Prénom *<input value={form.first_name} onChange={set("first_name")} required /></label>
          <label>Nom *<input value={form.last_name} onChange={set("last_name")} required /></label>
          <label>Date de naissance *
            <input type="date" max={today} value={form.birth_date} onChange={set("birth_date")} required />
          </label>
          <label>Âge
            <input value={age === null ? "" : `${age} ans`} readOnly style={{ background: "#f4f6f8" }} />
          </label>
        </div>
        <label>Établissement où vous étudiez *
          <input value={form.school} onChange={set("school")} placeholder="ex. École Nationale Polytechnique" required />
        </label>
        <label>Ce que vous faites *
          <input value={form.occupation} onChange={set("occupation")} placeholder="ex. Étudiant en génie logiciel, comptable, développeur…" required />
        </label>
        <label>Téléphone <span className="muted small">(facultatif)</span>
          <input value={form.phone} onChange={set("phone")} placeholder="+228 90 12 34 56" />
        </label>
        {error && <p className="error">{error}</p>}
        <button className="btn full" type="submit" disabled={busy}>{busy ? "Enregistrement…" : "Enregistrer et continuer"}</button>
      </form>
    </div>
  );
}
