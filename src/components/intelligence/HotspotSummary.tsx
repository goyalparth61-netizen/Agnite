import { sourceLabel, type Intelligence } from "../../ai/intelligence";
import DecisionSupport from "./DecisionSupport";
export default function HotspotSummary({ data }: { data: Intelligence }) {
  const s = data.selected;
  if (!s) return null;
  const metadata = s as typeof s & { sensor?: string; confidence?: string | number };
  const prediction = data.predictions[0];
  return (
    <>
      <section className="intel-card">
        <span className="eyebrow">
          HOTSPOT INTELLIGENCE · {sourceLabel(s.source)}
        </span>
        <h2>
          {s.latitude.toFixed(4)}°, {s.longitude.toFixed(4)}°
        </h2>
        <p>
          Selected thermal detection · Acquisition:{" "}
          {new Date(s.observedAt).toLocaleString()}
        </p>
        <div className="intel-grid">
          {[
            ["Current FRP", `${s.frp.toFixed(1)} MW`],
            [
              "Satellite brightness",
              s.brightness === undefined ? "Not reported by source" : `${s.brightness} K`,
            ],
            ["Sensor / source", metadata.sensor ?? sourceLabel(s.source)],
            ["Detection confidence", metadata.confidence === undefined ? "Not reported by source" : String(metadata.confidence)],
            [
              "Classification",
              data.report?.classification ?? "Run site analysis",
            ],
            [
              "Risk / recurrence score",
              prediction ? `${prediction.riskScore} /100` : "Needs selected evidence",
            ],
            [
              "Nearby detections",
              `${data.history.totalDetections} within 5 km, at or before acquisition`,
            ],
            ["Land cover (analysis context)", data.context.landCover === "unknown" ? "Context not established" : data.context.landCover],
            [
              "Industrial proximity (analysis context)",
              data.context.industrialDistanceKm === null
                ? "Context not established"
                : `${data.context.industrialDistanceKm} km`,
            ],
          ].map(([label, value]) => (
            <div className="intel-metric" key={label}>
              <small>{label}</small>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
        <p>
          History: {data.history.historicalDetections} earlier thermal
          detections; {data.history.trend} recent trend. Future recurrence/risk:{" "}
          {prediction ? `${prediction.level}, with ${prediction.confidence.toLowerCase()} evidence confidence` : "needs more selected evidence"}.
        </p>
        <p>
          AGNITE explanation:{" "}
          {data.report?.summary ??
            "FRP indicates detected thermal energy. History and local context are used when available; run site analysis for classification evidence."}
        </p>
        <small>
          Missing values are kept explicitly unknown rather than guessed. Brightness is a satellite measurement, not ground temperature.
          Classification confidence is uncalibrated; detections are not confirmed incidents.
        </small>
      </section>
      <DecisionSupport data={data} />
    </>
  );
}
