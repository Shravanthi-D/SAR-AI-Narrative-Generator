import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router";
import { Navigation } from "./components/navigation";
import { LoginScreen } from "./screens/login-screen";
import { DashboardScreen } from "./screens/dashboard-screen";
import { InvestigationScreen } from "./screens/investigation-screen";
import { EditorScreen } from "./screens/editor-screen";
import { AuditScreen } from "./screens/audit-screen";
import { BlockchainScreen } from "./screens/blockchain-screen";

// ─── Inner app that has access to React Router hooks ─────────────────────────

function AppInner() {
  const navigate = useNavigate();
  const [analystId, setAnalystId] = useState<string>(() => localStorage.getItem("analystId") ?? "");
  const [currentReportId, setCurrentReportId] = useState<string | null>(null);

  const isAuthenticated = analystId !== "";

  useEffect(() => {
    const stored = localStorage.getItem("analystId");
    if (stored && stored !== analystId) {
      setAnalystId(stored);
    }
  }, []);

  const handleLogin = (id: string) => {
    localStorage.setItem("analystId", id);
    setAnalystId(id);
    navigate("/dashboard");
  };

  const handleLogout = () => {
    localStorage.removeItem("analystId");
    setAnalystId("");
    setCurrentReportId(null);
    navigate("/login");
  };

  const handleNavigate = (screen: string) => {
    const routeMap: Record<string, string> = {
      dashboard: "/dashboard",
      investigation: "/cases",
      editor: "/editor",
      audit: "/audit",
      blockchain: "/blockchain",
      settings: "/settings",
    };
    navigate(routeMap[screen] ?? "/dashboard");
  };

  const handleReportReady = (reportId: string) => {
    setCurrentReportId(reportId);
    navigate("/editor");
  };

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<LoginScreen onLogin={handleLogin} />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <div
      className="min-h-screen flex"
      style={{ backgroundColor: "#0B1F3A", fontFamily: "IBM Plex Sans, Inter, sans-serif" }}
    >
      <Navigation
        activeScreen={locationToScreen()}
        onNavigate={handleNavigate}
        onLogout={handleLogout}
        analystId={analystId}
      />
      <div className="flex-1 h-screen overflow-hidden">
        <div className="h-full overflow-y-auto">
          <Routes>
            <Route path="/dashboard"  element={<DashboardScreen onNavigate={handleNavigate} />} />
            <Route path="/cases"      element={<InvestigationScreen onReportReady={handleReportReady} analystId={analystId} />} />
            <Route path="/editor"     element={<EditorScreen reportId={currentReportId} analystId={analystId} onNavigate={handleNavigate} />} />
            <Route path="/audit"      element={<AuditScreen />} />
            <Route path="/blockchain" element={<BlockchainScreen reportId={currentReportId} />} />
            <Route path="/settings"   element={
              <div className="p-6">
                <h1 className="text-white mb-1" style={{ fontSize: "22px", fontWeight: 500 }}>Settings</h1>
                <p className="text-[#9CA3AF]" style={{ fontSize: "13px" }}>System configuration and preferences</p>
              </div>
            } />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}

// Map current pathname to the nav activeScreen value
function locationToScreen(): string {
  const path = window.location.pathname;
  if (path.startsWith("/dashboard"))  return "dashboard";
  if (path.startsWith("/cases"))      return "investigation";
  if (path.startsWith("/editor"))     return "editor";
  if (path.startsWith("/audit"))      return "audit";
  if (path.startsWith("/blockchain")) return "blockchain";
  if (path.startsWith("/settings"))   return "settings";
  return "dashboard";
}

// ─── Root ─────────────────────────────────────────────────────────────────────

export default function App() {
  return (
    <BrowserRouter>
      <AppInner />
    </BrowserRouter>
  );
}
