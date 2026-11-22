"""Builds the A4 schedule report as HTML; Chrome headless prints it to PDF."""

from pathlib import Path

OUT = Path(__file__).parent / "out" / "report.html"
OUT.parent.mkdir(exist_ok=True)

HUE = {
    "sandbox": ("#2a78d6", "rgba(42,120,214,.13)"),
    "warehouse": ("#eb6834", "rgba(235,104,52,.14)"),
    "release": ("#1baf7a", "rgba(27,175,122,.16)"),
    "none": ("#9a9893", "rgba(154,152,147,.17)"),
}


def chips(stages):
    return "".join(f'<span class="chip">{s}</span>' for s in stages)


def hm(t):
    h = int(t) % 24
    m = round((t - int(t)) * 60)
    return f"{h:02d}:{m:02d}"


# ---------------------------------------------------------------- page 1: calendar
CAL_START, CAL_END = 8.0, 25.0  # 08:00 to 01:00
CAL_H = 128.0  # mm of the time grid
DAYS = ["Dom 22/11", "Seg 23/11", "Ter 24/11", "Qua 25/11", "Qui 26/11", "Sex 27/11"]
CAL_BLOCKS = [
    # day index, start, end, kind, title, line, stages
    (
        0,
        15.0,
        24.5,
        "sandbox",
        "N.9 · dia 3",
        "hub + Sandbox: mwaa, mlflow, bedrock-base, bedrock-agent",
        ["17", "6e", "6d"],
    ),
    (
        1,
        9.0,
        15.0,
        "none",
        "Sem ambiente",
        "09:00 atos seus: saldos, orçamento, senha · 10:00 Stage 17 10.5: Claude escreve e planeja, você aplica (estimativa)",
        ["17", "11", "5b", "6e", "7"],
    ),
    (
        2,
        9.0,
        17.5,
        "warehouse",
        "N.10 · dia 1",
        "hub + Sandbox: redshift, mwaa",
        ["5b", "6h", "19", "17", "20"],
    ),
    (
        3,
        9.0,
        17.25,
        "warehouse",
        "N.10 · dia 2",
        "hub + Sandbox: redshift",
        ["21", "19", "6h", "20"],
    ),
    (
        4,
        9.0,
        17.17,
        "release",
        "R2 · releases",
        "hub + GitLab BUILD=1 + egress de Staging e Production",
        ["8", "9", "10", "17", "20", "7"],
    ),
    (5, 10.0, 12.0, "none", "PR do 9.11 e fechamento", "sem ambiente", ["17", "8", "9", "10"]),
]


def calendar():
    rail_w, head_h, gap = 9.0, 7.0, 1.6
    total_w = 184.0
    col_w = (total_w - rail_w) / len(DAYS)
    parts = [f'<div class="cal" style="height:{CAL_H + head_h + 1}mm">']
    # hour lines and labels
    for h in range(int(CAL_START), int(CAL_END) + 1, 1):
        y = head_h + (h - CAL_START) / (CAL_END - CAL_START) * CAL_H
        strong = " strong" if h % 2 == 0 else ""
        parts.append(f'<div class="hline{strong}" style="top:{y:.2f}mm;left:{rail_w}mm"></div>')
        if h % 2 == 0 or h == int(CAL_END):
            parts.append(f'<div class="hlabel" style="top:{y - 1.6:.2f}mm">{h % 24:02d}h</div>')
    for i, d in enumerate(DAYS):
        x = rail_w + i * col_w
        parts.append(f'<div class="colhead" style="left:{x:.2f}mm;width:{col_w:.2f}mm">{d}</div>')
        if i:
            parts.append(
                f'<div class="vline" style="left:{x:.2f}mm;top:{head_h}mm;height:{CAL_H}mm"></div>'
            )
    for day, s, e, kind, title, line, stg in CAL_BLOCKS:
        x = rail_w + day * col_w + gap / 2
        y = head_h + (s - CAL_START) / (CAL_END - CAL_START) * CAL_H
        h = (e - s) / (CAL_END - CAL_START) * CAL_H
        border, fill = HUE[kind]
        small = " small" if h < 12 else ""
        parts.append(
            f'<div class="blk{small}" style="left:{x:.2f}mm;top:{y + 0.3:.2f}mm;width:{col_w - gap:.2f}mm;'
            f'height:{h - 0.6:.2f}mm;background:{fill};border-left-color:{border}">'
            f'<div class="bt">{title}</div><div class="bh">{hm(s)}–{hm(e)}</div>'
            + ("" if small else f'<div class="bl">{line}</div>')
            + f'<div class="bc">{chips(stg)}</div></div>'
        )
    parts.append("</div>")
    return "\n".join(parts)


