import type { DirectoryResult } from "./cityIntelligence";
import type { HeroMapResult, MapView } from "./heroMapData";
let worker: Worker | null = null;
let request = 0;
let initialization: Promise<DirectoryResult> | null = null;
const pending = new Map<
  number,
  { resolve: (value: unknown) => void; reject: (error: Error) => void }
>();
function getWorker() {
  if (worker) return worker;
  worker = new Worker(new URL("./cityDirectory.worker.ts", import.meta.url), {
    type: "module",
  });
  worker.onmessage = (
    event: MessageEvent<{ request: number; error?: string }>,
  ) => {
    const task = pending.get(event.data.request);
    if (!task) return;
    pending.delete(event.data.request);
    if ("error" in event.data)
      task.reject(new Error(event.data.error || "Directory unavailable."));
    else task.resolve(event.data);
  };
  worker.onerror = () => {
    for (const task of pending.values())
      task.reject(
        new Error("The city directory could not start. Please retry."),
      );
    pending.clear();
    worker?.terminate();
    worker = null;
    initialization = null;
  };
  return worker;
}
function send<T>(message: Record<string, unknown>): Promise<T> {
  return new Promise((resolve, reject) => {
    const id = ++request;
    pending.set(id, { resolve: (value) => resolve(value as T), reject });
    try {
      getWorker().postMessage({ ...message, request: id });
    } catch (error) {
      pending.delete(id);
      reject(error);
    }
  });
}
export function loadDirectory(): Promise<DirectoryResult> {
  if (!initialization)
    initialization = send<DirectoryResult>({
      kind: "init",
      query: "",
      region: "",
      page: 0,
    }).catch((error) => {
      initialization = null;
      throw error;
    });
  return initialization;
}
export async function searchDirectory(query: string, region = "", page = 0) {
  await loadDirectory();
  return send<DirectoryResult>({ kind: "query", query, region, page });
}
export async function loadMap(view: MapView) {
  await loadDirectory();
  return send<HeroMapResult>({ kind: "map", view });
}
