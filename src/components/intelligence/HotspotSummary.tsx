import { sourceLabel, type Intelligence } from "../../ai/intelligence";
import DecisionSupport from "./DecisionSupport";
export default function HotspotSummary({ data }: { data: Intelligence }) {
  const s = data.selected;
  if (!s) return null;
  const metadata = s as typeof s & { sensor?: string; confidence?: string };
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
          Location name unavailable · Acquisition:{" "}
          {new Date(s.observedAt).toLocaleString()}
        </p>
        <div className="intel-grid">
          {[
            ["Current FRP", `${s.frp.toFixed(1)} MW`],
            [
              "Satellite brightness",
              s.brightness === undefined ? "Unavailable" : `${s.brightness} K`,
            ],
            ["Sensor / source", metadata.sensor ?? sourceLabel(s.source)],
            ["Detection confidence", metadata.confidence ?? "Unavailable"],
            [
              "Classification",
              data.report?.classification ?? "Run site analysis",
            ],
            [
              "Risk estimate",
              `${data.predictions[0]?.riskScore ?? "Unavailable"} /100`,
            ],
            [
              "Nearby detections",
              `${data.history.totalDetections} within 5 km, at or before acquisition`,
            ],
            ["Land cover (supplied)", data.context.landCover],
            [
              "Industrial proximity (supplied)",
              data.context.industrialDistanceKm === null
                ? "Unavailable"
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
          detections; {data.history.trend} recent trend. Future risk:{" "}
          {data.predictions[0]?.level}, with{" "}
          {data.predictions[0]?.confidence.toLowerCase()} evidence confidence.
        </p>
        <p>
          AGNITE explanation:{" "}
          {data.report?.summary ??
            "FRP indicates detected thermal energy. History and local context are required to assess its likely origin; run site analysis for classification evidence."}
        </p>
        <small>
          Brightness is a satellite measurement, not ground temperature.
          Classification confidence is uncalibrated; detections are not
          confirmed incidents.
        </small>
      </section>
      <DecisionSupport data={data} />
    </>
  );
}
