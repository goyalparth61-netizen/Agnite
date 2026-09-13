import assert from "node:assert/strict";
let created = 0;
const sent = [];
let failNext = false;
class WorkerHarness {
  constructor() {
    created++;
  }
  postMessage(message) {
    sent.push(message);
    setTimeout(
      () => {
        if (failNext) {
          failNext = false;
          this.onmessage({
            data: { request: message.request, error: "Download failed" },
          });
          return;
        }
        this.onmessage({
          data: {
            request: message.request,
            kind: message.kind,
            query: message.query,
            total: 549021,
          },
        });
      },
      message.kind === "query" ? 1 : 5,
    );
  }
  terminate() {}
}
globalThis.Worker = WorkerHarness;
const { loadDirectory, searchDirectory, loadMap } =
  await import("../src/data/directoryClient.ts");
const initial = await Promise.all([
  loadDirectory(),
  loadDirectory(),
  searchDirectory("Pune"),
  loadMap({ x: 0, y: 0, width: 600, height: 620 }),
]);
assert.equal(created, 1);
assert.equal(sent.filter((x) => x.kind === "init").length, 1);
assert.equal(initial[0], initial[1]);
assert.equal(initial[2].query, "Pune");
assert.equal(initial[3].kind, "map");
const parallel = await Promise.all([
  searchDirectory("Mumbai"),
  loadMap({ x: 10, y: 20, width: 30, height: 31 }),
  searchDirectory("Chennai"),
]);
assert.equal(parallel[0].query, "Mumbai");
assert.equal(parallel[1].kind, "map");
assert.equal(parallel[2].query, "Chennai");
assert.equal(new Set(sent.map((x) => x.request)).size, sent.length);
failNext = true;
await assert.rejects(searchDirectory("Error"), /Download failed/);
assert.equal((await searchDirectory("Retry")).query, "Retry");
console.log(
  "PASS: shared client creates one worker, initializes once, routes concurrent requests correctly and recovers after request errors.",
);
