import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, formatError } from "@/api";
import { PageHead, Avatar, Reputation } from "@/components/common";
import ReviewModal from "@/components/ReviewModal";
import { Handshake, Check, X, ChatCircleDots, UserPlus, Star } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function Connections() {
  const nav = useNavigate();
  const [connections, setConnections] = useState([]);
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [reviewing, setReviewing] = useState(null);

  const load = () => {
    setLoading(true);
    Promise.all([
      api.get("/connections").then((r) => setConnections(r.data)).catch(() => {}),
      api.get("/connections/requests").then((r) => setRequests(r.data)).catch(() => {}),
    ]).finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, []);

  const respond = async (s, action) => {
    try {
      await api.post(`/connections/${s.id}/respond`, { action });
      toast.success(action === "accept" ? `Connected with ${s.name.split(" ")[0]}! 🤝` : "Request declined.");
      load();
    } catch (e) { toast.error(formatError(e?.response?.data?.detail)); }
  };

  return (
    <div className="max-w-5xl mx-auto px-5 md:px-10 py-8">
      <PageHead label="Your network" title="Connections." >
        <button className="nb-btn" onClick={() => nav("/app/discover")} data-testid="conn-find-btn">
          <UserPlus size={18} weight="bold" /> Find people
        </button>
      </PageHead>

      {/* Requests */}
      <div className="mb-10">
        <h2 className="font-display text-2xl font-bold tracking-tight mb-4 flex items-center gap-2">
          Requests {requests.length > 0 && <span className="nb-chip bg-[#FF7B54] text-white">{requests.length}</span>}
        </h2>
        {loading ? (
          <div className="text-sm text-[#4A4A4A]">Loading…</div>
        ) : requests.length === 0 ? (
          <div className="nb-card p-5 text-sm text-[#4A4A4A]">No pending requests right now.</div>
        ) : (
          <div className="grid sm:grid-cols-2 gap-4">
            {requests.map((s) => (
              <div key={s.id} className="nb-card p-4" data-testid={`request-${s.id}`}>
                <div className="flex items-center gap-3 mb-3">
                  <Avatar src={s.avatar} name={s.name} className="w-12 h-12" />
                  <div className="min-w-0">
                    <div className="font-bold truncate">{s.name}</div>
                    <div className="text-xs text-[#4A4A4A] truncate">{s.grade} · {s.school}</div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button className="nb-btn text-sm py-2 flex-1" onClick={() => respond(s, "accept")} data-testid={`req-accept-${s.id}`}>
                    <Check size={16} weight="bold" /> Accept
                  </button>
                  <button className="nb-btn nb-btn-ghost text-sm py-2" onClick={() => respond(s, "decline")} data-testid={`req-decline-${s.id}`}>
                    <X size={16} weight="bold" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Connections */}
      <div>
        <h2 className="font-display text-2xl font-bold tracking-tight mb-4 flex items-center gap-2">
          <Handshake size={24} weight="bold" /> My connections ({connections.length})
        </h2>
        {!loading && connections.length === 0 ? (
          <div className="nb-card p-6 text-center">
            <p className="font-medium text-[#4A4A4A] mb-3">You haven't connected with anyone yet.</p>
            <button className="nb-btn mx-auto" onClick={() => nav("/app/discover")}><UserPlus size={18} weight="bold" /> Discover students</button>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {connections.map((s) => (
              <div key={s.id} className="nb-card nb-card-hover p-5 flex flex-col" data-testid={`connection-${s.id}`}>
                <div className="flex items-center gap-3 mb-3">
                  <Avatar src={s.avatar} name={s.name} className="w-14 h-14" />
                  <div className="min-w-0">
                    <div className="font-display text-lg font-bold truncate">{s.name}</div>
                    <div className="text-xs text-[#4A4A4A] truncate">{s.grade} · {s.school}</div>
                    {s.location && <div className="text-xs text-[#4A4A4A] truncate">📍 {s.location}</div>}
                  </div>
                </div>
                <p className="text-sm text-[#4A4A4A] font-medium line-clamp-2 mb-3">{s.bio}</p>
                <div className="mb-4"><Reputation rep={s.reputation} /></div>
                <div className="mt-auto flex gap-2">
                  <button className="nb-btn nb-btn-sec text-sm py-2 flex-1" onClick={() => nav("/app/messages", { state: { to: s } })} data-testid={`conn-message-${s.id}`}>
                    <ChatCircleDots size={16} weight="bold" /> Message
                  </button>
                  <button className="nb-btn nb-btn-ghost text-sm py-2" title="Reviews" onClick={() => setReviewing({ ...s, can_review: true })} data-testid={`conn-review-${s.id}`}>
                    <Star size={16} weight="bold" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {reviewing && (
        <ReviewModal student={reviewing} onClose={() => setReviewing(null)} onSubmitted={load} />
      )}
    </div>
  );
}
