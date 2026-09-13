import { sourceLabel, type Intelligence } from "./intelligence";
import { distanceKm } from "./workspaceData";
import type { Observation, ObservationCoordinates } from "./thermalEngine";

export function acquisitionStatus(observedAt: string, now = Date.now()) {
  const ageHours = (now - Date.parse(observedAt)) / 3600000;
  if (!Number.isFinite(ageHours))
    return { label: "Acquisition time unavailable", ageHours: null };
  if (ageHours < 0)
    return { label: "Future-dated acquisition — check input", ageHours };
  return {
    label: `Acquired ${ageHours < 1 ? "less than 1 hour" : `${Math.floor(ageHours)} hours`} ago`,
    ageHours,
  };
}

/** One most recent observation per exact coordinate; bounded work for UI analysis. */
export function nearbyCandidates(
  observations: Observation[],
  location: ObservationCoordinates,
  radiusKm: number,
  maxAgeHours: number | null,
  now = Date.now(),
) {
  if (!Number.isFinite(radiusKm) || radiusKm < 1 || radiusKm > 500) return [];
  const locations = new Map<string, { row: Observation; distance: number }>();
  for (const row of observations) {
    const age = (now - Date.parse(row.observedAt)) / 3600000;
    if (
      !Number.isFinite(age) ||
      age < 0 ||
      (maxAgeHours !== null && age > maxAgeHours)
    )
      continue;
    const distance = distanceKm(row, location);
    if (!Number.isFinite(distance) || distance > radiusKm) continue;
    const key = `${row.source}:${row.latitude}:${row.longitude}`;
    const previous = locations.get(key);
    if (
      !previous ||
      Date.parse(row.observedAt) > Date.parse(previous.row.observedAt)
    )
      locations.set(key, { row, distance });
  }
  return [...locations.values()]
    .sort(
      (a, b) =>
        a.distance - b.distance ||
        Date.parse(b.row.observedAt) - Date.parse(a.row.observedAt),
    )
    .slice(0, 5);
}

export function intelligenceBrief(data: Intelligence, now = Date.now()) {
  const s = data.selected;
  if (!s) return "Select a hotspot to export an intelligence brief.";
  const h = data.history;
  return [
    "AGNITE | SELECTED HOTSPOT BRIEF",
    `Exported: ${new Date(now).toISOString()}`,
    `Source: ${sourceLabel(s.source)}`,
    `History sources: ${[...new Set(h.rows.map((r) => sourceLabel(r.source)))].join(", ")}`,
    `Coordinates: ${s.latitude.toFixed(4)}, ${s.longitude.toFixed(4)}`,
    `Acquisition: ${s.observedAt} | ${acquisitionStatus(s.observedAt, now).label}`,
    `FRP: ${s.frp} MW | Brightness: ${s.brightness === undefined ? "Unavailable" : `${s.brightness} K (satellite brightness)`}`,
    "",
    "CLASSIFICATION",
    data.report?.classification ?? "Unavailable",
    data.report?.summary ?? "Insufficient analyzed evidence.",
    "Experimental model; not a verified fire cause or calibrated confidence.",
    "",
    "HISTORICAL THERMAL ACTIVITY",
    `${h.historicalDetections} previous detections; ${h.distinctPasses} distinct passes; ${h.radiusKm} km radius.`,
    `Earliest: ${h.earliest ?? "Unavailable"} | Latest: ${h.latest ?? "Unavailable"}`,
    `Prior-pass mean baseline: ${h.baselineFrp?.toFixed(1) ?? "Unavailable"} MW | Deviation: ${h.anomalyPercent === null ? "Unavailable" : `${h.anomalyPercent.toFixed(1)}%`} | Trend: ${h.trend}`,
    "",
    "RISK ESTIMATE / SIMULATION — NOT FIRE PROBABILITY",
    ...data.predictions.map(
      (p) =>
        `${p.window} from acquisition: ${p.riskScore}/100 ${p.level}; evidence confidence ${p.confidence}`,
    ),
    "",
    "SUPPLIED CONTEXT",
    `Land cover: ${data.context.landCover}; industrial distance: ${data.context.industrialDistanceKm ?? "Unknown"} km; wind: ${data.context.windKph ?? "Unknown"} km/h.`,
    "",
    "EVIDENCE",
    ...(data.report?.evidence.map(
      (e) => `${e.label}: ${e.value}. ${e.detail}`,
    ) ?? ["Classification evidence unavailable."]),
    "",
    "MISSING EVIDENCE",
    ...(data.predictions[0]?.missingEvidence ?? []),
    "Field verification and validated incident labels are unavailable.",
    "",
    "LIMITATIONS",
    data.limitations,
    data.predictions[0]?.explanation ?? "No risk estimate available.",
    "Old acquisitions do not establish present conditions. Follow official local guidance.",
  ].join("\n");
}