# ---------------------------------------------------------------- page 2: today
TODAY = [
    # start, end, short, block text, stages, who
    (
        14.75,
        15.0,
        "0",
        "<b>Antes de subir.</b> O PR #376 deve receber o registro do 3.3 do Stage 17 (a execução das ~14:38 às 14:46) e a nota do TM-28; depois, o merge é seu. Se atrasar, o dia 3 começa assim mesmo e sincroniza depois. Abre-se uma sessão nova do Claude para o dia 3: este branch já entrou no main (#373) e está aposentado.",
        ["17", "6f", "19"],
        "você",
    ),
    (
        15.0,
        15.42,
        "1",
        "<b>Subida.</b> Claude avisa as outras sessões e lê <code>make status</code>; você sobe o túnel, <code>make hub-up</code> e <code>make up ENV=sandbox GROUPS=mwaa,mlflow,bedrock-base,bedrock-agent</code>; Claude lê <code>make status</code> de novo.",
        ["infra"],
        "você · Claude",
    ),
    (
        15.42,
        15.75,
        "2",
        "<b>Espaços e tars.</b> Os tars e os <code>.env</code> de <code>$HOME/tmp/stage17-day3/</code> sobem para o espaço de cada projeto e são desempacotados; o <code>.env</code> é carregado antes do deploy. O workflow do 9.6, que não chama o Bedrock, começa antes da janela e treina durante ela.",
        ["17"],
        "você",
    ),
    (
        15.75,
        16.75,
        "3",
        "<b>Janela do 6e 6.4</b> (cerca de 1 h). Uma sessão do Claude Code num espaço, no modelo padrão, com uma tarefa longa em vários turnos, e nenhuma outra chamada ao Bedrock na conta. Claude anota o início e o fim em UTC e lê <code>./aws/bedrock-usage.py</code> depois do atraso de publicação; o volume vai para o teto da decisão 2 do Stage 12.",
        ["6e", "12"],
        "você · Claude",
    ),
    (
        16.75,
        18.0,
        "4",
        "<b>9.6.</b> O <code>app-ml</code> é treinado, registrado e pontuado em <code>app-ml-dev</code> (verificação lx).",
        ["17"],
        "você · Claude",
    ),
    (
        18.0,
        19.75,
        "5",
        "<b>10.4.</b> Deploy do <code>app-genai</code> e as leituras 1 a 6. Cada apply de <code>sandbox/bedrock/</code> é Claude⚡ na sua palavra, e as duas chaves voltam a <code>false</code> no fim.",
        ["17"],
        "Claude⚡ · você",
    ),
    (
        19.75,
        21.5,
        "6",
        "<b>Pass 5</b> no espaço do <code>eighth-experimentation</code>: o pipeline escrito pelo SDK, executado e lido de volta, e os formulários do editor (5.1 a 5.4).",
        ["17"],
        "você",
    ),
    (
        21.5,
        21.67,
        "7",
        "<b>Verificação xxiv.</b> Do <code>jup</code>, um <code>Retrieve</code> no knowledge base <code>QWDNVYXADH</code> pelo <code>bedrock-agent-runtime</code>, com a saída colada (7.4b).",
        ["17"],
        "você",
    ),
    (
        21.67,
        23.0,
        "8",
        "<b>Restante do 6d</b> (cerca de 75 min), no espaço <code>code</code>, com os espaços do Stage 17 parados antes: a metade monitorada do 7.5 (cerca de 20 min, todo shell em <code>proxy-on</code>); o 7.7 depois do logout, lido aos 5 e aos 30 minutos; Claude lê o 6.1 (viii) no flow log durante a espera.",
        ["6d"],
        "você · Claude",
    ),
    (
        23.0,
        23.5,
        "9",
        "<b>Leituras de fechamento.</b> <code>./aws/sandbox-ml.py</code> e <code>./aws/catalog.py</code>; espaços parados e abas do portal fechadas (o passo 12 do 6d junto).",
        ["17", "6d"],
        "Claude · você",
    ),
    (
        23.5,
        24.0,
        "10",
        "<b>Descida.</b> <code>make down ENV=sandbox</code>, <code>make hub-down</code>, <code>make status</code>; as leituras do §R (<code>egress.py</code> e os apps do Studio).",
        ["infra"],
        "você · Claude",
    ),
    (24.0, 24.5, "11", "<b>Folga.</b> O plano estima o dia em cerca de 9,5 h.", [], ""),
]
STRIP_START, STRIP_END, STRIP_W = 14.75, 24.5, 184.0


def strip():
    def x(t):
        return (t - STRIP_START) / (STRIP_END - STRIP_START) * STRIP_W

    parts = ['<div class="strip">']
    for s, e, short, _, stg, _ in TODAY:
        kind = "none" if short in ("0", "11") else "sandbox"
        border, fill = HUE[kind]
        w = x(e) - x(s)
        parts.append(
            f'<div class="seg" style="left:{x(s) + 0.25:.2f}mm;width:{w - 0.5:.2f}mm;background:{fill};'
            f'border-bottom:0.8mm solid {border}"><span>{short}</span></div>'
        )
    # the training lane that overlaps the window
    parts.append(
        f'<div class="lane" style="left:{x(15.42) + 0.25:.2f}mm;width:{x(16.75) - x(15.42) - 0.5:.2f}mm">9.6 treina, sem Bedrock</div>'
    )
    for h in range(15, 25):
        parts.append(f'<div class="tick" style="left:{x(h):.2f}mm">{h % 24:02d}h</div>')
        parts.append(f'<div class="tline" style="left:{x(h):.2f}mm"></div>')
    parts.append("</div>")
    return "\n".join(parts)


def day_table(rows, kind, numbered=False):
    border, _ = HUE[kind]
    out = ['<table class="sched"><thead><tr>']
    if numbered:
        out.append("<th class='n'>#</th>")
    out.append("<th>Horário</th><th>Bloco</th><th>Stages</th><th>Quem</th></tr></thead><tbody>")
    for r in rows:
        s, e, short, text, stg, who = r
        k = "none" if short in ("0", "11") and kind == "sandbox" else kind
        b = HUE[k][0]
        out.append("<tr>")
        if numbered:
            out.append(f'<td class="n" style="border-left:1mm solid {b}">{short}</td>')
            out.append(f'<td class="t">{hm(s)}–{hm(e)}</td>')
        else:
            out.append(f'<td class="t" style="border-left:1mm solid {b}">{hm(s)}–{hm(e)}</td>')
        out.append(
            f'<td>{text}</td><td class="stg">{chips(stg)}</td><td class="who">{who}</td></tr>'
        )
    out.append("</tbody></table>")
    return "".join(out)


