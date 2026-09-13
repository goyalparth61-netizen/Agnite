/**
 * AGNITE Analysis API Service.
 *
 * Communicates with the FastAPI backend intelligence engine at /api/v1/analysis/run.
 * Dispatches hotspot observations and context, enforcing timeout and response validation.
 * If this request fails or times out, Workspace.tsx catches the error and invokes the
 * client-side thermalEngine.ts fallback.
 */

import type { AnalysisContext, AnalysisResult, Observation } from '../ai/thermalEngine';

export interface AnalysisRequestPayload {
  selectedObservation?: Observation | null;
  observations: Observation[];
  radiusKm?: number;
  context?: AnalysisContext;
}

const ANALYSIS_TIMEOUT_MS = 15_000;

export async function runAnalysis(payload: AnalysisRequestPayload): Promise<AnalysisResult> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), ANALYSIS_TIMEOUT_MS);

  try {
    const response = await fetch('/api/v1/analysis/run', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        selectedObservation: payload.selectedObservation ?? undefined,
        observations: payload.observations,
        radiusKm: payload.radiusKm ?? 5,
        context: payload.context,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorMessage = `Analysis endpoint returned HTTP ${response.status}`;
      try {
        const errorJson = await response.json();
        if (errorJson?.error?.message) {
          errorMessage = errorJson.error.message;
        } else if (typeof errorJson?.error === 'string') {
          errorMessage = errorJson.error;
        }
      } catch {
        // use default error message
      }
      throw new Error(errorMessage);
    }

    const data = (await response.json()) as AnalysisResult;

    // Strict validation of core response contract
    if (!data || typeof data !== 'object') {
      throw new Error('Malformed analysis response from backend.');
    }
    if (!data.classification || typeof data.classification !== 'string') {
      throw new Error('Analysis response missing valid classification.');
    }
    if (!data.risk || typeof data.risk.index !== 'number') {
      throw new Error('Analysis response missing valid risk index.');
    }
    if (!Array.isArray(data.evidence)) {
      throw new Error('Analysis response missing evidence array.');
    }

    return data;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err instanceof Error && err.name === 'AbortError') {
      throw new Error('Analysis request timed out after 15 seconds.');
    }
    throw err;
  }
}
