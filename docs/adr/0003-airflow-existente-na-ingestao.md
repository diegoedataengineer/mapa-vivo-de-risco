# ADR-0003 — O Airflow existente orquestra a ingestão das bases públicas

Data: 05/11/2026 · Status: aceita

## Contexto
As bases públicas (setorização do SGB, municípios do Cemaden, setores, CNEFE e agregados do Censo 2022, imagem) mudam
devagar, vêm de portais com URLs que trocam, e precisam de versão e linhagem. A Mundo dos Dados já opera um Airflow 3
numa VPS, com DAGs de coleta de dados públicos, retomada, retries e botão no painel. Replicar isso num job do Batch seria
código novo para um problema já resolvido.

## Decisão
- A ingestão é uma DAG no Airflow existente (`infra/airflow/dags/mvr_ingestao.py`), mensal e acionável sob demanda, com
  o pacote `mvr_ingestao` (catálogo de fontes, download com streaming, manifesto com sha256 e versão, publicação em
  `s3://<bucket>/bases/<fonte>/<versao>/`).
- O Airflow entra na AWS com um usuário IAM mínimo (módulo `orquestrador`): escrever em `bases/` e `imagens/` e
  submeter o job de exposição no Batch. Sem acesso ao banco, ao ECS nem a outros prefixos.
- A exposição continua no Batch, submetida pelo Airflow ao fim da ingestão, um job por município, com a versão das
  bases daquele dia nos parâmetros. A detecção continua orientada a evento do S3.
- A ingestão sai da lista de serviços em contêiner da AWS (sem ECR nem job definition para ela).

## Consequências
- Linhagem completa: cada exposição aponta para manifestos de base com sha256 e data; a URL de origem fica gravada.
- Dependência operacional da VPS: se o Airflow parar, a base não atualiza, mas nada em produção para, porque a API lê
  o PostGIS. Mitigação: alarme de ausência de ingestão mensal no CloudWatch (métrica de objeto novo em `bases/`).
- Chave de acesso de longa duração num ambiente fora da AWS: rotação trimestral e escopo mínimo compensam.
