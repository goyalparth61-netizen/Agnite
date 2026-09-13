import { aggregatePlaces, type MapView } from "./heroMapData";
import {
  normalize,
  queryDirectory,
  type PlaceDataset,
} from "./cityIntelligence";
let dataset: PlaceDataset | undefined;
let searches: string[] = [];
let regions: string[] = [];
self.onmessage = async (
  event: MessageEvent<{
    kind: string;
    request: number;
    query: string;
    region: string;
    page: number;
    view?: MapView;
  }>,
) => {
  const { kind, request, query, region, page } = event.data;
  try {
    if (kind === "init") {
      const response = await fetch(
        `${import.meta.env.BASE_URL}data/india-places.json.gz`,
      );
      if (!response.ok || !response.body)
        throw new Error("The city directory could not be downloaded.");
      // Some hosts (including Vite preview) automatically decode .gz responses.
      // Inspect the payload so both pre-decoded and raw compressed assets work.
      const bytes = new Uint8Array(await response.arrayBuffer());
      const packed = new Response(bytes);
      const decoded =
        bytes[0] === 0x1f && bytes[1] === 0x8b
          ? new Response(
              packed.body!.pipeThrough(new DecompressionStream("gzip")),
            )
          : packed;
      dataset = (await decoded.json()) as PlaceDataset;
      if (!Array.isArray(dataset.places) || !dataset.places.length)
        throw new Error("The city directory is empty.");
      searches = dataset.places.map((row) =>
        normalize(`${row[1]} ${row[2]} ${row[7]}`),
      );
      regions = [...new Set(dataset.places.map((row) => row[2]))].sort();
    }
    if (!dataset) return;
    if (kind === "map" && event.data.view) {
      self.postMessage({
        request,
        ...aggregatePlaces(dataset.places, event.data.view),
      });
      return;
    }
    self.postMessage({
      request,
      total: dataset.places.length,
      regions,
      downloaded: dataset.downloaded,
      ...queryDirectory(dataset.places, searches, query, region, page),
    });
  } catch (error) {
    self.postMessage({
      request,
      error:
        error instanceof Error && error.message
          ? error.message
          : "The city directory is unavailable.",
    });
  }
};
