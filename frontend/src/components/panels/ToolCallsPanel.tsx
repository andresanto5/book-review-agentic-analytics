import type { ChatResponse } from "../../types/api";
import { Badge } from "../common/Badge";
import { Card } from "../common/Card";

interface ToolCallsPanelProps {
  response?: ChatResponse;
}

export function ToolCallsPanel({ response }: ToolCallsPanelProps) {
  const hasStructured = !!response?.structured_results;
  const hasSemantic = !!response?.semantic_results;

  return (
    <Card
      title="Tool calls"
      description="Quais ferramentas estruturadas e semânticas foram usadas."
    >
      {!response ? (
        <p className="text-sm text-slate-500">
          As chamadas de ferramentas (structured e semantic) serão exibidas aqui após a
          primeira pergunta.
        </p>
      ) : (
        <div className="space-y-3 text-sm">
          <section>
            <div className="mb-1 flex items-center justify-between">
              <span className="font-medium text-slate-800">Structured tool</span>
              <Badge variant={hasStructured ? "success" : "muted"}>
                {hasStructured ? "Invocada" : "Não utilizada"}
              </Badge>
            </div>
            <p className="text-xs text-slate-500">
              Linhas retornadas: {response.structured_rows ?? 0}
            </p>
          </section>

          <section>
            <div className="mb-1 flex items-center justify-between">
              <span className="font-medium text-slate-800">Semantic tool</span>
              <Badge variant={hasSemantic ? "success" : "muted"}>
                {hasSemantic ? "Invocada" : "Não utilizada"}
              </Badge>
            </div>
            <p className="text-xs text-slate-500">
              Linhas retornadas: {response.semantic_rows ?? 0}
            </p>
          </section>

          {response.out_of_scope && (
            <p className="text-[11px] text-warning-500">
              Como a pergunta foi classificada como{" "}
              <span className="font-semibold">out_of_scope</span>, nenhuma ferramenta
              foi chamada.
            </p>
          )}
        </div>
      )}
    </Card>
  );
}

