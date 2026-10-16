# Busca semântica local — 16/10/2026

## Cenário reproduzível

Fixture `demo-synthetic-v1`: três livros fictícios e seis avaliações originais, identificados por `DEMO-SYNTHETIC`. Temas: programação Python, jardinagem e romance policial. Nenhum dado da Vert, cliente ou desafio foi utilizado.

O script `deploy/demo/seed_and_check.py` insere apenas os marcadores da fixture, reaproveita registros existentes em nova execução e atualiza seus embeddings. Ele recusa banco com outras avaliações. Usar somente em banco descartável de demonstração.

## Resultado

- Ranking via MCP com `min_reviews=1`: Practical Python 4,5; Garden Handbook 2,5; Slow Mystery 1,5. Cada livro possui duas avaliações.
- Consulta: `Python programming functions and coding examples`.
- Top-2: as duas avaliações do livro Practical Python, tanto na consulta direta como via MCP.
- Similaridades cosseno observadas: aproximadamente 0,807 e 0,696. São scores de proximidade, não probabilidades de acerto.
- Tempos de uma execução: busca direta 0,011 s; chamada semântica MCP 0,028 s. Tempo total do script, incluindo carga do modelo: 4,315 s. Amostra isolada, sem concorrência; não representa benchmark ou SLA.
- Modelo de embeddings: `all-MiniLM-L6-v2`, 384 dimensões, CPU.
- Nenhuma chamada ao Bedrock.

## Problema encontrado no índice

O índice IVFFlat original tinha 100 listas e havia sido criado com o banco vazio. Após inserir seis registros, a busca aproximada via MCP retornou zero resultados, enquanto a varredura exata retornou os dois esperados.

Na base sintética, o script reconstrói apenas esse índice com uma lista após inserir os embeddings. A busca MCP então correspondeu à busca exata. Essa configuração é específica para a fixture minúscula. Em uma base real, dimensionar o índice após a carga e comparar recall/latência com varredura exata, ajustando listas e probes.

## Repetir

Com o banco inicializado e a pilha de demonstração ativa:

```sh
docker cp deploy/demo/seed_and_check.py book-review-demo-api-1:/tmp/seed_and_check.py
docker compose --env-file /caminho/demo.env -f deploy/demo/compose.yml exec -T -e PYTHONPATH=/app api python /tmp/seed_and_check.py
```

O script testa ferramentas diretamente. O fluxo HTTP normal usa mínimo de 100 reviews em algumas consultas; os seis exemplos não satisfazem esse limiar. Não alterar silenciosamente o critério do projeto para apresentar esta fixture.

## Ainda pendente

Avaliação com conjunto representativo, consultas em português (o modelo atual não é uma escolha validada para esse idioma), geração final por LLM, teste AWS e custo observado. Esses testes demonstram funcionamento e coerência do caminho de recuperação em um cenário simples, não qualidade geral do produto.
