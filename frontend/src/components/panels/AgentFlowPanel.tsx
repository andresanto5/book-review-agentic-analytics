import type { ChatResponse } from "../../types/api";
import type { AgentFlowStep } from "../../types/ui";
import { Badge } from "../common/Badge";
import { Card } from "../common/Card";

interface AgentFlowPanelProps {
  response?: ChatResponse;
}

function buildSteps(response?: ChatResponse): AgentFlowStep[] {
  if (!response) {
    return [
      {
        id: "idle",
        label: "Aguardando primeira pergunta",
        status: "skipped"
      }
    ];
  }

  const base: AgentFlowStep[] = [
    { id: "interpret_query", label: "interpret_query", status: "executed" },
    {
      id: "run_structured_tool",
      label: "run_structured_tool",
      status: response.strategy === "structured" || response.strategy === "hybrid" ? "executed" : "skipped"
    },
    {
      id: "run_semantic_tool",
      label: "run_semantic_tool",
      status: response.strategy === "semantic" || response.strategy === "hybrid" ? "executed" : "skipped"
    },
    {
      id: "generate_final_answer",
      label: "generate_final_answer",
      status:
        response.strategy === "out_of_scope" || response.strategy === "unsupported_composite"
          ? "skipped"
          : "executed"
    },
    {
      id: "guardrails",
      label:
        response.strategy === "out_of_scope"
          ? "build_out_of_scope_response"
          : response.strategy === "unsupported_composite"
          ? "build_composite_suggestions"
          : "guardrails_check",
      status:
        response.strategy === "out_of_scope" ||
        response.strategy === "unsupported_composite"
          ? "warning"
          : "executed"
    }
  ];

  // Se o backend expõe path_used, usar para destacar o caminho real
  if (response.path_used && response.path_used.length) {
    return base.map((step) =>
      response.path_used!.includes(step.id)
        ? { ...step, status: step.status === "skipped" ? "executed" : step.status }
        : step
    );
  }

  return base;
}

export function AgentFlowPanel({ response }: AgentFlowPanelProps) {
  const steps = buildSteps(response);

  return (
    <Card
      title="Agent flow"
      description="Etapas percorridas no workflow LangGraph."
    >
      <div className="flex flex-col gap-2">
        <div className="flex flex-col gap-2">
          {steps.map((step, idx) => (
            <div key={step.id} className="flex items-center gap-2">
              <div
                className={`flex h-7 flex-1 items-center justify-between rounded-lg border px-2.5 text-[11px] ${
                  step.status === "executed"
                    ? "border-primary/30 bg-primary/5 text-primary"
                    : step.status === "warning"
                    ? "border-warning/40 bg-warning/5 text-warning"
                    : step.status === "error"
                    ? "border-danger/40 bg-danger/5 text-danger"
                    : "border-slate-200 bg-slate-50 text-slate-400"
                }`}
              >
                <span>{step.label}</span>
                <Badge
                  variant={
                    step.status === "executed"
                      ? "primary"
                      : step.status === "warning"
                      ? "warning"
                      : step.status === "error"
                      ? "danger"
                      : "muted"
                  }
                >
                  {step.status}
                </Badge>
              </div>
              {idx < steps.length - 1 && (
                <div className="flex h-7 w-3 items-center justify-center">
                  <div className="h-px w-full bg-slate-200" />
                </div>
              )}
            </div>
          ))}
        </div>

        <p className="mt-1 text-[10px] text-slate-500">
          O campo <code className="rounded bg-slate-100 px-1">path_used</code> da
          API pode ser usado para mostrar exatamente quais nós foram percorridos em
          cada execução.
        </p>
      </div>
    </Card>
  );
}

