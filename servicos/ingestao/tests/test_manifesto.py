from pathlib import Path

from mvr_ingestao import manifesto
from mvr_ingestao.fontes import FONTES


def test_manifesto_tem_sha_e_versao(tmp_path: Path):
    arq = tmp_path / "x.zip"
    arq.write_bytes(b"abc")
    m = manifesto(FONTES["ibge_setores_2022"], arq, "https://exemplo/x.zip", {"uf": "RJ"})
    assert m["sha256"] == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert m["fonte"] == "ibge_setores_2022" and m["parametros"] == {"uf": "RJ"} and len(m["versao"]) == 10


def test_todas_as_fontes_tem_origem_e_periodicidade():
    for f in FONTES.values():
        assert f.origem and f.periodicidade and f.por in ("nacional", "uf", "municipio")
