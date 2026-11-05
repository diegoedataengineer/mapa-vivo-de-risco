# Índice dos artigos levantados — Mapa Vivo de Risco

Quatro buscas em 05/11/2026, 48 referências verificadas na página da base ou no Crossref, nenhum DOI deduzido.
Arquivos com as fichas completas (referência, base, PDF aberto, resumo, relação com a solução):

| arquivo | recorte | fichas |
|---|---|---|
| `artigos-candidatos.md` | detecção de edificações por deep learning, exposição, suscetibilidade | 10 |
| `artigos-exposicao-e-campo.md` | população exposta, Censo × polígonos de risco, dasimetria, coleta de campo | 13 |
| `artigos-alerta-e-defesa-civil.md` | alerta antecipado, última milha, capacidade municipal, Nupdecs, LGPD | 14 |
| `artigos-mlops-e-arquitetura.md` | MLOps, arquitetura, CI/CD, confiabilidade, governança | 15 |

## O artigo da Parte 1 (anexar e fundamentar)

Escolher **um** entre estes três. Os dois primeiros são de equipes do Cemaden e do IBGE, em SciELO ou periódico do
IBGE, PDF aberto e em português; o terceiro é o estado da arte com o Censo 2022.

1. **Saito et al. (2019)** — *Urban population exposed to risks of landslides, floods and flash floods in Brazil*.
   Sociedade & Natureza, v. 31. DOI 10.14393/SN-v31-2019-46320. SciELO, CC BY, PT e EN.
   Cruza o Censo 2010 com os setores de risco do SGB/CPRM (BATER) em 479 municípios e declara a lacuna intraurbana
   que o sistema fecha com Censo 2022 e visão computacional. **Recomendado**: base reconhecida, aberto, tema exato.
2. **Souza et al. (2019)** — *Utilização de dados censitários para a análise de população em áreas de risco*. Revista
   Brasileira de Geografia (IBGE). DOI 10.21579/issn.2526-0375_2019_n1_122-135. Metodologia da BATER; citar junto
   do relatório oficial IBGE & Cemaden (2018), *População em áreas de risco no Brasil* (8,27 mi de pessoas, 2,47 mi de
   domicílios, 872 municípios).
3. **Araújo & Leitão (2024)** — *Database of areas of interest for characterizing the population vulnerable to
   hydrogeomorphological processes in Brazil*. Research, Society and Development, v. 13, n. 6. DOI 10.33448/rsd-v13i6.46213.
   Autores do IBGE cruzam a setorização do SGB com a malha urbana e o CNEFE do Censo 2022: 12.726 áreas, 1,55 mi de
   endereços, 3,85 mi de pessoas em risco. Base menos reconhecida que a SciELO, mas é o par de dados exato do sistema.

Achado que vale uma frase na justificativa: nenhuma das buscas encontrou artigo revisado por pares que atualize a
BATER nacional para o Censo 2022 nem que avalie sistematicamente a setorização do SGB nos municípios.

## Referências de apoio por seção

**Parte 1, problema e justificativa (última milha e capacidade municipal)**
- Marengo et al. (2024), Natural Hazards 120(8): São Sebastião 2023, alerta emitido com antecedência e resposta
  comunitária mínima, sem plano de contingência. DOI 10.1007/s11069-024-06558-5.
- Marengo et al. (2025), IJDRR 126: o Cemaden nas enchentes do RS de 2024. DOI 10.1016/j.ijdrr.2025.105645.
- Alcântara et al. (2023), NHESS: Petrópolis 2022.
- Cotting et al. (2025), Revista Brasileira de Geografia 70(2): capacidades de gestão de risco nos 267 municípios
  prioritários, 13 % sem órgão de defesa civil, mapeamento de deslizamento em só 45 %. DOI 10.21579/issn.2526-0375_2025_n2_346-367.
- Zandomenico & Martin (2022), Saúde e Sociedade: percepção de risco, medo da remoção maior que medo do deslizamento.
  Entra como risco do produto: o cadastro não pode ser lido como lista de remoção.
