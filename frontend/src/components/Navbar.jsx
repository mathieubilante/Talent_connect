import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import api, { getRole, serverLogout } from "../api";
import { InstallButton } from "./PwaTools.jsx";
import ThemeToggle from "./ThemeSwitcher.jsx";
import Avatar from "./Avatar.jsx";
import LangSwitch from "./LangSwitch.jsx";
import { t } from "../i18n.js";

const MENU = {
  candidate: [["/candidate", "menu_space"], ["/billing", "menu_subscription"], ["/kyc", "menu_documents"], ["/security", "menu_security"], ["/account", "menu_account"], ["/notifications", "menu_notifications"]],
  company: [["/company", "menu_company_space"], ["/import", "menu_import"], ["/billing", "menu_subscription"], ["/kyc", "menu_documents"], ["/security", "menu_security"], ["/account", "menu_account"], ["/notifications", "menu_notifications"]],
  admin: [["/admin", "menu_admin"], ["/notifications", "menu_notifications"]],
};

export default function Navbar() {
  const role = getRole();
  const navigate = useNavigate();
  const { pathname, search } = useLocation();
  const [unread, setUnread] = useState(0);
  const [menu, setMenu] = useState(false);
  const [me, setMe] = useState(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    setMenu(false);
    setOpen(false);
    if (!role) return;
    api.get("/notifications").then((r) => setUnread(r.data.unread)).catch(() => {});
    api.get("/profile/me").then((r) => setMe(r.data)).catch(() => {});
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
          <Link to="/offers?offer_type=emploi" className={cls("/offers?offer_type=emploi")}>{t("nav_jobs")}</Link>
          <Link to="/offers?offer_type=stage" className={cls("/offers?offer_type=stage")}>{t("nav_internships")}</Link>
          <Link to="/companies" className={cls("/companies")}>{t("nav_companies")}</Link>
          {role === "company" && <Link to="/company" className="btn small-btn">{t("nav_publish")}</Link>}
          {!role && <Link to="/login?mode=register&role=company" className="recruit">{t("nav_recruiters")}</Link>}
        </nav>
        <div className={`actions ${open ? "open" : ""}`}>
          <LangSwitch />
          <InstallButton />
          <ThemeToggle />
          {!role && (
            <>
              <Link to="/login" className="btn-outline">{t("nav_login")}</Link>
              <Link to="/login?mode=register" className="btn">{t("nav_signup")}</Link>
            </>
          )}
          {role && (
            <>
              <Link to="/notifications" className="bell" title={t("menu_notifications")}>🔔{unread > 0 && <b>{unread}</b>}</Link>
              <div className="usermenu">
                {me && <span className="nav-name">{me.full_name}</span>}
                <button className="avatar-btn" onClick={() => setMenu(!menu)} aria-label={t("menu_account")} title={me?.full_name || t("menu_account")}>
                  <Avatar hasPhoto={!!me?.has_avatar} initials={me?.initials || "?"} size={38} />
                </button>
                {menu && (
                  <>
                    <div className="menu-back" onClick={() => setMenu(false)} />
                    <div className="dropdown">
                      {me && <div className="dd-head"><b>{me.full_name}</b><span>{me.email}</span></div>}
                      {(MENU[role] || []).map(([to, key]) => <Link key={to} to={to}>{t(key)}</Link>)}
                      <button onClick={logout}>{t("menu_logout")}</button>
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
