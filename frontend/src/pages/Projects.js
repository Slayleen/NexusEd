import { useEffect, useState } from "react";
import { api, formatError } from "@/api";
import { useAuth } from "@/AuthContext";
import { PageHead, Avatar, Chips } from "@/components/common";
import { Rocket, Plus, X, Handshake, Clock, CheckCircle, Check } from "@phosphor-icons/react";
import { toast } from "sonner";

const CATEGORIES = ["AI / Machine Learning", "Robotics", "Web Dev", "Research", "Startups", "Nonprofit", "Game Dev", "Other"];

export default function Projects() {
  const { user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState("All");

  const load = () => api.get("/projects").then((r) => setProjects(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const connectOwner = async (p) => {
    try {
      const { data } = await api.post(`/connections/${p.owner_id}`);
      if (data.status === "connected") toast.success(`Connected with ${p.owner?.name?.split(" ")[0]}! 🤝`);
      else toast.success(`Connection request sent to ${p.owner?.name?.split(" ")[0]} about "${p.title}".`);
      load();
    } catch (e) { toast.error(formatError(e?.response?.data?.detail)); }
  };

  const shown = filter === "All" ? projects : projects.filter((p) => p.category === filter);

  return (
    <div className="max-w-6xl mx-auto px-5 md:px-10 py-8">
      <PageHead label="Project Hub" title="Build together.">
        <button className="nb-btn" onClick={() => setOpen(true)} data-testid="create-project-btn">
          <Plus size={18} weight="bold" /> New project
        </button>
      </PageHead>

      <div className="flex flex-wrap gap-2 mb-6">
        {["All", ...CATEGORIES].map((c) => (
          <button key={c} onClick={() => setFilter(c)} data-testid={`filter-${c}`}
            className={`nb-chip ${filter === c ? "bg-[#FF7B54]" : "bg-white"}`}>{c}</button>
        ))}
      </div>

      <div className="grid md:grid-cols-2 gap-5">
        {shown.map((p) => (
          <div key={p.id} className="nb-card nb-card-hover p-5 flex flex-col" data-testid={`project-${p.id}`}>
            <div className="flex items-center justify-between mb-2">
              <span className="nb-chip bg-[#A0C4FF]">{p.category}</span>
              {p.status === "completed"
                ? <span className="nb-chip bg-[#2ECC71] text-white"><CheckCircle size={14} weight="bold" /> Completed</span>
                : <span className="nb-chip bg-[#FFD166]"><Clock size={14} weight="bold" /> Active</span>}
            </div>
            <h3 className="font-display text-xl font-bold tracking-tight">{p.title}</h3>
            <p className="text-sm text-[#4A4A4A] font-medium mt-1 mb-3 line-clamp-3">{p.description}</p>

            <div className="mb-3">
              <div className="nb-label mb-1">Roles needed</div>
              <Chips items={p.roles_needed} color="bg-[#FFD166]" />
            </div>

            <div className="mb-4">
              <div className="flex justify-between text-xs font-bold mb-1"><span>Progress</span><span>{p.progress}%</span></div>
              <div className="h-3 border-2 border-[#0A0A0A] rounded-full bg-white overflow-hidden">
                <div className="h-full bg-[#FF7B54]" style={{ width: `${p.progress}%` }} />
              </div>
            </div>

            <div className="mt-auto flex items-center justify-between">
              <div className="flex items-center gap-2">
                {p.owner && <Avatar src={p.owner.avatar} name={p.owner.name} className="w-8 h-8" />}
                <div className="text-xs">
                  <div className="font-bold">{p.owner?.name}</div>
                  <div className="text-[#4A4A4A] flex items-center gap-1"><Clock size={12} /> {p.timeline}</div>
                </div>
              </div>
              {p.owner_id === user.id
                ? <span className="nb-chip bg-white">You own this</span>
                : p.owner?.connection_status === "connected"
                  ? <span className="nb-chip bg-[#2ECC71] text-white"><Check size={14} weight="bold" /> Connected</span>
                  : p.owner?.connection_status === "pending_out"
                    ? <span className="nb-chip bg-white"><Clock size={14} weight="bold" /> Requested</span>
                    : <button className="nb-btn nb-btn-sec text-sm py-2" onClick={() => connectOwner(p)} data-testid={`connect-owner-${p.id}`}>
                        <Handshake size={16} weight="bold" /> Connect
                      </button>}
            </div>
          </div>
        ))}
      </div>

      {open && <CreateModal onClose={() => setOpen(false)} onCreated={() => { load(); setOpen(false); }} />}
    </div>
  );
}

function CreateModal({ onClose, onCreated }) {
  const [f, setF] = useState({ title: "", description: "", category: CATEGORIES[0], roles: "", skills: "", timeline: "3 months" });
  const [saving, setSaving] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/projects", {
        title: f.title, description: f.description, category: f.category,
        roles_needed: f.roles.split(",").map((s) => s.trim()).filter(Boolean),
        skills: f.skills.split(",").map((s) => s.trim()).filter(Boolean),
        timeline: f.timeline,
      });
      toast.success("Project created! 🚀");
      onCreated();
    } catch { toast.error("Could not create project."); } finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <form onClick={(e) => e.stopPropagation()} onSubmit={submit} className="nb-card bg-[#FDFBF7] p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto" data-testid="create-project-modal">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-display text-2xl font-black flex items-center gap-2"><Rocket size={24} weight="bold" /> New project</h2>
          <button type="button" onClick={onClose}><X size={24} weight="bold" /></button>
        </div>
        <div className="space-y-3">
          <div><label className="nb-label">Title</label><input className="nb-input mt-1" value={f.title} onChange={set("title")} required data-testid="project-title" /></div>
          <div><label className="nb-label">Description</label><textarea className="nb-input mt-1 min-h-[80px]" value={f.description} onChange={set("description")} required data-testid="project-desc" /></div>
          <div><label className="nb-label">Category</label>
            <select className="nb-input mt-1" value={f.category} onChange={set("category")} data-testid="project-category">
              {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div><label className="nb-label">Roles needed (comma separated)</label><input className="nb-input mt-1" value={f.roles} onChange={set("roles")} placeholder="Frontend Developer, Designer" data-testid="project-roles" /></div>
          <div><label className="nb-label">Skills (comma separated)</label><input className="nb-input mt-1" value={f.skills} onChange={set("skills")} placeholder="React, Python" /></div>
          <div><label className="nb-label">Timeline</label><input className="nb-input mt-1" value={f.timeline} onChange={set("timeline")} /></div>
        </div>
        <button type="submit" disabled={saving} className="nb-btn w-full justify-center mt-5" data-testid="project-save">
          {saving ? "Creating…" : "Create project"}
        </button>
      </form>
    </div>
  );
}
