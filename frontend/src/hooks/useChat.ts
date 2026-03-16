import { useCallback, useMemo, useState } from "react";
import { v4 as uuid } from "uuid";
import { askQuestion } from "../api/client";
import { DEFAULT_MODEL_ID } from "../config/env";
import type { BedrockModelId, ChatMessage, ChatState } from "../types/ui";

export function useChat() {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false
  });
  const [modelId, setModelId] = useState<BedrockModelId>(
    DEFAULT_MODEL_ID as BedrockModelId
  );

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim()) return;

      const userMessage: ChatMessage = {
        id: uuid(),
        role: "user",
        content: content.trim(),
        createdAt: new Date().toISOString()
      };

      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
        isLoading: true,
        lastError: null
      }));

      const startedAt = performance.now();

      try {
        const response = await askQuestion(content, modelId);
        const totalTimeMs = performance.now() - startedAt;

        const assistantMessage: ChatMessage = {
          id: uuid(),
          role: "assistant",
          content: response.final_answer,
          createdAt: new Date().toISOString(),
          responseMeta: {
            strategy: response.strategy,
            targetEntity: response.target_entity,
            metricIntent: response.metric_intent,
            totalTimeMs: response.total_time_ms ?? totalTimeMs,
            structuredRows: response.structured_rows,
            semanticRows: response.semantic_rows,
            modelId: response.model_id ?? modelId
          }
        };

        setState((prev) => ({
          ...prev,
          isLoading: false,
          lastResponse: response,
          metrics: {
            totalTimeMs: response.total_time_ms ?? totalTimeMs,
            strategy: response.strategy,
            structuredRows: response.structured_rows,
            semanticRows: response.semantic_rows,
            modelId: response.model_id ?? modelId,
            mcpEnabled: true,
            fallbackEnabled: false
          },
          // prev.messages já contém userMessage; aqui adicionamos apenas a resposta
          messages: [...prev.messages, assistantMessage]
        }));
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Erro desconhecido ao chamar a API";
        setState((prev) => ({
          ...prev,
          isLoading: false,
          lastError: message
        }));
      }
    },
    [modelId]
  );

  const clearConversation = useCallback(() => {
    setState({
      messages: [],
      isLoading: false,
      lastError: null,
      lastResponse: undefined,
      metrics: undefined
    });
  }, []);

  const value = useMemo(
    () => ({
      state,
      modelId,
      setModelId,
      sendMessage,
      clearConversation
    }),
    [state, modelId, sendMessage, clearConversation]
  );

  return value;
}

