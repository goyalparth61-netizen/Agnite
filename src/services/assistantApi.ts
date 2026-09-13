/**
 * AGNITE AI Assistant API Service (Phase 5A).
 *
 * Communicates with the FastAPI backend endpoint at POST /api/v1/assistant/chat.
 * Dispatches user questions with grounded context references (analysisId, selectedObservationId, coordinates),
 * and manages response contracts and timeouts.
 */

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  text: string;
}

export interface AssistantChatRequest {
  question: string;
  selectedObservationId?: string;
  analysisId?: string;
  latitude?: number;
  longitude?: number;
  conversationHistory?: ChatMessage[];
}

export interface AssistantChatResponse {
  answer: string;
  mode: 'deterministic' | 'llm';
  grounded: boolean;
  analysisId?: string;
  classification?: string;
  risk?: number;
  sources: string[];
  evidenceUsed: string[];
  limitations: string[];
  suggestedQuestions: string[];
}

const ASSISTANT_TIMEOUT_MS = 15_000;

export async function sendAssistantChat(
  payload: AssistantChatRequest,
): Promise<AssistantChatResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), ASSISTANT_TIMEOUT_MS);

  try {
    const response = await fetch('/api/v1/assistant/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        question: payload.question.trim(),
        selectedObservationId: payload.selectedObservationId || undefined,
        analysisId: payload.analysisId || undefined,
        latitude: payload.latitude !== undefined ? payload.latitude : undefined,
        longitude: payload.longitude !== undefined ? payload.longitude : undefined,
        conversationHistory: payload.conversationHistory || [],
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorMessage = `Assistant returned HTTP ${response.status}`;
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

    const data = (await response.json()) as AssistantChatResponse;

    if (!data || typeof data.answer !== 'string') {
      throw new Error('Invalid assistant response contract: missing answer string.');
    }

    return data;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Assistant query timed out. The server took too long to respond.');
    }
    throw error;
  }
}
