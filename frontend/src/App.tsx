import { lazy, Suspense } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";
import Layout from "./components/Layout";
import LoginPage from "./pages/Login";
import NotificationToast from "./components/NotificationToast";

// 🚀 Core Loading Skeleton Shell to keep FCP / LCP instant
const PageLoader = () => (
  <div style={{ padding: '2rem', fontFamily: 'sans-serif', color: '#666' }}>
    Loading secure runtime module...
  </div>
);

// 📦 Split heavy pages into dynamic asynchronous chunks
const AlertsPage = lazy(() => import("./pages/Alerts"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Search = lazy(() => import("./pages/Search"));
const Status = lazy(() => import("./pages/Status"));
const OperationalDashboard = lazy(() => import("./pages/OperationalDashboard"));
const NeptuneConsole = lazy(() => import("./pages/NeptuneConsole"));

export default function App() {
  const location = useLocation();
  const isRetroRoute = ["/alerts", "/alerts-retro"].includes(location.pathname);

  return (
    <AuthProvider>
      <NotificationToast />
      <Suspense fallback={<PageLoader />}>
        {isRetroRoute ? (
          <Routes>
            <Route path="/alerts" element={<ProtectedRoute><AlertsPage /></ProtectedRoute>} />
            <Route path="/alerts-retro" element={<ProtectedRoute><AlertsPage /></ProtectedRoute>} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        ) : (
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/alerts" element={<ProtectedRoute><AlertsPage /></ProtectedRoute>} />
              <Route path="/alerts-retro" element={<ProtectedRoute><AlertsPage /></ProtectedRoute>} />
              <Route path="/search" element={<Search />} />
              <Route path="/status" element={<Status />} />
              <Route path="/ops" element={<ProtectedRoute><OperationalDashboard /></ProtectedRoute>} />
              <Route path="/console" element={<NeptuneConsole />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Layout>
        )}
      </Suspense>
    </AuthProvider>
  );
}
