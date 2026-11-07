import { useEffect, useState } from "react";
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import api, { clearSession, getRole } from "./api";
import Chatbot from "./components/Chatbot.jsx";
import TrialBanner from "./components/TrialBanner.jsx";
import Account from "./pages/Account.jsx";
import Kyc from "./pages/Kyc.jsx";
import Home from "./pages/Home.jsx";
import Login from "./pages/Login.jsx";
import Offers from "./pages/Offers.jsx";
import CandidateSpace from "./pages/CandidateSpace.jsx";
import CompanySpace from "./pages/CompanySpace.jsx";
import Notifications from "./pages/Notifications.jsx";
import Admin from "./pages/Admin.jsx";

const HOME_BY_ROLE = { candidate: "/candidate", company: "/company", admin: "/admin" };

function Navbar() {
  const role = getRole();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    if (!role) return;
    api.get("/notifications").then((r) => setUnread(r.data.unread)).catch(() => {});
  }, [pathname, role]);

  const logout = () => { clearSession(); navigate("/"); };
  const nav = (to, label) => <Link to={to} className={pathname === to ? "active" : ""}>{label}</Link>;

  return (
    <header className="navbar">
      <Link to="/" className="brand"><img src="/favicon.svg" alt="" /> Talent<span>Connect</span></Link>
      <nav>
        {role && nav("/offers", "Offres")}
        {role === "candidate" && nav("/candidate", "Mon espace")}
        {role === "company" && nav("/company", "Espace entreprise")}
        {role === "admin" && nav("/admin", "Administration")}
        {(role === "candidate" || role === "company") && nav("/kyc", "Documents")}
        {(role === "candidate" || role === "company") && nav("/account", "Mon compte")}
        {role && <Link to="/notifications" className="bell">🔔{unread > 0 && <b>{unread}</b>}</Link>}
        {role ? <button className="btn-outline" onClick={logout}>Déconnexion</button>
              : <Link to="/login" className="btn-outline">Connexion</Link>}
      </nav>
    </header>
  );
}

const Private = ({ role, children }) => {
  const current = getRole();
  if (!current) return <Navigate to="/login" replace />;
  if (role && current !== role) return <Navigate to={HOME_BY_ROLE[current] || "/offers"} replace />;
  return children;
};

export default function App() {
  const role = getRole();
  return (
    <>
      <Navbar />
      <main className="container">
        {(role === "candidate" || role === "company") && <TrialBanner />}
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/offers" element={<Private><Offers /></Private>} />
          <Route path="/notifications" element={<Private><Notifications /></Private>} />
          <Route path="/kyc" element={<Private><Kyc /></Private>} />
          <Route path="/account" element={<Private><Account /></Private>} />
          <Route path="/candidate" element={<Private role="candidate"><CandidateSpace /></Private>} />
          <Route path="/company" element={<Private role="company"><CompanySpace /></Private>} />
          <Route path="/admin" element={<Private role="admin"><Admin /></Private>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      {(role === "candidate" || role === "company") && <Chatbot />}
      <footer className="footer">© 2026 TalentConnect · Plateforme intelligente de recrutement, d'emploi et de stages</footer>
    </>
  );
}