# ---------------------------------------------------------------- pages 3 and 4: the next days
D1 = [
    (
        9.0,
        9.42,
        "",
        "<b>Subida.</b> Avisos e <code>make status</code>; você: <code>make hub-up</code>, <code>make up ENV=sandbox GROUPS=redshift,mwaa</code>; <code>make status</code>.",
        ["infra"],
        "você · Claude",
    ),
    (
        9.42,
        9.67,
        "",
        "<b>Espaços.</b> JupyterLab em <code>ml.t3.medium</code> no <code>eighth-experimentation</code>, no <code>test-experimentation</code> e no <code>app-dbt-dev</code>, cada um parado quando seus passos acabam.",
        ["6h", "19", "17", "20"],
        "você",
    ),
    (
        9.67,
        9.92,
        "",
        "<b>5b, passos 1 e 2.</b> <code>./aws/warehouse.py awsds-infra-sandbox-1 --sql</code> e o re-plano de <code>warehouse-compute/</code>. Uma mudança nesse plano suspende todo apply ao slice no dia.",
        ["5b"],
        "Claude",
    ),
    (
        9.92,
        10.58,
        "",
        "<b>6h passo 1 e 5b passo 3.</b> A primeira sessão do editor em <code>sandbox</code>; o teste do <code>max_query_execution_time</code>.",
        ["6h", "5b"],
        "você · Claude",
    ),
    (
        10.58,
        12.75,
        "",
        "<b>6h, passos 2 a 10.</b> 5.2, a metade devida do 5.2a, 5.3, 5.4 e a metade “antes” do 5.1; Claude⚡ o apply permanente (<code>sandbox/warehouse/</code>, depois <code>warehouse-compute/</code>); 5.2b; a metade “depois” do 5.1, do espaço do <code>app-dbt-dev</code>; a metade de portal do 0.4.",
        ["6h"],
        "você · Claude⚡",
    ),
    (
        12.75,
        14.17,
        "",
        "<b>Stage 19, pass 5 (1 a 6).</b> A sessão, <code>USAGE ON DATABASE awsdatacatalog</code>, a leitura do 5.2 só com o grant do DataZone (xiii), a metade Lake Formation do 5.1 só se ela for recusada, a cópia e a view, e a fonte do 5.3, que é o 2.2 do Stage 21.",
        ["19", "21"],
        "você · Claude",
    ),
    (
        14.17,
        16.17,
        "",
        "<b>Stage 17, pass 4 (4.1 a 4.6).</b> O endpoint pelo SDK, que fica no ar depois da sessão (decisão 6; 0,115 USD/h, fora do <code>make status</code>), o formulário do portal, o batch transform e os negativos de serverless e GPU. O endpoint é criado antes do pass 5 do Stage 20.",
        ["17"],
        "você · Claude",
    ),
    (
        16.17,
        16.92,
        "",
        "<b>Stage 20, pass 5 (5.2 e 5.3).</b> O modelo sobre a tabela assinada, do tar do 5.1 (<code>$HOME/tmp/stage20/app-dbt.tar</code>), sua leitura e seu grafo, e a aba <i>Lineage</i> como membro de outro projeto.",
        ["20"],
        "você · Claude",
    ),
    (
        16.92,
        17.5,
        "",
        "<b>Descida.</b> Espaços parados e abas fechadas; <code>make down ENV=sandbox</code>, <code>make hub-down</code>, <code>make status</code>, §R. Os grants do 5.1, a cópia e as duas assinaturas ficam para o dia 2.",
        ["infra"],
        "você · Claude",
    ),
]
D2 = [
    (
        9.0,
        9.5,
        "",
        "<b>Subida.</b> Avisos; você: <code>make hub-up</code>, <code>make up ENV=sandbox GROUPS=redshift</code>; os espaços nos dois projetos.",
        ["infra"],
        "você · Claude",
    ),
    (
        9.5,
        14.0,
        "",
        "<b>Stage 21, passes 2 a 4.</b> O pass 2 a partir do 2.1; o workgroup do consumidor pelos applies do 1.5 na ordem do 2.4 e sua remoção pelo 2.9; o pass 3; o pass 4 com o transfer role do 4.5 e o statement de chave em <code>sandbox/data/</code> aplicado (decisão 4 (b)), e o 4.8; as leituras de fechamento (<code>list-workgroups</code>, <code>describe-clusters</code>, <code>WH-8</code>).",
        ["21"],
        "você · Claude⚡",
    ),
    (
        14.0,
        16.0,
        "",
        "<b>Stage 21, pass 5.</b> O prefixo publicado do espaço do <code>eighth-experimentation</code>; o produto pedido de um notebook do <code>test-experimentation</code>, aprovado, lido e revogado, com a espera de 5 minutos da revogação.",
        ["21"],
        "você",
    ),
    (
        16.0,
        16.75,
        "",
        "<b>Stage 19 5.4 e o item 5 do rollback do Stage 21.</b> Os grants do 5.1 revogados, a view e as tabelas removidas, o <code>lab</code> mantido (6h 6.4); as assinaturas do item 6 revogadas (a do 4.12 pelo 2.5 e a do 5.0 do Stage 20), cada uma lida dos dois lados.",
        ["19", "21", "6h", "20"],
        "você · Claude",
    ),
    (
        16.75,
        17.25,
        "",
        "<b>Descida.</b> <code>make down ENV=sandbox</code>, <code>make hub-down</code>, <code>make status</code>, §R. O <code>make status</code> não lê workgroups; as leituras de fechamento do Stage 21 valem por ele.",
        ["infra"],
        "você · Claude",
    ),
]
R2 = [
    (
        9.0,
        9.67,
        "",
        "<b>Subida.</b> Avisos e <code>make status</code>; você: <code>make hub-up</code>, <code>make gitlab-up BUILD=1</code>, o túnel.",
        ["infra", "7"],
        "você · Claude",
    ),
    (
        9.67,
        10.33,
        "",
        "<b>O que o R1 deixou.</b> A senha do usuário local do GitLab confirmada ou rotacionada antes do primeiro push; <code>git pull</code> e <code>git push gitlab main</code>, o mirror de onde os legs clonam os scripts do #321; o merge request da linha <code>default-v0.10.1</code> no README do <code>awsds/dev-env</code> e seu mirror (Claude). O build runner é lido rodando antes de cada tag.",
        ["7", "8"],
        "você · Claude",
    ),
    (
        10.33,
        12.33,
        "",
        "<b><code>app-dbt</code> <code>v0.1.0</code></b> (Stage 20 8.7 a 8.9). Antes da tag, o 8.6 apaga em <code>app-dbt-dev</code> o asset do link do 5.0 e o da tabela do pass 5. <code>make up ENV=staging ONLY=egress</code> antes da primeira tag; <code>make up ENV=production ONLY=workloads-egress</code> antes do primeiro <code>production-gate</code>; as leituras por alvo.",
        ["20", "8", "9", "10"],
        "você · Claude",
    ),
    (
        12.33,
        14.33,
        "",
        "<b><code>app-ml</code></b> (Stage 17 9.7). O bundle leva o candidato que o <code>app-ml-dev</code> publicou por último.",
        ["17", "8"],
        "você · Claude",
    ),
    (
        14.33,
        16.0,
        "",
        "<b><code>app-genai</code></b> (Stage 17 10.6). Subidas de egress com <code>GROUPS=bedrock-base</code>; o pipeline não roda <code>pip-audit</code>. Claude⚡ inicia <code>awsds-prod-chain-app-genai-triage</code> na sua palavra.",
        ["17", "8", "10"],
        "você · Claude⚡",
    ),
    (
        16.0,
        16.67,
        "",
        "<b><code>app-etl</code></b>, o release que aposenta a metade do modelo (Stage 17 9.11), com o pin do lint em <code>4613ddc</code>.",
        ["17", "8"],
        "você",
    ),
    (
        16.67,
        17.17,
        "",
        "<b>Descida.</b> <code>make down ENV=staging</code> depois do último leg de Staging, <code>make down ENV=production ONLY=workloads-egress</code>, <code>make gitlab-down</code>, o túnel, <code>make hub-down</code>; <code>make status</code>, §R.",
        ["infra"],
        "você · Claude",
    ),
]

