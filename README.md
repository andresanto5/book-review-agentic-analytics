# Book Review Agentic Analytics

> **Free local validation:** [reproducible demo without AWS calls](docs/DEMO_GRATUITA.md). Real SQL/MCP/vector retrieval over synthetic data, with explicitly simulated final generation. [Local checks](docs/VALIDACAO_LOCAL.md) · [Semantic retrieval checks](docs/VALIDACAO_SEMANTICA.md). AWS deployment remains a future validation milestone.

**Proof of concept · Technical hiring challenge · Python / LangGraph / MCP / FastAPI / pgvector / Amazon Bedrock**

An analytics assistant that combines structured queries and semantic retrieval over book reviews, then uses Amazon Bedrock to generate a response grounded in the retrieved results.

## Portfolio overview

Developed as a proof of concept for a technical hiring challenge. The project demonstrates application design, tool orchestration, retrieval and integration with a managed language-model service.

| Question | Approach |
| --- | --- |
| Which books have the best ratings? | Structured queries and aggregations |
| What do reviewers say about a book? | Embeddings and semantic retrieval |
| Why does a ranked book stand out? | Structured results combined with retrieved review context |

### Engineering decisions

- Explicit routing between structured, semantic and hybrid workflows.
- Controlled MCP tools provide database access; generated responses use tool results.
- PostgreSQL/pgvector supports relational analytics and vector retrieval.
- FastAPI separates the HTTP interface from agent orchestration.
- The dashboard exposes the agent flow, tool calls and execution metadata.

### AWS experience demonstrated

The AWS component is **Amazon Bedrock integration at the application layer**, including configurable model selection and a fallback path described below. The proof of concept uses a local application stack connected to Bedrock. Production cloud deployment, infrastructure as code, IAM design, centralized monitoring, load testing and measured operating costs are areas for future extension and validation.

### Validation status

This repository is a technical demonstration. Setup instructions, example requests and test commands are documented below. A reproducible run should record the dataset version, environment, model access, test results and measured latency before making performance claims.

### Suggested next iteration

1. Document a small reproducible dataset and expected example outputs.
2. Record automated test results and retrieval/answer evaluation.
3. Add a short demo and measured latency/cost observations.
4. Develop and validate an AWS deployment as a separate, documented milestone.

## Documentação técnica em português

# Plataforma de Analytics Agêntico de Reviews de Livros

## 1. Visão geral e objetivo

Este projeto transforma um grande corpus de avaliações de livros em uma **plataforma de analytics agêntica** capaz de responder perguntas de negócio em linguagem natural, com foco em:

- **Livros**, **categorias** e **autores** (ex.: melhor avaliado, mais comentado, mais polarizado, piores avaliações, mais criticado).
- Combinação de **analytics estruturado** (rankings, agregados) com **busca semântica** (vetores sobre o texto das reviews) e **geração por LLM** (Amazon Bedrock).
- Acesso a dados **exclusivamente via ferramentas controladas** — o LLM **nunca** emite SQL livre.
- Arquitetura alinhada a requisitos enterprise (governança, observabilidade, rastreabilidade de ferramentas).

O resultado é uma API e um dashboard que permitem demonstrar, em entrevista/apresentação técnica, um fluxo completo de:

> Pergunta em linguagem natural → Interpretação da intenção → Chamada de tools estruturadas/semânticas → Resposta explicável com metadados e fluxo do agente.

---

## 2. Arquitetura em alto nível

```text
Usuário (Frontend React)
    ↓
FastAPI (API HTTP)
    ↓
LangGraph (workflow/roteamento)
    ↓
Cliente MCP (sessão persistente)
    ↓
Servidor MCP (processo separado)
    ↓
Ferramentas controladas (PostgreSQL + pgvector)
    ↓
Amazon Bedrock (somente para geração final de resposta)
```

- **Frontend (Vite + React + TS)**  
  Dashboard SaaS que exibe o chat, fluxo do agente, chamadas de tools, métricas de execução e diagrama de arquitetura.

