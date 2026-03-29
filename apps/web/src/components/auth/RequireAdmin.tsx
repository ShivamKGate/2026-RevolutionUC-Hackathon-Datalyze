import { type ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

export default function RequireAdmin({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="spinner-page spinner-page--full">
        <div className="spinner" />
      </div>
    );
  }

  if (!user || user.role !== "admin") {
    return <Navigate to="/settings/profile" replace />;
  }

  return <>{children}</>;
}
