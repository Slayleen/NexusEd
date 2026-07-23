import { useEffect, useMemo, useState } from "react";
import { api } from "@/api";
import { PageHead, sortAreas } from "@/components/common";
import { Trophy, CalendarBlank, ArrowSquareOut, Buildings, MapPin } from "@phosphor-icons/react";

const TYPES = ["All", "Research", "Competition", "Scholarship", "Internship", "Hackathon"];
const TYPE_COLOR = {
  Research: "bg-[#A0C4FF]", Competition: "bg-[#FF7B54]", Scholarship: "bg-[#FFD166]",
  Internship: "bg-[#2ECC71] text-white", Hackathon: "bg-[#FFB4A2]",
};
const OPEN_TO_ALL = ["Remote", "Nationwide", "Online"];

export default function Opportunities() {
  const [opps, setOpps] = useState([]);
  const [filter, setFilter] = useState("All");
  const [area, setArea] = useState("all");

  useEffect(() => { api.get("/opportunities").then((r) => setOpps(r.data)).catch(() => {}); }, []);

  const areas = useMemo(() => {
    const set = new Set();
    opps.forEach((o) => { if (o.location && !OPEN_TO_ALL.includes(o.location)) set.add(o.location); });
    return sortAreas(Array.from(set));
  }, [opps]);

  const shown = opps.filter((o) => {
    const typeOk = filter === "All" || o.type === filter;
    const areaOk = area === "all" || o.location === area || OPEN_TO_ALL.includes(o.location);
    return typeOk && areaOk;
  });

  return (
    <div className="max-w-6xl mx-auto px-5 md:px-10 py-8">
      <PageHead label="Opportunity Board" title="Discover what's next." />

      <div className="flex flex-wrap gap-2 mb-4">
        {TYPES.map((t) => (
          <button key={t} onClick={() => setFilter(t)} data-testid={`opp-filter-${t}`}
            className={`nb-chip ${filter === t ? "bg-[#FF7B54]" : "bg-white"}`}>{t}</button>
        ))}
      </div>

      <div className="flex items-center gap-2 mb-6">
        <MapPin size={18} weight="bold" className="text-[#4A4A4A]" />
        <select className="nb-input py-2 max-w-xs" value={area} onChange={(e) => setArea(e.target.value)} data-testid="opp-area-select">
          <option value="all">All areas</option>
          {areas.map((a) => <option key={a} value={a}>{a} + remote</option>)}
        </select>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
        {shown.map((o) => (
          <div key={o.id} className="nb-card nb-card-hover p-5 flex flex-col" data-testid={`opp-${o.id}`}>
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 bg-[#FFD166] border-2 border-[#0A0A0A] rounded-lg flex items-center justify-center">
                <Trophy size={20} weight="bold" />
              </div>
              <span className={`nb-chip ${TYPE_COLOR[o.type] || "bg-white"}`}>{o.type}</span>
            </div>
            <h3 className="font-display text-xl font-bold tracking-tight leading-tight">{o.title}</h3>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-bold text-[#4A4A4A] mt-1 mb-2">
              <span className="flex items-center gap-1"><Buildings size={14} weight="bold" /> {o.org}</span>
              {o.location && <span className="flex items-center gap-1"><MapPin size={14} weight="bold" /> {o.location}</span>}
            </div>
            <p className="text-sm text-[#4A4A4A] font-medium line-clamp-3 mb-4">{o.description}</p>
            <div className="mt-auto flex items-center justify-between">
              <span className="flex items-center gap-1 text-xs font-bold text-[#FF7B54]">
                <CalendarBlank size={14} weight="bold" /> {o.deadline}
              </span>
              <a href={o.link} target="_blank" rel="noreferrer" className="nb-btn nb-btn-accent text-sm py-2" data-testid={`opp-apply-${o.id}`}>
                Apply <ArrowSquareOut size={14} weight="bold" />
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
