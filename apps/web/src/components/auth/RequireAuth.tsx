import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

export default function RequireAuth() {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="spinner-page spinner-page--full">
        <div className="spinner" />
      </div>
    );
  }

  if (!user) return <Navigate to="/" replace />;
  if (!user.setup_complete && location.pathname !== "/setup")
    return <Navigate to="/setup" replace />;
  if (user.setup_complete && location.pathname === "/setup")
    return <Navigate to="/dashboard" replace />;

  return <Outlet />;
}
