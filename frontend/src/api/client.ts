import { API_BASE_URL } from "../config/env";
import type { ChatRequest, ChatResponse, HealthResponse } from "../types/api";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(
      `Erro na API (${res.status}): ${text || res.statusText || "Unknown error"}`
    );
  }
  return (await res.json()) as T;
}

export async function askQuestion(
  question: string,
  modelId?: string
): Promise<ChatResponse> {
  const body: ChatRequest = { question };

  // Mantém preparado para quando o backend suportar model_id
  if (modelId) {
    body.model_id = modelId;
  }

  const res = await fetch(`${API_BASE_URL}/chat/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(body)
  });

  return handleResponse<ChatResponse>(res);
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/health`, {
    method: "GET"
  });
  return handleResponse<HealthResponse>(res);
}

