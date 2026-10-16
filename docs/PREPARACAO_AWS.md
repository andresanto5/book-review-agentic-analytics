# Preparação de demonstração AWS

Estado: build CPU e integração local básica validados; implantação AWS pendente. Ver [evidências e limites da validação local](VALIDACAO_LOCAL.md). Nenhum recurso AWS foi criado nesta revisão.

## Revisão do código

- O cliente usa `boto3` e a API Converse, com credenciais pela cadeia padrão do SDK.
- Embeddings são locais (`all-MiniLM-L6-v2`), com uma cópia por processo de API/MCP.
- O Compose original inicializa apenas PostgreSQL. O novo pacote inclui web, API, MCP e banco.
- `/health` verifica somente o processo HTTP. Não comprova acesso ao banco, MCP ou Bedrock.
- `requirements.txt` inclui CUDA/NVIDIA e Triton; o pacote CPU remove essas dependências e instala PyTorch pelo índice CPU.
- O repositório contém `node_modules` e bytecode versionados; `.dockerignore` os exclui do build. A remoção do histórico não faz parte desta revisão.
- O README menciona testes em `tests/`, mas esse diretório não está presente no checkout. Não há resultado de testes para atribuir a esta versão.

## Pacote local

Arquivos em `deploy/demo/`. Copie `demo.env.example` para um arquivo local fora do Git, preencha senha e o modelo já autorizado. Não há credenciais AWS nos arquivos.

Na raiz do repositório:

```sh
docker compose --env-file /caminho/demo.env -f deploy/demo/compose.yml config --quiet
docker compose --env-file /caminho/demo.env -f deploy/demo/compose.yml build
docker compose --env-file /caminho/demo.env -f deploy/demo/compose.yml up -d
```

O build baixa bibliotecas e modelos podem ser baixados na primeira inicialização. A configuração não importa o dataset: executar o DDL em `sql/ddl` na ordem correta e carregar uma amostra autorizada, incluindo os embeddings, continuam sendo etapas obrigatórias antes de testar perguntas.

Acesse `http://localhost:8080`. Web usa `/api` no mesmo domínio. Banco, API e MCP não publicam portas no host. A porta web é restrita a loopback porque a aplicação ainda não possui autenticação para uma demonstração pública.

No computador local, o container não herda automaticamente o login AWS do host. Definir e validar um método de credenciais temporárias antes de chamar Bedrock; não colocar chaves em imagens ou no Git. Na EC2, usar instance profile e validar a cadeia do SDK dentro do container (incluindo IMDSv2 e hop limit compatível com bridge).

## Candidato AWS para sessão curta

Uma EC2 x86_64 com Docker Compose, armazenamento EBS e instance profile é uma primeira opção para demonstrar operação. O tipo e a memória dependem de medir o consumo dos dois processos de embeddings e do banco; não escolher uma micro instância apenas pelo nome. Esta configuração não oferece alta disponibilidade.

Sem portas de entrada no security group: acesso por Session Manager, encaminhando a porta 8080. A instância precisa de SSM Agent, permissões SSM e conectividade de saída para SSM, Bedrock e downloads. Escolher subnet e rota explicitamente; não pressupor VPC padrão nem adicionar NAT Gateway automaticamente.

Permissão de aplicação: `bedrock:InvokeModel` limitada ao ARN do modelo e região escolhidos. Converse usa essa permissão. Perfis de inferência podem exigir ARNs adicionais: confirmar o identificador realmente utilizado antes de escrever a política final. Não conceder administração AWS ao processo.

O Compose mantém modelo principal e fallback iguais para não selecionar outro modelo silenciosamente. Isso ainda permite uma repetição em algumas falhas, conforme o cliente atual. Uma evolução deve tornar o fallback desativável e registrar consumo por solicitação.

## Validação antes da implantação

1. Build CPU e build web limpos; resolver eventuais incompatibilidades de dependências.
2. Confirmar origem, licença, tamanho e esquema da amostra de dados; executar ingestão e embeddings.
3. Validar pergunta estruturada, semântica, híbrida, fora de escopo e falha do Bedrock.
4. Verificar API, MCP e banco separadamente; registrar erros e tempos.
5. Confirmar modelo/região, permissões mínimas e uso de credenciais temporárias.
6. Medir memória, tokens, duração da sessão, armazenamento e tráfego. Registrar os resultados, sem prometer SLA.
7. Definir limite de gastos com o titular antes de provisionar recursos. Alertas de orçamento não são um bloqueio rígido de cobrança.

## Encerramento

`docker compose --env-file /caminho/demo.env -f deploy/demo/compose.yml down` encerra os serviços e preserva o volume. A exclusão do volume exige decisão explícita após exportar a amostra que precisar ser preservada.

Na AWS, terminar a instância e verificar volumes, snapshots, IPs públicos, logs e imagens remanescentes. Parar EC2 não elimina custos de armazenamento. Não deixar endpoint público sem autenticação.

## Evidência para portfólio

Após execução real: diagrama, versão do código, configuração sem segredos, demo curta, tabela de testes, latência medida, uso de tokens e custo observado. Até lá, apresentar este pacote como preparação de implantação.

Fontes: [Bedrock InvokeModel](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InvokeModel.html), [Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html), [encaminhamento de portas](https://docs.aws.amazon.com/en_en/systems-manager/latest/userguide/session-manager-working-with-sessions-start.html).
