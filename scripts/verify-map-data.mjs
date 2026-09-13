import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { gunzipSync } from "node:zlib";
import {
  clusterCities,
  mercatorPoint,
  validPosition,
} from "../src/data/mapViewport.ts";
import { queryDirectory, normalize } from "../src/data/cityIntelligence.ts";
import { projectIndia, INDIA_PATH } from "../src/data/indiaGeometry.ts";
const data = JSON.parse(
  gunzipSync(
    await readFile(
      new URL("../public/data/india-places.json.gz", import.meta.url),
    ),
  ),
);
const searches = data.places.map((row) =>
  normalize(`${row[1]} ${row[2]} ${row[7]}`),
);
const directory = queryDirectory(data.places, searches, "", "", 0);
const points = directory.points;
for (const zoom of [3, 4.5, 8, 13, 18]) {
  const groups = clusterCities(points, zoom);
  const ids = groups.flatMap((group) => group.members.map((city) => city.id));
  assert.equal(ids.length, points.length, "No city is dropped at any zoom");
  assert.equal(new Set(ids).size, points.length, "No duplicate members");
  assert.ok(groups.every((g) => validPosition(g.latitude, g.longitude)));
  console.log(
    `Zoom ${zoom}: ${groups.length} interactive groups / ${ids.length} representative places`,
  );
}
assert.ok(
  clusterCities(points, 13).length > clusterCities(points, 4).length,
  "Groups separate when zoomed in",
);
const p = mercatorPoint(21.1466, 79.0889, 5);
const q = mercatorPoint(21.1466, 79.0889, 6);
assert.ok(Math.abs(q.x - p.x * 2) < 0.0001 && Math.abs(q.y - p.y * 2) < 0.0001);
assert.ok(!validPosition(NaN, 10));
assert.ok(!validPosition(91, 10));
assert.equal(clusterCities([{ ...points[0], latitude: NaN }], 5).length, 0);
for (const [lat, lon] of [
  [21.1466, 79.0889],
  [21.1702, 72.8311],
  [21.75, 86.33],
  [17.385, 78.4867],
]) {
  const p = projectIndia(lat, lon);
  assert.ok(p.x > 0 && p.x < 600 && p.y > 0 && p.y < 620);
}
assert.ok(INDIA_PATH.startsWith("M") && INDIA_PATH.length > 10000);
const page2 = queryDirectory(data.places, searches, "", "", 1);
assert.equal(
  points.map((c) => c.id).join(","),
  page2.points.map((c) => c.id).join(","),
  "Pagination must not change the map viewport key",
);
console.log(
  "PASS: clustering preserves every representative, expands at higher zoom, validates coordinates, and hero projection is within bounds.",
);