CSS = """
@page { size: A4; margin: 0; }
html, body { margin: 0; padding: 0; background: #ffffff; }
body { font-family: -apple-system, "Helvetica Neue", Helvetica, Arial, sans-serif; color: #1b1b1a;
  font-size: 8.4pt; line-height: 1.36; -webkit-print-color-adjust: exact; print-color-adjust: exact;
  font-variant-numeric: tabular-nums; }
.page { width: 210mm; height: 297mm; box-sizing: border-box; padding: 11mm 13mm 13mm; position: relative;
  overflow: hidden; break-after: page; }
.page:last-of-type { break-after: auto; }
.kicker { font-size: 7.2pt; letter-spacing: .07em; text-transform: uppercase; color: #6b6a66; font-weight: 600; }
h1 { font-size: 18.5pt; margin: 1.2mm 0 1mm; line-height: 1.15; font-weight: 700; letter-spacing: -.01em; }
h2 { font-size: 12.5pt; margin: 0 0 1mm; font-weight: 700; letter-spacing: -.005em; }
h3 { font-size: 9.6pt; margin: 3.2mm 0 1.2mm; font-weight: 700; }
p { margin: 0 0 1.4mm; }
.sub { color: #52514e; }
code { font-family: "SF Mono", Menlo, monospace; font-size: 7.3pt; background: #f2f1ee; padding: 0 .6mm;
  border-radius: .6mm; white-space: nowrap; }
.chip { display: inline-block; font-size: 6.6pt; font-weight: 650; border: .25mm solid #bdbbb4; background: #f7f6f3;
  color: #2b2a28; border-radius: 1mm; padding: 0 1mm; margin: 0 .5mm .5mm 0; line-height: 1.45; }
.tiles { display: flex; gap: 2.4mm; margin: 3mm 0 2.5mm; }
.tile { flex: 1; border: .25mm solid #dedcd5; border-radius: 1.5mm; padding: 2mm 2.4mm; }
.tile .l { font-size: 6.9pt; text-transform: uppercase; letter-spacing: .05em; color: #6b6a66; font-weight: 600; }
.tile .v { font-size: 13pt; font-weight: 700; margin: .6mm 0 .2mm; letter-spacing: -.01em; }
.tile .d { font-size: 7.2pt; color: #52514e; }
.legend { display: flex; flex-wrap: wrap; gap: 4mm; font-size: 7.4pt; color: #3a3936; margin: 1.6mm 0 0; }
.legend .sw { display: inline-block; width: 4.2mm; height: 2.8mm; border-radius: .6mm; border-left: 1mm solid;
  vertical-align: -0.4mm; margin-right: 1.2mm; }
.cal { position: relative; margin-top: 2mm; }
.cal .hline { position: absolute; right: 0; border-top: .18mm solid #f0efea; }
.cal .hline.strong { border-top-color: #e2e0d9; }
.cal .vline { position: absolute; border-left: .18mm solid #e2e0d9; }
.cal .hlabel { position: absolute; left: 0; width: 7.5mm; text-align: right; font-size: 6.4pt; color: #8a8984; }
.cal .colhead { position: absolute; top: 0; height: 6mm; font-weight: 700; font-size: 7.8pt; text-align: center;
  color: #2b2a28; }
.cal .nowmark { position: absolute; border-top: .45mm dashed #1b1b1a; }
.cal .blk { position: absolute; box-sizing: border-box; border-radius: 1.1mm; padding: 1.1mm 1.2mm .6mm 1.3mm;
  border-left: 1mm solid; overflow: hidden; }
.cal .bt { font-weight: 700; font-size: 7.6pt; line-height: 1.2; }
.cal .bh { font-size: 6.6pt; color: #52514e; margin: .2mm 0 .5mm; }
.cal .bl { font-size: 6.5pt; color: #3a3936; line-height: 1.25; margin-bottom: .8mm; }
.cal .blk.small .bt { font-size: 6.8pt; display: inline; }
.cal .blk.small .bh { display: inline; margin-left: 1mm; }
.cal .blk.small .bc { margin-top: .4mm; }
.box { border: .25mm solid #dedcd5; border-radius: 1.5mm; padding: 2mm 2.6mm; }
.box h3 { margin-top: 0; }
.cols { display: flex; gap: 3mm; }
.cols > * { flex: 1; }
ul { margin: 0; padding-left: 3.6mm; }
li { margin-bottom: .8mm; }
table { border-collapse: collapse; width: 100%; }
th { text-align: left; font-size: 6.8pt; text-transform: uppercase; letter-spacing: .05em; color: #6b6a66;
  font-weight: 600; border-bottom: .3mm solid #d9d7d0; padding: .8mm 1.4mm; }
td { vertical-align: top; padding: 1.1mm 1.4mm; border-bottom: .2mm solid #ecebe6; }
td.t { white-space: nowrap; font-weight: 650; width: 17mm; }
td.n { width: 4mm; font-weight: 700; text-align: center; color: #3a3936; }
th.n { width: 4mm; }
td.who { white-space: nowrap; color: #52514e; width: 20mm; font-size: 7.4pt; }
td.stg { width: 21mm; }
.sched td { font-size: 7.9pt; }
.strip { position: relative; height: 19mm; margin: 2.5mm 0 1mm; }
.strip .seg { position: absolute; top: 0; height: 8mm; border-radius: .9mm .9mm 0 0; box-sizing: border-box;
  display: flex; align-items: center; justify-content: center; font-size: 6.6pt; font-weight: 700; color: #1b1b1a; }
.strip .lane { position: absolute; top: 9.2mm; height: 3.6mm; border-radius: .8mm; background: rgba(42,120,214,.07);
  border: .25mm dashed #2a78d6; box-sizing: border-box; font-size: 5.9pt; color: #2b2a28; text-align: center;
  line-height: 3.2mm; }
.strip .tick { position: absolute; top: 14.4mm; font-size: 6.2pt; color: #8a8984; transform: translateX(-50%); }
.strip .tline { position: absolute; top: 0; height: 13.6mm; border-left: .18mm solid rgba(0,0,0,.18); }
.warn { border-left: 1mm solid #1b1b1a; background: #f6f5f2; padding: 1.8mm 2.4mm; border-radius: 0 1.2mm 1.2mm 0; }
.footer { position: absolute; left: 13mm; right: 13mm; bottom: 6.5mm; font-size: 6.6pt; color: #8a8984;
  display: flex; justify-content: space-between; border-top: .2mm solid #ecebe6; padding-top: 1.2mm; }
.dl { position: relative; height: 31mm; margin: 2mm 0 1mm; }
.dl .axis { position: absolute; left: 0; right: 0; top: 13mm; border-top: .3mm solid #b9b7b0; }
.dl .m { position: absolute; top: 11.4mm; width: 2.6mm; height: 2.6mm; border-radius: 50%; background: #1b1b1a;
  transform: translateX(-50%); border: .5mm solid #fff; box-sizing: content-box; }
.dl .lab { position: absolute; font-size: 6.4pt; line-height: 1.25; width: 30mm; }
.dl .lab b { font-size: 6.9pt; }
.dl .mon { position: absolute; top: 15.5mm; font-size: 6pt; color: #8a8984; transform: translateX(-50%); }
.left-table td:first-child { font-weight: 700; white-space: nowrap; width: 31mm; }
.left-table td { font-size: 7.6pt; }
"""

