# Mapa Vivo de Risco

Cadastro vivo das famílias que moram dentro das áreas de risco de deslizamento e inundação, para a Defesa Civil
municipal: cruza os polígonos de risco do SGB/CPRM e do Cemaden com o Censo 2022 do IBGE e imagem de satélite,
detecta edificações por visão computacional, prioriza as visitas de campo e entrega o cadastro georreferenciado
para alerta e evacuação. O modelo diz onde olhar; o cadastro é humano.

Responde às metas 1.1.6 e 1.1.7 do Plano Nacional de Proteção e Defesa Civil 2025–2035 e ao dever municipal de
alerta da Lei 12.608/2012. Sistematização da disciplina Ecossistemas Digitais Inteligentes (Prof. Ricardo Neiva,
novembro de 2026); produto independente da carteira de Defesa Civil para prefeituras.

## Arquitetura (orientada a eventos, serviços em contêiner)

```
bases públicas (SGB, Cemaden, Censo 2022, imagem)
        │ ingestão            ┌──────────────┐
        ▼                     │  deteccao    │  segmentação de edificações por tile (GPU em lote)
┌──────────────┐  eventos     └──────┬───────┘
│  exposicao   │◄─────────────────────┘  edificações detectadas
│  (PostGIS)   │  setor × polígono × edificações → lista priorizada de visitas
└──────┬───────┘
       │ API (FastAPI)
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐
│ app de campo │     │   painel     │     │ central de alertas   │
│ (offline)    │     │  (Compdec)   │     │ (contatos por polígono)│
└──────────────┘     └──────────────┘     └──────────────────────┘
```

| pasta | serviço | estado |
|---|---|---|
| `servicos/ingestao` | baixa e versiona SGB, Cemaden, Censo 2022 (setores e CNEFE) e imagens | esqueleto |
| `servicos/exposicao` | cruzamento geométrico e estimativa por setor de risco (método BATER com Censo 2022) | esqueleto |
| `servicos/deteccao` | inferência de segmentação de edificações sobre tiles dentro dos polígonos | esqueleto |
| `servicos/api` | cadastro de famílias, lista de visitas, contatos por polígono | `GET /saude` |
| `app` | aplicativo de campo offline (Expo) | planejado |
| `painel` | painel da Compdec | planejado |
| `infra` | Docker Compose local (PostGIS + API), Terraform para AWS | esqueleto |

Documentos: [docs/plano-sistematizacao.md](docs/plano-sistematizacao.md), [docs/artigos-indice.md](docs/artigos-indice.md),
decisões em [docs/adr](docs/adr).

## Rodar local

```bash
docker compose -f infra/docker-compose.yml up --build
curl http://localhost:8000/saude
```
