# Publicação da DAG de ingestão no Airflow existente (VPS da empresa, Airflow 3): copia a DAG e o pacote mvr_ingestao.
AIRFLOW_VPS   ?= root@212.85.2.140
AIRFLOW_CHAVE ?= ~/.ssh/id_ed25519_hostinger_vps

airflow-publicar:
	rsync -az -e "ssh -i $(AIRFLOW_CHAVE) -o IdentitiesOnly=yes" infra/airflow/dags/mvr_ingestao.py $(AIRFLOW_VPS):/opt/airflow/dags/
	rsync -az --delete -e "ssh -i $(AIRFLOW_CHAVE) -o IdentitiesOnly=yes" --exclude __pycache__ servicos/ingestao/mvr_ingestao/ $(AIRFLOW_VPS):/opt/airflow/src/mvr_ingestao/
	@echo "DAG mvr_ingestao publicada; configure a conexão aws_mvr e as Variables mvr_* (ver infra/airflow/dags/mvr_ingestao.py)"

ingestao-testes:
	cd servicos/ingestao && ruff check . && pytest -q
