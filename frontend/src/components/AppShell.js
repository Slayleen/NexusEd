import { useNavigate, useLocation, Link } from "react-router-dom";
import { useAuth } from "@/AuthContext";
import {
  SquaresFour, Sparkle, Rocket, Trophy, ChatCircleDots,
  UsersThree, Compass, SignOut, GraduationCap, Handshake,
} from "@phosphor-icons/react";

const NAV = [
  { to: "/app", label: "Dashboard", icon: SquaresFour },
  { to: "/app/match", label: "AI Match", icon: Sparkle },
  { to: "/app/projects", label: "Projects", icon: Rocket },
  { to: "/app/discover", label: "Discover", icon: Compass },
  { to: "/app/connections", label: "Connections", icon: Handshake },
  { to: "/app/opportunities", label: "Opportunities", icon: Trophy },
  { to: "/app/forum", label: "Forum", icon: UsersThree },
  { to: "/app/messages", label: "Messages", icon: ChatCircleDots },
];

export default function AppShell({ children }) {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();

  const handleLogout = async () => {
    await logout();
    nav("/");
  };

  return (
    <div className="min-h-screen bg-[#FDFBF7] flex">
      {/* Sidebar */}
      <aside className="hidden md:flex flex-col w-64 border-r-2 border-[#0A0A0A] bg-white sticky top-0 h-screen p-5">
        <Link to="/app" className="flex items-center gap-2 mb-8" data-testid="sidebar-logo">
          <div className="w-9 h-9 bg-[#FF7B54] border-2 border-[#0A0A0A] rounded-lg flex items-center justify-center">
            <GraduationCap size={20} weight="bold" />
          </div>
          <span className="font-display text-xl font-black tracking-tight">Nexus</span>
        </Link>
        <nav className="flex flex-col gap-1 flex-1">
          {NAV.map((n) => {
            const active = loc.pathname === n.to;
            const Icon = n.icon;
            return (
              <Link
                key={n.to}
                to={n.to}
                data-testid={`nav-${n.label.toLowerCase().replace(" ", "-")}`}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl font-bold border-2 transition-all ${
                  active
                    ? "bg-[#FFD166] border-[#0A0A0A] shadow-[3px_3px_0px_0px_rgba(10,10,10,1)]"
                    : "border-transparent hover:border-[#0A0A0A] hover:bg-[#FDFBF7]"
                }`}
              >
                <Icon size={20} weight="bold" />
                <span className="text-sm">{n.label}</span>
              </Link>
            );
          })}
        </nav>
        <Link to="/app/profile" data-testid="nav-profile" className="flex items-center gap-3 p-2 rounded-xl border-2 border-[#0A0A0A] bg-[#FDFBF7] mb-2 nb-card-hover">
          <img src={user.avatar} alt="" className="w-9 h-9 rounded-lg border-2 border-[#0A0A0A] bg-white" />
          <div className="overflow-hidden">
            <div className="text-sm font-bold truncate">{user.name}</div>
            <div className="text-xs text-[#4A4A4A] truncate">{user.grade || "Student"}</div>
          </div>
        </Link>
        <button onClick={handleLogout} data-testid="logout-btn" className="flex items-center gap-2 px-3 py-2 text-sm font-bold text-[#4A4A4A] hover:text-[#0A0A0A]">
          <SignOut size={18} weight="bold" /> Log out
        </button>
      </aside>

      {/* Mobile top bar */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="md:hidden flex items-center justify-between px-4 py-3 border-b-2 border-[#0A0A0A] bg-[#FDFBF7] sticky top-0 z-40">
          <Link to="/app" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-[#FF7B54] border-2 border-[#0A0A0A] rounded-lg flex items-center justify-center">
              <GraduationCap size={18} weight="bold" />
            </div>
            <span className="font-display text-lg font-black">Nexus</span>
          </Link>
          <button onClick={handleLogout} className="text-sm font-bold"><SignOut size={20} weight="bold" /></button>
        </header>
        <main className="flex-1 min-w-0">{children}</main>
        {/* Mobile bottom nav */}
        <nav className="md:hidden sticky bottom-0 flex justify-around items-center border-t-2 border-[#0A0A0A] bg-white py-2 z-40">
          {NAV.slice(0, 5).map((n) => {
            const Icon = n.icon;
            const active = loc.pathname === n.to;
            return (
              <Link key={n.to} to={n.to} className={`p-2 rounded-lg ${active ? "bg-[#FFD166] border-2 border-[#0A0A0A]" : ""}`}>
                <Icon size={22} weight="bold" />
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
