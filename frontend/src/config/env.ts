export const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  "http://localhost:8000";

export const DEFAULT_MODEL_ID = "amazon.nova-micro-v1:0";

