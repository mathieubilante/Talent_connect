import { Navigate, Route, Routes } from "react-router-dom";
import { apiMisconfigured, getRole } from "./api";
import Chatbot from "./components/Chatbot.jsx";
import IdleGuard from "./components/IdleGuard.jsx";
import { OfflineBanner } from "./components/PwaTools.jsx";
import Navbar from "./components/Navbar.jsx";
import SiteFooter from "./components/SiteFooter.jsx";
import TrialBanner from "./components/TrialBanner.jsx";
import Account from "./pages/Account.jsx";
import Admin from "./pages/Admin.jsx";
import Billing from "./pages/Billing.jsx";
import Receipt from "./pages/Receipt.jsx";
import Security from "./pages/Security.jsx";
import CandidateSpace from "./pages/CandidateSpace.jsx";
import Companies from "./pages/Companies.jsx";
import CompanyProfile from "./pages/CompanyProfile.jsx";
import CompanySpace from "./pages/CompanySpace.jsx";
import Home from "./pages/Home.jsx";
import Kyc from "./pages/Kyc.jsx";
import Login from "./pages/Login.jsx";
import Notifications from "./pages/Notifications.jsx";
import OfferDetail from "./pages/OfferDetail.jsx";
import Offers from "./pages/Offers.jsx";

const HOME_BY_ROLE = { candidate: "/candidate", company: "/company", admin: "/admin" };

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
      <OfflineBanner />
      {role && <IdleGuard />}
      {apiMisconfigured && (
        <div className="api-warning">
          ⚠️ Le serveur (API) n'est pas configuré pour ce site : l'inscription et la connexion ne peuvent pas fonctionner.
          Ajoutez la variable <b>VITE_API_URL</b> dans Vercel puis redéployez (voir DEPLOIEMENT.md).
        </div>
      )}
      <main className="container">
        {(role === "candidate" || role === "company") && <TrialBanner />}
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/offers" element={<Offers />} />
          <Route path="/offers/:id" element={<OfferDetail />} />
          <Route path="/companies" element={<Companies />} />
          <Route path="/companies/:id" element={<CompanyProfile />} />
          <Route path="/notifications" element={<Private><Notifications /></Private>} />
          <Route path="/billing" element={<Private><Billing /></Private>} />
          <Route path="/billing/receipt/:id" element={<Private><Receipt /></Private>} />
          <Route path="/security" element={<Private><Security /></Private>} />
          <Route path="/kyc" element={<Private><Kyc /></Private>} />
          <Route path="/account" element={<Private><Account /></Private>} />
          <Route path="/candidate" element={<Private role="candidate"><CandidateSpace /></Private>} />
          <Route path="/company" element={<Private role="company"><CompanySpace /></Private>} />
          <Route path="/admin" element={<Private role="admin"><Admin /></Private>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      {role !== "admin" && <Chatbot />}
      <SiteFooter />
    </>
  );
}
