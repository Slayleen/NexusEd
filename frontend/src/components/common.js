import { Trophy, Star, ShieldCheck } from "@phosphor-icons/react";
export { Star };

export function PageHead({ label, title, children }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4 mb-8">
      <div>
        {label && <div className="nb-label mb-1">{label}</div>}
        <h1 className="font-display text-4xl md:text-5xl font-black tracking-tight">{title}</h1>
      </div>
      {children}
    </div>
  );
}

export function Reputation({ rep, size = "sm" }) {
  if (!rep) return null;
  const cls = size === "sm" ? "text-xs" : "text-sm";
  const hasReviews = (rep.review_count || 0) > 0;
  return (
    <div className={`flex flex-wrap gap-2 ${cls}`}>
      <span className="nb-chip bg-[#FFD166]"><Trophy size={14} weight="bold" /> {rep.projects_completed} done</span>
      {hasReviews && (
        <span className="nb-chip bg-[#A0C4FF]"><Star size={14} weight="fill" /> {rep.avg_rating} ({rep.review_count})</span>
      )}
      <span className="nb-chip bg-white"><ShieldCheck size={14} weight="bold" /> {rep.reliability}% reliable</span>
    </div>
  );
}

export function Avatar({ src, name, className = "w-11 h-11" }) {
  return <img src={src} alt={name} className={`${className} rounded-lg border-2 border-[#0A0A0A] bg-white shrink-0`} />;
}

export function Chips({ items, color = "bg-white" }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {(items || []).map((i) => <span key={i} className={`nb-chip ${color}`}>{i}</span>)}
    </div>
  );
}

// Sort location strings "City, ST" by state first, then city.
export function areaSortKey(loc) {
  const parts = (loc || "").split(",").map((s) => s.trim());
  if (parts.length >= 2) return `${parts[1]} ${parts[0]}`.toLowerCase();
  return (loc || "").toLowerCase();
}
export function sortAreas(list) {
  return [...list].sort((a, b) => areaSortKey(a).localeCompare(areaSortKey(b)));
}
