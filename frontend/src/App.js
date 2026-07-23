import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/AuthContext";
import { Toaster } from "sonner";
import AppShell from "@/components/AppShell";
import Landing from "@/pages/Landing";
import Auth from "@/pages/Auth";
import Dashboard from "@/pages/Dashboard";
import Match from "@/pages/Match";
import Projects from "@/pages/Projects";
import Opportunities from "@/pages/Opportunities";
import Messages from "@/pages/Messages";
import Forum from "@/pages/Forum";
import Profile from "@/pages/Profile";
import Discover from "@/pages/Discover";
import Connections from "@/pages/Connections";

function Loader() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#FDFBF7]">
      <div className="font-display text-2xl font-black animate-pulse">Loading Nexus…</div>
    </div>
  );
}

function Protected({ children }) {
  const { user, ready } = useAuth();
  if (!ready) return <Loader />;
  if (!user) return <Navigate to="/" replace />;
  return <AppShell>{children}</AppShell>;
}

function PublicOnly({ children }) {
  const { user, ready } = useAuth();
  if (!ready) return <Loader />;
  if (user) return <Navigate to="/app" replace />;
  return children;
}

function App() {
  return (
    <AuthProvider>
      <Toaster position="top-right" richColors />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<PublicOnly><Landing /></PublicOnly>} />
          <Route path="/login" element={<PublicOnly><Auth mode="login" /></PublicOnly>} />
          <Route path="/signup" element={<PublicOnly><Auth mode="signup" /></PublicOnly>} />
          <Route path="/app" element={<Protected><Dashboard /></Protected>} />
          <Route path="/app/match" element={<Protected><Match /></Protected>} />
          <Route path="/app/projects" element={<Protected><Projects /></Protected>} />
          <Route path="/app/opportunities" element={<Protected><Opportunities /></Protected>} />
          <Route path="/app/discover" element={<Protected><Discover /></Protected>} />
          <Route path="/app/connections" element={<Protected><Connections /></Protected>} />
          <Route path="/app/messages" element={<Protected><Messages /></Protected>} />
          <Route path="/app/forum" element={<Protected><Forum /></Protected>} />
          <Route path="/app/profile" element={<Protected><Profile /></Protected>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
