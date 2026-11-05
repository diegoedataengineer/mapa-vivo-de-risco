# ADR-0001 — Tema, escopo e o que o ML decide

Data: 05/11/2026 · Status: aceita

## Contexto
A sistematização pede uma solução com IA/ML cobrindo arquitetura, nuvem e contêineres, CI/CD, qualidade e confiabilidade
e governança de dados, sem exigir implementação. O Radar Licitações foi descartado por ser sistema interno da empresa.
Só 121 municípios têm a população em área de risco quantificada (PN-PDC, meta 1.1.6); a estimativa nacional usa o
Censo 2010 e o setor censitário (IBGE; Cemaden, 2018; Saito et al., 2019).

## Decisão
- Produto: cadastro vivo de famílias em área de risco para a Defesa Civil municipal, com app de campo offline.
- ML: segmentação de edificações em imagem dentro dos polígonos de risco. A saída é lista priorizada de vistoria;
  nenhum registro de família nasce sem visita. O grau de risco do SGB entra na priorização.
- Dados: SGB/CPRM, Cemaden, Censo 2022 (setores e CNEFE), imagem de satélite ou ortofoto; método da BATER como ponto
  de partida.
- Arquitetura: serviços independentes em contêiner, comunicando por eventos; PostGIS como base geoespacial.
- Independente dos demais sistemas da carteira de Defesa Civil (integração por API, nunca banco compartilhado).

## Consequências
- O protótipo prioriza o pipeline de exposição com dados reais de um município-exemplo, que dá os números do vídeo.
- Detecção de imagem começa com modelo pré-treinado aberto; treino próprio só com rótulos de campo.
- LGPD: município é controlador, o sistema é operador; dado agregado para o indicador nacional sem dado pessoal.
