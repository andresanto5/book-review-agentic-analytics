import { Activity, Database, Network, Server, Shield } from "lucide-react";
import type { ExecutionMetrics } from "../../types/ui";
import { useSystemStatus } from "../../hooks/useSystemStatus";
import { Badge } from "../common/Badge";
import { Card } from "../common/Card";

interface SystemHealthPanelProps {
  metrics?: ExecutionMetrics;
}

export function SystemHealthPanel({ metrics }: SystemHealthPanelProps) {
  const { apiStatus } = useSystemStatus();

  return (
    <Card
      title="System health"
      description="Visão rápida da saúde dos componentes."
    >
      <ul className="space-y-1.5 text-sm">
        <HealthItem
          icon={<Server className="h-3.5 w-3.5" />}
          label="FastAPI"
          status={apiStatus === "online" ? "Online" : "Offline"}
          variant={apiStatus === "online" ? "success" : "danger"}
        />
        <HealthItem
          icon={<Network className="h-3.5 w-3.5" />}
          label="MCP integration"
          status={metrics?.mcpEnabled ? "Enabled" : "Configured"}
          variant={metrics?.mcpEnabled ? "success" : "muted"}
        />
        <HealthItem
          icon={<Activity className="h-3.5 w-3.5" />}
          label="Bedrock model"
          status={metrics?.modelId ?? "Configured in backend"}
          variant="primary"
        />
        <HealthItem
          icon={<Database className="h-3.5 w-3.5" />}
          label="Vector search"
          status="pgvector ready"
          variant="muted"
        />
        <HealthItem
          icon={<Shield className="h-3.5 w-3.5" />}
          label="Guardrails"
          status="Out-of-scope & composite routing"
          variant="muted"
        />
      </ul>
    </Card>
  );
}

interface HealthItemProps {
  icon: React.ReactNode;
  label: string;
  status: string;
  variant:
    | "primary"
    | "success"
    | "warning"
    | "danger"
    | "muted";
}

function HealthItem({ icon, label, status, variant }: HealthItemProps) {
  return (
    <li className="flex items-center justify-between gap-2">
      <div className="flex items-center gap-2">
        <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-slate-50 text-slate-500">
          {icon}
        </span>
        <span className="text-xs text-slate-700">{label}</span>
      </div>
      <Badge variant={variant}>{status}</Badge>
    </li>
  );
}

