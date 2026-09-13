import type { City } from "./cityIntelligence";
export const INDIA_BOUNDS: [[number, number], [number, number]] = [
  [6, 67],
  [37.5, 98.5],
];
export function validPosition(latitude: number, longitude: number) {
  return (
    Number.isFinite(latitude) &&
    Number.isFinite(longitude) &&
    latitude >= -85 &&
    latitude <= 85 &&
    longitude >= -180 &&
    longitude <= 180
  );
}
export function mercatorPoint(
  latitude: number,
  longitude: number,
  zoom: number,
) {
  const latitudeClamped = Math.max(-85, Math.min(85, latitude));
  const sin = Math.sin((latitudeClamped * Math.PI) / 180);
  const size = 256 * 2 ** zoom;
  return {
    x: ((longitude + 180) / 360) * size,
    y: (0.5 - Math.log((1 + sin) / (1 - sin)) / (4 * Math.PI)) * size,
  };
}
export function clusterCities(cities: City[], zoom: number) {
  const buckets = new Map<string, City[]>();
  for (const city of cities) {
    if (!validPosition(city.latitude, city.longitude)) continue;
    const p = mercatorPoint(city.latitude, city.longitude, zoom);
    const key = `${Math.floor(p.x / 44)}:${Math.floor(p.y / 44)}`;
    const bucket = buckets.get(key);
    if (bucket) bucket.push(city);
    else buckets.set(key, [city]);
  }
  return [...buckets.values()].map((members) => ({
    members,
    latitude: members.reduce((sum, c) => sum + c.latitude, 0) / members.length,
    longitude:
      members.reduce((sum, c) => sum + c.longitude, 0) / members.length,
  }));
}
