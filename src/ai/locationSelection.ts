export type SelectedLocation = { latitude: number; longitude: number };

export const LOCATION_SELECTION_EVENT = 'agnite:location-selected';
const STORAGE_KEY = 'agnite.selected-location.v1';

function valid(point: unknown): point is SelectedLocation {
  if (!point || typeof point !== 'object') return false;
  const value = point as SelectedLocation;
  return Number.isFinite(value.latitude) && value.latitude >= -90 && value.latitude <= 90 && Number.isFinite(value.longitude) && value.longitude >= -180 && value.longitude <= 180;
}

export function readSelectedLocation(): SelectedLocation | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const point = JSON.parse(raw);
    return valid(point) ? point : null;
  } catch {
    return null;
  }
}

export function rememberSelectedLocation(point: SelectedLocation) {
  if (!valid(point) || typeof window === 'undefined') return;
  try { window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(point)); } catch { /* session storage is optional */ }
  window.dispatchEvent(new CustomEvent<SelectedLocation>(LOCATION_SELECTION_EVENT, { detail: point }));
}

function setInputValue(name: 'latitude' | 'longitude', value: number, overwrite: boolean) {
  if (typeof document === 'undefined') return;
  document.querySelectorAll<HTMLInputElement>(`input[name="${name}"]`).forEach(input => {
    if (!overwrite && input.value.trim()) return;
    input.value = String(Number(value.toFixed(6)));
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
  });
}

export function fillCoordinateInputs(point: SelectedLocation, overwrite = true) {
  if (!valid(point)) return;
  setInputValue('latitude', point.latitude, overwrite);
  setInputValue('longitude', point.longitude, overwrite);
}

/**
 * Keeps latitude/longitude fields across the workspace aligned with the most
 * recently selected map location. Existing user edits are preserved on normal
 * re-renders; choosing a new map location intentionally replaces them.
 */
export function startLocationAutofill() {
  if (typeof window === 'undefined' || typeof document === 'undefined') return () => {};
  const applyStoredToNewFields = () => {
    const point = readSelectedLocation();
    if (point) fillCoordinateInputs(point, false);
  };
  const onLocation = (event: Event) => {
    const point = (event as CustomEvent<SelectedLocation>).detail;
    if (valid(point)) fillCoordinateInputs(point, true);
  };
  window.addEventListener(LOCATION_SELECTION_EVENT, onLocation);
  const observer = new MutationObserver(applyStoredToNewFields);
  const root = document.getElementById('root');
  if (root) observer.observe(root, { childList: true, subtree: true });
  queueMicrotask(applyStoredToNewFields);
  return () => {
    window.removeEventListener(LOCATION_SELECTION_EVENT, onLocation);
    observer.disconnect();
  };
}