- **FastAPI**  
  Único ponto de entrada HTTP. Expõe:
  - `GET /health` – health check.
  - `POST /chat/ask` – endpoint principal de chat.

- **LangGraph**  
  Orquestra o fluxo:
  - interpreta a pergunta,
  - classifica a estratégia (`structured`, `semantic`, `hybrid`, `out_of_scope`, `unsupported_composite`),
  - escolhe a ferramenta estruturada/semântica adequada,
  - chama o Bedrock apenas para gerar a resposta em linguagem natural com base nos resultados.

- **MCP (Model Context Protocol)**  
  Cliente MCP (na API) conversa com um servidor MCP (processo separado), que expõe as mesmas tools controladas. Garante:
  - uma única fonte de verdade para as tools,
  - possibilidade de reutilizar o servidor MCP por outros clientes (ex.: IDE, agentes externos).

- **PostgreSQL + pgvector**  
  Base transacional/analítica das entities (books, authors, categories, reviews) + embeddings de reviews para busca semântica.

- **Amazon Bedrock**  
  Utilizado apenas na etapa final de resposta, nunca para emitir SQL.  
  O modelo responde **no mesmo idioma da pergunta** (pt‑BR ou EN), exceto por nomes próprios.

---

## 3. Decisões de design

- **Sem SQL livre pelo LLM**  
  Toda consulta é mediada por tools explícitas, com assinaturas claras. Isso evita injeção de SQL, dificulta vazamento de dados e facilita auditoria.

- **Tools controladas e reusáveis**  
  As mesmas funções (por ex. `get_best_rated_books`, `get_lowest_rated_books`, `get_most_criticized_books`) são usadas:
  - via MCP,
  - e como fallback local na API.

- **MCP no fluxo principal**  
  A API não chama o banco diretamente a partir do LangGraph; o caminho preferencial é via MCP, o que espelha arquiteturas modernas de “data products” e serve como ponto forte na apresentação.

- **Estratégias explícitas**  
  As perguntas são classificadas em:
  - `structured` – rankings/aggregados,
  - `semantic` – resumo de opiniões, reclamações, temas,
  - `hybrid` – ranking + explicação,
  - `out_of_scope` – vendas, receita, lucro, estoque, etc.,
  - `unsupported_composite` – queries relacionais não cobertas por uma única tool.

- **Métricas positivas e negativas**  
  O roteador entende intenções como:
  - `best_rated`, `most_reviewed`, `most_polarized`, `theme_summary`, `complaint_summary`, `praise_summary`;
  - **negativas**: `worst_rated` (menor média) e `most_criticized` (maior massa de reviews com score ≤ 2).

---

## 4. Estrutura de diretórios

```text
book-review-genai-a3data/
├── api/                    # App FastAPI
│   ├── main.py             # Criação da app, startup, middlewares
│   ├── controllers/        # Orquestração de requests (ex.: handle_chat)
│   ├── routers/            # Rotas HTTP
│   └── schemas/            # Schemas Pydantic (ChatRequest/ChatResponse etc.)
├── src/
│   ├── agents/             # Estado do LangGraph, nós, workflow, tools
│   ├── config/             # Configurações (DB, MCP, Bedrock, etc.)
│   ├── embeddings/         # Cliente de embedding (sentence-transformers)
│   ├── llm/                # Cliente Amazon Bedrock (fallback automático)
│   ├── mcp/                # Cliente MCP (streamable-http)
│   └── repositories/       # Acesso a DB e pgvector (SQL)
├── mcp_server/             # Processo separado do servidor MCP (ex.: python -m mcp_server.server)
│   └── server.py
├── frontend/               # Dashboard Vite + React + TS + Tailwind
│   ├── src/
│   └── README.md
├── tests/                  # Testes de roteamento e sanity
├── docs/                   # Documentação adicional (MCP, diagramas)
├── .env.example            # Modelo de variáveis de ambiente
├── requirements.txt        # Dependências Python
└── README.md               # Este documento
```

---

## 5. Pré‑requisitos

Antes de rodar, verifique:

- **Sistema**:
  - Python 3.10+
  - Node.js 18+ (para o frontend)
  - Docker (opcional, mas recomendado para subir Postgres)
