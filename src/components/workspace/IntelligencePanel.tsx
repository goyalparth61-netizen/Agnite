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
  const currentSignal = h.currentFrp === null ? "No selected signal" : `${h.currentFrp.toFixed(1)} MW`;
  const baseline = h.baselineFrp === null ? "Needs an earlier pass" : `${h.baselineFrp.toFixed(1)} MW`;
  const deviation = h.anomalyPercent === null ? "Needs baseline" : `${h.anomalyPercent.toFixed(1)}%`;
  const persistence = h.persistenceScore === null ? "Needs ≥2 detected days" : `${h.persistenceScore.toFixed(1)} /100`;
  const recurrence = h.recurrencePerDay === null ? "Needs ≥24 h history" : `${h.recurrencePerDay.toFixed(1)} passes/day`;
  const peak = h.peakFrp === null ? "No observations" : `${h.peakFrp.toFixed(1)} MW`;
  const average = h.averageFrp === null ? "No observations" : `${h.averageFrp.toFixed(1)} MW`;
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
            ["Historical baseline", baseline],
            ["Current signal", currentSignal],
            ["Deviation", deviation],
            ["Persistence score", persistence],
            ["Recurrence", recurrence],
            ["Peak FRP", peak],
            ["Average FRP", average],
          ].map(([label, v]) => (
            <div className="ws-metric" key={label}>
              <span>{label}</span>
              <strong style={{ fontSize: "1.2rem" }}>{v}</strong>
            </div>
          ))}
        </div>
        {h.baselineFrp === null && (
          <div className="ws-notice">
            Baseline is not zero. AGNITE intentionally withholds it because no earlier satellite pass exists in the loaded history for this 5 km area. For live NASA data, switch the observation window to <strong>7 days</strong> or try another sensor to look for more prior passes.
          </div>
        )}
        <p>
          {h.repeatedDetections} repeated observation times · trend: {h.trend} ·{" "}
          {data.savedReports.length} relevant saved reports.
          <br />
          Earliest: {h.earliest ?? "No earlier pass loaded"} · latest: {h.latest ?? "No pass loaded"}
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
            calendar days in the loaded span; it needs detections on at least two
            calendar days. Recurrence is repeated distinct passes divided by elapsed
            days and needs at least 24 hours of observed span. Neither measures continuous burning.
          </p>
          <p>
            Gaps between passes, hours (latest 100):{" "}
            {h.gapsHours
              .slice(-100)
              .map((n) => n.toFixed(1))
              .join(", ") || "No inter-pass gap available yet"}
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
