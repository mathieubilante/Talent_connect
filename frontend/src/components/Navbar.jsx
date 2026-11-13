import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import api, { getRole, serverLogout } from "../api";
import { InstallButton } from "./PwaTools.jsx";
import ThemeSwitcher from "./ThemeSwitcher.jsx";

const MENU = {
  candidate: [["/candidate", "Mon espace"], ["/billing", "Abonnement"], ["/kyc", "Mes documents"], ["/security", "Sécurité"], ["/account", "Mon compte"], ["/notifications", "Notifications"]],
  company: [["/company", "Espace entreprise"], ["/billing", "Abonnement"], ["/kyc", "Mes documents"], ["/security", "Sécurité"], ["/account", "Mon compte"], ["/notifications", "Notifications"]],
  admin: [["/admin", "Administration"], ["/notifications", "Notifications"]],
};

export default function Navbar() {
  const role = getRole();
  const navigate = useNavigate();
  const { pathname, search } = useLocation();
  const [unread, setUnread] = useState(0);
  const [menu, setMenu] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    setMenu(false);
    setOpen(false);
    if (!role) return;
    api.get("/notifications").then((r) => setUnread(r.data.unread)).catch(() => {});
  }, [pathname, role]);

  const logout = async () => { await serverLogout(); setMenu(false); navigate("/"); };
  const current = pathname + search;
  const cls = (to) => (current === to || (to === "/companies" && pathname.startsWith("/companies")) ? "active" : "");

  return (
    <header className="topbar">
      <div className="topbar-in">
        <Link to="/" className="brand"><img src="/favicon.svg" alt="" /> Talent<span>Connect</span></Link>
        <button className="burger" onClick={() => setOpen(!open)} aria-label="Menu">☰</button>
        <nav className={`links ${open ? "open" : ""}`}>
          <Link to="/offers?offer_type=emploi" className={cls("/offers?offer_type=emploi")}>Emplois</Link>
          <Link to="/offers?offer_type=stage" className={cls("/offers?offer_type=stage")}>Stages</Link>
          <Link to="/companies" className={cls("/companies")}>Entreprises</Link>
          {role === "company" && <Link to="/company" className="btn small-btn">+ Publier une offre</Link>}
          {!role && <Link to="/login?mode=register&role=company" className="recruit">Espace recruteurs</Link>}
        </nav>
        <div className={`actions ${open ? "open" : ""}`}>
          <InstallButton />
          <ThemeSwitcher />
          {!role && (
            <>
              <Link to="/login" className="btn-outline">Connexion</Link>
              <Link to="/login?mode=register" className="btn">S'inscrire</Link>
            </>
          )}
          {role && (
            <>
              <Link to="/notifications" className="bell" title="Notifications">🔔{unread > 0 && <b>{unread}</b>}</Link>
              <div className="usermenu">
                <button className="btn-outline" onClick={() => setMenu(!menu)}>👤 Mon espace ▾</button>
                {menu && (
                  <>
                    <div className="menu-back" onClick={() => setMenu(false)} />
                    <div className="dropdown">
                      {(MENU[role] || []).map(([to, label]) => <Link key={to} to={to}>{label}</Link>)}
                      <button onClick={logout}>Déconnexion</button>
                    </div>
                  </>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
