import type { ExecutionMetrics } from "../../types/ui";
import { Badge } from "../common/Badge";
import { Card } from "../common/Card";

interface MetricsPanelProps {
  metrics?: ExecutionMetrics;
}

export function MetricsPanel({ metrics }: MetricsPanelProps) {
  return (
    <Card
      title="Execution metrics"
      description="Tempo, estratégia e volume de dados."
    >
      {!metrics ? (
        <p className="text-sm text-slate-500">
          As métricas de execução serão exibidas após a primeira pergunta.
        </p>
      ) : (
        <div className="space-y-2 text-sm">
          <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-slate-600">
            <Metric label="Total time">
              {metrics.totalTimeMs
                ? `${metrics.totalTimeMs.toFixed(1)} ms`
                : "n/d"}
            </Metric>
            <Metric label="Strategy">{metrics.strategy ?? "n/d"}</Metric>
            <Metric label="Structured rows">
              {metrics.structuredRows ?? 0}
            </Metric>
            <Metric label="Semantic rows">
              {metrics.semanticRows ?? 0}
            </Metric>
            <Metric label="Model">{metrics.modelId ?? "n/d"}</Metric>
            <Metric label="MCP enabled">
              <Badge variant={metrics.mcpEnabled ? "success" : "muted"}>
                {metrics.mcpEnabled ? "yes" : "no"}
              </Badge>
            </Metric>
            <Metric label="Fallback enabled">
              <Badge variant={metrics.fallbackEnabled ? "warning" : "muted"}>
                {metrics.fallbackEnabled ? "yes" : "no"}
              </Badge>
            </Metric>
          </div>
        </div>
      )}
    </Card>
  );
}

interface MetricProps {
  label: string;
  children: React.ReactNode;
}

function Metric({ label, children }: MetricProps) {
  return (
    <>
      <dt>{label}</dt>
      <dd className="text-right font-medium text-slate-800">{children}</dd>
    </>
  );
}

