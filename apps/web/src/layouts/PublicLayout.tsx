import { useState } from "react";
import { Link, Outlet } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import LoginModal from "../components/auth/LoginModal";
import SignupModal from "../components/auth/SignupModal";

export default function PublicLayout() {
  const { user, logout } = useAuth();
  const [loginOpen, setLoginOpen] = useState(false);
  const [signupOpen, setSignupOpen] = useState(false);
  const [avatarOpen, setAvatarOpen] = useState(false);

  function onLoginOpen() {
    setSignupOpen(false);
    setLoginOpen(true);
  }

  function onSignupOpen() {
    setLoginOpen(false);
    setSignupOpen(true);
  }

  return (
    <>
      <nav className="navbar">
        <div className="navbar-brand">
          <Link to="/" className="navbar-logo">Datalyze</Link>
          <span className="navbar-tagline">Raw Data ↓, AI-Driven Strategies ↑</span>
        </div>
        <div className="nav-links">
          {user ? (
            <>
              <Link to="/dashboard" className="nav-btn nav-btn-ghost">Dashboard</Link>
              <div className="avatar-menu-wrap">
                <button
                  className="avatar-btn"
                  onClick={() => setAvatarOpen((o) => !o)}
                  title={user.name}
                >
                  {user.name.charAt(0).toUpperCase()}
                </button>
                {avatarOpen && (
                  <div className="avatar-dropdown">
                    <Link
                      to="/settings/profile"
                      className="avatar-dropdown-item"
                      onClick={() => setAvatarOpen(false)}
                    >
                      Settings
                    </Link>
                    <button
                      className="avatar-dropdown-item avatar-dropdown-btn"
                      onClick={() => { setAvatarOpen(false); void logout(); }}
                    >
                      Logout
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <button className="nav-btn nav-btn-ghost" onClick={onLoginOpen}>Log In</button>
              <button className="nav-btn nav-btn-primary" onClick={onSignupOpen}>Sign Up</button>
            </>
          )}
        </div>
      </nav>

      <Outlet context={{ onLoginOpen, onSignupOpen }} />

      <LoginModal
        isOpen={loginOpen}
        onClose={() => setLoginOpen(false)}
        onSwitchToSignup={() => { setLoginOpen(false); setSignupOpen(true); }}
      />
      <SignupModal
        isOpen={signupOpen}
        onClose={() => setSignupOpen(false)}
        onSwitchToLogin={() => { setSignupOpen(false); setLoginOpen(true); }}
      />
    </>
  );
}
