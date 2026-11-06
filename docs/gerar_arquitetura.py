"""Gera docs/arquitetura.png com os ícones oficiais da AWS (pacote `diagrams`), sem Graphviz: layout fixo em Pillow.

Uso: python docs/gerar_arquitetura.py  (com `diagrams` e `pillow` instalados). O PNG vai para docs/arquitetura.png.
"""

from __future__ import annotations

import importlib.util
import math
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RES = Path(importlib.util.find_spec("diagrams").origin).parent.parent / "resources"
SAIDA = Path(__file__).with_name("arquitetura.png")
W, H = 2120, 1240
DX = 120  # deslocamento de tudo que fica à direita da coluna de bases e entrega
ICONE = 76
F = {}
for nome, tam in (("t", 32), ("g", 22), ("n", 18), ("p", 15)):
    for cand in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"):
        if Path(cand).exists():
            F[nome] = ImageFont.truetype(cand, tam)
            break
    else:
        F[nome] = ImageFont.load_default()

img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
LARANJA, CINZA, AZUL, VERDE, ROXO = "#FF9900", "#545B64", "#1F6FB2", "#2E7D32", "#6A1B9A"


def icone(cat, nome, x, y, rotulo, sub=None):
    im = Image.open(RES / cat / f"{nome}.png").convert("RGBA").resize((ICONE, ICONE))
    img.paste(im, (int(x - ICONE / 2), int(y - ICONE / 2)), im)
    d.text((x, y + ICONE / 2 + 6), rotulo, fill="black", font=F["n"], anchor="ma")
    if sub:
        for i, linha in enumerate(textwrap.wrap(sub, 26)):
            d.text((x, y + ICONE / 2 + 30 + i * 17), linha, fill=CINZA, font=F["p"], anchor="ma")


def caixa(x1, y1, x2, y2, titulo, cor, tracejada=False):
    if tracejada:
        for i in range(x1, x2, 14):
            d.line([(i, y1), (min(i + 8, x2), y1)], fill=cor, width=2)
            d.line([(i, y2), (min(i + 8, x2), y2)], fill=cor, width=2)
        for j in range(y1, y2, 14):
            d.line([(x1, j), (x1, min(j + 8, y2))], fill=cor, width=2)
            d.line([(x2, j), (x2, min(j + 8, y2))], fill=cor, width=2)
    else:
        d.rectangle([x1, y1, x2, y2], outline=cor, width=2)
    d.text((x1 + 12, y1 + 8), titulo, fill=cor, font=F["g"])


def seta(pontos, rotulo=None, cor=CINZA, pont=False, onde=0):
    """Polilinha com ponta de seta no fim; rótulo no meio do segmento `onde`."""
    for (x1, y1), (x2, y2) in zip(pontos, pontos[1:]):
        if pont:
            n = max(1, int(math.hypot(x2 - x1, y2 - y1) / 12))
            for i in range(0, n, 2):
                a = (x1 + (x2 - x1) * i / n, y1 + (y2 - y1) * i / n)
                b = (x1 + (x2 - x1) * (i + 1) / n, y1 + (y2 - y1) * (i + 1) / n)
                d.line([a, b], fill=cor, width=2)
        else:
            d.line([(x1, y1), (x2, y2)], fill=cor, width=2)
    (x1, y1), (x2, y2) = pontos[-2], pontos[-1]
    ang = math.atan2(y2 - y1, x2 - x1)
    pa = (x2 - 13 * math.cos(ang - 0.4), y2 - 13 * math.sin(ang - 0.4))
    pb = (x2 - 13 * math.cos(ang + 0.4), y2 - 13 * math.sin(ang + 0.4))
    d.polygon([(x2, y2), pa, pb], fill=cor)
    if rotulo:
        (ax, ay), (bx, by) = pontos[onde], pontos[onde + 1]
        mx, my = (ax + bx) / 2, (ay + by) / 2
        tw = d.textlength(rotulo, font=F["p"])
        d.rectangle([mx - tw / 2 - 5, my - 11, mx + tw / 2 + 5, my + 11], fill="white")
        d.text((mx, my), rotulo, fill=cor, font=F["p"], anchor="mm")


