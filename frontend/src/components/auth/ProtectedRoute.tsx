import { Navigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { status, isAuthenticated } = useAuth();

  if (status === "loading") {
    return (
      <div className="h-screen w-screen bg-black flex items-center justify-center font-mono text-phosphor-teal">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 border-2 border-t-transparent border-phosphor-teal rounded-full animate-spin" />
          <p className="text-xs uppercase tracking-widest animate-pulse">CRITICAL SECURE SESSION MATRIX INITIALIZING...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
