# ADR-0004 — Banco em Aurora Serverless v2 com pausa; módulo Rotinas lê o Airflow pela API

Data: 06/11/2026 · Status: aceita

## Contexto
O uso do sistema é em rajadas: ingestão mensal, exposição por município, detecção quando chega imagem, e consultas do
painel no horário comercial. Uma instância RDS fixa cobraria 24 h por dia. E o usuário quer ver DAGs e logs da ingestão
dentro do sistema, sem conta no Airflow da empresa, que hoje não tem permissão por DAG (SimpleAuthManager).

## Decisão
- **Aurora Serverless v2 (PostgreSQL 16.6) com mínimo 0 ACU.** Escala entre 0 e o máximo do ambiente (2 ACU em dev,
  8 em prod), pausa após ociosidade (10 min em dev, 30 em prod) e cobra só armazenamento parado. Retomada em segundos:
  a API faz retry na primeira conexão. Prod com duas instâncias `db.serverless` em AZs diferentes. PostGIS é extensão
  nativa.
- **Módulo Rotinas na API** (`/orquestracao`): consome a API REST do Airflow 3 com uma credencial de serviço guardada
  no Secrets Manager e injetada na tarefa; lista só DAGs com prefixo `mvr_`, mostra execuções, tarefas e logs, dispara
  execução. Qualquer outro `dag_id` responde 404 sem consultar o Airflow. O navegador nunca recebe o token.

## Consequências
- Custo de banco em dev perto de zero fora de uso; em prod o piso é o armazenamento e os picos pagam por ACU.
- Primeira requisição depois da pausa leva segundos; o painel mostra "acordando o banco" em vez de erro.
- O Airflow continua único e interno; o que o usuário do sistema vê é uma janela filtrada, com auditoria no lado da API.