FOOT = '<div class="footer"><span>AWS Data Science · cronograma do que falta no plano · gerado em 22/11/2026, 14h BRT, do main em <code>f37ff75c</code> e do PR #376 aberto</span><span>{p}/5</span></div>'

LEGEND = (
    '<div class="legend">'
    + "".join(
        f'<span><span class="sw" style="background:{HUE[k][1]};border-left-color:{HUE[k][0]}"></span>{t}</span>'
        for k, t in [
            ("sandbox", "Sandbox: hub + grupos do Sandbox"),
            ("warehouse", "Warehouse: hub + <code>redshift</code>"),
            ("release", "Release: hub + GitLab + egress dos alvos"),
            ("none", "Sem ambiente: custo zero"),
        ]
    )
    + '<span><span class="chip">17</span> o stage tratado no bloco</span></div>'
)


def page1():
    return f"""
<section class="page">
  <div class="kicker">AWS Data Science · planejamento da execução</div>
  <h1>Cronograma do que falta no plano</h1>
  <p class="sub">A próxima subida começa hoje às 15:00 (18:00 UTC). Horários em BRT (UTC−3); o plano registra UTC.
  A ordem e os prazos são do plano (<code>promotion.md</code> §N.6 e §N.12); os horários dos dias seguintes partem das 09:00 por
  convenção deste relatório, e você pode deslocá-los.</p>
  <div class="tiles">
    <div class="tile"><div class="l">Próxima subida</div><div class="v">Hoje, 15:00</div><div class="d">N.9 dia 3 · 18:00 UTC</div></div>
    <div class="tile"><div class="l">Fim do dia 3</div><div class="v">~00:30</div><div class="d">cerca de 9,5 h pelo plano</div></div>
    <div class="tile"><div class="l">Última subida</div><div class="v">Qui, 26/11</div><div class="d">R2; 25/11 se junto ao N.10 dia 2</div></div>
    <div class="tile"><div class="l">Prazo mais próximo</div><div class="v">18/12</div><div class="d">dbt Core 1.11 · release do <code>app-dbt</code></div></div>
  </div>
  <h2>A semana</h2>
  {LEGEND}
  {calendar()}
  <div class="cols" style="margin-top:2.5mm">
    <div class="box">
      <h3>Regras de cada sessão com ambiente</h3>
      <ul>
        <li>Começa na sua palavra, porque é medida; Claude avisa as outras sessões do laptop antes de qualquer write.</li>
        <li><b>Claude⚡</b> é um write que Claude executa na sua palavra, nomeando o ato.</li>
        <li>Termina em custo zero: abas do portal fechadas, <code>make down</code>, <code>make hub-down</code>, <code>make status</code>, §R.</li>
        <li>Cada subida é uma sessão nova do Claude, com branch próprio; este branch está aposentado.</li>
      </ul>
    </div>
    <div class="box">
      <h3>Dependências que fixam a ordem</h3>
      <ul>
        <li>O dia 3 e o N.10 não dependem um do outro.</li>
        <li>O 10.5 vem depois do dia 3: escreve nos alvos o que o 10.4 medir no Sandbox.</li>
        <li>O R2 espera o dia 3, os applies do 10.5 e o dia 1 do N.10, cujo pass 5 o Stage 20 põe antes do pass 8.</li>
        <li>O R2 pode dividir o dia com o N.10 dia 2, à sua escolha (§N.12.1).</li>
      </ul>
    </div>
  </div>
  {FOOT.format(p=1)}
</section>"""


