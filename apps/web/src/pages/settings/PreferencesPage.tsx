import { useState } from "react";

export default function PreferencesPage() {
  const [darkMode, setDarkMode] = useState(true);
  const [emailNotifications, setEmailNotifications] = useState(false);

  return (
    <div>
      <h2 style={{ marginTop: 0 }}>Preferences</h2>
      <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: 400 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <div style={{ fontWeight: 500 }}>Dark Mode</div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Use dark theme across the app</div>
          </div>
          <button
            type="button"
            onClick={() => setDarkMode((v) => !v)}
            style={{
              width: 44,
              height: 24,
              borderRadius: 12,
              border: "none",
              background: darkMode ? "var(--accent)" : "var(--border)",
              cursor: "pointer",
              position: "relative",
              transition: "background 0.2s",
            }}
          >
            <span style={{
              position: "absolute",
              top: 2,
              left: darkMode ? 22 : 2,
              width: 20,
              height: 20,
              borderRadius: "50%",
              background: "#fff",
              transition: "left 0.2s",
            }} />
          </button>
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <div style={{ fontWeight: 500 }}>Email Notifications</div>
            <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Receive updates on analysis completion</div>
          </div>
          <button
            type="button"
            onClick={() => setEmailNotifications((v) => !v)}
            style={{
              width: 44,
              height: 24,
              borderRadius: 12,
              border: "none",
              background: emailNotifications ? "var(--accent)" : "var(--border)",
              cursor: "pointer",
              position: "relative",
              transition: "background 0.2s",
            }}
          >
            <span style={{
              position: "absolute",
              top: 2,
              left: emailNotifications ? 22 : 2,
              width: 20,
              height: 20,
              borderRadius: "50%",
              background: "#fff",
              transition: "left 0.2s",
            }} />
          </button>
        </div>
      </div>
    </div>
  );
}
