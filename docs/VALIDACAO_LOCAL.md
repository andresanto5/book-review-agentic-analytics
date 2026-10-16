# Validação local — 16/10/2026

## Resultado comprovado

- Docker Engine 29.2.1 iniciado; builds web, API e MCP concluídos em CPU.
- Quatro serviços inicializados; API e PostgreSQL com healthcheck saudável.
- Interface em http://127.0.0.1:8080 e proxy `/api/health` retornando `{"status":"ok"}`.
- Esquema SQL 001 a 008 aplicado em banco de demonstração vazio.
- Chamada API → MCP → PostgreSQL (`get_best_rated_books`, mínimo 1 review, limite 3) retornou lista vazia sem erro.
- Testes em container com `--network none` e criação de cliente boto3 bloqueada: health HTTP, quatro perguntas fora de escopo em português/inglês e validação de campo obrigatório passaram.
- Interface confirmou o fluxo fora de escopo com geração final e ferramentas ignoradas. O nome de modelo exibido vem da seleção da interface; não é evidência de chamada ao Bedrock.

## Correções locais

- Perguntas com “vendeu” e “venderam” agora são reconhecidas como vendas, fora do escopo. Antes tentavam uma consulta de avaliações.
- Log da conexão deixa de imprimir a senha do PostgreSQL.
- Arquivos de build, Compose e exclusões para CPU adicionados.

## Limites

Sem credenciais AWS e sem chamadas Bedrock. Banco sem dados de reviews; recuperação semântica e respostas geradas ainda não foram validadas. `/health` não testa dependências.

Consumo observado em uma amostra de inicialização, sem carga: API 414,5 MiB; MCP 387,9 MiB; PostgreSQL 61,71 MiB. Não usar essa amostra como dimensionamento produtivo.

`npm ci` reportou 20 vulnerabilidades (5 moderadas, 15 altas). É necessário analisar o relatório detalhado e distinguir dependências de build de código distribuído antes de publicar um endpoint. Não foi aplicado `audit fix --force`.

## Repetir os testes sem AWS

```sh
docker run --rm --network none -e AWS_EC2_METADATA_DISABLED=true -e PYTHONPATH=/app \
  --mount type=bind,source="$(pwd)/deploy/demo/check_local.py",target=/tmp/check_local.py,readonly \
  book-review-demo-api python /tmp/check_local.py
```

Para a pilha local, acrescentar `-f deploy/demo/compose.local-check.yml` ao comando Compose. Esse override desabilita a busca de credenciais via metadados EC2; credenciais do host não são montadas nem passadas.

As mudanças ainda são locais e não foram enviadas ao GitHub. Não houve provisionamento AWS.
