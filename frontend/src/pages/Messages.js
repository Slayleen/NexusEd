import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { api, formatError } from "@/api";
import { useAuth } from "@/AuthContext";
import { Avatar } from "@/components/common";
import { PaperPlaneRight, ChatCircleDots, LockSimple } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function Messages() {
  const { user } = useAuth();
  const loc = useLocation();
  const [convos, setConvos] = useState([]);
  const [active, setActive] = useState(null); // {id,name,avatar}
  const [messages, setMessages] = useState([]);
  const [canSend, setCanSend] = useState(true);
  const [connected, setConnected] = useState(false);
  const [text, setText] = useState("");
  const endRef = useRef(null);

  const loadConvos = () => api.get("/conversations").then((r) => setConvos(r.data)).catch(() => {});

  useEffect(() => {
    loadConvos();
    if (loc.state?.to) setActive(loc.state.to);
  }, []); // eslint-disable-line

  useEffect(() => {
    if (!active) return;
    let alive = true;
    const load = () => api.get(`/messages/${active.id}`).then((r) => {
      if (!alive) return;
      setMessages(r.data.messages || []);
      setCanSend(r.data.can_send);
      setConnected(r.data.connected);
    }).catch(() => {});
    load();
    const iv = setInterval(load, 3000);
    return () => { alive = false; clearInterval(iv); };
  }, [active]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const send = async (e) => {
    e.preventDefault();
    if (!text.trim() || !active) return;
    const t = text;
    setText("");
    const optimistic = { id: `tmp-${Date.now()}`, from_user_id: user.id, text: t };
    setMessages((m) => [...m, optimistic]);
    try {
      await api.post("/messages", { to_user_id: active.id, text: t });
      loadConvos();
      if (!connected) setCanSend(false);
    } catch (err) {
      setMessages((m) => m.filter((x) => x.id !== optimistic.id));
      setText(t);
      setCanSend(false);
      toast.error(formatError(err?.response?.data?.detail));
    }
  };

  const mergedConvos = active && !convos.find((c) => c.user.id === active.id)
    ? [{ user: active, last_message: "New conversation", last_at: "" }, ...convos]
    : convos;

  return (
    <div className="max-w-6xl mx-auto px-5 md:px-10 py-8">
      <div className="nb-card overflow-hidden flex h-[75vh]">
        {/* Conversation list */}
        <div className={`w-full md:w-72 border-r-2 border-[#0A0A0A] flex flex-col ${active ? "hidden md:flex" : "flex"}`}>
          <div className="p-4 border-b-2 border-[#0A0A0A]">
            <h2 className="font-display text-xl font-black">Messages</h2>
          </div>
          <div className="flex-1 overflow-y-auto">
            {mergedConvos.length === 0 && <p className="p-4 text-sm text-[#4A4A4A] font-medium">No conversations yet. Find teammates in Discover or AI Match.</p>}
            {mergedConvos.map((c) => (
              <button key={c.user.id} onClick={() => setActive(c.user)} data-testid={`convo-${c.user.id}`}
                className={`w-full flex items-center gap-3 p-3 text-left border-b-2 border-[#0A0A0A]/10 hover:bg-[#FDFBF7] ${active?.id === c.user.id ? "bg-[#FFD166]" : ""}`}>
                <Avatar src={c.user.avatar} name={c.user.name} className="w-10 h-10" />
                <div className="min-w-0 flex-1">
                  <div className="font-bold text-sm truncate">{c.user.name}</div>
                  <div className="text-xs text-[#4A4A4A] truncate">{c.last_message}</div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Chat */}
        <div className={`flex-1 flex-col ${active ? "flex" : "hidden md:flex"}`}>
          {!active ? (
            <div className="flex-1 flex flex-col items-center justify-center text-[#4A4A4A]">
              <ChatCircleDots size={48} weight="bold" />
              <p className="font-bold mt-2">Select a conversation</p>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-3 p-4 border-b-2 border-[#0A0A0A] bg-[#FDFBF7]">
                <button className="md:hidden font-bold" onClick={() => setActive(null)}>←</button>
                <Avatar src={active.avatar} name={active.name} className="w-10 h-10" />
                <div className="font-display font-bold">{active.name}</div>
              </div>
              <div className="flex-1 overflow-y-auto p-4 space-y-2 bg-[#FDFBF7]">
                {messages.map((m) => {
                  const mine = m.from_user_id === user.id;
                  return (
                    <div key={m.id} className={`flex ${mine ? "justify-end" : "justify-start"}`}>
                      <div className={`max-w-[75%] px-4 py-2 rounded-xl border-2 border-[#0A0A0A] font-medium text-sm ${mine ? "bg-[#FF7B54]" : "bg-white"}`}>
                        {m.text}
                      </div>
                    </div>
                  );
                })}
                <div ref={endRef} />
              </div>
              <form onSubmit={send} className="flex flex-col gap-1 p-3 border-t-2 border-[#0A0A0A] bg-white">
                {!connected && (
                  <div className="flex items-center gap-1.5 text-xs font-bold text-[#4A4A4A] px-1">
                    <LockSimple size={13} weight="bold" />
                    {canSend
                      ? "You can send one intro message. Connect to keep chatting."
                      : "Message limit reached — send a connection request to keep chatting."}
                  </div>
                )}
                <div className="flex gap-2">
                  <input className="nb-input flex-1" placeholder={canSend ? "Type a message…" : "Connect to send more messages"}
                    value={text} onChange={(e) => setText(e.target.value)} disabled={!canSend} data-testid="message-input" />
                  <button type="submit" className="nb-btn px-4 disabled:opacity-40" disabled={!canSend} data-testid="message-send">
                    <PaperPlaneRight size={20} weight="bold" />
                  </button>
                </div>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
