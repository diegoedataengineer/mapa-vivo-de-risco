# Infraestrutura, CI/CD e operação

## Ambientes

| | dev | prod |
|---|---|---|
| gatilho | push na `main` | tag `vX.Y.Z` + aprovação manual |
| tag das imagens | `sha-<7>` | `vX.Y.Z` (e `sha-<7>`) |
| API | 1 a 2 tarefas Fargate ARM, 0,25 vCPU | 2 a 6 tarefas, 0,5 vCPU, multi-AZ |
| banco | Aurora Serverless v2 PostgreSQL 16.6 + PostGIS, 0 a 2 ACU, pausa após 10 min ocioso, 1 instância, 1 dia de backup | 0 a 8 ACU, pausa após 30 min, 2 instâncias em AZs distintas, 14 dias de backup, proteção contra exclusão |
| detecção | Batch em EC2 Spot com GPU, até 4 vCPU | até 16 vCPU |
| logs | 14 dias | 90 dias |

## Fluxo de entrega

```
feature/x ──PR──▶ main ──push──▶ ci ──▶ deploy-dev (imagens sha-<7> → terraform apply dev → fumaça /saude)
                   │
                   └──tag vX.Y.Z──▶ release (imagens vX.Y.Z → plan prod → aprovação → apply → fumaça → release no GitHub)
PR em infra/ ──▶ terraform-plan (comenta o plan de dev no PR)
```

Os workflows que tocam a AWS (`deploy-dev`, `release`, `terraform-plan`) só rodam quando a variável de repositório
`DEPLOY_ATIVO` for `true`; até o bootstrap da conta eles aparecem como pulados, não como falha.

Workflows em `.github/workflows`: `ci.yml`, `publicar-imagens.yml` (reutilizável), `deploy-dev.yml`, `release.yml`,
`terraform-plan.yml`. Segredos do repositório: `AWS_ROLE_ARN_DEV` e `AWS_ROLE_ARN_PROD` (ARNs das roles que o
Terraform cria no módulo `cicd`). Environments do GitHub: `dev` sem revisor, `prod` com revisor obrigatório.

## Terraform

`infra/terraform/modules`: `rede` (VPC, sub-redes públicas para Fargate e Batch, privadas para o banco), `dados` (S3
versionado com ciclo de vida, Aurora Serverless v2, segredos do banco e do Airflow), `registro` (ECR imutável com expiração), `servicos` (cluster ECS, API com ALB,
autoescala, circuit breaker), `lote` (Batch CPU em Fargate Spot e GPU em EC2 Spot, EventBridge de imagem nova para job
de detecção), `orquestrador` (usuário IAM mínimo para o Airflow da VPS), `observabilidade` (log group, alarmes de 5xx, latência p95, tarefas saudáveis, CPU do banco, job falho,
SNS por e-mail), `cicd` (provedor OIDC e role por ambiente). `envs/dev` e `envs/prod` compõem os módulos com o mesmo
`main.tf` e tfvars próprios; estado remoto em S3 com lock no DynamoDB (`bootstrap.md`).

Regra de operação: `terraform plan -out` sempre, `apply` do arquivo; nunca apply direto.

## Eventos

```
Airflow (VPS) ──mensal ou botão──▶ S3 bases/<fonte>/<versao>/ + manifest.json ──▶ Batch (CPU): exposicao, um job por município
S3 imagens/<municipio>/<data>.tif  ──Object Created──▶ EventBridge ──▶ Batch (GPU): deteccao ──▶ S3 deteccoes/ + PostGIS
Batch (CPU): exposicao  ◀── Airflow ao fim da ingestão, ou a API sob demanda ── cruza SGB × Censo 2022 × detecções → lista de visitas
Batch FAILED ──▶ EventBridge ──▶ SNS ──▶ e-mail
```

## Confiabilidade e observabilidade

Health check em `/saude` no contêiner e no ALB; deploy com 100 % de capacidade mínima e rollback automático; autoescala
por CPU a 60 %; retries nos jobs (3 na exposição, 2 na detecção) e timeout; Spot só onde o trabalho é idempotente por tile
e pode ser refeito; alarmes com ação no SNS; Container Insights ligado; logs estruturados por serviço. Teste de caos
planejado: matar a tarefa da API em dev durante a fumaça e exigir que o alarme de tarefas saudáveis dispare e o serviço
volte sozinho.

## Governança de dados na infra

Dados pessoais só no Aurora (criptografado, sub-rede privada, acesso só do security group dos serviços); S3 sem acesso
público, versionado, com imagens frias após 90 dias e tiles temporários expirando em 30; segredo do banco no Secrets
Manager, lido pela tarefa, nunca em variável de ambiente em texto; tags `dados_pessoais` e `lgpd` no banco para
inventário; trilha de auditoria da aplicação no PostgreSQL e dos acessos à AWS no CloudTrail (a ligar no bootstrap).

## Regerar o desenho

```bash
python -m venv .venv-diag && .venv-diag/bin/pip install diagrams pillow
.venv-diag/bin/python docs/gerar_arquitetura.py   # escreve docs/arquitetura.png com os ícones oficiais da AWS
```

## Módulo Rotinas (DAGs e logs no sistema)

A API expõe `/orquestracao/dags`, `/orquestracao/dags/{id}/execucoes`, `.../tarefas`, `.../tarefas/{tarefa}/log` e
`POST /orquestracao/dags/{id}/executar`, consumindo a API REST do Airflow 3 com a credencial de serviço do segredo
`mvr/<ambiente>/airflow` (url, usuario, senha). Só DAGs com prefixo `mvr_` existem para o módulo. O painel mostra isso
como a tela do Airflow: lista de rotinas, histórico de execuções com estado, tarefas da execução e o log de cada uma,
mais o botão de executar com parâmetros (UFs, municípios).
