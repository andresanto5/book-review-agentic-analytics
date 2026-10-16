# Demonstração local sem chamadas AWS

Esta trilha verifica a integração usando dados sintéticos, PostgreSQL/pgvector, embeddings locais e MCP reais. A geração final é substituída por uma resposta fixa explicitamente marcada como **SIMULAÇÃO LOCAL — SEM LLM/AWS**. Ela testa o transporte do contexto ao gerador e o retorno HTTP, não qualidade de escrita, raciocínio de um LLM ou acesso ao Bedrock.

## Preparação

1. Iniciar Docker Desktop.
2. Na raiz do projeto, copiar `deploy/demo/demo.env.example` para um arquivo local ignorado pelo Git e escolher uma senha de demonstração. O identificador de modelo pode permanecer fictício para esses testes.
3. Construir e subir a pilha com o override local:

```sh
docker compose --env-file /caminho/demo.env -f deploy/demo/compose.yml -f deploy/demo/compose.local-check.yml build
docker compose --env-file /caminho/demo.env -f deploy/demo/compose.yml -f deploy/demo/compose.local-check.yml up -d
```

Não configurar nem montar credenciais AWS. O script de integração bloqueia `boto3.client` por mock; o override desabilita a busca de credenciais via metadados EC2.

## Inicialização e dados

Aplicar os arquivos `sql/ddl/001_*.sql` até `008_*.sql` em ordem no banco `book_reviews`, usando `psql -v ON_ERROR_STOP=1`. O Compose original cria apenas o schema e a extensão.

```sh
docker cp deploy/demo/seed_and_check.py book-review-demo-api-1:/tmp/seed_and_check.py
docker compose --env-file /caminho/demo.env -f deploy/demo/compose.yml exec -T -e PYTHONPATH=/app api python /tmp/seed_and_check.py
```

O script contém seis avaliações fictícias e verifica a busca exata e via MCP. Recusa bancos com outras avaliações e reconstrói o índice dessa fixture com uma lista. Consulte [validação semântica](VALIDACAO_SEMANTICA.md).

## Testar o fluxo HTTP completo

```sh
docker cp deploy/demo/check_workflow_free.py book-review-demo-api-1:/tmp/check_workflow_free.py
docker compose --env-file /caminho/demo.env -f deploy/demo/compose.yml exec -T -e PYTHONPATH=/app api python /tmp/check_workflow_free.py
```

O TestClient exercita o app FastAPI e o workflow dentro de um processo de teste; as chamadas MCP e SQL utilizam os serviços reais. A substituição do gerador só existe nesse processo, sem alterar o servidor HTTP já em execução. Não testar perguntas que geram texto na interface normal esperando que ela use automaticamente a simulação.

## Resultados observados em 16/10/2026

| Fluxo | Linhas SQL | Linhas semânticas | Geração | Resultado |
|---|---:|---:|---|---|
| Structured | 3 | 0 | Simulada | Passou |
| Semantic | 0 | 5 | Simulada | Passou |
| Hybrid | 3 | 5 | Simulada | Passou |
| Out of scope | 0 | 0 | Ignorada | Passou |
| Unsupported composite | 0 | 0 | Ignorada | Passou |

O gerador simulado verifica se o prompt contém os registros `DEMO-SYNTHETIC`. O teste falha se houver tentativa de criar cliente AWS ou se a resposta perder o marcador de simulação. Foram três chamadas ao gerador simulado e nenhuma à AWS.

Os testes HTTP básicos e a validação de campo obrigatório estão em `deploy/demo/check_local.py`; veja [validação local](VALIDACAO_LOCAL.md). O teste completo usa consultas de volume de reviews para preservar os limiares de 100 avaliações das outras ferramentas.

## Como apresentar no portfólio

“Prova de conceito de analytics com roteamento estruturado, semântico e híbrido. Integração local validada com dados sintéticos, PostgreSQL/pgvector e ferramentas MCP. A trilha gratuita utiliza um gerador simulado; a integração Bedrock original permanece disponível para validação separada.”

Não apresentar esta trilha como implantação AWS, validação do Bedrock ou avaliação da qualidade de um LLM. A base pequena serve para regressão funcional; não representa validação estatística de recuperação.

## Encerrar

```sh
docker compose --env-file /caminho/demo.env -f deploy/demo/compose.yml -f deploy/demo/compose.local-check.yml down
```

Esse comando preserva o volume do banco. A pilha só publica a interface em loopback e não deve ser exposta publicamente sem autenticação e revisão das dependências. Os alertas do instalador npm estão registrados na validação local.