def page2():
    return f"""
<section class="page">
  <div class="kicker">Hoje · domingo, 22/11 · sessão Sandbox</div>
  <h2>N.9 dia 3: 6e 6.4, sessão C do Stage 17 com o pass 5, e o restante do 6d</h2>
  <p class="sub">15:00 → ~00:30 (18:00 → 03:30 UTC). Subida: <code>make hub-up</code>, depois
  <code>make up ENV=sandbox GROUPS=mwaa,mlflow,bedrock-base,bedrock-agent</code>. Sem GitLab e sem egress dos alvos.
  O plano dá cerca de 6,2 h à sessão C (blocos 2 a 7); a divisão interna dela é estimativa deste relatório.</p>
  {strip()}
  {day_table(TODAY, "sandbox", numbered=True)}
  <div class="cols" style="margin-top:2.6mm">
    <div class="box">
      <h3>Pronto, lido hoje com nada no ar</h3>
      <ul>
        <li>Os tars de <code>app-ml</code> e <code>app-genai</code> continuam válidos: <code>examples/</code> não mudou de <code>77fc285a</code> ao main; o #321 só mudou dois scripts que os tars não levam e que o dia 3 não chama.</li>
        <li><code>sandbox/bedrock/</code> e <code>sandbox/ml/</code>: <i>No changes</i> às 13:55 (16:55 UTC). Os applies das chaves do 10.4 só mudam a chave.</li>
        <li>O MLflow App do <code>app-ml-dev</code> e o perfil Nova Lite do <code>app-genai-dev</code> já existem (N.12.5).</li>
      </ul>
    </div>
    <div class="box">
      <h3>Custo e ponto de parada</h3>
      <ul>
        <li>Hub e endpoints: cerca de 0,28 USD/h antes dos espaços; cada espaço <code>ml.t3.medium</code> soma 0,050 USD/h. O dia fica entre 2 e 4 USD com o ciclo do Config; os tokens são cobrados à parte, e a janela do 6.4 é o maior deles.</li>
        <li>Se precisar parar antes: depois do xxiv, por volta das 21:40. O restante do 6d não chama grupo; já passou do dia 2 para o dia 3 por escolha sua, e mudá-lo de novo também é escolha sua.</li>
      </ul>
    </div>
  </div>
  {FOOT.format(p=2)}
</section>"""


def page3():
    return f"""
<section class="page">
  <div class="kicker">Segunda, 23/11 · sem ambiente</div>
  <h2>Stage 17 10.5 nos alvos, e os seus atos sem ambiente</h2>
  <div class="warn" style="margin:1.6mm 0 2mm">
    <b>Decisão antes do 10.5: TM-28.</b> A mudança do TM-28 em <code>staging/studio/</code> e <code>production/studio/</code>
    (<code>agent-registry</code> em <code>fenced_services</code>; cada plano lê 0 to add, 2 to change) está no main e não foi aplicada. O 10.5 aplica
    esses slices e espera um plano só com os statements do Bedrock. Opção (a): os três applies do TM-28 antes, cada um na sua
    palavra, com a bateria <code>--phase ou</code> depois (Stage 11). Opção (b): o plano do 10.5 nomeia as duas mudanças como esperadas.
    <span class="chip">11</span><span class="chip">17</span>
  </div>
  <div class="cols">
    <div class="box">
      <h3>09:00 · os seus atos <span class="chip">5b</span><span class="chip">6e</span><span class="chip">7</span><span class="chip">6d</span></h3>
      <ul>
        <li><b>Saldo do free trial do Redshift em Production</b>, no dia seguinte ao R1. Console; infrastructure user; conta Production; <code>InfrastructureAccess</code>. Última leitura: 299,18 de 300,00 (21/11).</li>
        <li><b>Saldo em Sandbox</b>, antes do N.10 dia 1. Mesmo usuário; conta Sandbox; <code>InfrastructureAccess</code>. Última: 287,51 (25/10).</li>
        <li><b>Alerta de orçamento</b> (6e, decisão 6; também o 2.1 do Stage 12): e-mail em 50, 80 e 100% do teto, e o Cost Anomaly Detection. Console da Management; usuário AWS Control Tower Admin; <code>AWSAdministratorAccess</code>. O aviso de 100% dispara na hora.</li>
        <li><b>Senha do usuário local do GitLab</b>: diga se já foi rotacionada; senão, é o primeiro ato do R2.</li>
        <li>Opcional, <b>6d 1.1 e 1.2</b>: um processing job sem <code>VpcConfig</code> e o mesmo com as subnets, como Data Scientist User (<code>awsds-scientist-sandbox</code>, conta Sandbox, <code>DataScientistAccess</code>). Os dois são recusados por desenho e nada é criado.</li>
      </ul>
    </div>
    <div class="box">
      <h3>10:00 → ~15:00 · 10.5, estimativa <span class="chip">17</span><span class="chip">11</span></h3>
      <ul>
        <li><b>Claude</b> escreve a entrada nova do threat model (o próximo <code>TM</code> livre, lido no commit) e emenda o <code>TM-30</code> e o gatilho <code>DT-14</code>. <b>Você</b> aceita o resíduo, ou as decisões 22 e 24 voltam à mesa.</li>
        <li><b>Claude</b> escreve e planeja: a tag do módulo (Recipe B); <code>genai.tf</code> nos dois <code>&lt;env&gt;/studio/</code> (perfil de inferência sobre o Nova Lite, os statements do papel, o guardrail da conta e sua configuração, decisão 27 (a)); a variável <code>optional_service_groups</code> em <code>staging/egress/</code>; <code>&lt;env&gt;/chains/</code>; os <code>state_read_keys</code> em <code>&lt;env&gt;/foundation/</code>.</li>
        <li><b>Você</b> aplica, cada um na sua palavra: <code>staging/studio/</code>, o modo de retenção <code>none</code> em <code>us-west-2</code> em Staging (ato seu), <code>production/studio/</code>, a retenção em Production, <code>&lt;env&gt;/chains/</code> e <code>&lt;env&gt;/foundation/</code> com o var-file de alerts.</li>
        <li><b>Claude</b> repete a simulação do 10.1 na boundary aplicada e lê <code>./aws/deploytargets.py</code>.</li>
      </ul>
    </div>
  </div>
  <h3 style="margin-top:3.4mm">Terça, 24/11 · N.10 dia 1, sessão warehouse · 09:00 → ~17:30</h3>
  <p class="sub">5b, 6h, o pass 5 do Stage 19, o pass 4 do Stage 17 e o pass 5 do Stage 20. O plano estima cerca de 7,5 h de blocos.
  O limite de uso é de 10 RPU-h por dia; num estouro, os passos do warehouse esperam a sua palavra, e os blocos dos Stages 17 e 20 seguem.</p>
  {day_table(D1, "warehouse")}
  {FOOT.format(p=3)}
</section>"""