# título
d.text((W / 2, 26), "Mapa Vivo de Risco — arquitetura na AWS", fill="black", font=F["t"], anchor="ma")
d.text((W / 2, 68), "serviços em contêiner orientados a eventos · dados pessoais só no PostGIS · o modelo diz onde olhar, o cadastro é humano", fill=CINZA, font=F["n"], anchor="ma")

# colunas e linhas da grade
X1, X2, X3, X4 = 680, 960, 1240, 1520
Y1, Y2, Y3, Y4 = 260, 540, 820, 975

# bases públicas (esquerda, em cima), em duas colunas
caixa(40, 120, 460, 500, "Bases públicas", VERDE, tracejada=True)
icone("aws/general", "internet-alt1", 150, 210, "SGB/CPRM", "polígonos de risco")
icone("aws/general", "internet-alt1", 350, 210, "Cemaden", "municípios monitorados")
icone("aws/general", "internet-alt1", 150, 370, "IBGE, Censo 2022", "setores, CNEFE, agregados")
icone("aws/general", "internet-alt1", 350, 370, "Imagem de satélite", "ortofoto em tiles")

# orquestração fora da AWS
caixa(40, 525, 460, 705, "Orquestração", AZUL, tracejada=True)
icone("onprem/workflow", "airflow", 350, 610, "Airflow (VPS existente)", "DAG mvr_ingestao, mensal ou botão")

# entrega contínua (esquerda, embaixo)
caixa(40, 725, 460, 1120, "Entrega contínua", ROXO, tracejada=True)
icone("onprem/vcs", "github", 150, 810, "GitHub", "main, tags vX.Y.Z")
icone("onprem/ci", "github-actions", 350, 810, "Actions", "ci · deploy-dev · release")
icone("aws/security", "identity-and-access-management-iam-role", 150, 960, "Role OIDC", "uma por ambiente")
icone("aws/compute", "ec2-container-registry", 350, 960, "ECR", "tags imutáveis sha-7, vX.Y.Z")
d.text((250, 1060), "Terraform: dev no push da main;\nprod só por tag com aprovação", fill=ROXO, font=F["p"], anchor="ma", align="center")

# nuvem
caixa(500, 120, 1700, 1120, "AWS · us-east-1 · mesmo código, um tfvars por ambiente (dev, prod)", LARANJA)
caixa(530, 160, 1670, 1095, "VPC", AZUL, tracejada=True)

icone("aws/security", "identity-and-access-management-iam-role", X1, Y1, "Usuário IAM do Airflow", "só S3 bases/ e imagens/, Batch SubmitJob")
icone("aws/storage", "simple-storage-service-s3", X2, Y1, "S3 dados", "bases, imagens, Parquet, detecções")
icone("aws/integration", "eventbridge", X3, Y1, "EventBridge", "Object Created em imagens/")
icone("aws/compute", "ec2-spot-instance", X4, Y1, "Batch · detecção (GPU)", "EC2 Spot: segmentação por tile, U-Net")

icone("aws/compute", "batch", X1, Y2, "Batch · exposição", "SGB × Censo × detecções, lista de visitas")
icone("aws/database", "rds-postgresql-instance", X2, Y2, "RDS PostgreSQL + PostGIS", "sub-rede privada, criptografado, multi-AZ em prod")
icone("aws/security", "secrets-manager", X3, Y2, "Secrets Manager", "credencial do banco")
icone("aws/management", "cloudtrail", 1590, Y2, "CloudTrail", "auditoria de acesso")

