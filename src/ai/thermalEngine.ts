import model from "./model.json";

export interface Observation {
  id: string;
  latitude: number;
  longitude: number;
  observedAt: string;
  frp: number;
  brightness?: number;
  source: "demo" | "imported" | "manual" | "firms";
}

export type ObservationCoordinates = Pick<Observation, "latitude" | "longitude">;

export interface AnalysisContext {
  industrialDistanceKm: number | null;
  landCover: "forest" | "urban" | "industrial" | "other" | "unknown";
  windKph: number | null;
}

export type ThermalClass = "Industrial Fire" | "Persistent Industrial Heat" | "Forest / Natural Fire" | "Other Thermal Anomaly";

export interface AnalysisResult {
  model: { name: string; version: string; trainingSource: string; syntheticValidationAccuracy: number; sampleCount: number; limitations: string[] };
  classification: ThermalClass | "Insufficient evidence";
  status: "classified" | "abstained";
  /** Relative softmax score, never a calibrated probability or confidence. */
  modelScore: number | null;
  scores: { label: string; score: number }[];
  risk: { index: number; level: "Low" | "Moderate" | "High" | "Critical"; method: string };
  summary: string;
  evidence: { label: string; value: string; detail: string }[];
  contributions: { feature: string; value: number; contribution: number; direction: "supports" | "opposes" }[];
  history: { observedAt: string; frp: number; baseline: number | null }[];
  statistics: {
    included: number; excluded: number; distinctTimes: number; spanHours: number;
    currentFrp: number; baselineFrp: number | null; changePercent: number | null;
    persistence: number; center: { latitude: number; longitude: number };
  };
  scenarios: { horizon: "24h" | "48h" | "7d"; low: number; central: number; high: number; label: string; assumption: string }[];
  warnings: string[];
}

const DAY = 86_400_000;
const clamp = (value: number, low = 0, high = 1) => Math.min(high, Math.max(low, value));
const round = (value: number, places = 1) => Number(value.toFixed(places));
const median = (values: number[]) => {
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
};

function validUtcTimestamp(value: unknown): value is string {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?Z$/.test(value)) return false;
  const timestamp = Date.parse(value);
  if (!Number.isFinite(timestamp)) return false;
  const canonical = new Date(timestamp).toISOString();
  // Date.parse normalizes invalid days such as February 30; reject those too.
  return canonical.slice(0, 19) === value.slice(0, 19);
}

function distanceKm(a: ObservationCoordinates, b: ObservationCoordinates) {
  const rad = Math.PI / 180;
  const dLat = (a.latitude - b.latitude) * rad;
  const dLon = (a.longitude - b.longitude) * rad;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.latitude * rad) * Math.cos(b.latitude * rad) * Math.sin(dLon / 2) ** 2;
  return 6371 * 2 * Math.atan2(Math.sqrt(clamp(h)), Math.sqrt(1 - clamp(h)));
}

/** Strict validation is exported so upload/feed adapters can use the same rules. */
export function validateObservations(observations: Observation[]): void {
  if (!Array.isArray(observations) || observations.length === 0) throw new Error("Add at least one observation before analysis.");
  if (observations.length > 50_000) throw new Error("Analyze at most 50,000 observations at a time.");
  observations.forEach((row, index) => {
    const prefix = `Observation ${index + 1}`;
    if (!row || typeof row !== "object") throw new Error(`${prefix}: invalid record.`);
    if (typeof row.id !== "string" || !row.id.trim()) throw new Error(`${prefix}: id is required.`);
    if (!Number.isFinite(row.latitude) || row.latitude < -90 || row.latitude > 90) throw new Error(`${prefix}: latitude must be between -90 and 90.`);
    if (!Number.isFinite(row.longitude) || row.longitude < -180 || row.longitude > 180) throw new Error(`${prefix}: longitude must be between -180 and 180.`);
    if (!validUtcTimestamp(row.observedAt)) throw new Error(`${prefix}: observedAt must be a valid UTC timestamp, for example 2026-09-13T12:30:00Z.`);
    if (!Number.isFinite(row.frp) || row.frp < 0 || row.frp > 1_000_000) throw new Error(`${prefix}: FRP must be a finite number from 0 to 1,000,000 MW.`);
    if (row.brightness !== undefined && (!Number.isFinite(row.brightness) || row.brightness <= 0)) throw new Error(`${prefix}: brightness must be a positive finite Kelvin value.`);
    if (!["demo", "imported", "manual", "firms"].includes(row.source)) throw new Error(`${prefix}: unsupported source.`);
  });
}

