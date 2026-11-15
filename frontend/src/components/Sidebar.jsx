import { Link, useLocation } from "react-router-dom";

export default function Sidebar({ isOpen, onClose, role }) {
  const location = useLocation();
  const isActive = (path) => location.pathname === path;

  // Adapt items based on role
  const isCandidate = role === "candidate";
  const isCompany = role === "company";
  const isAdmin = role === "admin";

  return (
    <>
      <div className={`sidebar ${isOpen ? "open" : "closed"}`}>
        <div className="sidebar-header">
          <Link to="/" className="sidebar-brand">
            <img src="/logo.svg" alt="Logo" /> MachPro
          </Link>
          <button className="sidebar-close" onClick={onClose}>✕</button>
        </div>
        <div className="sidebar-content">
          <ul className="sidebar-list">
            {isCandidate && (
              <>
                <li className="sidebar-item">
                  <Link to="/candidate" className={`sidebar-link ${isActive("/candidate") ? "active" : ""}`}>
                    📊 Mon Espace
                  </Link>
                </li>
                <li className="sidebar-item">
                  <Link to="/offers" className={`sidebar-link ${isActive("/offers") ? "active" : ""}`}>
                    💼 Offres d'emploi & stage
                  </Link>
                </li>
                <li className="sidebar-item">
                  <Link to="/kyc" className={`sidebar-link ${isActive("/kyc") ? "active" : ""}`}>
                    📄 Mes Documents (KYC)
                  </Link>
                </li>
                <li className="sidebar-item">
                  <Link to="/notifications" className={`sidebar-link ${isActive("/notifications") ? "active" : ""}`}>
                    🔔 Notifications
                  </Link>
                </li>
              </>
            )}

            {isCompany && (
              <>
                <li className="sidebar-item">
                  <Link to="/company" className={`sidebar-link ${isActive("/company") ? "active" : ""}`}>
                    🏢 Espace Entreprise
                  </Link>
                </li>
                <li className="sidebar-item">
                  <Link to="/offers" className={`sidebar-link ${isActive("/offers") ? "active" : ""}`}>
                    📋 Nos Offres Publiées
                  </Link>
                </li>
                <li className="sidebar-item">
                  <Link to="/kyc" className={`sidebar-link ${isActive("/kyc") ? "active" : ""}`}>
                    📜 Justificatifs Entreprise
                  </Link>
                </li>
                <li className="sidebar-item">
                  <Link to="/billing" className={`sidebar-link ${isActive("/billing") ? "active" : ""}`}>
                    💳 Abonnement & Factures
                  </Link>
                </li>
              </>
            )}

            {isAdmin && (
              <>
                <li className="sidebar-item">
                  <Link to="/admin" className={`sidebar-link ${isActive("/admin") ? "active" : ""}`}>
                    ⚙️ Administration globale
                  </Link>
                </li>
                <li className="sidebar-item">
                  <Link to="/security" className={`sidebar-link ${isActive("/security") ? "active" : ""}`}>
                    🛡️ Centre de Sécurité
                  </Link>
                </li>
              </>
            )}

            {/* Liens communs */}
            <li className="sidebar-item">
              <Link to="/security" className={`sidebar-link ${isActive("/security") ? "active" : ""}`}>
                🔒 Sécurité & Connexions
              </Link>
            </li>
            <li className="sidebar-item">
              <Link to="/account" className={`sidebar-link ${isActive("/account") ? "active" : ""}`}>
                👤 Mon Compte
              </Link>
            </li>
          </ul>
        </div>
        <div className="sidebar-footer">
          <Link to="/account" className="sidebar-btn">Réglages du compte</Link>
        </div>
      </div>
      <div className={`sidebar-overlay ${isOpen ? "open" : ""}`} onClick={onClose} />
    </>
  );
}
