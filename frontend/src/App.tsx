import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import Layout from "./components/Layout";
import AlertsPage from "./pages/Alerts";
import Dashboard from "./pages/Dashboard";
import Search from "./pages/Search";
import Status from "./pages/Status";
import OperationalDashboard from "./pages/OperationalDashboard";
import NeptuneConsole from "./pages/NeptuneConsole";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";
import LoginPage from "./pages/Login";
import NotificationToast from "./components/NotificationToast";

export default function App() {
  const location = useLocation();
  const isRetroRoute = ["/alerts", "/alerts-retro"].includes(location.pathname);

  return (
    <AuthProvider>
      <NotificationToast />
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
    </AuthProvider>
  );
}
