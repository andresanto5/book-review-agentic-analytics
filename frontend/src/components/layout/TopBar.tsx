import { Brain } from "lucide-react";
import { useSystemStatus } from "../../hooks/useSystemStatus";
import type { BedrockModelId } from "../../types/ui";
import { Badge } from "../common/Badge";

interface TopBarProps {
  modelId: BedrockModelId;
  onModelChange: (model: BedrockModelId) => void;
  onClearConversation: () => void;
}

export function TopBar({
  modelId,
  onModelChange,
  onClearConversation
}: TopBarProps) {
  const { apiStatus } = useSystemStatus();

  const apiLabel =
    apiStatus === "online"
      ? "API online"
      : apiStatus === "offline"
      ? "API offline"
      : "Verificando API...";

  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white/70 px-5 py-2.5 backdrop-blur">
      <div className="flex items-center gap-3">
        <span className="inline-flex h-9 w-9 items-center justify-center rounded-2xl bg-primary/10 text-primary shadow-sm">
          <Brain className="h-5 w-5" />
        </span>
        <div>
          <h1 className="text-base font-semibold text-slate-900">
            Book Review Agentic Analytics Platform
          </h1>
          <p className="mt-0.5 text-sm text-slate-500">
            FastAPI · LangGraph · MCP · Bedrock · PostgreSQL · pgvector
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-slate-500">API</span>
          <Badge variant={apiStatus === "online" ? "success" : "warning"}>
            <span
              className={`mr-1 inline-block h-1.5 w-1.5 rounded-full ${
                apiStatus === "online" ? "bg-success" : "bg-warning"
              }`}
            />
            {apiLabel}
          </Badge>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-slate-500">Modelo Bedrock</span>
          <select
            value={modelId}
            onChange={(e) => onModelChange(e.target.value as BedrockModelId)}
            className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 shadow-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/40"
          >
            <option value="amazon.nova-micro-v1:0">amazon.nova-micro-v1:0</option>
            <option value="amazon.nova-lite-v1:0">amazon.nova-lite-v1:0</option>
            <option value="amazon.nova-pro-v1:0">amazon.nova-pro-v1:0</option>
          </select>
        </div>

        <button
          type="button"
          onClick={onClearConversation}
          className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm hover:bg-slate-50"
        >
          Limpar conversa
        </button>
      </div>
    </header>
  );
}

