import { useNavigate } from "react-router-dom";
import PersonalInfoForm from "../components/PersonalInfoForm.jsx";
import Seo from "../components/Seo.jsx";

/* Premier passage après l'inscription (e-mail ou Google). Les mêmes champs se modifient ensuite dans Mon compte. */
export default function CompleteProfile() {
  const navigate = useNavigate();
  return (
    <div className="card" style={{ maxWidth: 640, margin: "20px auto" }}>
      <Seo title="Compléter mon profil" description="Renseignez vos informations personnelles." />
      <h2>Complétez votre profil</h2>
      <p className="muted">Ces informations sont nécessaires pour postuler. Vous pourrez les modifier à tout moment dans Mon compte.</p>
      <PersonalInfoForm onSaved={() => navigate("/candidate")} />
    </div>
  );
}
