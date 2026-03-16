# MCP – Model Context Protocol

## Objetivo

O MCP faz parte do **fluxo principal** da aplicação. A API FastAPI usa o LangGraph, que chama as tools **via um cliente MCP persistente** conectado a um **MCP server em processo separado**. Não há spawn do server por requisição; a latência fica baixa.

- **FastAPI:** porta principal de entrada (HTTP).
- **LangGraph:** orquestra interpretação, tools e resposta final.
- **MCP client** (`src/mcp/client.py`): **uma sessão persistente por processo**, conectada ao MCP server via streamable-http. Reutilizada em todas as chamadas de tool.
- **MCP server** (`mcp_server/server.py`): **processo separado e persistente**, expondo as tools em HTTP (streamable-http). Deve ser subido antes da API.
- **Fallback:** se `MCP_FALLBACK_TO_LOCAL=true` e o MCP falhar ou estiver indisponível, o workflow usa chamada direta a `src.agents.tools` e ao repositório vetorial.
- **Bedrock:** apenas na etapa final de geração de resposta.

## Arquitetura

```
Cliente HTTP
    → FastAPI
    → LangGraph
    → MCP client (sessão persistente, streamable-http)
    → MCP server (processo separado, já em execução)
    → tools (src.agents.tools + vector_repository)
    → PostgreSQL / pgvector
    → Bedrock (resposta final)
```

- A **API espera que o MCP server já esteja rodando**. O client conecta na primeira chamada de tool e mantém a conexão.
- Se o MCP estiver desligado ou falhar e `MCP_FALLBACK_TO_LOCAL=true`, o fluxo usa tools locais.

## Configuração (.env)

| Variável | Descrição | Default |
|----------|-----------|---------|
| `MCP_ENABLED` | Usar MCP como camada de tools | `true` |
| `MCP_TRANSPORT` | Transporte (uso atual: `streamable-http`) | `streamable-http` |
| `MCP_SERVER_URL` | URL do MCP server (onde a API conecta) | `http://127.0.0.1:8001/mcp` |
| `MCP_FALLBACK_TO_LOCAL` | Em falha/indisponibilidade, usar tools locais | `true` |
| `MCP_SERVER_HOST` | Host do MCP server (só ao subir o server) | `127.0.0.1` |
| `MCP_SERVER_PORT` | Porta do MCP server (só ao subir o server) | `8001` |

Exemplo:

```env
MCP_ENABLED=true
MCP_TRANSPORT=streamable-http
MCP_SERVER_URL=http://127.0.0.1:8001/mcp
MCP_FALLBACK_TO_LOCAL=true
MCP_SERVER_PORT=8001
```

## Como subir o MCP server (separadamente)

O MCP server **deve ser executado como processo separado** antes de usar a API com MCP.

1. Use o mesmo `.env` do projeto (PostgreSQL, etc.).
2. Na raiz do projeto:

```bash
python -m mcp_server.server
```

- Por padrão sobe em **streamable-http** em `http://127.0.0.1:8001/mcp` (porta via `MCP_SERVER_PORT`).
- **Preload de embeddings:** no startup do processo, o modelo de embeddings (`all-MiniLM-L6-v2`) é carregado uma vez (singleton). O log mostra `MCP startup: embedding model preloaded in X.XXXs (singleton ready for semantic MCP tools)`. Assim a primeira chamada semântica não fica lenta por carga do modelo.
- Para uso com Cursor/Claude Desktop (stdio), use: `python -m mcp_server.server stdio`.

A API **não** inicia o MCP server; ela apenas conecta à URL configurada.

## Como subir a API

1. Garanta que o MCP server está rodando (se for usar MCP).
2. Na raiz do projeto:

```bash
uvicorn api.main:app --reload
```

Ou com host/porta explícitos (ex.: API na 8000):

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

No startup a API registra no log se MCP está habilitado e a URL, e se o fallback local está ativo.

