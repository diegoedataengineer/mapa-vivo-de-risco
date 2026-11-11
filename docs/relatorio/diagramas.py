"""Gera os diagramas SVG da Parte 2 e monta parte2.render.html (os marcadores <!--svg:nome--> viram SVG embutido).

Uso: python3 diagramas.py   (depois: node pdf.mjs)
SVG embutido no HTML herda a fonte IBM Plex da página; como <img>, não herdaria.
"""

from pathlib import Path

DIR = Path(__file__).parent
TINTA, QUIETO, LINHA, FUNDO = "#0f172a", "#475569", "#94a3b8", "#f8fafc"
ACENTO, ACENTO_FUNDO = "#1e4e8c", "#e8eef7"
VERDE, VERMELHO = "#15803d", "#b91c1c"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg(w, h, corpo, rotulo):
    defs = (
        "<defs>"
        f"<marker id='seta' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='7' markerHeight='7' orient='auto-start-reverse'><path d='M0 0L10 5L0 10z' fill='{LINHA}'/></marker>"
        f"<marker id='seta-v' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='7' markerHeight='7' orient='auto-start-reverse'><path d='M0 0L10 5L0 10z' fill='{VERMELHO}'/></marker>"
        f"<marker id='seta-a' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='7' markerHeight='7' orient='auto-start-reverse'><path d='M0 0L10 5L0 10z' fill='{ACENTO}'/></marker>"
        "</defs>"
    )
    return (
        f"<svg viewBox='0 0 {w} {h}' width='100%' role='img' aria-label='{esc(rotulo)}' "
        f"style='font-family:\"IBM Plex Sans\",sans-serif'>{defs}{corpo}</svg>"
    )


def texto(x, y, s, tam=10.5, peso=400, cor=QUIETO, anc="start"):
    return f"<text x='{x}' y='{y}' font-size='{tam}' font-weight='{peso}' fill='{cor}' text-anchor='{anc}'>{esc(s)}</text>"


