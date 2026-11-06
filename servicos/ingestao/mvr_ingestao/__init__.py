"""Ingestão das bases públicas: baixar, conferir e versionar no S3. Executado como tarefas do Airflow existente."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path

import httpx

from mvr_ingestao.fontes import FONTES, Fonte

log = logging.getLogger(__name__)


def baixar(fonte: Fonte, destino: Path, url: str | None = None, **params: str) -> Path:
    """Baixa a fonte para `destino` (streaming) e devolve o caminho. `url` sobrescreve a padrão (Variable do Airflow)."""
    url = (url or fonte.url_padrao).format(**params)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with httpx.stream("GET", url, follow_redirects=True, timeout=600) as r:
        r.raise_for_status()
        with destino.open("wb") as f:
            for parte in r.iter_bytes(1 << 20):
                f.write(parte)
    log.info("baixado %s -> %s (%d bytes)", url, destino, destino.stat().st_size)
    return destino


def manifesto(fonte: Fonte, arquivo: Path, url: str, params: dict[str, str]) -> dict:
    sha = hashlib.sha256()
    with arquivo.open("rb") as f:
        for parte in iter(lambda: f.read(1 << 20), b""):
            sha.update(parte)
    return {
        "fonte": fonte.id,
        "origem": fonte.origem,
        "url": url,
        "parametros": params,
        "arquivo": arquivo.name,
        "tamanho": arquivo.stat().st_size,
        "sha256": sha.hexdigest(),
        "ingerido_em": datetime.now(UTC).isoformat(),
        "versao": datetime.now(UTC).strftime("%Y-%m-%d"),
    }


def publicar(fonte: Fonte, arquivo: Path, manifesto_: dict, bucket: str | None = None) -> str:
    """Sobe arquivo e manifesto para s3://<bucket>/bases/<fonte>/<versao>/ e devolve o prefixo. Idempotente por versão."""
    import boto3

    bucket = bucket or os.environ["MVR_BUCKET"]
    prefixo = f"bases/{fonte.id}/{manifesto_['versao']}/"
    s3 = boto3.client("s3")
    s3.upload_file(str(arquivo), bucket, prefixo + arquivo.name)
    s3.put_object(
        Bucket=bucket, Key=prefixo + "manifest.json", Body=json.dumps(manifesto_, ensure_ascii=False).encode()
    )
    log.info("publicado s3://%s/%s", bucket, prefixo)
    return prefixo


def ingerir(fonte_id: str, destino_dir: Path, url: str | None = None, bucket: str | None = None, **params: str) -> dict:
    """Uma fonte de ponta a ponta: baixa, calcula o manifesto e publica. Devolve o manifesto com o prefixo no S3."""
    fonte = FONTES[fonte_id]
    url_final = (url or fonte.url_padrao).format(**params)
    arquivo = destino_dir / fonte_id / Path(url_final).name
    baixar(fonte, arquivo, url=url, **params)
    m = manifesto(fonte, arquivo, url_final, params)
    m["s3_prefixo"] = publicar(fonte, arquivo, m, bucket)
    return m