- Marchezini et al. (2018), Frontiers in Earth Science 6:184: alerta participativo, "primeira milha" e "última milha".
  DOI 10.3389/feart.2018.00184. Referencial para cadastro + Nupdecs como coautores do alerta.

**Parte 2.2, integração de ML (detecção de edificações e desagregação)**
- Schuegraf et al. (2024), IGARSS, IEEE Xplore: segmentação de instâncias de edificações em assentamentos formais e
  informais (Medellín) para estimar população exposta a deslizamento. DOI 10.1109/IGARSS53475.2024.10642589.
- da Silva, Rodrigues-Jr & de Albuquerque (2025), Computers, Environment and Urban Systems 121: CNN detecta
  assentamentos precários em seis cidades brasileiras; F1 cai de 0,90 para menos de 0,80 fora da cidade de treino,
  o que justifica treinar com várias cidades e monitorar drift por município. DOI 10.1016/j.compenvurbsys.2025.102306.
- Firoze, Yeh & Aliaga (2026), AAAI: SAM2 com grafos para assentamentos densos, teste em Belo Horizonte.
- Garcia, Oliveira & Zêzere (2016), NHESS 16: dasimetria com footprints de edificações; setor censitário superestima
  expostos. DOI 10.5194/nhess-16-2769-2016.
- Gevaert et al. (2024), IEEE JSTARS: vieses de Open Buildings, OSM e Microsoft footprints. Herfort et al. (2023),
  Nature Communications: completude do OSM. Ambos sustentam não confiar em footprint pronto para área de risco.
- Xavier & Barella (2024), Revista Brasileira de Geomorfologia: suscetibilidade a deslizamento com regressão
  logística, random forest e redes neurais em Mariana (MG), para a camada de prioridade.

**Parte 2.1, 2.3 e 2.4, arquitetura, nuvem e CI/CD**
- Kreuzberger, Kühl & Hirschl (2023), IEEE Access 11: arquitetura de referência de MLOps, nove princípios, papéis.
  DOI 10.1109/ACCESS.2023.3262138. Molde para o diagrama do pipeline de ML.
- Amershi et al. (2019), ICSE: engenharia de software para ML, estudo de caso Microsoft.
- Shahin, Babar & Zhu (2017), IEEE Access: revisão de integração, entrega e implantação contínuas.
- Lewis et al. (2021), SEI: padrões de arquitetura para sistemas com ML.
- Paleyes, Urma & Lawrence (2022) e TorchGeo (2022): desafios de implantar ML e deep learning geoespacial em
  produção, inferência em lote sobre tiles.

**Parte 2.5, qualidade, confiabilidade e governança**
- Sculley et al. (2015), NeurIPS: dívida técnica oculta em sistemas de ML. Breck et al. (2017): ML Test Score.
- Basiri et al. (2016), IEEE Software: chaos engineering (casa com a webaula 03).
- Lu et al. (2019): detecção de drift. Abraham, Schneider & vom Brocke (2019): governança de dados, ao lado do
  DAMA-DMBOK.
- Lui et al. (2025), Revista de Sociologia e Política (SciELO): LGPD nas 27 capitais, governança fragmentada.
  DOI 10.1590/1678-98732433e008. Cristóvam & Hahn (2020), Revista Brasileira de Direito: LGPD no setor público.
- Ribeiro et al. (2020), RBRH: app Hidromapp offline para risco hidrológico, precedente de app de campo.
- Salvati et al. (2021), IJDRR: coleta de campo por edificação com ODK.

## Links diretos (página da base e PDF aberto)

Finalistas da Parte 1
- Saito et al. (2019): https://www.scielo.br/j/sn/a/nsTDtH7Nc8pdHV6H3xhdJCR/ (SciELO) · https://seer.ufu.br/index.php/sociedadenatureza/article/view/46320
- Souza et al. (2019): https://rbg.ibge.gov.br/index.php/rbg/article/view/2061 · relatório IBGE & Cemaden (2018): https://biblioteca.ibge.gov.br/visualizacao/livros/liv101589.pdf
- Araújo & Leitão (2024): https://rsdjournal.org/rsd/article/view/46213