def caixa(x, y, w, h, titulo, linhas, num=None, acento=False, sub=None):
    borda, fundo = (ACENTO, ACENTO_FUNDO) if acento else ("#cbd5e1", "#ffffff")
    out = [f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='7' fill='{fundo}' stroke='{borda}' stroke-width='{1.6 if acento else 1.1}'/>"]
    tx = x + 12
    if num is not None:
        out.append(f"<circle cx='{x + 20}' cy='{y + 19}' r='10' fill='{ACENTO}'/>")
        out.append(texto(x + 20, y + 23, str(num), 11, 700, "#ffffff", "middle"))
        tx = x + 38
    out.append(texto(tx, y + 23, titulo, 12, 600, TINTA))
    yy = y + 23
    if sub:
        yy += 15
        out.append(texto(tx, yy, sub, 10, 500, ACENTO))
    for ln in linhas:
        yy += 14.5
        out.append(texto(x + 12, yy, ln))
    return "".join(out)


def seta(d, cor="n"):
    c = {"n": LINHA, "v": VERMELHO, "a": ACENTO}[cor]
    m = {"n": "seta", "v": "seta-v", "a": "seta-a"}[cor]
    tr = " stroke-dasharray='4 3'" if cor == "v" else ""
    return f"<path d='{d}' fill='none' stroke='{c}' stroke-width='1.3'{tr} marker-end='url(#{m})'/>"


# ---------------------------------------------------------------- fluxo (2.1)
def fluxo():
    W, bw, bh, g = 760, 228, 104, 28
    xs = [12, 12 + bw + g, 12 + 2 * (bw + g)]
    y1, y2 = 40, 40 + bh + 44
    p = [texto(12, 22, "Do dado público ao alerta, em seis passos", 13.5, 700, TINTA)]
    p.append(caixa(xs[0], y1, bw, bh, "Ingestão", ["Airflow baixa SGB, Cemaden, Censo", "2022 e a imagem; grava manifesto", "com sha256 e versão em S3 bases/"], 1, sub="DAG mvr_ingestao · mensal"))
    p.append(caixa(xs[1], y1, bw, bh, "Evento de imagem nova", ["Objeto criado em S3 imagens/", "dispara uma regra que submete", "o job de detecção no Batch"], 2, sub="EventBridge"))
    p.append(caixa(xs[2], y1, bw, bh, "Detecção de edificações", ["U-Net segmenta cada tile dentro", "dos polígonos; grava pegadas", "com a versão do modelo"], 3, sub="Batch · EC2 Spot com GPU"))
    p.append(caixa(xs[2], y2, bw, bh, "Exposição e prioridade", ["Cruza polígono × Censo 2022 ×", "detecções; estima pessoas e gera", "a lista priorizada de visitas"], 4, sub="Batch · Fargate Spot (CPU)"))
    p.append(caixa(xs[1], y2, bw, bh, "Visita de campo", ["Agente recebe a lista no app", "offline, cadastra a família e", "sincroniza quando há rede"], 5, acento=True, sub="App Expo → API (ECS Fargate)"))
    p.append(caixa(xs[0], y2, bw, bh, "Alerta e painel", ["API entrega os contatos por", "polígono atingido; painel mostra", "cobertura e o indicador 1.1.6"], 6, sub="API → central de alertas"))
    # setas do fluxo
    my1, my2 = y1 + bh / 2, y2 + bh / 2
    p.append(seta(f"M{xs[0] + bw} {my1} L{xs[1] - 2} {my1}"))
    p.append(seta(f"M{xs[1] + bw} {my1} L{xs[2] - 2} {my1}"))
    p.append(seta(f"M{xs[2] + bw / 2} {y1 + bh} L{xs[2] + bw / 2} {y2 - 2}"))
    p.append(seta(f"M{xs[2]} {my2} L{xs[1] + bw + 2} {my2}"))
    p.append(seta(f"M{xs[1]} {my2} L{xs[0] + bw + 2} {my2}"))
    p.append(texto(xs[2] + bw / 2 - 8, y1 + bh + 26, "Airflow submete ao fim da ingestão", 9.5, anc="end"))
    # banco
    yb = y2 + bh + 34
    p.append(f"<rect x='12' y='{yb}' width='{W - 24}' height='46' rx='7' fill='{FUNDO}' stroke='#cbd5e1' stroke-width='1.1'/>")
    p.append(texto(24, yb + 19, "Aurora Serverless v2 + PostGIS", 12, 600, TINTA))
    p.append(texto(24, yb + 35, "geometrias, detecções, lista de visitas e cadastro · único lugar com dado pessoal · sub-rede privada, criptografado", 10))
    for cx in (xs[0] + bw / 2, xs[1] + bw / 2, xs[2] + bw / 2):
        p.append(f"<path d='M{cx} {y2 + bh} L{cx} {yb}' stroke='{LINHA}' stroke-width='1.1' stroke-dasharray='3 3'/>")
    p.append(texto(W - 12, y2 + bh + 22, "tracejado: leitura e gravação no banco", 9.5, anc="end"))
    return svg(W, yb + 58, "".join(p), "Do dado público ao alerta, em seis passos")


# ---------------------------------------------------------------- nuvem (2.3)
def nuvem():
    W = 760
    p = [texto(12, 22, "Onde cada parte roda na AWS, e por quê", 13.5, 700, TINTA)]

    def grupo(x, y, w, h, nome):
        return (f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='9' fill='{FUNDO}' stroke='#cbd5e1' stroke-dasharray='5 3'/>"
                + texto(x + 12, y + 20, nome, 11, 700, ACENTO))

    gw, gh = 362, 214
    gx = [12, 12 + gw + 12]
    gy = [36, 36 + gh + 14]
    iw, ih = gw - 24, 52

    def item(x, y, servico, papel, porque):
        return (f"<rect x='{x}' y='{y}' width='{iw}' height='{ih}' rx='6' fill='#ffffff' stroke='#cbd5e1'/>"
                + texto(x + 10, y + 18, servico, 11.5, 600, TINTA)
                + texto(x + iw - 10, y + 18, papel, 10, 500, ACENTO, "end")
                + texto(x + 10, y + 37, porque, 10))

    p.append(grupo(gx[0], gy[0], gw, gh, "EXECUÇÃO"))
    p.append(item(gx[0] + 12, gy[0] + 32, "ECS Fargate (ARM) + ALB", "API do cadastro", "contêiner sem servidor; autoescala por CPU; health check"))
    p.append(item(gx[0] + 12, gy[0] + 32 + ih + 8, "AWS Batch · EC2 Spot com GPU", "detecção", "paga só os minutos de inferência; retentativa na fila"))
    p.append(item(gx[0] + 12, gy[0] + 32 + 2 * (ih + 8), "AWS Batch · Fargate Spot", "exposição", "um job por município, em paralelo, sem máquina parada"))

    p.append(grupo(gx[1], gy[0], gw, gh, "DADOS"))
    p.append(item(gx[1] + 12, gy[0] + 32, "Aurora Serverless v2 + PostGIS", "cadastro", "consulta espacial nativa; 0 a 8 ACU; pausa sem uso"))
    p.append(item(gx[1] + 12, gy[0] + 32 + ih + 8, "S3 versionado, ciclo de vida", "bases e imagens", "versão de cada base guardada; imagens frias em 90 dias"))
    p.append(item(gx[1] + 12, gy[0] + 32 + 2 * (ih + 8), "ECR com tags imutáveis", "imagens Docker", "roda exatamente o que foi testado; varredura no envio"))

    p.append(grupo(gx[0], gy[1], gw, 154, "INTEGRAÇÃO"))
    p.append(item(gx[0] + 12, gy[1] + 32, "Amazon EventBridge", "eventos", "imagem nova no S3 submete o job; falha vira alarme"))
    p.append(item(gx[0] + 12, gy[1] + 32 + ih + 8, "Airflow 3 (VPS da empresa)", "ingestão", "reaproveita agenda, retentativas e histórico existentes"))

    p.append(grupo(gx[1], gy[1], gw, 154, "OPERAÇÃO E SEGURANÇA"))
    p.append(item(gx[1] + 12, gy[1] + 32, "CloudWatch + SNS", "monitoramento", "logs, métricas e alarmes por e-mail"))
    p.append(item(gx[1] + 12, gy[1] + 32 + ih + 8, "Secrets Manager · IAM · CloudTrail", "segurança", "segredo fora do código; role mínima; auditoria"))

    yf = gy[1] + 154 + 14
    p.append(f"<rect x='12' y='{yf}' width='{W - 24}' height='34' rx='7' fill='{ACENTO_FUNDO}' stroke='{ACENTO}'/>")
    p.append(texto(W / 2, yf + 21, "Tudo em Docker e descrito em Terraform: dev e prod com o mesmo código e um tfvars por ambiente", 11, 600, TINTA, "middle"))
    return svg(W, yf + 46, "".join(p), "Onde cada parte roda na AWS, e por quê")


# ---------------------------------------------------------------- pipeline (2.4)
def pipeline():
    W, cw, g = 760, 168, 22
    xs = [12 + i * (cw + g) for i in range(4)]
    y0 = 40
    p = [texto(12, 22, "O que acontece em cada etapa do pipeline", 13.5, 700, TINTA)]
    etapas = [
        ("Versionamento", "GitHub", ["branch curta da main", "pull request", "revisão de outra pessoa", "ADR para cada decisão", "tag semântica vX.Y.Z"]),
        ("Integração e testes", "workflow ci", ["ruff: lint e formato", "pytest: unitários", "integração com PostGIS", "docker build por serviço", "terraform fmt e validate", "plan de dev no PR (infra/)", "F1 do modelo por município"]),
        ("Artefatos", "publicar-imagens", ["imagem por serviço", "tag sha-<7 do commit>", "ECR imutável", "scan de vulnerabilidades", "tag vX.Y.Z na release"]),
        ("Implantação", "deploy-dev · release", ["terraform plan -out", "apply do arquivo do plano", "ecs wait services-stable", "fumaça em /saude", "prod: aprovação manual", "rollback: tag anterior"]),
    ]
    hmax = 40 + 22 * 7 + 12
    for i, (nome, wf, passos) in enumerate(etapas):
        x = xs[i]
        ac = i == 3
        p.append(f"<rect x='{x}' y='{y0}' width='{cw}' height='{hmax}' rx='8' fill='{ACENTO_FUNDO if ac else '#ffffff'}' stroke='{ACENTO if ac else '#cbd5e1'}' stroke-width='{1.6 if ac else 1.1}'/>")
        p.append(f"<circle cx='{x + 20}' cy='{y0 + 19}' r='10' fill='{ACENTO}'/>")
        p.append(texto(x + 20, y0 + 23, str(i + 1), 11, 700, "#ffffff", "middle"))
        p.append(texto(x + 37, y0 + 23, nome, 12, 600, TINTA))
        p.append(texto(x + 12, y0 + 42, wf, 10, 500, ACENTO))
        for j, ps in enumerate(passos):
            yy = y0 + 52 + j * 22
            p.append(f"<rect x='{x + 10}' y='{yy}' width='{cw - 20}' height='18' rx='4' fill='{FUNDO}' stroke='#e2e8f0'/>")
            p.append(texto(x + 18, yy + 13, ps, 10, 400, TINTA))
        if i < 3:
            p.append(seta(f"M{x + cw} {y0 + hmax / 2} L{xs[i + 1] - 2} {y0 + hmax / 2}"))
    # portões
    yp = y0 + hmax + 10
    portoes = [
        (xs[1], "portão: tudo verde para o merge"),
        (xs[3], "portão: aprovação humana em prod"),
    ]
    for x, s in portoes:
        p.append(texto(x + cw / 2, yp + 14, s, 10, 600, VERDE, "middle"))
    p.append(seta(f"M{xs[1] + cw / 2} {y0 + hmax + 26} L{xs[1] + cw / 2} {y0 + hmax + 42} L{xs[0] + cw / 2} {y0 + hmax + 42} L{xs[0] + cw / 2} {y0 + hmax + 2}", "v"))
    p.append(texto((xs[0] + xs[1] + cw) / 2, y0 + hmax + 56, "falhou: volta ao autor, nada é publicado", 10, 500, VERMELHO, "middle"))
    p.append(texto(W - 12, y0 + hmax + 56, "OIDC: uma role por ambiente, sem chave no repositório", 10, 400, QUIETO, "end"))
    return svg(W, y0 + hmax + 66, "".join(p), "O que acontece em cada etapa do pipeline")


DIAGRAMAS = {"fluxo": fluxo, "nuvem": nuvem, "pipeline": pipeline}

if __name__ == "__main__":
    for nome, f in DIAGRAMAS.items():
        (DIR / "figs" / f"{nome}.svg").write_text(f(), encoding="utf-8")
    html = (DIR / "parte2.html").read_text(encoding="utf-8")
    for nome in DIAGRAMAS:
        html = html.replace(f"<!--svg:{nome}-->", (DIR / "figs" / f"{nome}.svg").read_text(encoding="utf-8"))
    (DIR / "parte2.render.html").write_text(html, encoding="utf-8")
    print("diagramas e parte2.render.html prontos")
