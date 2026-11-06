"""Módulo Rotinas: o painel vê DAGs, execuções, tarefas e logs do Airflow existente, só as deste projeto (prefixo mvr_).

O backend fala com a API REST do Airflow 3 com uma credencial de serviço (usuário do Airflow dedicado ao projeto),
guarda o token em memória e renova quando expira. O navegador nunca recebe o token nem enxerga o Airflow.
Todo dag_id que não começa com o prefixo responde 404: o módulo não sabe que as outras DAGs existem.
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/orquestracao", tags=["orquestracao"])


class Cliente:
    def __init__(
        self,
        base: str | None = None,
        usuario: str | None = None,
        senha: str | None = None,
        prefixo: str | None = None,
        http: httpx.Client | None = None,
    ):
        self.base = (base or os.environ.get("MVR_AIRFLOW_URL", "")).rstrip("/")
        self.usuario = usuario or os.environ.get("MVR_AIRFLOW_USUARIO", "")
        self.senha = senha or os.environ.get("MVR_AIRFLOW_SENHA", "")
        self.prefixo = prefixo or os.environ.get("MVR_AIRFLOW_PREFIXO", "mvr_")
        self.http = http or httpx.Client(timeout=30)
        self._token: str | None = None
        self._token_ate = 0.0

    def _token_valido(self) -> str:
        if self._token and time.time() < self._token_ate:
            return self._token
        r = self.http.post(f"{self.base}/auth/token", json={"username": self.usuario, "password": self.senha})
        if r.status_code != 201 and r.status_code != 200:
            raise HTTPException(502, "não foi possível autenticar no orquestrador")
        self._token = r.json()["access_token"]
        self._token_ate = time.time() + 20 * 60  # renova antes do padrão de 24 h; barato e tolera rotação
        return self._token

    def _chamar(self, metodo: str, caminho: str, **kw: Any) -> Any:
        for tentativa in (1, 2):
            cab = {"Authorization": f"Bearer {self._token_valido()}", **kw.pop("headers", {})}
            r = self.http.request(metodo, f"{self.base}/api/v2{caminho}", headers=cab, **kw)
            if r.status_code == 401 and tentativa == 1:
                self._token = None
                continue
            if r.status_code == 404:
                raise HTTPException(404, "não encontrado no orquestrador")
            if r.status_code >= 400:
                raise HTTPException(502, f"orquestrador respondeu {r.status_code}")
            return r.json() if "json" in r.headers.get("content-type", "") else r.text
        raise HTTPException(502, "orquestrador recusou a credencial")

    def _conferir(self, dag_id: str) -> None:
        if not dag_id.startswith(self.prefixo):
            raise HTTPException(404, "rotina não encontrada")

    def dags(self) -> list[dict]:
        dados = self._chamar("GET", "/dags", params={"dag_id_pattern": self.prefixo, "limit": 100})
        return [
            {
                "id": d["dag_id"],
                "descricao": d.get("dag_display_name") or d["dag_id"],
                "pausada": d.get("is_paused"),
                "agenda": d.get("timetable_description"),
                "proxima": d.get("next_dagrun_run_after"),
                "etiquetas": [t["name"] for t in d.get("tags", [])],
            }
            for d in dados.get("dags", [])
            if d["dag_id"].startswith(self.prefixo)
        ]

    def execucoes(self, dag_id: str, limite: int = 20) -> list[dict]:
        self._conferir(dag_id)
        dados = self._chamar("GET", f"/dags/{dag_id}/dagRuns", params={"limit": limite, "order_by": "-run_after"})
        return [
            {
                "id": r["dag_run_id"],
                "estado": r["state"],
                "tipo": r["run_type"],
                "inicio": r.get("start_date"),
                "fim": r.get("end_date"),
                "conf": r.get("conf"),
            }
            for r in dados.get("dag_runs", [])
        ]

    def tarefas(self, dag_id: str, execucao_id: str) -> list[dict]:
        self._conferir(dag_id)
        dados = self._chamar("GET", f"/dags/{dag_id}/dagRuns/{execucao_id}/taskInstances", params={"limit": 200})
        return [
            {
                "tarefa": t["task_id"],
                "indice": t.get("map_index", -1),
                "estado": t.get("state"),
                "tentativa": t.get("try_number"),
                "inicio": t.get("start_date"),
                "fim": t.get("end_date"),
                "duracao_s": t.get("duration"),
            }
            for t in dados.get("task_instances", [])
        ]

    def log(self, dag_id: str, execucao_id: str, tarefa: str, tentativa: int = 1, indice: int = -1) -> str:
        self._conferir(dag_id)
        dados = self._chamar(
            "GET",
            f"/dags/{dag_id}/dagRuns/{execucao_id}/taskInstances/{tarefa}/logs/{tentativa}",
            params={"map_index": indice} if indice >= 0 else {},
            headers={"Accept": "application/json"},
        )
        if isinstance(dados, dict):
            partes = dados.get("content", [])
            if partes and isinstance(partes[0], dict):
                return "\n".join(
                    f"[{p.get('timestamp', '')}] {p.get('level', '')} {p.get('event', '')}" for p in partes
                )
            return "\n".join(str(p) for p in partes)
        return str(dados)

    def executar(self, dag_id: str, conf: dict | None = None) -> dict:
        self._conferir(dag_id)
        r = self._chamar("POST", f"/dags/{dag_id}/dagRuns", json={"logical_date": None, "conf": conf or {}})
        return {"id": r["dag_run_id"], "estado": r["state"]}


_cliente: Cliente | None = None


def cliente() -> Cliente:
    global _cliente
    if _cliente is None:
        _cliente = Cliente()
    return _cliente


class PedidoExecucao(BaseModel):
    conf: dict = {}


@router.get("/dags")
def listar_dags() -> list[dict]:
    return cliente().dags()


@router.get("/dags/{dag_id}/execucoes")
def listar_execucoes(dag_id: str, limite: int = Query(20, ge=1, le=100)) -> list[dict]:
    return cliente().execucoes(dag_id, limite)


@router.get("/dags/{dag_id}/execucoes/{execucao_id}/tarefas")
def listar_tarefas(dag_id: str, execucao_id: str) -> list[dict]:
    return cliente().tarefas(dag_id, execucao_id)


@router.get("/dags/{dag_id}/execucoes/{execucao_id}/tarefas/{tarefa}/log")
def ver_log(dag_id: str, execucao_id: str, tarefa: str, tentativa: int = 1, indice: int = -1) -> dict:
    return {"log": cliente().log(dag_id, execucao_id, tarefa, tentativa, indice)}


@router.post("/dags/{dag_id}/executar", status_code=202)
def executar_dag(dag_id: str, pedido: PedidoExecucao) -> dict:
    return cliente().executar(dag_id, pedido.conf)