Problema e justificativa
- Marengo et al. (2024), São Sebastião: https://doi.org/10.1007/s11069-024-06558-5 · PDF: https://repositorio.unesp.br/entities/publication/05b97acb-b508-43d5-b77e-52b7d71c1fe0/full
- Marengo et al. (2025), RS 2024: https://doi.org/10.1016/j.ijdrr.2025.105645 · https://bv.fapesp.br/en/publicacao/281073
- Alcântara et al. (2023), Petrópolis: https://nhess.copernicus.org/articles/23/1157/2023/
- Cotting et al. (2025), capacidade municipal: https://rbg.ibge.gov.br/index.php/rbg/article/view/4744
- Marchezini et al. (2018), alerta participativo: https://www.frontiersin.org/articles/10.3389/feart.2018.00184/full
- Zandomenico & Martin (2022), percepção de risco: https://www.scielo.br/scielo.php?script=sci_arttext&pid=S0104-12902022000400317&tlng=pt

Machine learning e exposição
- Schuegraf et al. (2024), IGARSS: https://doi.org/10.1109/IGARSS53475.2024.10642589 · PDF: https://elib.dlr.de/206759/1/IGARSS_2024_Medellin.pdf
- da Silva et al. (2025), CNN em cidades brasileiras: https://doi.org/10.1016/j.compenvurbsys.2025.102306 · https://eprints.gla.ac.uk/354795/
- Firoze, Yeh & Aliaga (2026), AAAI: https://ojs.aaai.org/index.php/AAAI/article/view/41187
- Garcia, Oliveira & Zêzere (2016), dasimetria: https://nhess.copernicus.org/articles/16/2769/2016/
- Gevaert et al. (2024), vieses de footprints: https://research.utwente.nl/en/publications/auditing-geospatial-datasets-for-biases-using-global-building-dat-2/
- Herfort et al. (2023), completude do OSM: https://eprints.gla.ac.uk/302440
- Xavier & Barella (2024), suscetibilidade em Mariana: https://rbgeomorfologia.org.br/rbg/article/view/2584
- Dias et al. (2017), Blumenau: https://seer.ufu.br/index.php/revistabrasileiracartografia/article/view/44040

Arquitetura, CI/CD, MLOps
- Kreuzberger et al. (2023), MLOps: https://ieeexplore.ieee.org/document/10081336
- Amershi et al. (2019), ICSE: https://ieeexplore.ieee.org/document/8804457
- Shahin et al. (2017), CI/CD: https://ieeexplore.ieee.org/document/7884954
- Sculley et al. (2015), dívida técnica em ML: https://proceedings.neurips.cc/paper/2015/hash/86df7dcfd896fcaf2674f757a2463eba-Abstract.html
- Breck et al. (2017), ML Test Score: https://ieeexplore.ieee.org/document/8258038
- Paleyes et al. (2022), desafios de implantação: https://dl.acm.org/doi/10.1145/3533378
- TorchGeo (2022): https://dl.acm.org/doi/10.1145/3557915.3560953
- Basiri et al. (2016), chaos engineering: https://ieeexplore.ieee.org/document/7436642
- Lu et al. (2019), drift: https://ieeexplore.ieee.org/document/8496795

Governança e LGPD
- Lui et al. (2025), LGPD nas capitais: https://www.scielo.br/j/rsocp/a/BGDJY9FTnv6H8PKffpb3JjG/?lang=pt
- Cristóvam & Hahn (2020), LGPD no setor público: https://dialnet.unirioja.es/servlet/articulo?codigo=8075713
- Abraham et al. (2019), governança de dados: https://www.sciencedirect.com/science/article/pii/S0268401219300787
- Ribeiro et al. (2020), app Hidromapp: https://www.scielo.br/j/rbrh/a/WwgvfxjPLnQK8rk4zcQbjgh/?lang=en

## Lacunas declaradas pelas quatro buscas

Sem artigo revisado por pares sobre SMS 40199 ou cell broadcast no Brasil; sobre ODK, KoBo ou QField em defesas
civis brasileiras; sobre arquitetura orientada a eventos para dados geoespaciais; e com custo quantificado de GPU em
lote versus tempo real. Onde faltar artigo, usar relatório oficial (Cemaden, IBGE, SGB) e dizer que é relatório.