- **Banco de dados**:
  - PostgreSQL com extensão **pgvector** habilitada.
- **AWS**:
  - Credenciais com acesso ao Amazon Bedrock (modelo configurado via `BEDROCK_MODEL_ID`).

---

## 6. Passo a passo para rodar tudo (ordem recomendada)

### 6.1. Configurar variáveis de ambiente

Na raiz do projeto:

```bash
cp .env.example .env
```

Depois, edite `.env` e configure pelo menos:

- **Banco de dados**:
  - `POSTGRES_HOST`
  - `POSTGRES_PORT`
  - `POSTGRES_DB`
  - `POSTGRES_USER`
  - `POSTGRES_PASSWORD`
  - `DATABASE_URL` (ex.: `postgresql+psycopg://user:pass@localhost:5432/db`)
- **AWS / Bedrock**:
  - `AWS_REGION`
  - `BEDROCK_MODEL_ID` (ex.: `anthropic.claude-3-haiku-20240307-v1:0` ou `amazon.nova-micro-v1:0`)
  - `BEDROCK_FALLBACK_MODEL_ID` (ex.: `amazon.nova-micro-v1:0`)
- **MCP**:
  - `MCP_SERVER_PORT` (padrão: `8001`)

---

### 6.2. Subir o PostgreSQL com pgvector (via Docker)

Se você não tiver um Postgres com pgvector local, pode usar um container Docker típico:

```bash
docker run --name bookreviews-pg \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=bookreviews \
  -p 5432:5432 \
  -d ankane/pgvector:latest
```

Ajuste o `DATABASE_URL` no `.env` para apontar para esse container.

> **Obs.:** Se você já tem um Postgres com pgvector configurado, basta garantir que a URL e credenciais em `.env` estão corretas.

---

### 6.3. Criar ambiente Python e instalar dependências

Na raiz do projeto:

```bash
python -m venv .venv
source .venv/bin/activate       # Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 6.4. Subir o servidor MCP (processo 1)

Em um terminal separado, com o virtualenv ativo:

```bash
python -m mcp_server.server
```

O servidor MCP:

- escuta por padrão em `http://127.0.0.1:8001/mcp` (configurável via `.env`),
- pré‑carrega o modelo de embeddings (`all-MiniLM-L6-v2`) no startup,  
  log típico:

```text
MCP startup: embedding model preloaded in X.XXXs (singleton ready for semantic MCP tools)
```

---

### 6.5. Subir a API FastAPI (processo 2)

Em outro terminal, ainda com o virtualenv ativo:

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Verificações:

- Documentação interativa: `http://localhost:8000/docs`
- Health check:

  ```bash
  curl -s http://localhost:8000/health
  ```

---

### 6.6. Subir o frontend (processo 3)

Em outro terminal, na pasta `frontend/`:

```bash
cd frontend
npm install
npm run dev

Ou, da raiz, em um único comando:
npm run dev --prefix frontend
```

O Vite sobe em:

- `http://localhost:5173/`

O frontend se conecta ao backend em `http://localhost:8000` por padrão.  
Se precisar apontar para outra URL, crie um `.env` dentro de `frontend/` com:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

---

## 7. Como interagir com a API diretamente

### 7.1. Exemplos de requisições

**Estruturada – livros melhor avaliados**

```bash
curl -s -X POST http://localhost:8000/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Qual o livro melhor avaliado?"}'
```

**Semântica – o que as reviews dizem**

```bash
curl -s -X POST http://localhost:8000/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "O que as avaliações falam sobre o livro Harry Potter?"}'
```

**Negativa – piores avaliações / mais criticado**

```bash
curl -s -X POST http://localhost:8000/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Qual o autor com as piores avaliações?"}'
```

```bash
curl -s -X POST http://localhost:8000/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Qual o livro mais criticado?"}'
```

**Fora de escopo – vendas/receita (guardrail)**

```bash
curl -s -X POST http://localhost:8000/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Qual livro mais vendeu?"}'
```

**Composta – não suportada por uma única tool**

