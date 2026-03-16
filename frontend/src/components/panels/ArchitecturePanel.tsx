import { Brain, Database, Globe2, Network, Server, Workflow } from "lucide-react";
import type { Strategy } from "../../types/api";
import { Card } from "../common/Card";

interface ArchitecturePanelProps {
  strategy?: Strategy;
}

export function ArchitecturePanel({ strategy }: ArchitecturePanelProps) {
  const highlight =
    strategy === "semantic"
      ? "semantic"
      : strategy === "structured"
      ? "structured"
      : strategy === "out_of_scope" || strategy === "unsupported_composite"
      ? "guardrail"
      : "hybrid";

  return (
    <Card
      title="Architecture"
      description="Fluxo ponta a ponta desta plataforma agentic."
    >
      <div className="flex flex-col gap-1.5 text-sm text-slate-700">
        <Node
          label="Frontend dashboard"
          icon={<Globe2 className="h-3.5 w-3.5" />}
          highlight
        />
        <Arrow />
        <Node
          label="FastAPI"
          icon={<Server className="h-3.5 w-3.5" />}
          highlight
        />
        <Arrow />
        <Node
          label="LangGraph workflow"
          icon={<Workflow className="h-3.5 w-3.5" />}
          highlight
        />
        <Arrow />
        <Node
          label="MCP client"
          icon={<Network className="h-3.5 w-3.5" />}
          highlight={highlight !== "guardrail"}
        />
        <Arrow />
        <Node
          label={
            highlight === "semantic" || highlight === "hybrid"
              ? "MCP server + semantic tools"
              : "MCP server + tools"
          }
          icon={<Network className="h-3.5 w-3.5" />}
          highlight={highlight !== "guardrail"}
        />
        <Arrow />
        <Node
          label={
            highlight === "semantic" || highlight === "hybrid"
              ? "PostgreSQL + pgvector"
              : "PostgreSQL"
          }
          icon={<Database className="h-3.5 w-3.5" />}
          highlight={highlight !== "guardrail"}
        />
        <Arrow />
        <Node
          label="Amazon Bedrock"
          icon={<Brain className="h-3.5 w-3.5" />}
          highlight={highlight !== "guardrail"}
        />
      </div>
      <p className="mt-2 text-[10px] text-slate-500">
        A UI destaca semantic vs structured vs out_of_scope para explicar a
        decisão do agente durante a entrevista técnica.
      </p>
    </Card>
  );
}

interface NodeProps {
  label: string;
  icon: React.ReactNode;
  highlight?: boolean;
}

function Node({ label, icon, highlight }: NodeProps) {
  return (
    <div
      className={`flex w-full flex-row items-center justify-between rounded-lg border px-3 py-2 text-left ${
        highlight
          ? "border-primary/40 bg-primary/5 text-primary"
          : "border-slate-200 bg-slate-50 text-slate-500"
      }`}
    >
      <span className="mr-2 inline-flex h-7 w-7 items-center justify-center rounded-full bg-white shadow-sm">
        {icon}
      </span>
      <span className="flex-1 text-xs font-medium">{label}</span>
    </div>
  );
}

function Arrow() {
  return (
    <div className="flex h-2 w-full items-center justify-center">
      <div className="h-px w-6 bg-slate-200" />
    </div>
  );
}

