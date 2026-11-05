# Plano da sistematização — Ecossistemas Digitais Inteligentes

Prazo: domingo, 15/11/2026, 23:55 (Moodle, tentativa única). Prof. Ricardo Neiva.
Tema escolhido em 05/11/2026: **Famílias em área de risco**, produto da carteira de Defesa Civil para prefeituras
(não é sistema interno da empresa). Nome de trabalho: **Mapa Vivo de Risco**.

## O problema em uma frase

Só 121 dos 5.570 municípios sabem quantas pessoas moram em área de risco de desastre; o PN-PDC 2025–2035 quer 1.210
até 2035 (meta 1.1.6) e o cruzamento do Censo com as áreas monitoradas pelo Cemaden em 2.240 municípios (meta 1.1.7).
A Defesa Civil municipal não tem cadastro de famílias por setor de risco, então o alerta e a evacuação vão às cegas
(Petrópolis 2022, RS 2024).

## A solução em uma frase

Sistema web e app que cruza os polígonos de risco do SGB/CPRM e do Cemaden com os setores censitários do Censo 2022
e com imagem de satélite ou ortofoto, usa visão computacional para detectar edificações dentro dos polígonos, estima
moradias e população expostas por setor, gera a lista priorizada de visitas de campo para o agente cadastrar as famílias
(app offline) e entrega à Compdec o cadastro georreferenciado com pessoas com mobilidade reduzida, para alerta e evacuação.

## Como o tema cobre as seis temáticas do enunciado

| temática | decisão a defender | webaula |
|---|---|---|
| Arquitetura | serviços em contêiner orientados a eventos: ingestão de bases públicas, inferência de imagem, API do cadastro, app de campo, painel; fila de eventos entre eles | 01, 03 |
| Nuvem e contêineres | AWS (S3 para imagens e Parquet, ECS Fargate para serviços, Batch/GPU sob demanda para inferência), Postgres com PostGIS gerenciado, Docker em tudo | 02, 03 |
| DevOps e CI/CD | GitHub Actions: lint, testes, build de imagem por SHA, scan, deploy por ambiente com Terraform; versionamento do modelo junto do código | 04, 05 |
| Qualidade e confiabilidade | app offline-first, filas com retry, inferência idempotente por tile, SLO de disponibilidade da API de alerta, monitoramento e alarmes | 06 |
| Governança de dados | LGPD (dados de famílias e crianças), base legal de política pública, RLS por município, trilha de auditoria, qualidade das bases públicas (versão do polígono, data da imagem), catálogo e linhagem | 07 |
| Machine Learning | segmentação de edificações (U-Net ou modelo de fundação ajustado) sobre tiles; métricas IoU/F1 por município; saída vai para vistoria humana, nunca para cadastro automático; monitoramento de drift por imagem nova e retreino com rótulos de campo | 08 |

Argumento central: o ML reduz o custo de descobrir onde estão as famílias, mas o cadastro é humano; a arquitetura
existe para fechar o ciclo entre imagem, campo e alerta.

Vocabulário das webaulas a usar na Parte 2 (para o avaliador reconhecer a disciplina): arquitetura orientada a
eventos e arquitetura evolutiva, trade-offs arquiteturais, observabilidade e rastreabilidade, resiliência e chaos
engineering (01, 03); pipeline de deploy, Terraform, versionamento por serviço (03, 04); GCS: itens de configuração,
nomeação e versionamento, auditoria da configuração, plano de GCS (05); QA, QC e V&V (06); governança versus gestão de
dados, pilares, papéis, catálogo e linhagem, maturidade, LGPD (07); pipeline de ML: features, treino, validação,
deploy, tipos de aprendizagem (08).

## Entregáveis e orçamento de páginas

1. **Artigo científico** (PDF anexado) — candidatos em `artigos-candidatos.md`; escolher um até 06/11.
2. **Parte 1 — Pesquisa e definição (20 pts, 2–3 páginas)**: problema e contexto · justificativa e benefícios ·
   objetivo · público (Compdec, agentes de campo, famílias, Sedec como leitora do indicador) · funcionalidades ·
   fundamentação (artigo: objetivos, contribuições, relação).
3. **Parte 2 — Arquitetura e planejamento técnico (40 pts, 4–6 páginas)**: 2.1 diagrama e estilo arquitetural ·
   2.2 integração do ML (problema, técnica, dados, integração) · 2.3 nuvem e contêineres · 2.4 fluxo de CI/CD
   (diagrama) · 2.5 qualidade, confiabilidade e governança.
4. **Parte 3 — Vídeo (40 pts, ≤ 8 min, apresentado por você)**: roteiro com um bloco por item do enunciado;
   link do Google Drive com visualização aberta dentro do documento da Parte 2.

## Roteiro do vídeo (8 minutos)

| min | bloco | o que mostrar |
|---|---|---|
| 0:00–1:00 | contexto e justificativa | número de municípios sem cadastro, meta 1.1.6, caso RS 2024 |
| 1:00–2:00 | funcionalidades e benefícios | fluxo imagem → lista de visitas → cadastro → alerta |
| 2:00–3:30 | diagrama arquitetural | componentes e comunicação por eventos |
| 3:30–4:45 | integração de ML | tiles, segmentação, métricas, revisão humana, drift |
| 4:45–6:00 | nuvem e CI/CD | serviços AWS escolhidos, pipeline do GitHub ao deploy |
| 6:00–7:30 | desafios, riscos, limitações, evolução | falso positivo da imagem, LGPD, conectividade, custo de GPU; evolução para sirenes e Nupdecs |
| 7:30–8:00 | fechamento | o que o sistema entrega ao indicador do PN-PDC |

## Calendário

- 05–06/11: escolher o artigo; escrever a Parte 1.
- 07–09/11: diagramas (arquitetura, CI/CD, pipeline de ML); escrever a Parte 2.
- 10–11/11: roteiro final, slides, gravação.
- 12/11: revisão, link do Drive no documento, envio com três dias de folga.

## Fontes já levantadas (reaproveitar)

- PN-PDC 2025–2035: metas 1.1.6 (121 → 1.210), 1.1.7 (1.100 → 2.240), 2.2.4 (Cemaden 1.133 → 2.500); 1.942 municípios
  prioritários (Casa Civil, NT 1/2023 e 1/2025); Lei 12.608/2012 art. 8 V-B (alerta por sirene e celular, Lei 14.750/2023).
- TCU Acórdão 1781/2026: Sinpdec fragmentado, municípios sem pessoal e plano, indicadores administrativos.
- RS 2024: 11,2 % da população cadastrada no SMS; estações de monitoramento fora do ar um ano depois.
- Notas completas em `../../nupdec-conecta/research_notes/Metas de desastres EUA e Brasil/brasil_pnpdc_e_nupdecs.md`.
