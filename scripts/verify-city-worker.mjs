import assert from "node:assert/strict";
import { readdir, readFile } from "node:fs/promises";
const base = "http://127.0.0.1:4173/";
const originalFetch = globalThis.fetch;
globalThis.fetch = (url, options) => originalFetch(new URL(url, base), options);
let received;
globalThis.self = {
  postMessage: (value) => {
    received = value;
  },
};
const files = await readdir(new URL("../dist/assets/", import.meta.url));
const worker = files.find(
  (name) => name.startsWith("cityDirectory.worker-") && name.endsWith(".js"),
);
assert.ok(worker, "Run npm run build first");
await import(new URL(`../dist/assets/${worker}`, import.meta.url));
await self.onmessage({
  data: { kind: "init", request: 1, query: "", region: "", page: 0 },
});
assert.equal(received.request, 1);
assert.ok(!("error" in received), received.error);
assert.ok(received.total > 500000);
assert.equal(received.cities.length, 8);
await self.onmessage({
  data: {
    kind: "query",
    request: 2,
    query: "Pune",
    region: "Maharashtra",
    page: 0,
  },
});
assert.equal(received.request, 2);
assert.ok(received.cities.some((city) => city.name === "Pune"));
await self.onmessage({
  data: {
    kind: "map",
    request: 20,
    view: { x: 0, y: 0, width: 600, height: 620 },
  },
});
assert.equal(received.request, 20);
assert.equal(received.visible, received.total);
assert.equal(
  received.clusters.reduce((sum, group) => sum + group.count, 0),
  received.total,
);
const packed = await readFile(
  new URL("../public/data/india-places.json.gz", import.meta.url),
);
globalThis.fetch = async () => new Response(packed);
await self.onmessage({
  data: {
    kind: "init",
    request: 3,
    query: "Kavaratti",
    region: "Lakshadweep",
    page: 0,
  },
});
assert.ok(!("error" in received), received.error);
assert.ok(received.matching > 0);
globalThis.fetch = async () => new Response("unavailable", { status: 503 });
await self.onmessage({
  data: { kind: "init", request: 4, query: "", region: "", page: 0 },
});
assert.equal(received.request, 4);
assert.ok(received.error);
console.log(
  "PASS: built worker handles server-decoded and raw gzip data; search and download failure messages work.",
);
