import { lazy, Suspense, useEffect } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { apiMisconfigured, getRole } from "./api";
import Chatbot from "./components/Chatbot.jsx";
import IdleGuard from "./components/IdleGuard.jsx";
import { OfflineBanner } from "./components/PwaTools.jsx";
import Navbar from "./components/Navbar.jsx";
import SiteFooter from "./components/SiteFooter.jsx";
import TrialBanner from "./components/TrialBanner.jsx";
import WelcomeModal from "./components/WelcomeModal.jsx";
import CookieBanner from "./components/CookieBanner.jsx";
import Analytics from "./components/Analytics.jsx";
import { PrivacyPage, TermsPage } from "./pages/Legal.jsx";
import NotFound from "./pages/NotFound.jsx";
import api from "./api";

const Account = lazy(() => import("./pages/Account.jsx"));
const Admin = lazy(() => import("./pages/Admin.jsx"));
const Billing = lazy(() => import("./pages/Billing.jsx"));
const Receipt = lazy(() => import("./pages/Receipt.jsx"));
const Security = lazy(() => import("./pages/Security.jsx"));
const CandidateSpace = lazy(() => import("./pages/CandidateSpace.jsx"));
const Companies = lazy(() => import("./pages/Companies.jsx"));
const CompanyProfile = lazy(() => import("./pages/CompanyProfile.jsx"));
const CompanySpace = lazy(() => import("./pages/CompanySpace.jsx"));
const Kyc = lazy(() => import("./pages/Kyc.jsx"));
const CompleteProfile = lazy(() => import("./pages/CompleteProfile.jsx"));
const ImportOffers = lazy(() => import("./pages/ImportOffers.jsx"));
const PasswordReset = lazy(() => import("./pages/PasswordReset.jsx"));
const Notifications = lazy(() => import("./pages/Notifications.jsx"));
const OfferDetail = lazy(() => import("./pages/OfferDetail.jsx"));
const Offers = lazy(() => import("./pages/Offers.jsx"));
const Login = lazy(() => import("./pages/Login.jsx"));
const Home = lazy(() => import("./pages/Home.jsx"));
const Landing = lazy(() => import("./pages/Landing.jsx"));

const HOME_BY_ROLE = { candidate: "/candidate", company: "/company", admin: "/admin" };

const Private = ({ role, children }) => {
  const current = getRole();
  if (!current) return <Navigate to="/login" replace />;
  if (role && current !== role) return <Navigate to={HOME_BY_ROLE[current] || "/offers"} replace />;
  return children;
};

export default function App() {
  const role = getRole();
  const location = useLocation();
  const navigate = useNavigate();
  useEffect(() => {
    // Candidat connecté avec un profil incomplet : on l'emmène compléter son profil (Google compris)
    if (role !== "candidate" || location.pathname === "/complete-profile") return;
    api.get("/profile/me").then((r) => { if (!r.data.profile_complete) navigate("/complete-profile", { replace: true }); })
      .catch(() => {});
  }, [role, location.pathname]);
  return (
    <>
      <a href="#contenu" className="skip-link">Aller au contenu</a>
      <Navbar />
      <OfflineBanner />
      {role && <IdleGuard />}
      {apiMisconfigured && (
        <div className="api-warning">
          ⚠️ Le serveur (API) n'est pas configuré pour ce site : l'inscription et la connexion ne peuvent pas fonctionner.
          Ajoutez la variable <b>VITE_API_URL</b> dans Vercel puis redéployez (voir DEPLOIEMENT.md).
        </div>
      )}
      <main className="container" id="contenu">
        {(role === "candidate" || role === "company") && <TrialBanner />}
        <Suspense fallback={<p className="muted" style={{ padding: 24 }}>Chargement…</p>}>
        <Routes>
          <Route path="/" element={role ? <Home /> : <Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/mot-de-passe-oublie" element={<PasswordReset />} />
          <Route path="/offers" element={<Offers />} />
          <Route path="/offers/:id" element={<OfferDetail />} />
          <Route path="/companies" element={<Companies />} />
          <Route path="/companies/:id" element={<CompanyProfile />} />
          <Route path="/notifications" element={<Private><Notifications /></Private>} />
          <Route path="/billing" element={<Private><Billing /></Private>} />
          <Route path="/billing/receipt/:id" element={<Private><Receipt /></Private>} />
          <Route path="/security" element={<Private><Security /></Private>} />
          <Route path="/import" element={<Private role="company"><ImportOffers /></Private>} />
          <Route path="/complete-profile" element={<Private role="candidate"><CompleteProfile /></Private>} />
          <Route path="/kyc" element={<Private><Kyc /></Private>} />
          <Route path="/account" element={<Private><Account /></Private>} />
          <Route path="/candidate" element={<Private role="candidate"><CandidateSpace /></Private>} />
          <Route path="/company" element={<Private role="company"><CompanySpace /></Private>} />
          <Route path="/admin" element={<Private role="admin"><Admin /></Private>} />
          <Route path="/confidentialite" element={<PrivacyPage />} />
          <Route path="/conditions" element={<TermsPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
        </Suspense>
      </main>
      {!role && <WelcomeModal />}
      <CookieBanner />
      <Analytics />
      {role !== "admin" && <Chatbot />}
      <SiteFooter />
    </>
  );
}
