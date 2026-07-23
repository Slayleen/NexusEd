import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, formatError } from "@/api";
import { PageHead, Avatar, Reputation, Chips } from "@/components/common";
import ReviewModal from "@/components/ReviewModal";
import { ChatCircleDots, MagnifyingGlass, Handshake, Check, Clock, Star } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function Discover() {
  const nav = useNavigate();
  const [students, setStudents] = useState([]);
  const [q, setQ] = useState("");
  const [reviewing, setReviewing] = useState(null);

  const load = () => api.get("/students").then((r) => setStudents(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const connect = async (s) => {
    try {
      const { data } = await api.post(`/connections/${s.id}`);
      if (data.status === "connected") toast.success(`You're connected with ${s.name.split(" ")[0]}! 🤝`);
      else toast.success(`Connection request sent to ${s.name.split(" ")[0]}.`);
      load();
    } catch (e) { toast.error(formatError(e?.response?.data?.detail)); }
  };

  const respond = async (s, action) => {
    try {
      await api.post(`/connections/${s.id}/respond`, { action });
      toast.success(action === "accept" ? `Connected with ${s.name.split(" ")[0]}! 🤝` : "Request declined.");
      load();
    } catch (e) { toast.error(formatError(e?.response?.data?.detail)); }
  };

  const shown = students.filter((s) => {
    const hay = `${s.name} ${s.school} ${s.location || ""} ${(s.skills || []).join(" ")} ${(s.interests || []).join(" ")}`.toLowerCase();
    return hay.includes(q.toLowerCase());
  });

  const ConnectBtn = ({ s }) => {
    if (s.connection_status === "connected")
      return <button className="nb-btn nb-btn-ghost text-sm py-2 flex-1 !bg-[#2ECC71] !text-white" disabled data-testid={`connected-${s.id}`}><Check size={16} weight="bold" /> Connected</button>;
    if (s.connection_status === "pending_out")
      return <button className="nb-btn nb-btn-ghost text-sm py-2 flex-1" disabled data-testid={`pending-${s.id}`}><Clock size={16} weight="bold" /> Requested</button>;
    if (s.connection_status === "pending_in")
      return (
        <div className="flex gap-1 flex-1">
          <button className="nb-btn text-sm py-2 flex-1" onClick={() => respond(s, "accept")} data-testid={`accept-${s.id}`}><Check size={16} weight="bold" /> Accept</button>
          <button className="nb-btn nb-btn-ghost text-sm py-2" onClick={() => respond(s, "decline")} data-testid={`decline-${s.id}`}>✕</button>
        </div>
      );
    return <button className="nb-btn nb-btn-sec text-sm py-2 flex-1" onClick={() => connect(s)} data-testid={`connect-${s.id}`}><Handshake size={16} weight="bold" /> Connect</button>;
  };

  return (
    <div className="max-w-6xl mx-auto px-5 md:px-10 py-8">
      <PageHead label="Discover students" title="Find your people." />

      <div className="nb-card flex items-center gap-2 px-4 mb-6 max-w-md">
        <MagnifyingGlass size={20} weight="bold" className="text-[#4A4A4A]" />
        <input className="flex-1 py-3 outline-none bg-transparent font-medium" placeholder="Search by skill, interest, area or school…"
          value={q} onChange={(e) => setQ(e.target.value)} data-testid="discover-search" />
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
        {shown.map((s) => (
          <div key={s.id} className="nb-card nb-card-hover p-5 flex flex-col" data-testid={`student-${s.id}`}>
            <div className="flex items-center gap-3 mb-3">
              <Avatar src={s.avatar} name={s.name} className="w-14 h-14" />
              <div className="min-w-0">
                <div className="font-display text-lg font-bold truncate">{s.name}</div>
                <div className="text-xs text-[#4A4A4A] truncate">{s.grade} · {s.school}</div>
                {s.location && <div className="text-xs text-[#4A4A4A] truncate">📍 {s.location}</div>}
              </div>
            </div>
            <p className="text-sm text-[#4A4A4A] font-medium line-clamp-2 mb-3">{s.bio}</p>
            <div className="mb-2"><Chips items={s.skills} color="bg-[#FFD166]" /></div>
            {s.looking_for?.length > 0 && (
              <div className="mb-3">
                <div className="nb-label mb-1">Looking for</div>
                <Chips items={s.looking_for} color="bg-[#A0C4FF]" />
              </div>
            )}
            <div className="mb-4"><Reputation rep={s.reputation} /></div>
            <div className="mt-auto flex gap-2">
              <ConnectBtn s={s} />
              <button className="nb-btn nb-btn-ghost text-sm py-2" title="Message" onClick={() => nav("/app/messages", { state: { to: s } })} data-testid={`message-${s.id}`}>
                <ChatCircleDots size={16} weight="bold" />
              </button>
              <button className="nb-btn nb-btn-ghost text-sm py-2" title="Reviews" onClick={() => setReviewing(s)} data-testid={`review-${s.id}`}>
                <Star size={16} weight="bold" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {reviewing && (
        <ReviewModal student={reviewing} onClose={() => setReviewing(null)} onSubmitted={load} />
      )}
    </div>
  );
}
