import type { ChatResponse, Strategy, TargetEntity } from "./api";

export type Role = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  createdAt: string;
  responseMeta?: ChatResponseMeta;
}

export interface ChatResponseMeta {
  strategy: Strategy;
  targetEntity: TargetEntity;
  metricIntent: string | null;
  totalTimeMs?: number;
  structuredRows?: number;
  semanticRows?: number;
  modelId?: string;
}

export interface ExecutionMetrics {
  totalTimeMs?: number;
  strategy?: Strategy;
  structuredRows?: number;
  semanticRows?: number;
  modelId?: string;
  mcpEnabled?: boolean;
  fallbackEnabled?: boolean;
}

export interface AgentFlowStep {
  id: string;
  label: string;
  status: "executed" | "skipped" | "warning" | "error";
}

export interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  lastResponse?: ChatResponse;
  lastError?: string | null;
  metrics?: ExecutionMetrics;
}

export type BedrockModelId =
  | "amazon.nova-micro-v1:0"
  | "amazon.nova-lite-v1:0"
  | "amazon.nova-pro-v1:0";

