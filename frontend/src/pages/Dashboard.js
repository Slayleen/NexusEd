import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/api";
import { useAuth } from "@/AuthContext";
import { PageHead, Avatar, Reputation } from "@/components/common";
import { AreaFilter } from "@/components/AreaSelect";
import { parseLocation, citiesForState } from "@/constants/locations";
import { Sparkle, Rocket, Trophy, Handshake, ArrowRight, CalendarBlank, MapPin } from "@phosphor-icons/react";

const OPEN_TO_ALL = ["Remote", "Nationwide", "Online"];

export default function Dashboard() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [data, setData] = useState(null);
  const [recs, setRecs] = useState([]);
  const [area, setArea] = useState({ state: "all", city: "all" });

  useEffect(() => {
    api.get("/dashboard").then((r) => setData(r.data)).catch(() => {});
    api.get("/opportunities/recommended?limit=12").then((r) => setRecs(r.data.recommendations || [])).catch(() => {});
  }, []);

  const stats = data?.stats || {};
  const allOpps = useMemo(() => recs, [recs]);

  // Default the area to the student's own area (constrain) once profile is known.
  useEffect(() => {
    if (recs.length && area.state === "all" && user.location) {
      const { state, city } = parseLocation(user.location);
      if (state) setArea({ state, city: city && citiesForState(state).includes(city) ? city : "all" });
    }
    // eslint-disable-next-line
  }, [recs]);

  const opps = useMemo(() => {
    if (area.state === "all") return allOpps;
    return allOpps.filter((o) => {
      if (OPEN_TO_ALL.includes(o.location)) return true;
      const p = parseLocation(o.location);
      return p.state === area.state && (area.city === "all" || p.city === area.city);
    });
  }, [allOpps, area]);

  return (
    <div className="max-w-6xl mx-auto px-5 md:px-10 py-8">
      <PageHead label={`${user.grade || "Student"} · ${user.school || "Nexus"}`} title={`Hey ${user.name.split(" ")[0]} 👋`}>
        <button className="nb-btn" onClick={() => nav("/app/discover")} data-testid="dash-match-btn">
          <Sparkle size={18} weight="fill" /> Find teammates
        </button>
      </PageHead>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <Stat icon={Rocket} color="bg-[#FF7B54]" value={stats.projects ?? 0} label="My projects" />
        <Stat icon={Handshake} color="bg-[#A0C4FF]" value={stats.connections ?? 0}
          label="Connections" onClick={() => nav("/app/connections")} testid="dash-connections"
          badge={stats.connection_requests ? stats.connection_requests : null} />
        <Stat icon={Trophy} color="bg-[#FFD166]" value={stats.opportunities ?? 0} label="Opportunities" />
      </div>

      {/* AI goal prompt card */}
      <div className="nb-card nb-card-hover bg-[#A0C4FF] p-6 mb-8 cursor-pointer" onClick={() => nav("/app/match")} data-testid="dash-ai-card">
        <div className="flex items-center gap-2 mb-2">
          <Sparkle size={22} weight="fill" className="text-[#FF7B54]" />
          <span className="nb-label">Nexus AI</span>
        </div>
        <h3 className="font-display text-2xl md:text-3xl font-bold tracking-tight">Tell me your goal, I'll find your team.</h3>
        <p className="font-medium mt-1 flex items-center gap-1">Try "I need a designer for my startup" <ArrowRight size={16} weight="bold" /></p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {/* Suggested teammates */}
        <div className="md:col-span-2">
          <h2 className="font-display text-2xl font-bold tracking-tight mb-4">Suggested teammates</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            {(data?.suggested_teammates || []).map((s) => (
              <div key={s.id} className="nb-card nb-card-hover p-4 cursor-pointer" onClick={() => nav("/app/discover")} data-testid={`dash-teammate-${s.id}`}>
                <div className="flex items-center gap-3 mb-2">
                  <Avatar src={s.avatar} name={s.name} />
                  <div className="min-w-0">
                    <div className="font-bold truncate">{s.name}</div>
                    <div className="text-xs text-[#4A4A4A] truncate">{s.grade} · {s.school}</div>
                  </div>
                </div>
                <p className="text-sm text-[#4A4A4A] font-medium line-clamp-2 mb-2">{s.bio}</p>
                <Reputation rep={s.reputation} />
              </div>
            ))}
          </div>
        </div>

        {/* Opportunities — AI-picked & scoped by area */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Sparkle size={20} weight="fill" className="text-[#FF7B54]" />
            <h2 className="font-display text-2xl font-bold tracking-tight">For you</h2>
          </div>

          {/* Area / scope selector: State + City */}
          <div className="nb-card p-3 mb-4">
            <label className="nb-label flex items-center gap-1 mb-1"><MapPin size={14} weight="bold" /> Your area</label>
            <AreaFilter state={area.state} city={area.city} onChange={setArea} testidPrefix="opp" />
            <p className="text-xs text-[#4A4A4A] mt-1">
              {area.state === "all" ? "AI picks across all areas (broadened)." : "AI picks in your area plus remote/nationwide."}
            </p>
          </div>

          <div className="space-y-3">
            {opps.length === 0 && (
              <div className="nb-card p-4 text-sm text-[#4A4A4A]">No matches in this area yet — try broadening the scope.</div>
            )}
            {opps.slice(0, 6).map((o) => (
              <div key={o.id} className="nb-card p-4" data-testid={`dash-opp-${o.id}`}>
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  <span className="nb-chip bg-[#FFD166]">{o.type}</span>
                  {o.location && <span className="nb-chip bg-white text-xs"><MapPin size={12} weight="bold" /> {o.location}</span>}
                  {typeof o.score === "number" && <span className="nb-chip bg-[#A0C4FF] text-xs ml-auto">{o.score}% match</span>}
                </div>
                <div className="font-bold leading-tight">{o.title}</div>
                <div className="text-xs text-[#4A4A4A] mt-1">{o.org}</div>
                {o.reason && (
                  <div className="flex items-start gap-1 text-xs font-medium text-[#4A4A4A] mt-2 bg-[#A0C4FF]/20 border-2 border-[#0A0A0A]/10 rounded-lg p-2">
                    <Sparkle size={13} weight="fill" className="text-[#FF7B54] mt-0.5 shrink-0" /> {o.reason}
                  </div>
                )}
                <div className="flex items-center gap-1 text-xs font-bold text-[#FF7B54] mt-2">
                  <CalendarBlank size={14} weight="bold" /> {o.deadline}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function Stat({ icon: Icon, color, value, label, onClick, testid, badge }) {
  return (
    <div className={`nb-card p-4 md:p-5 relative ${onClick ? "nb-card-hover cursor-pointer" : ""}`} onClick={onClick} data-testid={testid}>
      {badge != null && (
        <span className="absolute top-3 right-3 nb-chip bg-[#FF7B54] text-white text-xs">{badge} new</span>
      )}
      <div className={`w-10 h-10 ${color} border-2 border-[#0A0A0A] rounded-lg flex items-center justify-center mb-3`}>
        <Icon size={20} weight="bold" />
      </div>
      <div className="font-display text-3xl md:text-4xl font-black">{value}</div>
      <div className="nb-label mt-1">{label}</div>
    </div>
  );
}
