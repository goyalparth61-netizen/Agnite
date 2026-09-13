export type PlaceRow = [
  number,
  string,
  string,
  number,
  number,
  number,
  string,
  string,
];
export interface PlaceDataset {
  source: string;
  sourceUrl: string;
  license: string;
  downloaded: string;
  coverage: string;
  places: PlaceRow[];
}
export interface City {
  id: number;
  name: string;
  region: string;
  latitude: number;
  longitude: number;
  population: number;
  search: string;
}
export const normalize = (text: string) =>
  text
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
export function parseCities(data: PlaceDataset): City[] {
  return data.places.map(
    ([id, name, region, latitude, longitude, population, , aliases]) => ({
      id,
      name,
      region,
      latitude,
      longitude,
      population,
      search: normalize(`${name} ${region} ${aliases}`),
    }),
  );
}
export const anomalyTypes = [
  "Industrial Fire",
  "Persistent Industrial Heat",
  "Forest / Natural Fire",
  "Other Thermal Anomaly",
] as const;
export function seedFor(id: number) {
  return Math.imul(id ^ (id >>> 16), 0x45d9f3b) >>> 0;
}
export function citySummary(city: City) {
  const seed = seedFor(city.id);
  return {
    count: 1 + (seed % 6),
    category: seed % 4,
    risk: 18 + (seed % 78),
    confidence: 68 + (seed % 29),
  };
}
export function simulateCity(city: City) {
  const { count, category, risk, confidence } = citySummary(city);
  const seed = seedFor(city.id);
  const history = Array.from({ length: 7 }, (_, day) =>
    Math.max(
      5,
      Math.min(
        99,
        Math.round(risk * (0.35 + day / 10) + ((seed >>> day) % 13) - 6),
      ),
    ),
  );
  const detections = Array.from({ length: count }, (_, index) => ({
    id: `SIM-${city.id}-${index + 1}`,
    latitude:
      city.latitude + (index === 0 ? 0 : Math.sin(seed + index) * 0.035),
    longitude:
      city.longitude + (index === 0 ? 0 : Math.cos(seed + index) * 0.035),
    frp: Math.round((8 + ((seed + index * 17) % 830) / 10) * 10) / 10,
    confidence: Math.min(99, confidence + index),
  }));
  return {
    name: `${city.name}, ${city.region}`,
    type: anomalyTypes[category],
    risk,
    confidence,
    history,
    detections,
    evidence: [
      "This generated scenario pairs an abrupt thermal rise with assumed industrial context. It is not evidence of an actual fire in this city.",
      "This generated scenario illustrates recurring industrial heat. Industrial land use and recurrence have not been verified for this location.",
      "This generated scenario illustrates a possible natural-fire signature. Forest cover and fire activity have not been verified here.",
      "This generated scenario illustrates an isolated thermal anomaly with insufficient context. No real satellite detection is attached.",
    ][category],
    factors: [
      ["Simulated thermal increase", "Assumed industrial context"],
      ["Simulated recurrence", "Assumed operational baseline"],
      ["Simulated heat cluster", "Assumed natural cover"],
      ["Synthetic isolated signal", "Context unavailable"],
    ][category],
    action:
      "Demo workflow: verify satellite observations and local context before making any operational decision.",
  };
}
export function summarizeCities(cities: City[]) {
  const result = {
    count: 0,
    industrial: 0,
    persistent: 0,
    natural: 0,
    high: 0,
    confidence: 0,
  };
  for (const city of cities) {
    const s = citySummary(city);
    result.count += s.count;
    if (s.category === 0) result.industrial += s.count;
    if (s.category === 1) result.persistent += s.count;
    if (s.category === 2) result.natural += s.count;
    if (s.risk >= 70) result.high++;
    result.confidence += s.confidence;
  }
  result.confidence = cities.length
    ? Math.round(result.confidence / cities.length)
    : 0;
  return result;
}

export function rowToCity([
  id,
  name,
  region,
  latitude,
  longitude,
  population,
]: PlaceRow): City {
  return { id, name, region, latitude, longitude, population, search: "" };
}
export interface DirectoryResult {
  request: number;
  total: number;
  matching: number;
  page: number;
  regions: string[];
  cities: City[];
  points: City[];
  summary: ReturnType<typeof summarizeCities>;
  downloaded: string;
}
export function queryDirectory(
  rows: PlaceRow[],
  searches: string[],
  query: string,
  region: string,
  page: number,
) {
  const needle = normalize(query);
  const matched: PlaceRow[] = [];
  const cells = new Map<string, City>();
  const summary = {
    count: 0,
    industrial: 0,
    persistent: 0,
    natural: 0,
    high: 0,
    confidence: 0,
  };
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    if (
      (region && row[2] !== region) ||
      (needle && !searches[i].includes(needle))
    )
      continue;
    matched.push(row);
    const city = rowToCity(row);
    const value = citySummary(city);
    summary.count += value.count;
    if (value.category === 0) summary.industrial += value.count;
    if (value.category === 1) summary.persistent += value.count;
    if (value.category === 2) summary.natural += value.count;
    if (value.risk >= 70) summary.high++;
    summary.confidence += value.confidence;
    const cell = `${Math.floor(row[3] * 2)}:${Math.floor(row[4] * 2)}`;
    if (!cells.has(cell)) cells.set(cell, city);
  }
  summary.confidence = matched.length
    ? Math.round(summary.confidence / matched.length)
    : 0;
  const safePage = Math.min(
    Math.max(0, page),
    Math.max(0, Math.ceil(matched.length / 8) - 1),
  );
  return {
    matching: matched.length,
    page: safePage,
    cities: matched.slice(safePage * 8, safePage * 8 + 8).map(rowToCity),
    points: [...cells.values()],
    summary,
  };
}
