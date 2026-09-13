import RiskOverview from "../risk/RiskOverview";
import ExplainabilityPanel from "../intelligence/ExplainabilityPanel";
import PersistentHeatComparison from "../intelligence/PersistentHeatComparison";
import { Reveal } from "../common/SectionHeader";
import { useState } from "react";
import { sourceLabel, type Intelligence } from "../../ai/intelligence";

export default function IntelligencePanel({
  data,
  ask,
}: {
  data: Intelligence;
  ask: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  if (!data.selected) return null;
  const h = data.history;
  const rows = expanded ? h.rows.slice(-200) : h.rows.slice(-8);
  const value = (n: number | null, suffix = "") =>
    n === null ? "Unavailable" : `${n.toFixed(1)}${suffix}`;
  return (
    <>
      <section className="ws-panel">
        <span className="ws-kicker">
          SELECT → SIGNAL → HISTORY → BASELINE → CLASSIFICATION → RISK →
          EXPLANATION → ACTION
        </span>
        <h2>Historical Intelligence</h2>
        <p>
          {sourceLabel(data.selected.source)} · Selected acquisition:{" "}
          {new Date(data.selected.observedAt).toLocaleString()} · {h.radiusKm}{" "}
          km radius
        </p>
        <div className="ws-metrics">
          {[
            ["Historical detections", String(h.historicalDetections)],
            ["Historical baseline", value(h.baselineFrp, " MW")],
            ["Current signal", value(h.currentFrp, " MW")],
            ["Deviation", value(h.anomalyPercent, "%")],
            ["Persistence score", value(h.persistenceScore, " /100")],
            ["Recurrence", value(h.recurrencePerDay, " passes/day")],
            ["Peak FRP", value(h.peakFrp, " MW")],
            ["Average FRP", value(h.averageFrp, " MW")],
          ].map(([label, v]) => (
            <div className="ws-metric" key={label}>
              <span>{label}</span>
              <strong style={{ fontSize: "1.2rem" }}>{v}</strong>
            </div>
          ))}
        </div>
        <p>
          {h.repeatedDetections} repeated observation times · trend: {h.trend} ·{" "}
          {data.savedReports.length} relevant saved reports.
          <br />
          Earliest: {h.earliest} · latest: {h.latest}
        </p>
        <Reveal>
          <ol
            className="ws-list thermal-timeline"
            aria-label="Historical thermal timeline"
          >
            {rows.map((row, i) => (
              <li className="ws-list-item" key={`${row.source}-${row.id}-${i}`}>
                <div>
                  <span className="ws-kicker">
                    {new Date(row.observedAt).toLocaleString()}
                  </span>
                  <h3>
                    {row.id === data.selected?.id
                      ? "Current observation"
                      : i
                        ? "Repeated thermal observation"
                        : "Thermal detection"}
                  </h3>
                  <p>
                    FRP: {row.frp.toFixed(1)} MW · {sourceLabel(row.source)}
                    {row.brightness !== undefined
                      ? ` · Satellite brightness: ${row.brightness} K`
                      : ""}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        </Reveal>
        {h.rows.length > 8 && (
          <button className="ws-button" onClick={() => setExpanded(!expanded)}>
            {expanded
              ? "Show recent 8"
              : "Expand timeline (up to 200 detections)"}
          </button>
        )}
        <details>
          <summary>History method and observation gaps</summary>
          <p>
            {data.limitations} Persistence is detected calendar days divided by
            calendar days in the loaded span; unavailable for a single detected
            day. Recurrence is repeated distinct passes divided by elapsed days,
            available after 24 hours. Neither measures continuous burning.
          </p>
          <p>
            Gaps between passes, hours (latest 100):{" "}
            {h.gapsHours
              .slice(-100)
              .map((n) => n.toFixed(1))
              .join(", ") || "Unavailable"}
          </p>
        </details>
      </section>
      <ExplainabilityPanel data={data} />
      <PersistentHeatComparison />
      <RiskOverview data={data} />
      <button className="ws-button primary" onClick={ask}>
        Ask AGNITE about this evidence
      </button>
    </>
  );
}