```bash
curl -s -X POST http://localhost:8000/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Qual a categoria com o autor que tem melhor avaliação?"}'
```

---

## 8. Testes automatizados

Para validar a interpretação e o roteamento (sem precisar de DB/MCP):

```bash
pytest tests/test_interpret_routing.py -v
```

Para testes que exercitam tools reais (requerem DB e, opcionalmente, MCP):

```bash
pytest tests/test_mcp_sanity.py -v
```

---

## 9. Modelos Bedrock

- **Modelo principal (demo):**  
  `anthropic.claude-3-haiku-20240307-v1:0` (configurado via `BEDROCK_MODEL_ID`).

- **Fallback automático:**  
  Se o modelo principal falhar por acesso/permissão/use‑case, o cliente troca para `amazon.nova-micro-v1:0` (ou o valor em `BEDROCK_FALLBACK_MODEL_ID`).  
  Logs típicos:
  - `Primary Bedrock model failed, switching to fallback model...`
  - `Fallback Bedrock model succeeded.`

- **Perfil de baixo custo/dev:**  
  Defina `BEDROCK_MODEL_ID=amazon.nova-micro-v1:0` para usar apenas Nova Micro.

Ambos IDs são lidos do ambiente – não há hard‑code em múltiplos pontos.

---

## 10. Guardrails e limitações

- **Fora de escopo:**  
  Perguntas sobre vendas, receita, lucro, estoque, etc., são marcadas como `out_of_scope`.  
  Nesses casos:
  - não são chamadas tools estruturadas/semânticas,
  - não é chamado o Bedrock para resposta completa,
  - o usuário recebe uma explicação curta e sugestões de perguntas de analytics disponíveis.

- **Queries compostas (`unsupported_composite`):**  
  Perguntas que misturam múltiplas entidades/relacionamentos (ex.: “categoria com o autor que…”) são tratadas como:
  - `strategy = unsupported_composite`,
  - resposta transparente explicando a limitação atual,
  - sugestões de reformulação em perguntas simples (categoria melhor avaliada, autor melhor avaliado, livros mais polarizados).

- **Interpretação crítica vs. piores notas:**  
  - `worst_rated`: menor média de score, com mínimo de reviews (ranking de “piores avaliados”).  
  - `most_criticized`: maior massa de reviews negativas (score ≤ 2) – não é a mesma coisa que “pior média”.

---

## 11. Destaques técnicos para apresentação

- **MCP no fluxo principal**  
  Tools são chamadas via MCP (cliente + servidor persistentes). A API não inicia o servidor MCP por requisição, e o mesmo servidor pode ser reutilizado.

- **LangGraph como orquestrador**  
  - Caminhos claros (`structured`, `semantic`, `hybrid`, `out_of_scope`, `unsupported_composite`).
  - Facilidade de explicar o fluxo no painel “Agent Flow” do frontend.

- **pgvector + embeddings locais**  
  - Modelo de embedding `all-MiniLM-L6-v2` pré‑carregado na API e no MCP.
  - Busca semântica sobre o texto de reviews, combinável com métricas estruturadas.

- **Bedrock apenas para geração final**  
  - O LLM nunca executa tools/SQL diretamente.
  - Sempre responde no idioma da pergunta (com prompts especiais para pt‑BR), preservando nomes próprios.

- **Tools controladas e auditáveis**  
  - Ranking positivo (`get_best_rated_books`, `get_most_recommended_books`).
  - Ranking negativo (`get_lowest_rated_books` para worst_rated).
  - “Mais criticados” (`get_most_criticized_books`) com definição clara.

- **Frontend orientado a demo técnica**  
  - Mostra:
    - fluxo do agente,
    - chamadas de tools e contagem de linhas,
    - métricas de execução (tempo total, modelo, rows),
    - diagrama de arquitetura com os componentes destacados conforme a estratégia da pergunta.

Com esses pontos, o projeto fica pronto tanto para **rodar localmente** quanto para ser apresentado como um case completo de “Agentic Analytics” em entrevistas técnicas ou demonstrações executivas.

