"""Testa o módulo Rotinas contra um Airflow falso (MockTransport): filtro por prefixo, renovação de token, logs."""

import httpx
import pytest
from fastapi import HTTPException

from mvr_api.orquestracao import Cliente

CHAMADAS: list[str] = []


def airflow_falso(req: httpx.Request) -> httpx.Response:
    CHAMADAS.append(f"{req.method} {req.url.path}")
    if req.url.path == "/auth/token":
        return httpx.Response(201, json={"access_token": "tok"})
    if req.headers.get("authorization") != "Bearer tok":
        return httpx.Response(401, json={})
    if req.url.path == "/api/v2/dags":
        return httpx.Response(
            200,
            json={
                "dags": [
                    {
                        "dag_id": "mvr_ingestao",
                        "is_paused": False,
                        "timetable_description": "mensal",
                        "tags": [{"name": "mvr"}],
                    },
                    {"dag_id": "radar_coleta", "is_paused": False, "timetable_description": "3 h", "tags": []},
                ]
            },
        )
    if req.url.path == "/api/v2/dags/mvr_ingestao/dagRuns" and req.method == "GET":
        return httpx.Response(
            200, json={"dag_runs": [{"dag_run_id": "manual__1", "state": "success", "run_type": "manual"}]}
        )
    if req.url.path == "/api/v2/dags/mvr_ingestao/dagRuns" and req.method == "POST":
        return httpx.Response(200, json={"dag_run_id": "manual__2", "state": "queued"})
    if req.url.path.endswith("/logs/1"):
        return httpx.Response(
            200, json={"content": [{"timestamp": "2026-11-06T00:00:00", "level": "info", "event": "baixado"}]}
        )
    return httpx.Response(404, json={})


@pytest.fixture
def cli():
    CHAMADAS.clear()
    return Cliente(
        base="http://airflow",
        usuario="svc",
        senha="x",
        prefixo="mvr_",
        http=httpx.Client(transport=httpx.MockTransport(airflow_falso)),
    )


def test_lista_so_as_dags_do_projeto(cli):
    dags = cli.dags()
    assert [d["id"] for d in dags] == ["mvr_ingestao"]
    assert dags[0]["etiquetas"] == ["mvr"]


def test_dag_de_outro_projeto_e_404(cli):
    with pytest.raises(HTTPException) as e:
        cli.execucoes("radar_coleta")
    assert e.value.status_code == 404
    assert not any("radar_coleta" in c for c in CHAMADAS)  # nem pergunta ao Airflow


def test_token_e_pedido_uma_vez_e_reaproveitado(cli):
    cli.dags()
    cli.execucoes("mvr_ingestao")
    assert CHAMADAS.count("POST /auth/token") == 1


def test_log_vem_formatado(cli):
    log = cli.log("mvr_ingestao", "manual__1", "nacionais", 1)
    assert "baixado" in log and "info" in log


def test_executar_devolve_id(cli):
    assert cli.executar("mvr_ingestao", {"ufs": ["RJ"]}) == {"id": "manual__2", "estado": "queued"}
