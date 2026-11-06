"""Ingestão das bases públicas do Mapa Vivo de Risco no Airflow existente (VPS da Mundo dos Dados, Airflow 3).

  relógio mensal ─▶ mvr_ingestao: baixa SGB, Cemaden, IBGE (setores, CNEFE, agregados) ─▶ S3 bases/<fonte>/<versao>/
                                          └─▶ submete o job de exposição no AWS Batch para cada município configurado
  botão/trigger   ─▶ o mesmo, com conf {"municipios": [...], "ufs": [...]}

Pré-requisitos no Airflow: pacote `mvr_ingestao` no PYTHONPATH (rsync de servicos/ingestao), conexão `aws_mvr`
(usuário IAM criado pelo módulo Terraform `orquestrador`, só S3 bases/ e batch:SubmitJob), Variables `mvr_bucket`,
`mvr_fila_cpu`, `mvr_job_exposicao`, `mvr_ufs` (lista) e `mvr_municipios` (lista de códigos IBGE), opcionalmente
`mvr_url_<fonte>` para sobrescrever a URL de uma fonte quando o portal mudar.
"""

from __future__ import annotations

import json
from pathlib import Path

import pendulum
from airflow.models import Variable
from airflow.providers.amazon.aws.operators.batch import BatchOperator
from airflow.sdk import DAG, Asset, task

FUSO = pendulum.timezone("America/Sao_Paulo")
BASES = Asset(name="mvr_bases", uri="mvr://bases")
PADRAO = {"owner": "mvr", "retries": 2, "retry_delay": pendulum.duration(minutes=10)}
TMP = Path("/tmp/mvr")


def _lista(nome: str, padrao: list[str]) -> list[str]:
    return json.loads(Variable.get(nome, default_var=json.dumps(padrao)))


with DAG(
    dag_id="mvr_ingestao",
    description="Mapa Vivo de Risco: baixa e versiona no S3 as bases públicas (SGB, Cemaden, IBGE) e dispara a exposição no Batch",
    schedule="0 3 1 * *",  # dia 1 de cada mês, 03:00
    start_date=pendulum.datetime(2026, 11, 1, tz=FUSO),
    catchup=False,
    max_active_runs=1,
    tags=["mvr", "ingestao"],
    default_args=PADRAO,
    params={"ufs": [], "municipios": []},
):

    @task(task_id="nacionais")
    def nacionais() -> list[dict]:
        from mvr_ingestao import ingerir

        bucket = Variable.get("mvr_bucket")
        saida = []
        for fonte in ("cemaden_municipios", "ibge_agregados_setores_2022"):
            saida.append(ingerir(fonte, TMP, url=Variable.get(f"mvr_url_{fonte}", default_var=None), bucket=bucket))
        return saida

    @task(task_id="por_uf")
    def por_uf(uf: str) -> list[dict]:
        from mvr_ingestao import ingerir

        bucket = Variable.get("mvr_bucket")
        return [
            ingerir("ibge_setores_2022", TMP, url=Variable.get("mvr_url_ibge_setores_2022", default_var=None), bucket=bucket, uf=uf),
            ingerir("ibge_cnefe_2022", TMP, url=Variable.get("mvr_url_ibge_cnefe_2022", default_var=None), bucket=bucket, uf=uf),
        ]

    @task(task_id="sgb_por_municipio")
    def sgb_por_municipio(municipio: str) -> dict:
        from mvr_ingestao import ingerir

        return ingerir("sgb_setorizacao", TMP, url=Variable.get("mvr_url_sgb_setorizacao", default_var=None), bucket=Variable.get("mvr_bucket"), municipio_ibge=municipio)

    @task(task_id="ufs", trigger_rule="all_done", outlets=[BASES])
    def ufs(params=None) -> list[str]:
        return list(params.get("ufs") or []) or _lista("mvr_ufs", ["RJ"])

    @task(task_id="municipios")
    def municipios(params=None) -> list[str]:
        return list(params.get("municipios") or []) or _lista("mvr_municipios", ["3303906"])  # Petrópolis

    lista_ufs, lista_municipios = ufs(), municipios()
    bases = [nacionais(), por_uf.expand(uf=lista_ufs), sgb_por_municipio.expand(municipio=lista_municipios)]

    # exposição no Batch (Fargate Spot): um job por município, com a versão das bases do dia
    exposicao = BatchOperator.partial(
        task_id="exposicao",
        aws_conn_id="aws_mvr",
        job_name="exposicao",
        job_queue=Variable.get("mvr_fila_cpu", default_var="mvr-dev-cpu"),
        job_definition=Variable.get("mvr_job_exposicao", default_var="mvr-dev-exposicao"),
        wait_for_completion=True,
        deferrable=True,
    ).expand(parameters=lista_municipios.map(lambda m: {"municipio": m}))

    bases >> exposicao