def page4():
    return f"""
<section class="page">
  <div class="kicker">Quarta, 25/11 · sessão warehouse</div>
  <h2>N.10 dia 2: Stage 21 · 09:00 → ~17:15</h2>
  <p class="sub">Os passes 2 a 5 do Stage 21, o 5.4 do Stage 19 com o rollback do Stage 21, e as assinaturas revogadas no fim.
  O plano estima cerca de 7,5 h. As duas sessões do N.10 somam cerca de 9,5 USD (entre 6,5 e 13), mais o endpoint do pass 4, que custa
  2,76 USD por dia até ser apagado; o free trial absorve a parte do warehouse até 19/12.</p>
  {day_table(D2, "warehouse")}
  <h3 style="margin-top:3.6mm">Quinta, 26/11 · R2, sessão de release · 09:00 → ~17:10</h3>
  <p class="sub">Os primeiros releases de <code>app-dbt</code>, <code>app-ml</code> e <code>app-genai</code>, e a metade do modelo do <code>app-etl</code>.
  O plano estima de 6 a 8 h e cerca de 0,48 USD/h antes do egress dos alvos (mais 0,080 USD/h por egress no ar), de 4 a 6 USD no total.
  Cada leg leva uma hora ou mais; os atos sem leg cabem nas esperas.</p>
  {day_table(R2, "release")}
  <div class="cols" style="margin-top:2.6mm">
    <div class="box">
      <h3>Recomendado no R2, fora do §N.11.2 <span class="chip">7</span></h3>
      <p>Um backup do GitLab à mão (<code>gitlab-backup create</code> numa sessão SSM). O mais novo, do R1, sai do bucket em 23/12; sem
      GitLab no ar depois disso, não sobra backup corrente.</p>
    </div>
    <div class="box">
      <h3>Sexta, 27/11 · sem ambiente <span class="chip">17</span><span class="chip">8</span><span class="chip">9</span><span class="chip">10</span></h3>
      <ul>
        <li><b>Claude</b>: o PR do estado do 9.11, planejado de um <code>main</code> que já tenha o release (item 11).</li>
        <li><b>Você</b>: fechar os Stages 8, 9 e 10 como o Stage 4 fechou, com o que espera indo para o seu gatilho (item 12).</li>
      </ul>
    </div>
  </div>
  {FOOT.format(p=4)}
</section>"""


DEADLINES = [
    # (date label, x position in months from 2026-11-01, title, text, above?)
    (
        "01/12",
        1.0,
        "Stage 11",
        "analyzer de acesso interno, se criado, apagado antes: cobra a cada dia 1",
        True,
    ),
    ("18/12", 1.55, "dbt Core 1.11", "release do <code>app-dbt</code> (R2) antes", False),
    ("19/12", 1.6, "Free trial Sandbox", "o N.10 antes; as contas do 5b e do 6h depois", True),
    ("23/12", 1.73, "Backup do GitLab", "o mais novo sai do bucket", False),
    ("08/01", 2.25, "Sonnet 4.5", "sucessor escolhido (<code>BS-8</code>); 6e", True),
    ("21/01", 2.67, "Free trial Production", "a conta do warehouse do Stage 9", False),
    ("08/04", 5.23, "Sonnet 4.5", "fim de vida", True),
    ("22/09", 10.7, "TLS do GitLab", "folhas reemitidas; vencem 22/10", False),
]


DEADLINE_ROWS = [
    (
        "01/12/2026",
        "Analyzer de acesso interno",
        "se for criado, apagado antes: cobra na criação e a cada dia 1",
        ["11"],
    ),
    (
        "18/12/2026",
        "dbt Core 1.11 sem suporte crítico",
        "o release do <code>app-dbt</code> (R2) vem antes, ou o archive passa para o 1.12",
        ["20"],
    ),
    (
        "19/12/2026",
        "Fim do free trial do Redshift em Sandbox",
        "o N.10 vem antes; as metades de conta do 5b (x) e do 6h (xii) ficam legíveis depois",
        ["5b", "6h", "19", "21"],
    ),
    (
        "23/12/2026",
        "O backup mais novo do GitLab sai do bucket",
        "um backup no R2 estende a cobertura; sem GitLab no ar depois disso, não sobra backup corrente",
        ["7"],
    ),
    (
        "08/01/2027",
        "Sucessor do Sonnet 4.5 escolhido",
        "o <code>BS-8</code> do <code>bedrock-scope.py</code> falha nessa data; os modelos 5.5 são recusados à conta (<code>EXC-08</code>)",
        ["6e"],
    ),
    (
        "21/01/2027",
        "Fim do free trial do Redshift em Production",
        "a conta do warehouse do Stage 9 fica legível",
        ["9"],
    ),
    ("08/04/2027", "Fim de vida do Sonnet 4.5", "", ["6e"]),
    (
        "22/09/2027",
        "Folhas TLS do GitLab reemitidas",
        "vencem em 22/10/2027; o plano de <code>production/pki/</code> propõe a reemissão a partir daí",
        ["7"],
    ),
]


