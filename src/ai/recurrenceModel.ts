import artifact from './recurrence-model.json' with { type: 'json' };
import type { AnalysisContext, Observation } from './thermalEngine.ts';

export type RecurrenceWindow = '24h' | '48h' | '7d';

export interface RecurrencePrediction {
  window: RecurrenceWindow;
  score: number;
  threshold: number;
  targetPrecision: number;
  achievedPrecision: number | null;
  targetMet: boolean;
  modelVersion: string;
  trainingSource: string;
}

type HistoryLike = {
  rows: Observation[];
  baselineFrp: number | null;
  currentFrp: number | null;
};

type ExtendedObservation = Observation & {
  brightTi5?: number;
  confidence?: number | string;
  dayNight?: string;
  hotspotType?: number;
};

const sigmoid = (value: number) => 1 / (1 + Math.exp(-Math.max(-40, Math.min(40, value))));

const confidenceValue = (value: ExtendedObservation['confidence']) => {
  if (typeof value === 'number' && Number.isFinite(value)) return Math.max(0, Math.min(1, value / 100));
  const text = String(value ?? '').toLowerCase();
  if (text === 'h' || text === 'high') return 0.9;
  if (text === 'n' || text === 'nominal') return 0.6;
  if (text === 'l' || text === 'low') return 0.25;
  return 0.5;
};

function featureMap(selectedBase: Observation, history: HistoryLike, _context: AnalysisContext) {
  const selected = selectedBase as ExtendedObservation;
  const now = Date.parse(selected.observedAt);
  const prior = history.rows
    .filter(row => Date.parse(row.observedAt) < now)
    .sort((a, b) => Date.parse(a.observedAt) - Date.parse(b.observedAt));

  const inWindow = (hours: number) => prior.filter(row => Date.parse(row.observedAt) >= now - hours * 3_600_000);
  const prior24 = inWindow(24);
  const prior7 = inWindow(24 * 7);
  const prior30 = inWindow(24 * 30);
  const mean = (rows: Observation[]) => rows.length ? rows.reduce((sum, row) => sum + row.frp, 0) / rows.length : selected.frp;
  const mean7 = mean(prior7);
  const mean30 = mean(prior30);
  const previous = prior.length ? prior[prior.length - 1] : null;
  const gapHours = previous
    ? Math.min(24 * 30, Math.max(0, (now - Date.parse(previous.observedAt)) / 3_600_000))
    : 24 * 30;
  const days30 = new Set(prior30.map(row => new Date(row.observedAt).toISOString().slice(0, 10))).size;
  const timestamp = new Date(selected.observedAt);
  const hourUtc = timestamp.getUTCHours() + timestamp.getUTCMinutes() / 60;
  const month = timestamp.getUTCMonth();
  const monthAngle = 2 * Math.PI * month / 12;
  const hourAngle = 2 * Math.PI * hourUtc / 24;
  const isNightApprox = hourUtc < 6 || hourUtc >= 18 ? 1 : 0;
  const isNight = selected.dayNight ? Number(selected.dayNight.toUpperCase() === 'N') : isNightApprox;
  const staticSource = Number(selected.hotspotType === 2);
  const logFrp = Math.log1p(Math.max(0, selected.frp));
  const logCount24 = Math.log1p(prior24.length);
  const logCount7 = Math.log1p(prior7.length);
  const logCount30 = Math.log1p(prior30.length);
  const latScaled = (selected.latitude - 22) / 16;
  const lonScaled = (selected.longitude - 83) / 16;

  return {
    log_current_frp: logFrp,
    log_frp_vs_7d_mean: Math.log((selected.frp + 1) / (mean7 + 1)),
    log_frp_vs_30d_mean: Math.log((selected.frp + 1) / (mean30 + 1)),
    detections_24h: prior24.length,
    detections_7d: prior7.length,
    detections_30d: prior30.length,
    distinct_days_30d: days30,
    hours_since_previous: gapHours / 24,
    bright_ti4_scaled: selected.brightness === undefined ? 0 : Math.max(0, Math.min(500, selected.brightness)) / 500,
    bright_ti5_scaled: selected.brightTi5 === undefined ? 0 : Math.max(0, Math.min(500, selected.brightTi5)) / 500,
    confidence_scaled: confidenceValue(selected.confidence),
    is_night: isNight,
    static_source_type: staticSource,
    log_detections_24h: logCount24,
    log_detections_7d: logCount7,
    log_detections_30d: logCount30,
    persistence_7d_30d: prior7.length / Math.max(1, prior30.length),
    active_days_ratio_30d: days30 / 30,
    log_gap_hours: Math.log1p(gapHours),
    recent_repeat_48h: Number(gapHours <= 48),
    frp_x_log_detections_7d: logFrp * logCount7,
    frp_x_static_source: logFrp * staticSource,
    night_x_log_detections_7d: isNight * logCount7,
    month_sin: Math.sin(monthAngle),
    month_cos: Math.cos(monthAngle),
    hour_sin: Math.sin(hourAngle),
    hour_cos: Math.cos(hourAngle),
    latitude_scaled: latScaled,
    longitude_scaled: lonScaled,
    lat_lon_interaction: latScaled * lonScaled,
  } as Record<string, number>;
}

export function recurrencePredictions(
  selected: Observation | null,
  history: HistoryLike,
  context: AnalysisContext,
): RecurrencePrediction[] | null {
  if (!selected || !artifact.trained) return null;

  const names = artifact.featureNames as string[];
  const mean = artifact.scaler.mean as number[];
  const scale = artifact.scaler.scale as number[];
  const values = featureMap(selected, history, context);
  const raw = names.map(name => values[name]);

  if (
    !names.length ||
    raw.some(value => typeof value !== 'number' || !Number.isFinite(value)) ||
    mean.length !== raw.length ||
    scale.length !== raw.length
  ) return null;

  const standardized = raw.map((value, index) => (value - mean[index]) / (scale[index] || 1));

  return (['24h', '48h', '7d'] as const).flatMap(window => {
    const model = (artifact.models as Record<string, {
      coefficient: number[];
      intercept: number;
      decisionThreshold: {
        threshold: number;
        targetPrecision: number;
        achievedPrecision: number | null;
        targetMet: boolean;
      };
    }>)[window];

    if (!model || model.coefficient.length !== standardized.length) return [];
    const logit = model.intercept + model.coefficient.reduce(
      (sum, weight, index) => sum + weight * standardized[index],
      0,
    );

    return [{
      window,
      score: sigmoid(logit),
      threshold: model.decisionThreshold.threshold,
      targetPrecision: model.decisionThreshold.targetPrecision,
      achievedPrecision: model.decisionThreshold.achievedPrecision,
      targetMet: model.decisionThreshold.targetMet,
      modelVersion: artifact.version,
      trainingSource: artifact.trainingSource,
    }];
  });
}

export function recurrenceModelStatus() {
  return {
    trained: Boolean(artifact.trained),
    name: artifact.name,
    version: artifact.version,
    task: artifact.task,
    trainingSource: artifact.trainingSource,
    limitations: artifact.limitations,
  };
}
