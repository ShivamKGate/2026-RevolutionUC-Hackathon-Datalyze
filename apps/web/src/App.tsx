import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import PublicLayout from "./layouts/PublicLayout";
import AppLayout from "./layouts/AppLayout";
import SettingsLayout from "./layouts/SettingsLayout";
import RequireAuth from "./components/auth/RequireAuth";
import HomePage from "./pages/HomePage";
import SetupPage from "./pages/SetupPage";
import DashboardPage from "./pages/DashboardPage";
import UploadPage from "./pages/UploadPage";
import PipelinePage from "./pages/PipelinePage";
import AgentsPage from "./pages/AgentsPage";
import DeveloperPage from "./pages/DeveloperPage";
import NotFoundPage from "./pages/NotFoundPage";
import ProfilePage from "./pages/settings/ProfilePage";
import CompanyPage from "./pages/settings/CompanyPage";
import PreferencesPage from "./pages/settings/PreferencesPage";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route element={<PublicLayout />}>
          <Route path="/" element={<HomePage />} />
        </Route>
        <Route element={<RequireAuth />}>
          <Route path="/setup" element={<SetupPage />} />
          <Route element={<AppLayout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/pipeline" element={<PipelinePage />} />
            <Route path="/agents" element={<AgentsPage />} />
            <Route path="/settings">
              <Route index element={<Navigate to="profile" replace />} />
              <Route element={<SettingsLayout />}>
                <Route path="profile" element={<ProfilePage />} />
                <Route path="company" element={<CompanyPage />} />
                <Route path="preferences" element={<PreferencesPage />} />
                <Route path="developer" element={<DeveloperPage />} />
              </Route>
            </Route>
          </Route>
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </AuthProvider>
  );
}