def deadlines():
    rows = "".join(
        f"<tr><td class='t'>{d}</td><td><b>{t}</b></td><td>{x}</td><td class='stg'>{chips(s)}</td></tr>"
        for d, t, x, s in DEADLINE_ROWS
    )
    return (
        "<table class='sched'><thead><tr><th>Data</th><th>Prazo</th><th>O que muda</th><th>Stages</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )


def page5():
    rows_left = [
        (
            "5b · Redshift Serverless",
            "a leitura <code>--sql</code>, o re-plano do <code>enable_large_strings_opt_in</code>, o teste do <code>max_query_execution_time</code>; a metade da conta (x)",
            "24/11; depois de 19/12",
        ),
        (
            "6d · Unified Studio",
            "a metade monitorada do 7.5, o 7.7, o 6.1 (viii); as suas tentativas 1.1 e 1.2; o 6.1 (xvii)",
            "hoje; sem ambiente",
        ),
        (
            "6e · Claude Code no Bedrock",
            "a janela do 6.4; o alerta de orçamento (decisão 6); o sucessor do Sonnet 4.5",
            "hoje; 23/11; até 08/01",
        ),
        (
            "6f · Catálogo sobre o lake",
            "o 11.12, o rollback, quando chamado; o 2.7 foi feito, com registro no PR #376",
            "sob demanda",
        ),
        (
            "6h · Conexão Redshift",
            "o editor em <code>sandbox</code>, 5.1 a 5.4, 5.2b, a metade de portal do 0.4; o 6.4 com o <code>lab</code> mantido; a metade da conta (xii)",
            "24 e 25/11; depois de 19/12",
        ),
        (
            "7 · GitLab (operação)",
            "a senha do usuário local; um backup antes de 23/12; as folhas TLS até 22/09/2027",
            "26/11",
        ),
        (
            "8, 9, 10 · Pipelines, alvos, orquestração",
            "o R2 e o fechamento dos três; a conta do warehouse de Production (9)",
            "26 e 27/11; depois de 21/01",
        ),
        (
            "17 · ML no Sandbox",
            "9.6, 10.4, o pass 5 e o xxiv; o 10.5; o pass 4; 9.7, 10.6 e 9.11; o PR do 9.11",
            "22, 23, 24, 26 e 27/11",
        ),
        (
            "19 · Data product nativo",
            "o pass 5; o 5.4; o fechamento (a sua sessão 12)",
            "24 e 25/11; depois de 19/12",
        ),
        ("20 · dbt e linhagem", "o pass 5; o pass 8 (8.6 a 8.9) antes de 18/12", "24 e 26/11"),
        (
            "21 · Redshift e S3 como data products",
            "os passes 2 a 5; o fechamento",
            "25/11; depois da conta",
        ),
    ]
    rows_out = [
        (
            "11 · Proteção de dados",
            "os applies do TM-28, que encostam no 10.5; a decisão 12 (o principal filtrado); o <code>TM-17</code>; as decisões 1, 2, 5 e 9 (Macie, repositório, Malware Protection, ECR enhanced, <code>SUP-437</code>); o invocation logging do Bedrock (decisão 11); os controles de rede do Identity Center (D39)",
        ),
        (
            "12 · Observabilidade e FinOps",
            "o 2.4, um alarme de cada classe provocado, cabe em qualquer sessão com o hub; a decisão due 3; o gatilho do D12 (teto de 50 USD; 53,31 em agosto, 74,48 em setembro); 4.1, 4.2, 7.1; 8.4, os testes de RTO; 8.5, a rotação da raiz da CA",
        ),
        ("13 · Web tier público", "o nome de domínio"),
        ("14 · Vending do Sandbox", "a cota de contas e o degrau do D34"),
        ("15 · GuardDuty", "as decisões 1 a 4"),
        (
            "Adiados por você",
            "o relatório da decisão 17 (d) do Stage 19 (<code>SUP-346</code>); o <code>TM-04</code>; as exceções de git no <code>CLAUDE.md</code>; a OQ 27",
        ),
        (
            "Depois do calendário (N.5)",
            "uma segunda aplicação que consome o marcador de outra, um endpoint de <code>monitoring</code>, os eventos de dados S3 do Stage 11, um release que remove um arquivo, a 50ª versão de um workflow, uma reconciliação de blueprint",
        ),
    ]
    t1 = "".join(
        f"<tr><td>{a}</td><td>{b}</td><td style='white-space:nowrap;color:#52514e'>{c}</td></tr>"
        for a, b, c in rows_left
    )
    t2 = "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in rows_out)
    return f"""
<section class="page">
  <div class="kicker">Prazos e pendências</div>
  <h2>Prazos do plano</h2>
  {deadlines()}
  <h3>O que falta, por stage, e onde entra no cronograma</h3>
  <table class="left-table"><thead><tr><th>Stage</th><th>O que falta</th><th>Quando</th></tr></thead><tbody>{t1}</tbody></table>
  <h3 style="margin-top:3.4mm">Fora do calendário: decisões e atos só seus, sem data</h3>
  <table class="left-table"><tbody>{t2}</tbody></table>
  <p class="sub" style="margin-top:2.4mm">Stages feitos: 0, 1a a 1d, 2, 3, 4, 5a, 6a, 6b, 6c, 6g, 6i, 7, 16 e 18. Não iniciados: 13 e 15.
  O 14 está bloqueado pela cota de contas. Os demais estão em andamento.</p>
  {FOOT.format(p=5)}
</section>"""


html = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Cronograma do plano</title><style>{CSS}</style></head><body>
{page1()}{page2()}{page3()}{page4()}{page5()}
</body></html>"""
OUT.write_text(html, encoding="utf-8")
print(OUT)
