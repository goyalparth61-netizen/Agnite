/**
 * AGNITE Location History API Service.
 *
 * Queries persistent observation history and calculated metrics from /api/v1/history.
 */

import type { Observation } from '../ai/thermalEngine';

export interface HistoryQueryResponse {
  location: { latitude: number; longitude: number };
  radiusKm: number;
  period: { from: string; to: string };
  observationCount: number;
  observations: Observation[];
  statistics: Record<string, unknown>;
  timeline: Array<{ observedAt: string; frp: number; baseline?: number }>;
  recurrence: {
    signal: string;
    persistenceScore: number;
    coverageRatio: number;
    stabilityFactor: number;
    uniqueDays: number;
    distinctTimes: number;
  };
  provenance: Record<string, number>;
}

export async function fetchLocationHistory(params: {
  latitude: number;
  longitude: number;
  radiusKm?: number;
  days?: number;
}): Promise<HistoryQueryResponse> {
  const url = new URL('/api/v1/history', window.location.origin);
  url.searchParams.set('latitude', params.latitude.toString());
  url.searchParams.set('longitude', params.longitude.toString());
  url.searchParams.set('radiusKm', (params.radiusKm ?? 5).toString());
  url.searchParams.set('days', (params.days ?? 30).toString());

  const response = await fetch(url.toString(), {
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`History query returned HTTP ${response.status}`);
  }

  return (await response.json()) as HistoryQueryResponse;
}
