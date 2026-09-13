/**
 * AGNITE Monitoring & Watch API Service.
 *
 * Communicates with /api/v1/watches and /api/v1/alerts.
 */

import type { WatchLocation } from '../ai/workspaceData';

export interface ServerWatch {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  radiusKm: number;
  frpThreshold: number;
  riskThreshold: number;
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
  lastCheckedAt?: string | null;
}

export interface ServerAlert {
  id: string;
  watchId: string;
  watchName?: string | null;
  observationId?: string | null;
  analysisId?: string | null;
  type: string;
  severity: 'INFO' | 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  title: string;
  message: string;
  latitude: number;
  longitude: number;
  frp?: number | null;
  risk?: number | null;
  confidence?: number | null;
  fingerprint: string;
  acknowledged: boolean;
  createdAt: string;
}

export async function fetchWatchesBackend(): Promise<WatchLocation[]> {
  const response = await fetch('/api/v1/watches', {
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch watches (HTTP ${response.status})`);
  }
  const data = (await response.json()) as ServerWatch[];
  return data.map((w) => ({
    id: w.id,
    name: w.name,
    latitude: w.latitude,
    longitude: w.longitude,
    threshold: w.frpThreshold,
  }));
}

export async function createWatchBackend(payload: {
  name: string;
  latitude: number;
  longitude: number;
  threshold: number;
  radiusKm?: number;
}): Promise<WatchLocation> {
  const response = await fetch('/api/v1/watches', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({
      name: payload.name,
      latitude: payload.latitude,
      longitude: payload.longitude,
      radiusKm: payload.radiusKm ?? 5.0,
      frpThreshold: payload.threshold,
    }),
  });
  if (!response.ok) {
    throw new Error(`Failed to create watch (HTTP ${response.status})`);
  }
  const w = (await response.json()) as ServerWatch;
  return {
    id: w.id,
    name: w.name,
    latitude: w.latitude,
    longitude: w.longitude,
    threshold: w.frpThreshold,
  };
}

export async function deleteWatchBackend(id: string): Promise<boolean> {
  const response = await fetch(`/api/v1/watches/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  });
  return response.ok;
}

export async function fetchAlertsBackend(watchId?: string): Promise<ServerAlert[]> {
  const url = new URL('/api/v1/alerts', window.location.origin);
  if (watchId) {
    url.searchParams.set('watchId', watchId);
  }
  const response = await fetch(url.toString(), {
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch alerts (HTTP ${response.status})`);
  }
  const data = (await response.json()) as { alerts: ServerAlert[] };
  return data.alerts ?? [];
}

export async function acknowledgeAlertBackend(id: string): Promise<ServerAlert> {
  const response = await fetch(`/api/v1/alerts/${encodeURIComponent(id)}/acknowledge`, {
    method: 'PATCH',
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`Failed to acknowledge alert (HTTP ${response.status})`);
  }
  return (await response.json()) as ServerAlert;
}
