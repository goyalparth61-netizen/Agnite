import { useEffect, useState } from "react";
import { Download, Copy, Check, Clock3 } from "lucide-react";
import type { Intelligence } from "../../ai/intelligence";
import { acquisitionStatus, intelligenceBrief } from "../../ai/decisionSupport";
import { downloadText } from "../../ai/workspaceData";

export default function DecisionSupport({ data }: { data: Intelligence }) {
  const [now, setNow] = useState(() => Date.now());
  const [message, setMessage] = useState("");
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 60000);
    return () => clearInterval(timer);
  }, []);
  useEffect(() => setMessage(""), [data]);
  if (!data.selected) return null;
  const freshness = acquisitionStatus(data.selected.observedAt, now);
  const checks = [
    {
      label: "Historical baseline",
      available: data.history.baselineFrp !== null,
      detail: "Mean of earlier distinct passes within 5 km.",
    },
    {
      label: "Repeated passes",
      available: data.history.distinctPasses >= 4,
      detail: `${data.history.distinctPasses} distinct passes loaded; gaps do not establish continuous heat.`,
    },
    {
      label: "Land-cover context",
      available: data.context.landCover !== "unknown",
      detail: "User-supplied context; no automatic verification.",
    },
    {
      label: "Industrial proximity",
      available: data.context.industrialDistanceKm !== null,
      detail: "User-supplied distance; no automatic site lookup.",
    },
    {
      label: "Wind context",
      available: data.context.windKph !== null,
      detail: "User-supplied measurement, not a weather forecast.",
    },
  ];
  async function copy() {
    try {
      await navigator.clipboard.writeText(intelligenceBrief(data));
      setMessage("Brief copied.");
    } catch {
      setMessage("Clipboard unavailable. Use Download brief instead.");
    }
  }
  return (
    <section className="intel-card decision-support">
      <span className="eyebrow">BEFORE YOU ACT</span>
      <h3>Evidence readiness</h3>
      <p className="acquisition-age">
        <Clock3 size={16} />
        {freshness.label}
      </p>
      {freshness.ageHours !== null && freshness.ageHours >= 24 && (
        <p className="evidence-chip">
          The 24-hour estimate window has ended. Load a newer acquisition before
          interpreting present risk.
        </p>
      )}
      <p>
        {checks.filter((c) => c.available).length} of {checks.length} input
        checks available. This is a completeness checklist, not confidence or
        accuracy.
      </p>
      <div className="readiness-grid">
        {checks.map((c) => (
          <div key={c.label}>
            <span
              className={`readiness-status ${c.available ? "available" : ""}`}
            >
              {c.available ? (
                <Check size={14} />
              ) : (
                <span aria-hidden="true">○</span>
              )}
              {c.available ? "Available" : "Missing"}
            </span>
            <strong>{c.label}</strong>
            <small>{c.detail}</small>
          </div>
        ))}
      </div>
      <div className="ws-actions">
        <button
          className="ws-button"
          onClick={() =>
            downloadText(
              "agnite-hotspot-brief.txt",
              intelligenceBrief(data),
              "text/plain;charset=utf-8",
            )
          }
        >
          <Download size={15} /> Download brief
        </button>
        <button className="ws-button" onClick={() => void copy()}>
          <Copy size={15} /> Copy brief
        </button>
      </div>
      {message && <p role="status">{message}</p>}
    </section>
  );
}
