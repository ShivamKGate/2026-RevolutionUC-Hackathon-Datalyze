import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

type Props = {
  isOpen: boolean;
  onClose: () => void;
  onSwitchToSignup: () => void;
};

export default function LoginModal({
  isOpen,
  onClose,
  onSwitchToSignup,
}: Props) {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const user = await login(email, password, rememberMe);
      onClose();
      navigate(user.setup_complete ? "/dashboard" : "/setup");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Log In</h2>
          <button className="modal-close" onClick={onClose}>
            &times;
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {error && (
              <div
                className="status error"
                style={{
                  margin: 0,
                  padding: "0.6rem 0.75rem",
                  borderRadius: 6,
                }}
              >
                {error}
              </div>
            )}
            <div className="form-group">
              <label className="form-label" htmlFor="login-email">
                Email
              </label>
              <input
                id="login-email"
                type="email"
                className="form-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoFocus
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="login-password">
                Password
              </label>
              <input
                id="login-password"
                type="password"
                className="form-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <label
              className="form-group"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                cursor: "pointer",
              }}
            >
              <input
                id="login-remember"
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
              />
              <span className="form-label" style={{ margin: 0 }}>
                Remember me for 1 day
              </span>
            </label>
          </div>
          <div className="modal-footer">
            <button type="submit" disabled={loading}>
              {loading ? "Logging in..." : "Log In"}
            </button>
            <p className="modal-switch-text">
              Don&apos;t have an account?{" "}
              <button
                type="button"
                className="link-btn"
                onClick={onSwitchToSignup}
              >
                Sign up
              </button>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}