icone("aws/network", "elb-application-load-balancer", X1, Y3, "ALB", "health check em /saude")
icone("aws/compute", "fargate", X2, Y3, "ECS Fargate · API", "FastAPI, autoescala, rollback automático")
icone("aws/management", "cloudwatch", X3, Y3, "CloudWatch", "logs e alarmes: 5xx, p95, tarefas saudáveis")
icone("aws/integration", "simple-notification-service-sns", X4, Y3, "SNS", "alertas por e-mail")

icone("aws/security", "identity-and-access-management-iam", 1415, Y2, "IAM", "role por tarefa")

# município (direita)
caixa(1740, 120, 2080, 1120, "Município", VERDE, tracejada=True)
icone("aws/general", "mobile-client", 1910, 260, "App de campo (offline)", "agentes e Nupdecs")
icone("aws/general", "client", 1910, 500, "Painel da Compdec", "cadastro vivo, visitas, indicador")
icone("aws/general", "users", 1910, 740, "Central de alertas", "contatos por polígono atingido")
icone("aws/general", "user", 1910, 980, "Famílias", "alerta nominal e rota de saída")

m = ICONE / 2 + 6
# fontes -> ingestão (linha horizontal em Y1 vem das três fontes por um tronco vertical em x=400)
seta([(350, 500), (350, 610 - m)], "baixa")
seta([(410, 610), (520, 610), (520, Y1), (X1 - m, Y1)], "versiona", onde=0)
# ingestão -> S3 -> EventBridge -> Batch GPU
seta([(X1 + m, Y1), (X2 - m, Y1)])
seta([(X1 - 30, Y1 + 72), (X1 - 30, Y2 - m)], "submete a exposição", onde=0)
seta([(X2 + m, Y1), (X3 - m, Y1)], "evento")
seta([(X3 + m, Y1), (X4 - m, Y1)], "submete job")
# detecções voltam ao S3 (por baixo)
seta([(X4, Y1 + 72), (X4, Y1 + 130), (X2 + 40, Y1 + 130), (X2 + 40, Y1 + 72)], "detecções em S3", pont=True, onde=1)
# S3 -> exposição (L) e exposição -> RDS
seta([(X2 - 40, Y1 + 72), (X2 - 40, Y1 + 150), (X1 + 60, Y1 + 150), (X1 + 60, Y2 - m)], "lê bases e detecções", onde=1)
seta([(X1 + m, Y2), (X2 - m, Y2)], "grava exposição")
# segredo -> RDS/API
seta([(X3 - m, Y2), (X2 + m, Y2)], "credencial", pont=True)
# API <-> RDS, ALB -> API, API -> CloudWatch -> SNS
seta([(X2, Y3 - m), (X2, Y2 + 72)], "SQL")
seta([(X1 + m, Y3), (X2 - m, Y3)])
seta([(X2 + m, Y3), (X3 - m, Y3)], "logs e métricas", pont=True)
seta([(X3 + m, Y3), (X4 - m, Y3)], "alarme")
# município -> ALB (tronco vertical em x=1600 e entrada por baixo do ALB)
seta([(1860, 260), (1720, 260), (1720, 1000), (X1, 1000), (X1, Y3 + 72)], "sincroniza o cadastro", onde=2)
seta([(1860, 500), (1720, 500)])
# API -> central de alertas -> famílias
seta([(X2, Y3 + 72), (X2, 950), (1680, 950), (1680, 740), (1860, 740)], "contatos por polígono atingido", onde=1)
seta([(1910, 790), (1910, 930)], "alerta nominal")
# CI/CD -> ECR -> serviços
seta([(390, 960), (480, 960), (480, 1080), (X2, 1080), (X2, Y3 + 110)], "imagem por tag", cor=ROXO, pont=True, onde=2)
seta([(480, 1080), (1655, 1080), (1655, Y1 + 160), (X4, Y1 + 160), (X4, Y1 + 72)], cor=ROXO, pont=True)

img.save(SAIDA, optimize=True)
print(SAIDA, img.size)
