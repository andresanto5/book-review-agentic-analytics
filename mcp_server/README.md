# MCP Server – Book Review Tools

Interface **MCP (Model Context Protocol)** que expõe as mesmas ferramentas controladas do projeto para clientes agentic (ex.: Claude Desktop, Cursor, outros clientes MCP). Não duplica regra de negócio: todas as chamadas passam por `src.agents.tools` e pelo mesmo banco (PostgreSQL + pgvector).

O pacote local chama-se **`mcp_server`** para não conflitar com o pacote instalado **`mcp`** (SDK).

## O que o MCP expõe

O servidor expõe **ferramentas (tools)** apenas. Não há recursos (resources), prompts ou geração de resposta via Bedrock no MCP; a resposta final fica a cargo do cliente que consome as tools.

### Tools disponíveis

| Tool | Descrição | Parâmetros (defaults) |
|------|-----------|------------------------|
| `get_top_categories_by_avg_score` | Categorias com maior média de avaliação | `min_reviews=100`, `limit=10` |
| `get_top_books_by_review_volume` | Livros com maior volume de reviews | `limit=10` |
| `get_best_rated_books` | Livros com maior média de score (melhor avaliados) | `min_reviews=100`, `limit=10` |
| `get_most_polarized_books` | Livros mais polarizados (maior variância de score) | `min_reviews=50`, `limit=10` |
| `search_similar_reviews` | Busca semântica: reviews similares ao texto da query | `query_text`, `top_k=5` |
| `resolve_book_candidates` | Candidatos de livros por título (fragmento) | `book_title`, `limit=10` |
| `get_book_review_context_by_book_pk` | Contexto de reviews de um livro por ID | `book_pk`, `limit=5` |

Retornos são listas/dicionários JSON-friendly (nada de objetos específicos do banco).

## Como rodar

1. **Variáveis de ambiente**  
   Use o mesmo `.env` do projeto (conexão PostgreSQL, etc.). Ex.: copie `.env.example` para `.env` e ajuste.

2. **Do diretório raiz do projeto** (onde está `src/` e `mcp_server/`):

   ```bash
   python -m mcp_server.server
   ```

   O servidor sobe com transporte **stdio** (entrada/saída padrão), que é o esperado por clientes como Claude Desktop ao configurar um servidor MCP.

3. **Comando exato recomendado** (raiz do repositório):

   ```bash
   python -m mcp_server.server
   ```

   Não é necessário especificar transporte; o código usa `stdio` por padrão.

## Dependências

- O pacote **`mcp`** (Model Context Protocol Python SDK) deve estar instalado, por exemplo:

  ```bash
  pip install mcp
  ```

- O restante (PostgreSQL, `src.agents.tools`, etc.) usa as mesmas dependências do projeto (veja `requirements.txt` / `pyproject.toml`).

## Relação com FastAPI e LangGraph

- **FastAPI** continua sendo a API HTTP principal (workflow completo: guardrails, classificação, tools, Bedrock).
- **LangGraph** continua orquestrando o fluxo agentic interno.
- O **MCP** é uma interface **adicional**: expõe apenas as tools para clientes MCP, sem substituir a API nem o workflow.

Nenhuma autenticação ou SQL livre é exposto pelo MCP; apenas as tools listadas acima, com parâmetros controlados.
