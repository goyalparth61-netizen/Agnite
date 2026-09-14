import artifact from './recurrence-model.json';
import type { AnalysisContext, Observation } from './thermalEngine';

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

const DAY = 86_400_000;
const sigmoid = (value: number) => 1 / (1 + Math.exp(-Math.max(-40, Math.min(40, value))));
const confidenceValue = (value: Observation['confidence']) => {
  if (typeof value === 'number' && Number.isFinite(value)) return Math.max(0, Math.min(1, value / 100));
  const text = String(value ?? '').toLowerCase();
  if (text === 'h' || text === 'high') return 0.9;
  if (text === 'n' || text === 'nominal') return 0.6;
  if (text === 'l' || text === 'low') return 0.25;
  return 0.5;
};

function features(selected: Observation, history: HistoryLike, _context: AnalysisContext) {
  const now = Date.parse(selected.observedAt);
  const prior = history.rows.filter(row => Date.parse(row.observedAt) < now);
  const inWindow = (hours: number) => prior.filter(row => Date.parse(row.observedAt) >= now - hours * 3_600_000);
  const prior7 = inWindow(24 * 7);
  const prior30 = inWindow(24 * 30);
  const mean = (rows: Observation[]) => rows.length ? rows.reduce((sum, row) => sum + row.frp, 0) / rows.length : selected.frp;
  const mean7 = mean(prior7);
  const mean30 = mean(prior30);
  const previous = prior.length ? prior[prior.length - 1] : null;
  const gapHours = previous ? Math.min(24 * 30, Math.max(0, (now - Date.parse(previous.observedAt)) / 3_600_000)) : 24 * 30;
  const days30 = new Set(prior30.map(row => new Date(row.observedAt).toISOString().slice(0, 10))).size;
  const hourUtc = new Date(selected.observedAt).getUTCHours();
  const isNightApprox = hourUtc < 6 || hourUtc >= 18 ? 1 : 0;
  return [
    Math.log1p(Math.max(0, selected.frp)),
    Math.log((selected.frp + 1) / (mean7 + 1)),
    Math.log((selected.frp + 1) / (mean30 + 1)),
    inWindow(24).length,
    prior7.length,
    prior30.length,
    days30,
    gapHours / 24,
    selected.brightness === undefined ? 0 : Math.max(0, Math.min(500, selected.brightness)) / 500,
    selected.brightTi5 === undefined ? 0 : Math.max(0, Math.min(500, selected.brightTi5)) / 500,
    confidenceValue(selected.confidence),
    selected.dayNight ? Number(selected.dayNight.toUpperCase() === 'N') : isNightApprox,
    Number(selected.hotspotType === 2),
  ];
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
  const raw = features(selected, history, context);
  if (!names.length || raw.length !== names.length || mean.length !== raw.length || scale.length !== raw.length) return null;
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
    const logit = model.intercept + model.coefficient.reduce((sum, weight, index) => sum + weight * standardized[index], 0);
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
