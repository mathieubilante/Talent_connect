import { useState } from "react";
import api from "../api";

export default function ProfileAvatar({ name, email, onUpload }) {
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState("");

  const handleFile = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setError("Veuillez choisir une image (JPG, PNG, etc.)");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError("L'image doit faire moins de 5 Mo");
      return;
    }

    const localPreview = URL.createObjectURL(file);
    setPreview(localPreview);
    setError("");

    const form = new FormData();
    form.append("file", file);
    try {
      const res = await api.post("/profile/avatar", form);
      onUpload(res.data);
    } catch (err) {
      setError("Échec de l'upload de la photo");
    }
  };

  const initials = name
    ? name.split(" ").map((n) => n[0]).slice(0, 2).join("").toUpperCase()
    : "?";

  return (
    <div className="profile-avatar" style={{ position: "relative", display: "inline-flex", alignItems: "center", gap: "16px" }}>
      <div
        className="avatar-circle"
        title={name || email || "Votre nom"}
        style={{
          width: "80px",
          height: "80px",
          borderRadius: "50%",
          background: preview ? `url(${preview}) center/cover no-repeat` : "var(--blue)",
          color: "#fff",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "1.8rem",
          fontWeight: "700",
          cursor: "pointer",
          border: "3px solid #fff",
          boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
          transition: "transform 0.2s",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.transform = "scale(1.05)")}
        onMouseLeave={(e) => (e.currentTarget.style.transform = "scale(1)")}
      >
        {!preview && initials}
      </div>
      <div>
        <label className="btn" style={{ cursor: "pointer", marginBottom: "6px" }}>
          📷 {preview ? "Changer la photo" : "Ajouter une photo"}
          <input
            type="file"
            accept="image/*"
            capture="user"
            style={{ display: "none" }}
            onChange={handleFile}
          />
        </label>
        {error && <p className="error small">{error}</p>}
      </div>
    </div>
  );
}