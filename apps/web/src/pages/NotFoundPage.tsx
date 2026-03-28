import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="empty-state" style={{ paddingTop: "8rem" }}>
      <h1 style={{ fontSize: "3rem", marginBottom: "0.5rem" }}>404</h1>
      <p style={{ fontSize: "1.1rem", marginBottom: "1.5rem" }}>Page Not Found</p>
      <Link to="/">
        <button className="btn-primary">Back to Home</button>
      </Link>
    </div>
  );
}
