import { useAuth } from "../contexts/AuthContext";
import { Link } from "react-router-dom";

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Welcome back, {user?.name ?? "there"}!</h1>
      <div className="dashboard-grid">
        <div className="stat-card">
          <h3>Running Jobs</h3>
          <div className="stat-value">0</div>
        </div>
        <div className="stat-card">
          <h3>Completed Analyses</h3>
          <div className="stat-value">0</div>
        </div>
        <div className="stat-card">
          <h3>Status</h3>
          <div className="stat-value" style={{ fontSize: "1.25rem", color: "#4ade80" }}>Ready</div>
        </div>
      </div>
      <div className="empty-state">
        <p>No analyses yet. Upload your first dataset to get started.</p>
        <Link to="/upload">
          <button className="btn-primary" style={{ marginTop: "0.75rem" }}>
            Start Your First Analysis
          </button>
        </Link>
      </div>
    </div>
  );
}
