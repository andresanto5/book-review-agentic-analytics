export type Strategy =
  | "structured"
  | "semantic"
  | "hybrid"
  | "out_of_scope"
  | "unsupported_composite";

export type TargetEntity = "book" | "category" | "author" | "review" | null;

export interface ChatRequest {
  question: string;
  model_id?: string;
}

export interface ChatResponse {
  question: string;
  final_answer: string;
  strategy: Strategy;
  target_entity: TargetEntity;
  metric_intent: string | null;
  path_used: string[] | null;
  out_of_scope: boolean;
  scope_message: string | null;
  is_composite_query: boolean;
  composite_reason: string | null;
  structured_results?: unknown;
  semantic_results?: unknown;
  suggestions?: string[] | null;
  routing_reason?: string | null;
  errors?: string[] | null;
  // Optional execution metadata from backend if available
  total_time_ms?: number;
  structured_rows?: number;
  semantic_rows?: number;
  model_id?: string;
}

export interface HealthResponse {
  status: "ok" | "error";
  detail?: string;
}

