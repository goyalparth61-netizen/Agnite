import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { gunzipSync } from "node:zlib";
import {
  aggregatePlaces,
  NATIONAL_VIEW,
  projectPlace,
  viewForCluster,
  zoomView,
  limitView,
} from "../src/data/heroMapData.ts";
const { places } = JSON.parse(
  gunzipSync(
    await readFile(
      new URL("../public/data/india-places.json.gz", import.meta.url),
    ),
  ),
);
const national = aggregatePlaces(places, NATIONAL_VIEW);
assert.equal(
  national.visible,
  places.length,
  "Every source record must be represented in the national hero map",
);
assert.equal(
  national.clusters.reduce((total, c) => total + c.count, 0),
  places.length,
);
assert.ok(national.clusters.length < 250, "Keep SVG element count bounded");
const group = national.clusters.find((c) => c.count > 100);
const localView = viewForCluster(group);
const local = aggregatePlaces(places, localView);
assert.ok(localView.width < NATIONAL_VIEW.width);
const direct = places.filter((row) => {
  const p = projectPlace(row[3], row[4]);
  return (
    p.x >= localView.x &&
    p.x <= localView.x + localView.width &&
    p.y >= localView.y &&
    p.y <= localView.y + localView.height
  );
});
assert.equal(local.visible, direct.length);
assert.equal(
  local.clusters.reduce((sum, c) => sum + c.count, 0),
  direct.length,
);
const tiny = zoomView(NATIONAL_VIEW, 500, projectPlace(21.1466, 79.0889));
assert.ok(tiny.width >= 1.2 && tiny.width <= 600);
assert.deepEqual(zoomView(NATIONAL_VIEW, 0.5), NATIONAL_VIEW);
assert.ok(limitView({ x: -9999, y: 9999, width: 10, height: 10 }).x >= -10);
const empty = aggregatePlaces([], NATIONAL_VIEW);
assert.equal(empty.visible, 0);
assert.equal(empty.clusters.length, 0);
console.log(
  `PASS: all ${places.length.toLocaleString()} records represented in ${national.clusters.length} national groups. Zoomed viewport counts, view limits and empty states verified.`,
);
