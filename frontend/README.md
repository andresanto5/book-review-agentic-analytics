## Book Review Agentic Analytics Frontend

Frontend em React/TypeScript para demonstrar, em formato de dashboard SaaS, a plataforma **Book Review Agentic Analytics Platform**.

### Stack

- Vite + React + TypeScript
- Tailwind CSS
- lucide-react (ícones)
- Recharts (gráficos simples, se necessário)

### Estrutura principal

- `AppShell` com **TopBar**, **Sidebar**, área de chat e painéis laterais.
- Área central:
  - `ChatHistory` (histórico de perguntas e respostas)
  - `ChatInput` (entrada estilo chat)
- Painéis analíticos:
  - `ResponseSummaryPanel` — resumo executivo da última resposta (strategy, entity, métricas).
  - `AgentFlowPanel` — fluxo LangGraph/agent em forma de pipeline visual (usa `path_used` quando disponível).
  - `ToolCallsPanel` — visão de chamadas structured/semantic e contagem de linhas.
  - `MetricsPanel` — métricas de execução (tempo, strategy, rows, modelo).
  - `SystemHealthPanel` — status de API, MCP, Bedrock, vetor e guardrails.
  - `ArchitecturePanel` — diagrama interativo da arquitetura end‑to‑end.

### Integração com o backend

- URL padrão da API: `http://localhost:8000` (configurável via `VITE_API_BASE_URL`).
- Endpoint principal consumido: `POST /chat/ask`.
- Health check: `GET /health` (usado para mostrar status da API).
- Tipos de resposta (`src/types/api.ts`) refletem os campos expostos pelo backend:
  - `strategy`, `target_entity`, `metric_intent`
  - `path_used`
  - `structured_results`, `semantic_results`
  - `out_of_scope`, `is_composite_query`, `scope_message`, `composite_reason`
  - métricas opcionais: `total_time_ms`, `structured_rows`, `semantic_rows`, `model_id`

### Como rodar

No diretório `frontend/`:

```bash
npm install
npm run dev
```

Por padrão o Vite sobe em `http://localhost:5173`.

Certifique‑se de que o backend FastAPI esteja rodando em `http://localhost:8000` (ou ajuste `VITE_API_BASE_URL` em um arquivo `.env` na raiz do frontend).

### O que destacar em uma apresentação técnica

- **Fluxo do agente**:
  - Use o painel **Agent Flow** para mostrar o caminho structured, semantic, hybrid, out_of_scope e composite.
- **Tool calling governado**:
  - Use o painel **Tool Calls** para evidenciar:
    - quando ferramentas structured vs semantic são chamadas;
    - quantas linhas retornam;
    - que out_of_scope não dispara tools.
- **Metadata e métricas**:
  - Use `ResponseSummaryPanel` + `MetricsPanel` para explicar:
    - strategy, entidade alvo e intenção de métrica;
    - tempo total, rows e modelo usado.
- **Arquitetura**:
  - Use **ArchitecturePanel** para contar a história end‑to‑end:
    - Frontend → FastAPI → LangGraph → MCP Client → MCP Server → PostgreSQL + pgvector → Amazon Bedrock.

