"""Catálogo das bases públicas que o Mapa Vivo de Risco ingere, com origem, periodicidade e como versionar.

Cada fonte vira um prefixo no S3: bases/<fonte>/<data-da-ingestão>/<arquivo> + manifest.json (origem, data, sha256,
tamanho). A versão da base entra na linhagem de toda exposição calculada a partir dela (governança: catálogo e linhagem).
As URLs são padrões conhecidos dos portais; o Airflow pode sobrescrevê-las por Variable quando o portal mudar.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Fonte:
    id: str
    nome: str
    origem: str
    url_padrao: str  # pode ter {uf} ou {municipio_ibge}
    periodicidade: str
    formato: str
    por: str  # "nacional" | "uf" | "municipio"


FONTES: dict[str, Fonte] = {
    "sgb_setorizacao": Fonte(
        id="sgb_setorizacao",
        nome="Setorização de áreas de risco geológico e hidrológico",
        origem="Serviço Geológico do Brasil (SGB/CPRM), GeoSGB",
        url_padrao="https://geosgb.sgb.gov.br/geosgb/downloads.html#setorizacao",
        periodicidade="trimestral",
        formato="shapefile/geopackage por município",
        por="municipio",
    ),
    "cemaden_municipios": Fonte(
        id="cemaden_municipios",
        nome="Municípios monitorados pelo Cemaden",
        origem="Cemaden/MCTI",
        url_padrao="https://www.gov.br/cemaden/pt-br/assuntos/monitoramento/municipios-monitorados",
        periodicidade="mensal",
        formato="csv",
        por="nacional",
    ),
    "ibge_setores_2022": Fonte(
        id="ibge_setores_2022",
        nome="Malha de setores censitários do Censo 2022",
        origem="IBGE, geoftp",
        url_padrao="https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_de_setores_censitarios__divisoes_intramunicipais/censo_2022/setores/shp/UF/{uf}/{uf}_setores_CD2022.zip",
        periodicidade="anual",
        formato="shapefile por UF",
        por="uf",
    ),
    "ibge_cnefe_2022": Fonte(
        id="ibge_cnefe_2022",
        nome="Cadastro Nacional de Endereços para Fins Estatísticos, Censo 2022",
        origem="IBGE, ftp",
        url_padrao="https://ftp.ibge.gov.br/Cadastro_Nacional_de_Enderecos_para_Fins_Estatisticos/Censo_Demografico_2022/Arquivos_CNEFE/CSV/UF/{uf}.zip",
        periodicidade="anual",
        formato="csv por UF",
        por="uf",
    ),
    "ibge_agregados_setores_2022": Fonte(
        id="ibge_agregados_setores_2022",
        nome="Agregados por setor censitário do Censo 2022 (domicílios e moradores)",
        origem="IBGE",
        url_padrao="https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/",
        periodicidade="anual",
        formato="csv nacional",
        por="nacional",
    ),
    "imagem": Fonte(
        id="imagem",
        nome="Imagem de satélite ou ortofoto do município",
        origem="provedor contratado pelo município ou base aberta (ex.: ortofotos estaduais)",
        url_padrao="s3://{bucket}/imagens/{municipio_ibge}/",
        periodicidade="sob demanda",
        formato="GeoTIFF em tiles",
        por="municipio",
    ),
}
