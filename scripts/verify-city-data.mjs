import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { gunzipSync } from "node:zlib";
import {
  normalize,
  queryDirectory,
  rowToCity,
  simulateCity,
  summarizeCities,
} from "../src/data/cityIntelligence.ts";
const dataset = JSON.parse(
  gunzipSync(
    await readFile(
      new URL("../public/data/india-places.json.gz", import.meta.url),
    ),
  ),
);
const rows = dataset.places;
assert.ok(rows.length > 500000);
assert.equal(
  new Set(rows.map((row) => row[0])).size,
  rows.length,
  "IDs must be unique even when names repeat",
);
assert.ok(
  rows.every((row) => Number.isFinite(row[3]) && Number.isFinite(row[4])),
);
const regions = new Set(rows.map((row) => row[2]));
for (const region of [
  "Maharashtra",
  "Tamil Nadu",
  "Delhi",
  "Ladakh",
  "Lakshadweep",
  "Andaman and Nicobar",
  "Sikkim",
])
  assert.ok(regions.has(region), region);
const searches = rows.map((row) => normalize(`${row[1]} ${row[2]} ${row[7]}`));
for (const [query, region] of [
  ["Mumbai", "Maharashtra"],
  ["Bangalore", "Karnataka"],
  ["Chennai", "Tamil Nadu"],
  ["Delhi", "Delhi"],
  ["Kavaratti", "Lakshadweep"],
]) {
  const result = queryDirectory(rows, searches, query, region, 0);
  assert.ok(result.matching > 0, query);
  assert.ok(result.cities.every((city) => city.region === region));
  console.log(`${query}: ${result.matching} matches`);
}
const empty = queryDirectory(
  rows,
  searches,
  "this-place-does-not-exist-98120",
  "",
  0,
);
assert.equal(empty.matching, 0);
assert.equal(empty.summary.count, 0);
assert.equal(empty.summary.confidence, 0);
assert.equal(empty.points.length, 0);
const first = queryDirectory(rows, searches, "", "", 0);
const second = queryDirectory(rows, searches, "", "", 1);
assert.equal(first.cities.length, 8);
assert.ok(!first.cities.some((a) => second.cities.some((b) => a.id === b.id)));
const end = queryDirectory(rows, searches, "", "", 9999999);
assert.equal(end.page, Math.ceil(rows.length / 8) - 1);
for (const city of [...first.cities, ...second.cities]) {
  const scenario = simulateCity(city);
  assert.deepEqual(scenario, simulateCity(city));
  assert.ok(scenario.detections.length >= 1 && scenario.detections.length <= 6);
  assert.ok(scenario.history.every((value) => value >= 0 && value <= 100));
  assert.ok(
    scenario.detections.every(
      (s) =>
        Math.abs(s.latitude - city.latitude) <= 0.035 &&
        Math.abs(s.longitude - city.longitude) <= 0.035,
    ),
  );
}
const sample = rows.slice(0, 8);
const result = queryDirectory(sample, searches.slice(0, 8), "", "", 0);
assert.deepEqual(result.summary, summarizeCities(sample.map(rowToCity)));
console.log(
  `PASS: ${rows.length.toLocaleString()} places; ${regions.size - Number(regions.has("Unspecified region"))} named states/UTs. Search, aliases, pagination, empty results, deterministic simulations and metrics verified.`,
);
