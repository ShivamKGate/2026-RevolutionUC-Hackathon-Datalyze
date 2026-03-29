import { useState } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function AppLayout() {
  const { user, logout } = useAuth();
  const [avatarOpen, setAvatarOpen] = useState(false);

  return (
    <div className="app-shell">
      <nav className="navbar">
        <div className="navbar-brand">
          <Link to="/" className="navbar-logo">
            Datalyze
          </Link>
        </div>
        <div className="nav-links">
          <Link to="/dashboard" className="nav-btn nav-btn-ghost">
            Dashboard
          </Link>
          {user && (
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
                    onClick={() => {
                      setAvatarOpen(false);
                      void logout();
                    }}
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </nav>
      <div className="page-container">
        <aside className="sidebar">
          <NavLink
            to="/dashboard"
            className={({ isActive }) =>
              "sidebar-link" + (isActive ? " active" : "")
            }
          >
            Dashboard
          </NavLink>
          <NavLink
            to="/upload"
            className={({ isActive }) =>
              "sidebar-link" + (isActive ? " active" : "")
            }
          >
            Upload
          </NavLink>
          <NavLink
            to="/pipeline"
            className={({ isActive }) =>
              "sidebar-link" + (isActive ? " active" : "")
            }
          >
            Pipeline
          </NavLink>
          <NavLink
            to="/agents"
            className={({ isActive }) =>
              "sidebar-link" + (isActive ? " active" : "")
            }
          >
            Agents
          </NavLink>
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              "sidebar-link" + (isActive ? " active" : "")
            }
          >
            Settings
          </NavLink>
          {user?.role === "admin" && (
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                "sidebar-link" + (isActive ? " active" : "")
              }
            >
              Admin
            </NavLink>
          )}
        </aside>
        <main className="app-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
