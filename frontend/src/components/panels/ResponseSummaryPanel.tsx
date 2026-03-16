import type { ChatResponse } from "../../types/api";
import { Badge } from "../common/Badge";
import { Card } from "../common/Card";

interface ResponseSummaryPanelProps {
  response?: ChatResponse;
}

export function ResponseSummaryPanel({ response }: ResponseSummaryPanelProps) {
  if (!response) {
    return (
      <Card
        title="Response summary"
        description="Resumo executivo da próxima resposta."
      >
        <p className="text-xs text-slate-500">
          Envie uma pergunta para visualizar estratégia, entidade alvo e métricas.
        </p>
      </Card>
    );
  }

  return (
    <Card
      title="Response summary"
      description="Visão executiva da decisão do agente."
    >
      <div className="space-y-2 text-sm">
        <div className="flex flex-wrap items-center gap-1.5">
          <Badge variant="primary">Strategy: {response.strategy}</Badge>
          {response.target_entity && (
            <Badge variant="muted">Entity: {response.target_entity}</Badge>
          )}
          {response.metric_intent && (
            <Badge variant="outline">Metric: {response.metric_intent}</Badge>
          )}
          {response.out_of_scope && <Badge variant="warning">Out of scope</Badge>}
          {response.is_composite_query && (
            <Badge variant="danger">Composite query</Badge>
          )}
        </div>

        <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-[11px] text-slate-600">
          <dt>Modelo</dt>
          <dd className="text-right">{response.model_id ?? "configurado no backend"}</dd>
          <dt>Structured rows</dt>
          <dd className="text-right">{response.structured_rows ?? 0}</dd>
          <dt>Semantic rows</dt>
          <dd className="text-right">{response.semantic_rows ?? 0}</dd>
          <dt>Tempo total</dt>
          <dd className="text-right">
            {response.total_time_ms ? `${response.total_time_ms.toFixed(1)} ms` : "n/d"}
          </dd>
        </dl>

        {response.scope_message && (
          <p className="mt-1 text-[11px] text-slate-500">{response.scope_message}</p>
        )}
        {response.composite_reason && (
          <p className="mt-1 text-[11px] text-slate-500">{response.composite_reason}</p>
        )}
      </div>
    </Card>
  );
}

