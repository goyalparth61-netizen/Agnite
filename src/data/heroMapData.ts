import type { City, PlaceRow } from "./cityIntelligence";
export interface MapView {
  x: number;
  y: number;
  width: number;
  height: number;
}
export const NATIONAL_VIEW: MapView = { x: 0, y: 0, width: 600, height: 620 };
export interface PlaceCluster {
  key: string;
  x: number;
  y: number;
  count: number;
  bounds: MapView;
  city: City;
}
export interface HeroMapResult {
  request: number;
  total: number;
  visible: number;
  clusters: PlaceCluster[];
}
export function projectPlace(latitude: number, longitude: number) {
  return {
    x: 35 + ((longitude - 67) / 32) * 530,
    y: 585 - ((latitude - 5) / 33) * 550,
  };
}
export function limitView(view: MapView): MapView {
  const width = Math.min(600, Math.max(1.2, view.width));
  const height = (width * 620) / 600;
  return {
    width,
    height,
    x: Math.max(-10, Math.min(610 - width, view.x)),
    y: Math.max(-10, Math.min(630 - height, view.y)),
  };
}
export function zoomView(
  view: MapView,
  factor: number,
  center = { x: view.x + view.width / 2, y: view.y + view.height / 2 },
): MapView {
  const width = Math.min(600, Math.max(1.2, view.width / factor));
  const height = (width * 620) / 600;
  return limitView({
    x: center.x - width / 2,
    y: center.y - height / 2,
    width,
    height,
  });
}
export function viewForCluster(cluster: PlaceCluster): MapView {
  const width =
    Math.max(cluster.bounds.width, (cluster.bounds.height * 600) / 620, 1.2) *
    1.35;
  return limitView({
    x: cluster.bounds.x + cluster.bounds.width / 2 - width / 2,
    y: cluster.bounds.y + cluster.bounds.height / 2 - (width * 620) / 600 / 2,
    width,
    height: (width * 620) / 600,
  });
}
export function aggregatePlaces(
  rows: PlaceRow[],
  view: MapView,
): Omit<HeroMapResult, "request"> {
  const cell = view.width / 13;
  const buckets = new Map<string, PlaceCluster>();
  let visible = 0;
  for (const row of rows) {
    const p = projectPlace(row[3], row[4]);
    if (
      p.x < view.x ||
      p.x > view.x + view.width ||
      p.y < view.y ||
      p.y > view.y + view.height
    )
      continue;
    visible++;
    const key = `${Math.floor((p.x - view.x) / cell)}:${Math.floor((p.y - view.y) / cell)}`;
    const group = buckets.get(key);
    if (group) {
      const minX = Math.min(group.bounds.x, p.x);
      const minY = Math.min(group.bounds.y, p.y);
      const maxX = Math.max(group.bounds.x + group.bounds.width, p.x);
      const maxY = Math.max(group.bounds.y + group.bounds.height, p.y);
      group.x += p.x;
      group.y += p.y;
      group.count++;
      group.bounds = {
        x: minX,
        y: minY,
        width: maxX - minX,
        height: maxY - minY,
      };
    } else
      buckets.set(key, {
        key,
        x: p.x,
        y: p.y,
        count: 1,
        bounds: { x: p.x, y: p.y, width: 0, height: 0 },
        city: {
          id: row[0],
          name: row[1],
          region: row[2],
          latitude: row[3],
          longitude: row[4],
          population: row[5],
          search: "",
        },
      });
  }
  return {
    total: rows.length,
    visible,
    clusters: [...buckets.values()].map((group) => ({
      ...group,
      x: group.x / group.count,
      y: group.y / group.count,
    })),
  };
}
