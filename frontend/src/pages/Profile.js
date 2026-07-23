import { useState } from "react";
import { api } from "@/api";
import { useAuth } from "@/AuthContext";
import { PageHead, Avatar, Reputation } from "@/components/common";
import { ShieldCheck, FloppyDisk, X, Plus, Shuffle, LinkSimple } from "@phosphor-icons/react";
import { toast } from "sonner";

const AVATAR_STYLES = ["thumbs", "bottts", "fun-emoji", "adventurer", "notionists", "lorelei", "micah", "personas"];
const buildAvatar = (style, seed) => `https://api.dicebear.com/7.x/${style}/svg?seed=${encodeURIComponent(seed)}`;

function AvatarPicker({ value, name, onChange }) {
  const [customUrl, setCustomUrl] = useState("");
  const styleOptions = AVATAR_STYLES.map((s) => buildAvatar(s, name || "nexus"));

  const shuffle = () => {
    const style = AVATAR_STYLES[Math.floor(Math.random() * AVATAR_STYLES.length)];
    onChange(buildAvatar(style, `${name}-${Math.floor(Math.random() * 99999)}`));
  };

  return (
    <div>
      <label className="nb-label">Avatar</label>
      <div className="flex items-center gap-3 mt-1 mb-3">
        <Avatar src={value} name={name} className="w-16 h-16" />
        <button type="button" className="nb-btn nb-btn-sec text-sm py-2" onClick={shuffle} data-testid="avatar-shuffle">
          <Shuffle size={16} weight="bold" /> Shuffle
        </button>
      </div>
      <div className="flex flex-wrap gap-2 mb-3">
        {styleOptions.map((url) => (
          <button type="button" key={url} onClick={() => onChange(url)} data-testid="avatar-option"
            className={`rounded-lg border-2 p-0.5 ${value === url ? "border-[#FF7B54] bg-[#FF7B54]" : "border-[#0A0A0A] bg-white"}`}>
            <img src={url} alt="" className="w-10 h-10 rounded-md" />
          </button>
        ))}
      </div>
      <div className="flex gap-2">
        <div className="flex items-center gap-2 nb-input py-2 flex-1">
          <LinkSimple size={16} weight="bold" className="text-[#4A4A4A]" />
          <input className="flex-1 outline-none bg-transparent text-sm" placeholder="Paste an image URL…"
            value={customUrl} onChange={(e) => setCustomUrl(e.target.value)} data-testid="avatar-url-input" />
        </div>
        <button type="button" className="nb-btn nb-btn-ghost py-2 px-3 text-sm"
          onClick={() => { if (customUrl.trim()) { onChange(customUrl.trim()); toast.success("Avatar updated"); } }}
          data-testid="avatar-url-apply">Use</button>
      </div>
    </div>
  );
}

function TagEditor({ label, items, color, onChange, testid }) {
  const [val, setVal] = useState("");
  const add = () => {
    const t = val.trim();
    if (t && !items.includes(t)) { onChange([...items, t]); setVal(""); }
  };
  return (
    <div>
      <label className="nb-label">{label}</label>
      <div className="flex flex-wrap gap-1.5 mt-1 mb-2">
        {items.map((i) => (
          <span key={i} className={`nb-chip ${color}`}>{i}
            <button type="button" onClick={() => onChange(items.filter((x) => x !== i))}><X size={12} weight="bold" /></button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input className="nb-input py-2" value={val} onChange={(e) => setVal(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); add(); } }}
          placeholder="Type & press Enter" data-testid={testid} />
        <button type="button" className="nb-btn nb-btn-sec py-2 px-3" onClick={add}><Plus size={18} weight="bold" /></button>
      </div>
    </div>
  );
}

export default function Profile() {
  const { user, setUser } = useAuth();
  const [f, setF] = useState({
    name: user.name, school: user.school || "", grade: user.grade || "11th", bio: user.bio || "",
    avatar: user.avatar, interests: user.interests || [], skills: user.skills || [], looking_for: user.looking_for || [],
    location: user.location || "",
  });
  const [saving, setSaving] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const save = async () => {
    setSaving(true);
    try {
      const { data } = await api.put("/profile", f);
      setUser(data);
      toast.success("Profile saved! ✨");
    } catch { toast.error("Could not save."); } finally { setSaving(false); }
  };

  return (
    <div className="max-w-4xl mx-auto px-5 md:px-10 py-8">
      <PageHead label="Your Profile" title="Your verified identity." />

      <div className="grid md:grid-cols-3 gap-6">
        {/* Card preview */}
        <div className="md:col-span-1">
          <div className="nb-card p-5 text-center sticky top-8" data-testid="profile-preview">
            <Avatar src={f.avatar} name={user.name} className="w-24 h-24 mx-auto" />
            <h3 className="font-display text-xl font-bold mt-3">{f.name}</h3>
            <p className="text-xs text-[#4A4A4A]">{f.grade} · {f.school}</p>
            {f.location && <p className="text-xs text-[#4A4A4A]">📍 {f.location}</p>}
            {user.verified && (
              <div className="nb-chip bg-[#2ECC71] text-white mt-2 mx-auto"><ShieldCheck size={14} weight="fill" /> Verified student</div>
            )}
            <div className="mt-4"><Reputation rep={user.reputation} /></div>
          </div>
        </div>

        {/* Editor */}
        <div className="md:col-span-2 nb-card p-6 space-y-4">
          <AvatarPicker value={f.avatar} name={f.name} onChange={(url) => setF({ ...f, avatar: url })} />
          <div className="grid sm:grid-cols-2 gap-3">
            <div><label className="nb-label">Name</label><input className="nb-input mt-1" value={f.name} onChange={set("name")} data-testid="profile-name" /></div>
            <div><label className="nb-label">Grade</label>
              <select className="nb-input mt-1" value={f.grade} onChange={set("grade")} data-testid="profile-grade">
                {["9th", "10th", "11th", "12th"].map((g) => <option key={g}>{g}</option>)}
              </select>
            </div>
          </div>
          <div><label className="nb-label">School</label><input className="nb-input mt-1" value={f.school} onChange={set("school")} data-testid="profile-school" /></div>
          <div><label className="nb-label">Area / Location (for opportunities near you)</label><input className="nb-input mt-1" value={f.location} onChange={set("location")} data-testid="profile-location" placeholder="e.g. Boston, MA" /></div>
          <div><label className="nb-label">Bio</label><textarea className="nb-input mt-1 min-h-[80px]" value={f.bio} onChange={set("bio")} data-testid="profile-bio" placeholder="What are you passionate about?" /></div>

          <TagEditor label="Skills" items={f.skills} color="bg-[#FFD166]" onChange={(v) => setF({ ...f, skills: v })} testid="profile-skills" />
          <TagEditor label="Interests" items={f.interests} color="bg-[#A0C4FF]" onChange={(v) => setF({ ...f, interests: v })} testid="profile-interests" />
          <TagEditor label="Looking for" items={f.looking_for} color="bg-white" onChange={(v) => setF({ ...f, looking_for: v })} testid="profile-looking" />

          <button className="nb-btn w-full justify-center" onClick={save} disabled={saving} data-testid="profile-save">
            <FloppyDisk size={18} weight="bold" /> {saving ? "Saving…" : "Save profile"}
          </button>
        </div>
      </div>
    </div>
  );
}
