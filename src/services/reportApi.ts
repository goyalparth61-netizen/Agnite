/**
 * AGNITE Report API Service.
 *
 * Communicates with /api/v1/reports for persistent backend report storage,
 * with graceful fallback to localStorage when backend is unavailable.
 */

import type { SavedReport } from '../ai/workspaceData';

export async function saveReportBackend(report: SavedReport): Promise<SavedReport> {
  const response = await fetch('/api/v1/reports', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({
      id: report.id,
      label: report.label,
      latitude: report.report.statistics?.center?.latitude ?? 0,
      longitude: report.report.statistics?.center?.longitude ?? 0,
      classification: report.classification,
      confidence: (report.report as any).confidence ?? report.report.modelScore ?? null,
      risk: report.risk,
      summary: report.summary,
      report: report.report,
      context: report.context,
      observations: report.observations,
    }),
  });

  if (!response.ok) {
    throw new Error(`Report save returned HTTP ${response.status}`);
  }

  const data = await response.json();
  return {
    id: data.id,
    createdAt: data.createdAt,
    label: data.label,
    classification: data.classification,
    risk: data.risk,
    summary: data.summary,
    report: data.report,
    context: data.context,
    observations: data.observations,
  };
}

export async function fetchReportsBackend(): Promise<SavedReport[]> {
  const response = await fetch('/api/v1/reports', {
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Report fetch returned HTTP ${response.status}`);
  }

  const data = await response.json();
  const reports = data.reports || [];
  return reports.map((r: any) => ({
    id: r.id,
    createdAt: r.createdAt,
    label: r.label,
    classification: r.classification,
    risk: r.risk,
    summary: r.summary,
    report: r.report,
    context: r.context,
    observations: r.observations,
  }));
}

export async function deleteReportBackend(id: string): Promise<boolean> {
  const response = await fetch(`/api/v1/reports/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  });
  return response.ok;
}
