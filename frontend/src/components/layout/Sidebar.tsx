import { type Dispatch, type SetStateAction } from "react";
import {
  Beaker,
  BookOpenCheck,
  GitBranch,
  HelpCircle,
  LineChart,
  ShieldAlert
} from "lucide-react";
import type { BedrockModelId } from "../../types/ui";
import { Card } from "../common/Card";

const EXAMPLES = {
  structured: [
    "Qual o livro melhor avaliado?",
    "Qual a categoria melhor avaliada?",
    "Qual o autor com melhores avaliações?",
    "Quais livros são mais polarizados?"
  ],
  semantic: [
    "Resuma as principais reclamações sobre Harry Potter",
    "O que as avaliações falam sobre o livro Lilla Belle: The First Stages?",
    "Quais temas aparecem nas avaliações de fantasia?"
  ],
  out_of_scope: ["Qual o livro mais vendido?"],
  composite: ["Qual a categoria com o autor que tem melhores avaliações?"]
};

interface SidebarProps {
  onExampleClick: (text: string, autoSend?: boolean) => void;
  modelId: BedrockModelId;
  setModelId: Dispatch<SetStateAction<BedrockModelId>>;
}

export function Sidebar({ onExampleClick }: SidebarProps) {
  return (
    <aside className="flex h-full w-80 flex-col gap-4 border-r border-slate-200 bg-slate-50/60 px-4 py-4">
      <Card
        title="Example queries"
        description="Use casos reais para testar o agente."
        className="overflow-hidden"
      >
        <div className="flex flex-col gap-3 overflow-y-auto pr-1 text-sm">
          <Section
            icon={<LineChart className="h-3.5 w-3.5 text-primary" />}
            title="Structured"
            description="Analytics com ferramentas controladas."
          >
            {EXAMPLES.structured.map((ex) => (
              <ExampleButton
                key={ex}
                label={ex}
                onClick={() => onExampleClick(ex, true)}
              />
            ))}
          </Section>

          <Section
            icon={<BookOpenCheck className="h-3.5 w-3.5 text-accent" />}
            title="Semantic"
            description="Busca vetorial + síntese LLM."
          >
            {EXAMPLES.semantic.map((ex) => (
              <ExampleButton
                key={ex}
                label={ex}
                onClick={() => onExampleClick(ex, true)}
              />
            ))}
          </Section>

          <Section
            icon={<ShieldAlert className="h-3.5 w-3.5 text-warning" />}
            title="Out of scope"
            description="Guardrails para perguntas fora de escopo."
          >
            {EXAMPLES.out_of_scope.map((ex) => (
              <ExampleButton
                key={ex}
                label={ex}
                onClick={() => onExampleClick(ex, true)}
              />
            ))}
          </Section>

          <Section
            icon={<GitBranch className="h-3.5 w-3.5 text-danger" />}
            title="Composite"
            description="Queries relacionais não executadas automaticamente."
          >
            {EXAMPLES.composite.map((ex) => (
              <ExampleButton
                key={ex}
                label={ex}
                onClick={() => onExampleClick(ex, true)}
              />
            ))}
          </Section>
        </div>
      </Card>

      <Card
        title="Quick notes"
        description="Resumo do comportamento do agente."
        className="text-sm"
      >
        <ul className="space-y-2">
          <li className="flex items-start gap-2">
            <LineChart className="mt-0.5 h-3.5 w-3.5 text-primary" />
            <span>
              <strong>Structured</strong> = analytics com ferramentas SQL
              controladas.
            </span>
          </li>
          <li className="flex items-start gap-2">
            <BookOpenCheck className="mt-0.5 h-3.5 w-3.5 text-accent" />
            <span>
              <strong>Semantic</strong> = busca vetorial em pgvector + síntese no
              Bedrock.
            </span>
          </li>
          <li className="flex items-start gap-2">
            <ShieldAlert className="mt-0.5 h-3.5 w-3.5 text-warning" />
            <span>
              <strong>Out of scope</strong> = perguntas sobre vendas, receita etc.
              são bloqueadas por guardrails.
            </span>
          </li>
          <li className="flex items-start gap-2">
            <GitBranch className="mt-0.5 h-3.5 w-3.5 text-danger" />
            <span>
              <strong>Composite</strong> = queries relacionais complexas geram
              sugestões de reformulação ao invés de SQL livre.
            </span>
          </li>
          <li className="flex items-start gap-2">
            <Beaker className="mt-0.5 h-3.5 w-3.5 text-slate-400" />
            <span>
              <strong>MCP server</strong> expõe tools compartilhadas entre API e
              outros clientes.
            </span>
          </li>
          <li className="flex items-start gap-2">
            <HelpCircle className="mt-0.5 h-3.5 w-3.5 text-slate-400" />
            <span>
              Use os exemplos acima durante a entrevista para demonstrar cada
              caminho do agente.
            </span>
          </li>
        </ul>
      </Card>
    </aside>
  );
}

interface SectionProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  children: React.ReactNode;
}

function Section({ icon, title, description, children }: SectionProps) {
  return (
    <section>
      <div className="mb-1 flex items-center gap-2">
        <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-white shadow-sm">
          {icon}
        </span>
        <div>
          <h4 className="text-sm font-semibold text-slate-900">{title}</h4>
          <p className="text-xs text-slate-500">{description}</p>
        </div>
      </div>
      <div className="space-y-1.5">{children}</div>
    </section>
  );
}

interface ExampleButtonProps {
  label: string;
  onClick: () => void;
}

function ExampleButton({ label, onClick }: ExampleButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-left text-[11px] text-slate-700 shadow-sm transition hover:border-primary/40 hover:bg-primary/5"
    >
      {label}
    </button>
  );
}

