import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { stripTypeScriptTypes } from 'node:module';
import ts from 'typescript';

const model = JSON.parse(await readFile(new URL('../src/ai/model.json', import.meta.url), 'utf8'));
const source = await readFile(new URL('../src/ai/thermalEngine.ts', import.meta.url), 'utf8');
const inlineSource = source.replace(/^import model from ["']\.\/model\.json["'];?/m, `const model = ${JSON.stringify(model)};`);
// TypeScript 7 removed the legacy compiler API; Node 24 supplies a native fallback.
const javascript = typeof ts.transpileModule === 'function'
  ? ts.transpileModule(inlineSource, { compilerOptions: { target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.ESNext } }).outputText
  : stripTypeScriptTypes(inlineSource, { mode: 'strip' });
const { analyzeObservations, validateObservations } = await import(`data:text/javascript;base64,${Buffer.from(javascript).toString('base64')}`);

const DAY = 86_400_000;
const latest = Date.parse('2026-09-13T12:00:00Z');
const context = { landCover: 'industrial', industrialDistanceKm: 0.5, windKph: 12 };
const observation = (id = 'one', daysAgo = 0, frp = 20, extras = {}) => ({
  id, latitude: 21.1466, longitude: 79.0889,
  observedAt: new Date(latest - daysAgo * DAY).toISOString(), frp, source: 'imported', ...extras,
});
const history = (values, ages = values.map((_, index) => values.length - 1 - index)) => values.map((value, index) => observation(`pass-${index}`, ages[index], value));
const rising = history([18, 21, 19, 20, 55, 100]);

assert.throws(() => validateObservations([]), /at least one/);
assert.throws(() => validateObservations(null), /at least one/);
assert.throws(() => validateObservations(Array(50_001).fill(observation())), /50,000/);
assert.doesNotThrow(() => validateObservations(Array(50_000).fill(observation())));
assert.throws(() => validateObservations([null]), /invalid record/);
for (const invalid of [
  { id: '' }, { id: '  ' }, { id: 1 },
  { latitude: NaN }, { latitude: 91 }, { latitude: -91 }, { latitude: '21' },
  { longitude: Infinity }, { longitude: 181 }, { longitude: -181 },
  { frp: NaN }, { frp: Infinity }, { frp: -1 }, { frp: 1_000_001 }, { frp: '20' },
  { brightness: 0 }, { brightness: -1 }, { brightness: Infinity },
  { observedAt: '2026-02-30T12:00:00Z' }, { observedAt: '2026-02-29T12:00:00Z' },
  { observedAt: '2026-09-13T24:00:00Z' }, { observedAt: '2026-09-13T12:60:00Z' },
  { observedAt: '2026-09-13T12:00:60Z' }, { observedAt: '2026-09-13T12:00:00' },
  { observedAt: '2026-09-13T17:30:00+05:30' }, { observedAt: '' },
  { source: 'verified' }, { source: null },
]) assert.throws(() => validateObservations([observation('invalid', 0, 20, invalid)]), /Observation 1:/, JSON.stringify(invalid));
for (const valid of [
  { latitude: -90, longitude: -180, frp: 0 },
  { latitude: 90, longitude: 180, frp: 1_000_000 },
  { observedAt: '2024-02-29T23:59:59.999Z' },
  ...['demo', 'manual', 'imported', 'firms'].map((source) => ({ source })),
]) assert.doesNotThrow(() => validateObservations([observation('valid', 0, 20, valid)]));
for (const invalidContext of [
  null, {}, { ...context, landCover: 'water' },
  { ...context, industrialDistanceKm: -1 }, { ...context, industrialDistanceKm: Infinity },
  { ...context, windKph: -1 }, { ...context, windKph: 501 }, { ...context, windKph: NaN },
]) assert.throws(() => analyzeObservations(rising, invalidContext));

const assertAbstained = (result, reason) => {
  assert.equal(result.status, 'abstained');
  assert.equal(result.classification, 'Insufficient evidence');
  assert.equal(result.modelScore, null);
  assert.deepEqual(result.scores, []);
  assert.deepEqual(result.contributions, []);
  assert.ok(result.warnings.some((warning) => reason.test(warning)), `Missing abstention reason: ${reason}`);
};
assertAbstained(analyzeObservations([observation()], context), /four distinct observation times/);
assertAbstained(analyzeObservations(history([10, 20, 40], [4, 2, 0]), context), /four distinct observation times/);
assertAbstained(analyzeObservations(history([10, 20, 30, 40], [0.9, 0.6, 0.3, 0]), context), /48 hours/);
assertAbstained(analyzeObservations(history([10, 20, 30, 40], [3, 1, 0.5, 0]), context), /two baseline passes/);
assertAbstained(analyzeObservations(rising, { ...context, landCover: 'unknown' }), /Land cover and industrial distance/);
assertAbstained(analyzeObservations(rising, { ...context, industrialDistanceKm: null }), /Land cover and industrial distance/);
assertAbstained(analyzeObservations(history([1, 1, 1, 1, 1, 1_000_000]), context), /outside this synthetic model/);
assertAbstained(analyzeObservations(history([2, 2, 2, 5], [6, 4, 2, 0]), context), /conservative abstention gate/);
const noWeather = analyzeObservations(rising, { ...context, windKph: null });
assert.ok(noWeather.warnings.some((warning) => /Wind is unknown/.test(warning)));

const cases = [
  { label: 'Industrial Fire', rows: rising, context },
  { label: 'Persistent Industrial Heat', rows: history([35, 34, 36, 35, 34, 35]), context },
  { label: 'Forest / Natural Fire', rows: history([12, 11, 15, 65], [6, 4, 2, 0]), context: { landCover: 'forest', industrialDistanceKm: 20, windKph: 35 } },
  { label: 'Other Thermal Anomaly', rows: history([2, 3, 2, 2], [9, 7, 3, 0]), context: { landCover: 'other', industrialDistanceKm: 20, windKph: 5 } },
];
const results = [];
for (const sample of cases) {
  const result = analyzeObservations(sample.rows, sample.context);
  assert.equal(result.status, 'classified', sample.label);
  assert.equal(result.classification, sample.label);
  assert.deepEqual(result, analyzeObservations([...sample.rows].reverse(), sample.context), 'Input order must not change analysis');
  assert.ok(result.modelScore >= 0.5 && result.modelScore <= 1);
  assert.equal(result.scores.length, 4);
  assert.ok(Math.abs(result.scores.reduce((sum, entry) => sum + entry.score, 0) - 1) < 1e-12);
  assert.equal(result.scores[0].score, result.modelScore);
  assert.ok(result.scores.every((entry, index) => index === 0 || entry.score <= result.scores[index - 1].score));
  assert.equal(result.contributions.length, model.featureNames.length);
  assert.ok(result.contributions.every((entry) => Number.isFinite(entry.value) && Number.isFinite(entry.contribution)));
  assert.ok(!('confidence' in result) && !('probability' in result), 'Do not expose an uncalibrated confidence or fire probability');
  assert.match(result.model.trainingSource, /synthetic/i);
  assert.ok(result.warnings.some((warning) => /not calibrated confidence or fire probabilities/.test(warning)));
  assert.ok(result.model.limitations.some((limitation) => /No real-world validation/.test(limitation)));
  results.push(result);
}

const deduped = analyzeObservations([...rising, { ...rising[0] }, { ...rising[1], id: 'same-measurement' }], context);
assert.equal(deduped.statistics.included, rising.length);
assert.equal(deduped.statistics.excluded, 2);
assert.deepEqual(deduped.history, results[0].history);
assert.equal(deduped.classification, results[0].classification);
assert.ok(deduped.warnings.some((warning) => /2 duplicate records/.test(warning)));

const degreesPerKm = 180 / (Math.PI * 6371);
const spatialRows = history([15, 18, 20, 22]).map((row) => ({ ...row, latitude: 0, longitude: 0 }));
const spatial = analyzeObservations([
  ...spatialRows,
  observation('within-radius', 0.5, 50, { latitude: 4.99 * degreesPerKm, longitude: 0 }),
  observation('outside-radius', 0.5, 1_000, { latitude: 5.01 * degreesPerKm, longitude: 0 }),
  observation('thirty-days', 30, 10, { latitude: 0, longitude: 0 }),
  observation('too-old', 30.001, 999, { latitude: 0, longitude: 0 }),
], context);
assert.equal(spatial.statistics.included, 6);
assert.equal(spatial.statistics.excluded, 2);
assert.equal(spatial.statistics.spanHours, 720);
assert.deepEqual(spatial.statistics.center, { latitude: 0, longitude: 0 });
assert.ok(spatial.warnings.some((warning) => /2 observations outside 5 km/.test(warning)));
assert.ok(spatial.history.every((point) => point.frp < 999));

const explicitCenter = { latitude: 0, longitude: 0 };
const oppositeSides = history([15, 18, 20, 22]).map((row, index) => ({
  ...row, latitude: (index === 3 ? 4.9 : -4.9) * degreesPerKm, longitude: 0,
}));
const anchored = analyzeObservations([
  ...oppositeSides,
  observation('remote-future', -60, 900, { latitude: 20, longitude: 20 }),
], context, explicitCenter);
assert.equal(anchored.statistics.included, 4, 'Both sides of the supplied site radius remain included');
assert.equal(anchored.statistics.excluded, 1);
assert.equal(anchored.statistics.distinctTimes, 4);
assert.equal(anchored.statistics.spanHours, 72, 'Remote newer detections do not move the site time window');
assert.equal(anchored.statistics.currentFrp, 22);
assert.deepEqual(anchored.statistics.center, explicitCenter, 'Report location remains the supplied site center');
assert.ok(anchored.warnings.some((warning) => /outside 5 km of the selected site/.test(warning)));
assert.equal(analyzeObservations(oppositeSides, context).statistics.included, 1, 'Omitting a site center preserves the original latest-detection behavior');
assert.throws(() => analyzeObservations(oppositeSides, context, { latitude: 60, longitude: 60 }), /No observations.*within 5 km/);
for (const invalidCenter of [null, {}, { latitude: NaN, longitude: 0 }, { latitude: 91, longitude: 0 }, { latitude: 0, longitude: Infinity }, { latitude: 0, longitude: -181 }]) {
  assert.throws(() => analyzeObservations(rising, context, invalidCenter), /Site center/);
}
assert.doesNotThrow(() => analyzeObservations([observation('pole', 0, 20, { latitude: 90, longitude: 180 })], context, { latitude: 90, longitude: 180 }));

const passMeans = analyzeObservations([
  observation('old-one', 4, 10), observation('old-one-neighbor', 4, 30, { latitude: 21.147 }),
  observation('old-two', 3, 30), observation('old-three', 2, 10),
  observation('recent', 1, 40),
  observation('current', 0, 40), observation('current-neighbor', 0, 80, { latitude: 21.147 }),
], context);
assert.equal(passMeans.statistics.currentFrp, 60, 'Current pass uses mean detection FRP, not pixel sum');
assert.equal(passMeans.statistics.baselineFrp, 20, 'Baseline is median of earlier pass means, excluding exactly 24-hour-old observations');
assert.equal(passMeans.statistics.changePercent, 200);
assert.equal(passMeans.statistics.distinctTimes, 5);
assert.equal(passMeans.statistics.included, 7);
assert.equal(passMeans.statistics.persistence, 1);

const zeroBaseline = analyzeObservations(history([0, 0, 0, 0, 5, 20]), context);
assert.equal(zeroBaseline.statistics.baselineFrp, 0);
assert.equal(zeroBaseline.statistics.changePercent, null, 'A zero baseline cannot yield a finite relative change');
const tinyBaseline = analyzeObservations(history([Number.MIN_VALUE, Number.MIN_VALUE, Number.MIN_VALUE, 1, 1, 100]), context);
assert.equal(tinyBaseline.statistics.changePercent, null, 'An overflowing relative change must stay unavailable');
assert.ok(tinyBaseline.warnings.some((warning) => /exceeds the supported numeric range/.test(warning)));
assert.equal(analyzeObservations([observation('zero', 0, 0)], { ...context, windKph: null }).risk.index, 0);
assert.equal(analyzeObservations(history([1, 1, 1, 1, 1, 1, 1_000_000]), { landCover: 'forest', industrialDistanceKm: 20, windKph: 500 }).risk.index, 100);
const sameDay = analyzeObservations(history([10, 10, 10, 10], [0.3, 0.2, 0.1, 0]), context);
assert.equal(sameDay.statistics.persistence, 1);
const acrossMidnight = analyzeObservations(history([10, 10, 10, 10], [0.51, 0.5, 0.1, 0]), context);
assert.equal(acrossMidnight.statistics.persistence, 1, 'Coverage uses calendar-day count');

for (const source of ['demo', 'manual', 'imported', 'firms']) {
  const result = analyzeObservations(rising.map((row) => ({ ...row, source })), context);
  assert.ok(result.warnings.some((warning) => ({ demo: /DEMO \/ SIMULATION/, manual: /provenance has not been independently verified/, imported: /provenance has not been independently verified/, firms: /NASA has not supplied or endorsed/ }[source]).test(warning)));
}

const checkFiniteTree = (value, path = 'result') => {
  if (typeof value === 'number') assert.ok(Number.isFinite(value), `Non-finite output at ${path}`);
  else if (Array.isArray(value)) value.forEach((entry, index) => checkFiniteTree(entry, `${path}[${index}]`));
  else if (value && typeof value === 'object') Object.entries(value).forEach(([key, entry]) => checkFiniteTree(entry, `${path}.${key}`));
};
for (const result of [...results, spatial, passMeans, zeroBaseline, sameDay, noWeather,
  analyzeObservations(history([1, 1, 1, 1, 1, 1_000_000]), { landCover: 'forest', industrialDistanceKm: 1_000, windKph: 500 }),
  tinyBaseline,
]) {
  checkFiniteTree(result);
  assert.ok(result.risk.index >= 0 && result.risk.index <= 100);
  assert.match(result.risk.method, /Not a fire probability/);
  assert.equal(result.scenarios.length, 3);
  assert.deepEqual(result.scenarios.map((scenario) => scenario.horizon), ['24h', '48h', '7d']);
  result.scenarios.forEach((scenario, index) => {
    assert.ok(scenario.low >= 0 && scenario.low <= scenario.central && scenario.central <= scenario.high && scenario.high <= 100);
    assert.equal(scenario.central, result.risk.index);
    assert.match(scenario.label, /WHAT-IF heuristic/);
    assert.match(scenario.assumption, /not statistical intervals or weather forecasts/);
    if (index) assert.ok(scenario.high - scenario.low >= result.scenarios[index - 1].high - result.scenarios[index - 1].low);
  });
}

const frozenRows = Object.freeze(rising.map((row) => Object.freeze({ ...row })));
assert.doesNotThrow(() => analyzeObservations(frozenRows, Object.freeze({ ...context })), 'Analysis must not mutate supplied observations/context');
assert.equal(model.confusionMatrix.flat().reduce((sum, value) => sum + value, 0), model.validationCount);
assert.equal(model.confusionMatrix.reduce((sum, row, index) => sum + row[index], 0) / model.validationCount, model.syntheticValidationAccuracy);
assert.ok(model.scales.every((value) => Number.isFinite(value) && value > 0));
assert.equal(model.weights.length, model.classes.length);
assert.ok(model.weights.every((row) => row.length === model.featureNames.length));
assert.ok(model.selectiveValidation.achievedPrecision >= model.selectiveValidation.targetPrecision);
assert.ok(model.selectiveValidation.coverage > 0 && model.selectiveValidation.coverage <= 1);

console.log('PASS: strict engine validation, conservative abstention, four synthetic archetypes, deterministic analysis, duplicate/spatial/time filtering, pass means, source disclosures, finite outputs, and bounded heuristic scenarios.');