## Como validar que a API está usando MCP persistente

1. **Startup:** log com `MCP enabled (persistent client to http://...)` e `Fallback local=true/false`.
2. **Primeira chamada de tool:** log `MCP client connected to ... in X.XXs (persistent session).`
3. **Chamadas seguintes:** log `MCP call_tool name=... rows=N elapsed=X.XXs persistent=yes` e `run_structured_tool: ... (via MCP, persistent).`
4. **Quantidade de linhas:** `rows=N` deve refletir o retorno real da tool (ex.: 10 linhas para `limit=10`).
5. **Fallback:** se o MCP estiver fora do ar e `MCP_FALLBACK_TO_LOCAL=true`, deve aparecer `using fallback` e `(fallback local)`.

## Formato da resposta MCP (tools que retornam lista)

As tools que retornam listas (ex.: `get_best_rated_books`, `search_similar_reviews`) devolvem **sempre** uma lista de dicionários. O client:

1. Lê `structuredContent` ou `content` (blocos de texto JSON).
2. **Desenvelope:** se o payload for um dict com chave `result`, `data`, `rows` ou `content` contendo lista, usa essa lista.
3. Normaliza para `list[dict]` (um item por registro).

Assim, **`rows` representa o número real de registros** (ex.: 10 para `get_best_rated_books` com `limit=10`). O log do MCP client inclui `parsing=...` (ex.: `content_multi_block(n=10)` ou `content_single_block`) para inspeção.

## Validação: roteamento e parsing

| Pergunta | Esperado (strategy / target_entity / metric_intent) |
|----------|-----------------------------------------------------|
| "O que as avaliações falam sobre o livro Lilla Belle: The First Stages?" | semantic / book / theme_summary |
| "Resuma as principais reclamações sobre Harry Potter" | semantic / book / complaint_summary |
| "Quais livros são mais polarizados?" | structured / book / most_polarized |
| "Qual o livro melhor avaliado?" | structured / book / best_rated |

Para **MCP** `get_best_rated_books` com `limit=10`: o workflow deve registrar **rows=10** (não 1). Verifique no log: `run_structured_tool: tool=get_best_rated_books rows=10 (real)` e `Chat request completed ... rows_struct=10`.

## Fallback local

- **`MCP_FALLBACK_TO_LOCAL=true`:** em falha ou indisponibilidade do MCP, o LangGraph chama `src.agents.tools` e o repositório vetorial diretamente. A API continua respondendo.
- **`MCP_FALLBACK_TO_LOCAL=false`:** em falha do MCP, o workflow não usa tools locais; o resultado da tool fica vazio e a resposta pode ser limitada.

## Tools disponíveis no MCP server

| # | Tool | Descrição |
|---|------|-----------|
| 1 | `get_top_categories_by_avg_score` | Categorias com maior média de avaliação |
| 2 | `get_top_books_by_review_volume` | Livros com maior volume de reviews |
| 3 | `get_best_rated_books` | Livros com maior média de score |
| 4 | `get_lowest_rated_books` | Livros com menor média |
| 5 | `get_most_polarized_books` | Livros mais polarizados |
| 6 | `get_most_recommended_books` | Livros mais recomendados |
| 7 | `get_top_authors_by_avg_score` | Autores com maior média |
| 8 | `get_top_authors_by_review_volume` | Autores com maior volume de reviews |
| 9 | `search_similar_reviews` | Busca semântica em reviews |
| 10 | `resolve_book_candidates` | Candidatos de livros por título |
| 11 | `get_book_review_context_by_book_pk` | Contexto de reviews por ID do livro |

Retornos são listas/dicionários JSON; o server reutiliza `src.agents.tools` (sem duplicar regra de negócio).

## Dependência

Pacote **`mcp`** (SDK), já em `requirements.txt`. O servidor local chama-se **`mcp_server`** para não conflitar com o pacote `mcp`.
