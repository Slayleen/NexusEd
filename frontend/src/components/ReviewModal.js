import { useEffect, useState } from "react";
import { api, formatError } from "@/api";
import { Avatar } from "@/components/common";
import { Star, ShieldCheck, X } from "@phosphor-icons/react";
import { toast } from "sonner";

function StarRating({ value, onChange, size = 26, readOnly = false }) {
  const [hover, setHover] = useState(0);
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((n) => {
        const active = (hover || value) >= n;
        return (
          <button
            key={n}
            type="button"
            disabled={readOnly}
            onMouseEnter={() => !readOnly && setHover(n)}
            onMouseLeave={() => !readOnly && setHover(0)}
            onClick={() => !readOnly && onChange(n)}
            className={readOnly ? "cursor-default" : "cursor-pointer"}
            data-testid={readOnly ? undefined : `star-${n}`}
          >
            <Star size={size} weight={active ? "fill" : "regular"} className={active ? "text-[#FF7B54]" : "text-[#4A4A4A]"} />
          </button>
        );
      })}
    </div>
  );
}

export default function ReviewModal({ student, onClose, onSubmitted }) {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [rating, setRating] = useState(0);
  const [reliability, setReliability] = useState(90);
  const [comment, setComment] = useState("");
  const [saving, setSaving] = useState(false);

  const load = () => {
    setLoading(true);
    api.get(`/students/${student.id}/reviews`)
      .then((r) => setReviews(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };
  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [student.id]);

  const submit = async () => {
    if (!rating) { toast.error("Please pick a star rating."); return; }
    setSaving(true);
    try {
      await api.post(`/students/${student.id}/reviews`, { rating, reliability: Number(reliability), comment });
      toast.success(`Review submitted for ${student.name.split(" ")[0]}! 🌟`);
      setRating(0); setComment(""); setReliability(90);
      load();
      onSubmitted && onSubmitted();
    } catch (e) {
      toast.error(formatError(e?.response?.data?.detail));
    } finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" onClick={onClose} data-testid="review-modal">
      <div className="nb-card bg-[#FDFBF7] w-full max-w-lg max-h-[88vh] overflow-y-auto p-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <Avatar src={student.avatar} name={student.name} className="w-12 h-12" />
            <div>
              <div className="font-display text-xl font-bold">{student.name}</div>
              <div className="text-xs text-[#4A4A4A]">Collaborator reviews</div>
            </div>
          </div>
          <button onClick={onClose} className="nb-btn nb-btn-ghost p-2" data-testid="review-close"><X size={18} weight="bold" /></button>
        </div>

        {student.can_review ? (
          <div className="nb-card bg-white p-4 mb-5 space-y-3">
            <div className="nb-label">Leave a review</div>
            <div>
              <div className="text-sm font-bold mb-1">Overall rating</div>
              <StarRating value={rating} onChange={setRating} />
            </div>
            <div>
              <div className="flex items-center justify-between text-sm font-bold mb-1">
                <span className="flex items-center gap-1"><ShieldCheck size={16} weight="bold" /> Reliability</span>
                <span>{reliability}%</span>
              </div>
              <input type="range" min="0" max="100" step="5" value={reliability}
                onChange={(e) => setReliability(e.target.value)} className="w-full accent-[#FF7B54]" data-testid="review-reliability" />
            </div>
            <textarea className="nb-input min-h-[70px] w-full" placeholder="How was it working together?"
              value={comment} onChange={(e) => setComment(e.target.value)} data-testid="review-comment" />
            <button className="nb-btn w-full justify-center" onClick={submit} disabled={saving} data-testid="review-submit">
              {saving ? "Submitting…" : "Submit review"}
            </button>
          </div>
        ) : (
          <div className="nb-card bg-[#FFD166] p-3 mb-5 text-sm font-medium">
            You can review someone once you've collaborated on a project together.
          </div>
        )}

        <div className="nb-label mb-2">{reviews.length} review{reviews.length === 1 ? "" : "s"}</div>
        {loading ? (
          <div className="text-sm text-[#4A4A4A]">Loading…</div>
        ) : reviews.length === 0 ? (
          <div className="text-sm text-[#4A4A4A]">No reviews yet. Be the first collaborator to leave one.</div>
        ) : (
          <div className="space-y-3">
            {reviews.map((r) => (
              <div key={r.id} className="nb-card bg-white p-3" data-testid={`review-item-${r.id}`}>
                <div className="flex items-center gap-2 mb-1">
                  {r.reviewer?.avatar && <Avatar src={r.reviewer.avatar} name={r.reviewer?.name} className="w-8 h-8" />}
                  <div className="font-bold text-sm">{r.reviewer?.name || "Student"}</div>
                  <span className="ml-auto"><StarRating value={r.rating} readOnly size={16} /></span>
                </div>
                <div className="flex items-center gap-1 text-xs font-bold text-[#4A4A4A] mb-1">
                  <ShieldCheck size={14} weight="bold" /> {r.reliability}% reliable
                </div>
                {r.comment && <p className="text-sm text-[#4A4A4A]">{r.comment}</p>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
