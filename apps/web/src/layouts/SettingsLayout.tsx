import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function SettingsLayout() {
  const { user } = useAuth();

  return (
    <div className="settings-shell">
      <aside className="settings-sidebar">
        <NavLink
          to="/settings/profile"
          className={({ isActive }) =>
            "sidebar-link" + (isActive ? " active" : "")
          }
        >
          Profile
        </NavLink>
        <NavLink
          to="/settings/company"
          className={({ isActive }) =>
            "sidebar-link" + (isActive ? " active" : "")
          }
        >
          Company
        </NavLink>
        <NavLink
          to="/settings/files"
          className={({ isActive }) =>
            "sidebar-link" + (isActive ? " active" : "")
          }
        >
          Uploaded files
        </NavLink>
        <NavLink
          to="/settings/preferences"
          className={({ isActive }) =>
            "sidebar-link" + (isActive ? " active" : "")
          }
        >
          Preferences
        </NavLink>
        {user?.role === "admin" && (
          <NavLink
            to="/settings/developer"
            className={({ isActive }) =>
              "sidebar-link" + (isActive ? " active" : "")
            }
          >
            Developer
          </NavLink>
        )}
      </aside>
      <div className="settings-content">
        <Outlet />
      </div>
    </div>
  );
}