function validateContext(context: AnalysisContext) {
  if (!context || !["forest", "urban", "industrial", "other", "unknown"].includes(context.landCover)) throw new Error("Choose a valid land-cover context.");
  if (context.industrialDistanceKm !== null && (!Number.isFinite(context.industrialDistanceKm) || context.industrialDistanceKm < 0)) throw new Error("Industrial distance must be a non-negative number, or unknown.");
  if (context.windKph !== null && (!Number.isFinite(context.windKph) || context.windKph < 0 || context.windKph > 500)) throw new Error("Wind must be between 0 and 500 km/h, or unknown.");
}

const featureLabels = ["Current FRP (log)", "Current / baseline change (log)", "Observed day coverage", "Industrial proximity", "Forest cover", "Industrial cover", "Urban cover", "User-supplied wind"];

export function analyzeObservations(observations: Observation[], context: AnalysisContext, siteCenter?: ObservationCoordinates): AnalysisResult {
  validateObservations(observations);
  validateContext(context);
  if (siteCenter !== undefined && (!siteCenter || !Number.isFinite(siteCenter.latitude) || Math.abs(siteCenter.latitude) > 90 || !Number.isFinite(siteCenter.longitude) || Math.abs(siteCenter.longitude) > 180)) throw new Error("Site center must contain a latitude from -90 to 90 and longitude from -180 to 180.");
  const warnings = [
    "Experimental classifier trained only on synthetic examples; no field validation. Model scores are not calibrated confidence or fire probabilities.",
    "A thermal detection does not establish a fire cause. Verify observations and local conditions before operational decisions.",
  ];
  const seenIds = new Set<string>();
  const seenMeasurements = new Set<string>();
  const unique = observations.filter((row) => {
    const key = `${Date.parse(row.observedAt)}:${row.latitude.toFixed(5)}:${row.longitude.toFixed(5)}`;
    if (seenIds.has(row.id) || seenMeasurements.has(key)) return false;
    seenIds.add(row.id);
    seenMeasurements.add(key);
    return true;
  }).sort((a, b) => Date.parse(a.observedAt) - Date.parse(b.observedAt) || a.id.localeCompare(b.id));
  const center = siteCenter ?? unique[unique.length - 1];
  const atSite = unique.filter((row) => distanceKm(row, center) < 5);
  if (!atSite.length) throw new Error("No observations were found within 5 km of the selected site.");
  // Anchor time to the latest detection at this site, never to a newer remote site.
  const latest = Date.parse(atSite[atSite.length - 1].observedAt);
  const nearby = atSite.filter((row) => latest - Date.parse(row.observedAt) <= 30 * DAY);
  if (unique.length !== observations.length) warnings.push(`${observations.length - unique.length} duplicate records were excluded.`);
  if (nearby.length !== unique.length) warnings.push(`${unique.length - nearby.length} observations outside 5 km of ${siteCenter ? "the selected site" : "the latest detection"} or older than 30 days were excluded.`);
  if (nearby.some((row) => row.source === "demo")) warnings.push("DEMO / SIMULATION: this analysis includes synthetic observations and does not describe a verified event.");
  if (nearby.some((row) => row.source === "imported" || row.source === "manual")) warnings.push("Uploaded/manual observation provenance has not been independently verified.");
  if (nearby.some((row) => row.source === "firms")) warnings.push("NASA FIRMS observations are detection inputs; NASA has not supplied or endorsed this model's classification.");
  if (context.windKph === null) warnings.push("Wind is unknown; no observed weather or weather forecast is used.");
  warnings.push("Day coverage describes supplied detection days only; missing passes, cloud and non-detections are unknown.");

  // Use mean FRP per detection at each pass, avoiding a jump caused only by
  // importing more pixels in one overpass. It is not total incident energy.
  const grouped = new Map<number, number[]>();
  nearby.forEach((row) => {
    const timestamp = Date.parse(row.observedAt);
    const group = grouped.get(timestamp) ?? [];
    group.push(row.frp);
    grouped.set(timestamp, group);
  });
  const series = [...grouped.entries()].sort(([a], [b]) => a - b).map(([timestamp, values]) => ({ timestamp, frp: values.reduce((sum, value) => sum + value, 0) / values.length }));
  const baselinePoints = series.filter((point) => point.timestamp < latest - DAY);
  const baselineFrp = baselinePoints.length ? median(baselinePoints.map((point) => point.frp)) : null;
  const currentFrp = series[series.length - 1].frp;
  const spanHours = (latest - series[0].timestamp) / 3_600_000;
  const days = new Set(nearby.map((row) => new Date(row.observedAt).toISOString().slice(0, 10))).size;
  const calendarSpanDays = Math.floor(latest / DAY) - Math.floor(series[0].timestamp / DAY) + 1;
  const persistence = days / calendarSpanDays;
  const relativeChange = baselineFrp !== null && baselineFrp > 0 ? (currentFrp / baselineFrp - 1) * 100 : null;
  const changePercent = relativeChange !== null && Number.isFinite(relativeChange) ? relativeChange : null;
  if (relativeChange !== null && !Number.isFinite(relativeChange)) warnings.push("Relative baseline change exceeds the supported numeric range and is unavailable.");
  const logRatio = baselineFrp === null ? 0 : Math.log((currentFrp + 1) / (baselineFrp + 1));
  const features = [Math.log1p(currentFrp), logRatio, persistence, context.industrialDistanceKm === null ? 0 : 1 / (1 + context.industrialDistanceKm / 2), Number(context.landCover === "forest"), Number(context.landCover === "industrial"), Number(context.landCover === "urban"), Math.min(context.windKph ?? 12, 100) / 50];
  const scaled = features.map((feature, index) => (feature - model.means[index]) / model.scales[index]);
  const reasons: string[] = [];
  if (series.length < 4 || baselinePoints.length < 2 || spanHours < 48) reasons.push("At least four distinct observation times spanning 48 hours, including two baseline passes older than 24 hours, are required.");
  if (context.landCover === "unknown" || context.industrialDistanceKm === null) reasons.push("Land cover and industrial distance are required to distinguish thermal causes.");
  if (scaled.some((value, index) => index < 2 && Math.abs(value) > 6)) reasons.push("Thermal measurements are outside this synthetic model's supported range.");

  const logits = model.weights.map((weights, k) => model.bias[k] + weights.reduce((sum, weight, j) => sum + weight * scaled[j], 0));
  const maxLogit = Math.max(...logits);
  const exponentials = logits.map((value) => Math.exp(value - maxLogit));
  const total = exponentials.reduce((sum, value) => sum + value, 0);
  const ranked = exponentials.map((value, index) => ({ index, label: model.classes[index], score: value / total })).sort((a, b) => b.score - a.score);
  if (!reasons.length && (ranked[0].score < 0.5 || ranked[0].score - ranked[1].score < 0.14)) reasons.push("The synthetic model does not separate the candidate classes clearly enough.");
  const abstained = reasons.length > 0;
  warnings.push(...reasons);
  const contributions = abstained ? [] : features.map((value, j) => {
    const contribution = (model.weights[ranked[0].index][j] - model.weights[ranked[1].index][j]) * scaled[j];
    return { feature: featureLabels[j], value: round(value, 3), contribution: round(contribution, 3), direction: contribution >= 0 ? "supports" as const : "opposes" as const };
  }).sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));

  // Transparent heuristic; this is independent of learned class scores.
  const intensity = clamp(Math.log1p(currentFrp) / Math.log(201));
  const escalation = clamp(logRatio / Math.log(5));
  const repeatSupport = clamp((days - 1) / 6);
  const windSupport = context.landCover === "forest" && context.windKph !== null ? clamp(context.windKph / 60) : 0;
  const riskIndex = Math.round(100 * clamp(0.5 * intensity + 0.3 * escalation + 0.1 * repeatSupport + 0.1 * windSupport));
  const horizons = [{ horizon: "24h" as const, multiplier: 1 }, { horizon: "48h" as const, multiplier: 1.5 }, { horizon: "7d" as const, multiplier: 2.5 }];
  const scenarios = horizons.map(({ horizon, multiplier }) => ({
    horizon,
    low: Math.round(clamp(riskIndex - 12 * multiplier, 0, 100)),
    central: riskIndex,
    high: Math.round(clamp(riskIndex + (12 + windSupport * 8) * multiplier, 0, 100)),
    label: "WHAT-IF heuristic index range",
    assumption: `Illustrative easing / unchanged / escalating thermal conditions over ${horizon}. Central assumes unchanged inputs; wider ranges are chosen scenario bounds, not statistical intervals or weather forecasts.`,
  }));
  const classification = abstained ? "Insufficient evidence" : ranked[0].label as ThermalClass;
  const baselineDescription = baselineFrp === null ? "No baseline passes older than 24h" : `${round(baselineFrp)} MW median of ${baselinePoints.length} earlier pass means`;
  return {
    model: { name: model.name, version: model.version, trainingSource: model.trainingSource, syntheticValidationAccuracy: model.syntheticValidationAccuracy, sampleCount: model.trainingCount, limitations: model.limitations },
    classification,
    status: abstained ? "abstained" : "classified",
    modelScore: abstained ? null : ranked[0].score,
    scores: abstained ? [] : ranked.map(({ label, score }) => ({ label, score })),
    risk: { index: riskIndex, level: riskIndex >= 80 ? "Critical" : riskIndex >= 60 ? "High" : riskIndex >= 35 ? "Moderate" : "Low", method: "Heuristic 0–100 screening index: 50% log FRP intensity + 30% positive baseline change + 10% repeated-day support + 10% supplied forest wind. Not a fire probability; missing baseline/weather terms contribute zero." },
    summary: abstained ? "Cause classification withheld: additional history or verified context is needed. The screening index summarizes only the supplied measurements." : `${classification} is the strongest synthetic-model pattern. This experimental label does not establish a real fire cause.`,
    evidence: [
      { label: "Current thermal signal", value: `${round(currentFrp)} MW`, detail: "Mean FRP per detection at the latest timestamp within 5 km; not total incident energy." },
      { label: "Historical baseline", value: baselineFrp === null ? "Unavailable" : `${round(baselineFrp)} MW`, detail: baselineDescription },
      { label: "Change from baseline", value: changePercent === null ? "Unavailable" : `${changePercent >= 0 ? "+" : ""}${round(changePercent)}%`, detail: "Latest pass mean compared with median earlier pass means; sensor and sampling differences are not corrected." },
      { label: "Repeated detection days", value: `${days} / ${calendarSpanDays} supplied days`, detail: "Detection-day coverage is not continuous burning or an estimate of non-detection frequency." },
      { label: "Spatial context", value: `${context.landCover}; industry ${context.industrialDistanceKm === null ? "unknown" : `${context.industrialDistanceKm} km`}`, detail: "User-supplied assumptions; no automatic land-cover or facility verification." },
    ],
    contributions,
    history: series.map((point) => ({ observedAt: new Date(point.timestamp).toISOString(), frp: round(point.frp, 2), baseline: baselineFrp === null ? null : round(baselineFrp, 2) })),
    statistics: { included: nearby.length, excluded: observations.length - nearby.length, distinctTimes: series.length, spanHours: round(spanHours), currentFrp: round(currentFrp, 2), baselineFrp: baselineFrp === null ? null : round(baselineFrp, 2), changePercent: changePercent === null ? null : round(changePercent), persistence: round(persistence, 3), center: { latitude: center.latitude, longitude: center.longitude } },
    scenarios,
    warnings,
  };
}
