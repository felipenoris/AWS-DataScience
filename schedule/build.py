"""Builds the A4 schedule report as HTML; Chrome headless prints it to PDF."""

from pathlib import Path

OUT = Path(__file__).parent / "out" / "report.html"
OUT.parent.mkdir(exist_ok=True)

HUE = {
    "sandbox": ("#2a78d6", "rgba(42,120,214,.13)"),
    "warehouse": ("#eb6834", "rgba(235,104,52,.14)"),
    "release": ("#1baf7a", "rgba(27,175,122,.16)"),
    "none": ("#9a9893", "rgba(154,152,147,.17)"),
    "done": ("#cfcdc6", "rgba(154,152,147,.07)"),
}


def chips(stages):
    return "".join(f'<span class="chip">{s}</span>' for s in stages)


def hm(t):
    if t == 24.0:
        return "24:00"
    h = int(t) % 24
    m = round((t - int(t)) * 60)
    return f"{h:02d}:{m:02d}"


# ---------------------------------------------------------------- page 1: calendar
CAL_START, CAL_END = 8.0, 24.0  # 08:00 to 24:00
CAL_H = 128.0  # mm of the time grid
NOW = 13 + 5 / 60  # the revision's reading time, drawn on day 0
DAYS = ["Seg 23/11", "Ter 24/11", "Qua 25/11"]
CAL_BLOCKS = [
    # day index, start, end, kind, title, line, stages[, lane, lanes]
    (
        0,
        9.0,
        12 + 57 / 60,
        "done",
        "Feito, sem ambiente",
        "o 10.5 aplicado nos dois alvos; os saldos lidos; o TM-36 aceito; os PRs #384 e #386 a #391 no main",
        ["17", "11", "5b", "9"],
    ),
    (
        0,
        12 + 57 / 60,
        14.0,
        "none",
        "Preparação",
        "",
        [],
    ),
    (
        0,
        14.0,
        17 + 10 / 60,
        "sandbox",
        "N.10 · o resto",
        "Sandbox sem grupos · pass 5 do Stage 21 e o rollback; o portal pelo Chrome",
        ["21"],
        0,
        2,
    ),
    (0, 17 + 10 / 60, 18.0, "none", "Registros", "", [], 0, 2),
    (
        0,
        14.0,
        22.25,
        "release",
        "R2 · releases",
        "hub + GitLab BUILD=1 + egress dos alvos com bedrock-base · app-dbt, app-ml, app-genai, app-etl · desce o hub por último",
        ["8", "9", "10", "17", "20", "7"],
        1,
        2,
    ),
    (
        1,
        9.0,
        10.5,
        "none",
        "Seus atos e o SUP-466",
        "",
        ["5b", "6d", "17"],
    ),
    (
        1,
        10.5,
        13.0,
        "none",
        "PR do 9.11 e registros",
        "o estado do 9.11; o CLAUDE.md; 8, 9 e 10 fechados",
        ["17", "8", "9", "10"],
    ),
    (
        2,
        9.0,
        14 + 40 / 60,
        "sandbox",
        "Sandbox · as sobras",
        "hub + Sandbox: bedrock-base, mwaa · pass 4 do Stage 17, janela do 6e 6.4 e leitura 6 do 10.4, restante do 6d por último",
        ["17", "6e", "6d"],
    ),
]


def calendar():
    rail_w, head_h, gap = 9.0, 7.0, 1.6
    total_w = 184.0
    col_w = (total_w - rail_w) / len(DAYS)

    def y(t):
        return head_h + (t - CAL_START) / (CAL_END - CAL_START) * CAL_H

    parts = [f'<div class="cal" style="height:{CAL_H + head_h + 1}mm">']
    # hour lines and labels
    for h in range(int(CAL_START), int(CAL_END) + 1, 1):
        strong = " strong" if h % 2 == 0 else ""
        parts.append(f'<div class="hline{strong}" style="top:{y(h):.2f}mm;left:{rail_w}mm"></div>')
        if h % 2 == 0 or h == int(CAL_END):
            parts.append(f'<div class="hlabel" style="top:{y(h) - 1.6:.2f}mm">{h % 24:02d}h</div>')
    for i, d in enumerate(DAYS):
        x = rail_w + i * col_w
        parts.append(f'<div class="colhead" style="left:{x:.2f}mm;width:{col_w:.2f}mm">{d}</div>')
        if i:
            parts.append(
                f'<div class="vline" style="left:{x:.2f}mm;top:{head_h}mm;height:{CAL_H}mm"></div>'
            )
    for blk in CAL_BLOCKS:
        day, s, e, kind, title, line, stg = blk[:7]
        lane, lanes = blk[7:9] if len(blk) > 7 else (0, 1)
        lane_w = col_w / lanes
        x = rail_w + day * col_w + lane * lane_w + gap / 2
        h = (e - s) / (CAL_END - CAL_START) * CAL_H
        border, fill = HUE[kind]
        small = " small" if h < 12 or not line else ""
        done = " done" if kind == "done" else ""
        parts.append(
            f'<div class="blk{small}{done}" style="left:{x:.2f}mm;top:{y(s) + 0.3:.2f}mm;width:{lane_w - gap:.2f}mm;'
            f'height:{h - 0.6:.2f}mm;background:{fill};border-left-color:{border}">'
            f'<div class="bt">{title}</div><div class="bh">{hm(s)}–{hm(e)}</div>'
            + ("" if small else f'<div class="bl">{line}</div>')
            + f'<div class="bc">{chips(stg)}</div></div>'
        )
    # the revision's reading time on day 0
    parts.append(
        f'<div class="nowmark" style="left:{rail_w:.2f}mm;width:{col_w:.2f}mm;top:{y(NOW):.2f}mm"></div>'
        f'<div class="nowlab" style="left:{rail_w + col_w - 13:.2f}mm;top:{y(NOW) - 3.1:.2f}mm">agora {hm(NOW)}</div>'
    )
    parts.append("</div>")
    return "\n".join(parts)


# ---------------------------------------------------------------- page 2: this afternoon
LIMIT = 23 + 43 / 60  # app-dbt-dev's daily source run, 02:43 UTC: app-dbt's tag comes before it
STRIP_START, STRIP_END = 14.0, 24.0
STRIP_LABEL_W, STRIP_W = 22.0, 162.0
STRIP_TICKS = [
    (14.0, "14h"),
    (16.0, "16h"),
    (18.0, "18h"),
    (20.0, "20h"),
    (22.0, "22h"),
    (24.0, "24h"),
]
STRIP_TRACKS = [
    # track label, then (start, end, segment label, kind)
    (
        "Hub",
        [(14.0, 22.25, "um comando seu sobe tudo às 14:00; o hub desce por último", "release")],
    ),
    (
        "N.10 · Sandbox",
        [
            (14.0, 14 + 25 / 60, "↑", "sandbox"),
            (14 + 25 / 60, 16.5, "pass 5 · 5.1 a 5.7", "sandbox"),
            (16.5, 16 + 50 / 60, "rb", "sandbox"),
            (16 + 50 / 60, 17 + 10 / 60, "↓", "sandbox"),
            (17 + 10 / 60, 18.0, "registros", "none"),
        ],
    ),
    (
        "R2 · GitLab",
        [
            (14.0, 14 + 40 / 60, "↑", "release"),
            (14 + 40 / 60, 15 + 20 / 60, "R1", "release"),
            (15 + 20 / 60, 17 + 20 / 60, "app-dbt v0.1.0", "release"),
            (17 + 20 / 60, 19 + 20 / 60, "app-ml", "release"),
            (19 + 20 / 60, 21.0, "app-genai", "release"),
            (21.0, 21 + 40 / 60, "app-etl", "release"),
            (21 + 40 / 60, 22.25, "↓", "release"),
        ],
    ),
]


def strip():
    def x(t):
        return STRIP_LABEL_W + (t - STRIP_START) / (STRIP_END - STRIP_START) * STRIP_W

    row_h, row_gap = 6.0, 1.4
    bottom = len(STRIP_TRACKS) * (row_h + row_gap) - row_gap
    parts = [f'<div class="strip" style="height:{bottom + 5.2:.1f}mm">']
    ticks = [(t, lab, "") for t, lab in STRIP_TICKS] + [(LIMIT, f"fonte {hm(LIMIT)}", " lim")]
    for t, lab, cls in ticks:
        parts.append(
            f'<div class="tline{cls}" style="left:{x(t):.2f}mm;height:{bottom + 0.8:.2f}mm"></div>'
        )
        parts.append(
            f'<div class="tick{cls}" style="left:{x(t):.2f}mm;top:{bottom + 1.2:.2f}mm">{lab}</div>'
        )
    for i, (label, segs) in enumerate(STRIP_TRACKS):
        top = i * (row_h + row_gap)
        parts.append(f'<div class="trk" style="top:{top:.2f}mm">{label}</div>')
        for s, e, text, kind in segs:
            s = max(s, STRIP_START)
            border, fill = HUE[kind]
            parts.append(
                f'<div class="seg" style="top:{top:.2f}mm;left:{x(s) + 0.25:.2f}mm;width:{x(e) - x(s) - 0.5:.2f}mm;'
                f'background:linear-gradient({fill},{fill}),#fff;border-left-color:{border}"><span>{text}</span></div>'
            )
    parts.append("</div>")
    return "\n".join(parts)


def day_table(rows, kind, numbered=False):
    out = ['<table class="sched"><thead><tr>']
    if numbered:
        out.append("<th class='n'>#</th>")
    out.append("<th>Horário</th><th>Bloco</th><th>Stages</th><th>Quem</th></tr></thead><tbody>")
    for r in rows:
        s, e, short, text, stg, who = r[:6]
        b = HUE[r[6] if len(r) > 6 else kind][0]
        when = s if isinstance(s, str) else f"{hm(s)}–{hm(e)}"  # a string start is the cell itself
        out.append("<tr>")
        if numbered:
            out.append(f'<td class="n" style="border-left:1mm solid {b}">{short}</td>')
            out.append(f'<td class="t">{when}</td>')
        else:
            out.append(f'<td class="t" style="border-left:1mm solid {b}">{when}</td>')
        out.append(
            f'<td>{text}</td><td class="stg">{chips(stg)}</td><td class="who">{who}</td></tr>'
        )
    out.append("</tbody></table>")
    return "".join(out)


N10 = [
    (
        14.0,
        14 + 25 / 60,
        "",
        "<b>Subida, pelo seu comando</b> (a linha do R2 abaixo): o Sandbox sem grupos, porque o pass 5 não usa o warehouse; <code>make status</code>. JupyterLab em <code>ml.t3.medium</code> no <code>eighth-experimentation</code> e no <code>test-experimentation</code>, pelo Chrome.",
        ["infra", "21"],
        "você · Claude⚡",
    ),
    (
        14 + 25 / 60,
        16.5,
        "",
        "<b>Stage 21, pass 5: imagens como S3 Object Collection (5.1 a 5.7).</b> As imagens do gerador do 1.4 em <code>shared/stage21-images/</code> e a tabela <code>stage21_images</code>; o prefixo publicado (5.2); o asset da tabela e o produto dos dois (5.3); o pedido do <code>test-experimentation</code> aprovado só leitura (5.4) e lido do portal e de um notebook com <code>s3control get-data-access</code> (5.5); uma segunda aprovação, leitura e escrita (5.6); a revogação com credenciais emitidas antes, lida em cinco minutos (5.7). No Chrome, como Data Scientist, cada ato na sua palavra.",
        ["21"],
        "Claude⚡ · você",
    ),
    (
        16.5,
        16 + 50 / 60,
        "",
        "<b>O rollback do pass 5.</b> A listagem retirada e o produto apagado; os arquivos de <code>shared/stage21-images/</code> e a tabela <code>stage21_images</code>.",
        ["21"],
        "Claude⚡ · você",
    ),
    (
        16 + 50 / 60,
        17 + 10 / 60,
        "",
        "<b>Descida do Sandbox.</b> Espaços parados e abas do portal fechadas; <code>make down ENV=sandbox</code>; <code>make status</code> lendo o Sandbox em zero; o aviso à sessão do R2, que desce o hub no fim.",
        ["infra"],
        "você · Claude",
    ),
    (
        17 + 10 / 60,
        18.0,
        "",
        "<b>Registros, sem ambiente.</b> O log e o Status do Stage 21; o §6 do pass 5: <code>catalog.md</code>, <code>SMUS.md</code>, <code>GOVERNANCE.md</code>, <code>./aws/catalog.py</code>, os <code>SUP</code> e a entrada do threat model; o PR.",
        ["21", "11"],
        "Claude",
        "none",
    ),
]
R2 = [
    (
        14.0,
        14 + 40 / 60,
        "",
        "<b>Subida, um comando seu</b>: <code>./aws/login.py</code>, <code>make hub-up</code>, <code>make up ENV=sandbox</code>, <code>make gitlab-up BUILD=1</code>, os egress de Staging e de Production com <code>GROUPS=bedrock-base</code>, <code>make status</code>; depois o túnel. O build runner é lido rodando antes de cada tag.",
        ["infra", "7"],
        "você · Claude",
    ),
    (
        14 + 40 / 60,
        15 + 20 / 60,
        "",
        "<b>O que o R1 deixou.</b> A entrada <code>gitlab.awsds.internal</code> do keychain apagada, se guardar a senha de antes da rotação; <code>git pull</code> e <code>git push gitlab main</code> na pasta do projeto, o mirror de onde os legs clonam os scripts do #321; o merge request da linha <code>default-v0.10.1</code> no README do <code>awsds/dev-env</code> e o seu mirror (Claude).",
        ["7", "8"],
        "você · Claude",
    ),
    (
        15 + 20 / 60,
        17 + 20 / 60,
        "",
        "<b><code>app-dbt</code> <code>v0.1.0</code></b> (Stage 20 8.6 a 8.9). O 8.6, o asset da tabela do pass 5 do Stage 20 apagado no <code>app-dbt-dev</code>; o <code>pip-audit</code> e a leitura do 2.4; o primeiro push, o pipeline do <code>main</code> e a tag, antes das 23:43. Os egress dos alvos no ar desde a subida; as leituras por alvo.",
        ["20", "8", "9", "10"],
        "você · Claude",
    ),
    (
        17 + 20 / 60,
        19 + 20 / 60,
        "",
        "<b><code>app-ml</code></b> (Stage 17 9.7). O bundle leva o candidato que o <code>app-ml-dev</code> publicou por último (9.6); o <code>pip-audit</code> antes da tag. Claude⚡ inicia a cadeia de score de Production na sua palavra, antes e depois do seu <code>production-approve</code>.",
        ["17", "8", "10"],
        "você · Claude⚡",
    ),
    (
        19 + 20 / 60,
        21.0,
        "",
        "<b><code>app-genai</code></b> (Stage 17 10.6), sobre o 10.5 aplicado nos dois alvos. O pipeline não roda <code>pip-audit</code>. Claude⚡ inicia <code>awsds-prod-chain-app-genai-triage</code> na sua palavra.",
        ["17", "8", "10"],
        "você · Claude⚡",
    ),
    (
        21.0,
        21 + 40 / 60,
        "",
        "<b><code>app-etl</code></b>, o release que aposenta a metade do modelo (Stage 17 9.11), com o pin do lint em <code>4401f91</code>; o seu leg de Staging é o último. Depois de cada leg, a primeira metade do lxiv e o xxvi do Stage 8.",
        ["17", "8"],
        "você · Claude",
    ),
    (
        21 + 40 / 60,
        22.25,
        "",
        "<b>Descida, por último.</b> <code>make down ENV=staging</code>, <code>make down ENV=production ONLY=workloads-egress</code>; um backup à mão (<code>gitlab-backup create</code> numa sessão SSM), lido no bucket; <code>make gitlab-down</code>, o túnel; <code>make hub-down</code> depois de o Sandbox ler zero; <code>make status</code>, §R.",
        ["infra", "7"],
        "você · Claude",
    ),
]

# ---------------------------------------------------------------- page 3: Tuesday and Wednesday
TUE = [
    (
        9.0,
        9.5,
        "",
        "<b>Os seus atos, sem ambiente.</b> O saldo do free trial do Sandbox no dia seguinte ao N.10; o de Production não muda, nenhum warehouse de Production sobe hoje. <i>Update project</i>, como dono, no <code>test-experimentation</code>, no <code>app-dbt-dev</code>, no <code>app-ml-dev</code>, no <code>app-genai-dev</code> e no <code>eighth-experimentation</code> (<code>SUP-380</code>), com o R2 terminado.",
        ["5b", "6d"],
        "você",
    ),
    (
        9.5,
        10.5,
        "",
        "<b>A decisão do <code>SUP-466</code></b>: como o guardrail da conta é aplicado no Sandbox (<code>ALL</code> sem os embeddings, outro mecanismo, ou nenhum). Com ela, a mudança de <code>sandbox/bedrock/</code> escrita, planejada e mesclada sem nada no ar; sem ela, a leitura 6 de quarta fica fora da sessão.",
        ["17"],
        "você · Claude",
    ),
    (
        10.5,
        13.0,
        "",
        "<b>Registros, sem ambiente.</b> Claude: o PR do estado do 9.11, planejado de um <code>main</code> que já tenha o release (item 11); o PR do <code>CLAUDE.md</code> do orquestrador, com o N.10 e o R2 fechados. Você: os merges, e fechar os Stages 8, 9 e 10 como o Stage 4 fechou, o que espera indo para o seu gatilho (item 12).",
        ["17", "8", "9", "10"],
        "você · Claude",
    ),
]
WED = [
    (
        9.0,
        9.5,
        "",
        "<b>Subida.</b> Avisos e <code>make status</code>; você: <code>make hub-up</code>, <code>make up ENV=sandbox GROUPS=bedrock-base,mwaa</code>; <code>make status</code>. Os espaços: o <code>jup</code> do <code>eighth-experimentation</code>, e o <code>code</code>, que espera o 6d.",
        ["infra"],
        "você · Claude",
    ),
    (
        9.5,
        11.5,
        "",
        "<b>Stage 17, pass 4 (4.1 a 4.6).</b> O endpoint pelo SDK, que fica no ar depois da sessão (decisão 6; 0,115 USD/h, fora do <code>make status</code> e do <code>make down</code>), o formulário do portal, o batch transform e os negativos de serverless e GPU.",
        ["17"],
        "você · Claude",
    ),
    (
        11.5,
        12.5,
        "",
        "<b>6e 6.4, a janela.</b> Uma sessão do Claude Code num espaço, no modelo padrão, uma tarefa longa em vários turnos e nenhuma outra chamada ao Bedrock na conta. Claude marca início e fim em UTC e lê <code>./aws/bedrock-usage.py</code> depois do atraso de publicação; o volume vai para o teto da decisão due 2 do Stage 12.",
        ["6e", "12"],
        "você · Claude",
    ),
    (
        12.5,
        12 + 50 / 60,
        "",
        "<b>Stage 17 10.4, leitura 6</b>, fora da janela: o guardrail da conta pela decisão do <code>SUP-466</code>, escrito e planejado antes sem nada no ar; cada apply de <code>sandbox/bedrock/</code> é Claude⚡ na sua palavra, e as duas chaves voltam a <code>false</code> no fim. Os dois workflows da leitura usam o grupo <code>mwaa</code>.",
        ["17"],
        "você · Claude⚡",
    ),
    (
        12 + 50 / 60,
        14 + 5 / 60,
        "",
        "<b>Restante do 6d</b> no espaço <code>code</code>, depois do último apply, com os espaços do Stage 17 parados: a metade monitorada do 7.5 pelo deep link (cerca de 20 min, todo shell em <code>proxy-on</code>, os terminais das outras sessões quietos); o 7.7 depois do logout do portal, lido aos 5 e aos 30 minutos; Claude lê o 6.1 (viii) no flow log durante a espera.",
        ["6d"],
        "você · Claude",
    ),
    (
        14 + 5 / 60,
        14 + 40 / 60,
        "",
        "<b>Fechamento e descida.</b> <code>./aws/sandbox-ml.py</code> e <code>./aws/catalog.py</code>; espaços parados e abas fechadas (o passo 12 do 6d); <code>make down ENV=sandbox</code>, <code>make hub-down</code>, <code>make status</code>, §R. O endpoint do pass 4 segue cobrando 2,76 USD por dia até ser apagado.",
        ["infra", "17", "6d"],
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
.cal .nowlab { position: absolute; font-size: 6.2pt; font-weight: 700; color: #1b1b1a; background: #fff;
  padding: 0 .6mm; white-space: nowrap; }
.cal .blk { position: absolute; box-sizing: border-box; border-radius: 1.1mm; padding: 1.1mm 1.2mm .6mm 1.3mm;
  border-left: 1mm solid; overflow: hidden; }
.cal .bt { font-weight: 700; font-size: 7.6pt; line-height: 1.2; }
.cal .bh { font-size: 6.6pt; color: #52514e; margin: .2mm 0 .5mm; }
.cal .bl { font-size: 6.5pt; color: #3a3936; line-height: 1.25; margin-bottom: .5mm; }
.cal .blk.small .bt { font-size: 6.8pt; display: inline; }
.cal .blk.small .bh { display: inline; margin-left: 1mm; white-space: nowrap; }
.cal .blk.small .bc { display: inline; margin-left: 1mm; }
.cal .blk.done { color: #6b6a66; border-left-style: dashed; }
.cal .blk.done .bl, .cal .blk.done .bh { color: #8a8984; }
.cal .blk.done .chip { color: #8a8984; border-color: #dedcd5; background: #fbfaf8; }
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
.strip { position: relative; height: 26mm; margin: 2.8mm 0 1mm; }
.strip .trk { position: absolute; left: 0; width: 21mm; height: 6mm; line-height: 6mm; font-size: 6.6pt;
  font-weight: 650; color: #3a3936; white-space: nowrap; }
.strip .seg { position: absolute; height: 6mm; border-radius: .9mm; box-sizing: border-box; border-left: .8mm solid;
  display: flex; align-items: center; padding: 0 1.2mm; font-size: 6.4pt; font-weight: 700; color: #1b1b1a;
  white-space: nowrap; overflow: hidden; }
.strip .tick { position: absolute; font-size: 6.2pt; color: #8a8984; transform: translateX(-50%); }
.strip .tline { position: absolute; top: 0; border-left: .18mm solid rgba(0,0,0,.18); }
.strip .tline.lim { border-left: .35mm dashed #1b1b1a; }
.strip .tick.lim { color: #1b1b1a; font-weight: 700; }
.warn { border-left: 1mm solid #1b1b1a; background: #f6f5f2; padding: 1.8mm 2.4mm; border-radius: 0 1.2mm 1.2mm 0; }
.footer { position: absolute; left: 13mm; right: 13mm; bottom: 6.5mm; font-size: 6.6pt; color: #8a8984;
  display: flex; justify-content: space-between; border-top: .2mm solid #ecebe6; padding-top: 1.2mm; }
.left-table td:first-child { font-weight: 700; white-space: nowrap; width: 31mm; }
.left-table td { font-size: 7.6pt; }
"""

FOOT = '<div class="footer"><span>AWS Data Science · cronograma do que falta no plano · gerado em 23/11/2026, 13:05 BRT, do main em <code>684ec8b1</code>, com as sessões do N.10 e do R2 abertas</span><span>{p}/4</span></div>'

LEGEND = (
    '<div class="legend">'
    + "".join(
        f'<span><span class="sw" style="background:{HUE[k][1]};border-left-color:{HUE[k][0]}"></span>{t}</span>'
        for k, t in [
            ("sandbox", "Sandbox: hub + grupos"),
            ("release", "Release: hub + GitLab + egress dos alvos"),
            ("none", "Sem ambiente: custo zero"),
            ("done", "Feito"),
        ]
    )
    + '<span><span class="chip">17</span> o stage tratado no bloco</span></div>'
)


def page1():
    return f"""
<section class="page">
  <div class="kicker">AWS Data Science · planejamento da execução</div>
  <h1>Cronograma do que falta no plano</h1>
  <p class="sub">Revisto às 13:05 de segunda, 23/11, com o ambiente fora do ar (<code>make status</code> 0,0000 USD/h às
  12:56). Horários em BRT (UTC−3); o plano registra UTC. A ordem e os prazos são do plano (<code>promotion.md</code> §N.6 e
  §N.12). O resto do N.10 e o R2 rodam em paralelo hoje à tarde, numa subida só do hub, por escolha sua; as sobras do
  Sandbox ficam na quarta, como estavam. Os horários dos dias seguintes partem das 09:00 por convenção deste relatório,
  e você pode deslocá-los.</p>
  <div class="tiles">
    <div class="tile"><div class="l">Subida de hoje</div><div class="v">14:00</div><div class="d">um comando seu para as duas sessões</div></div>
    <div class="tile"><div class="l">N.10, o resto</div><div class="v">~17:10</div><div class="d">o pass 5 do Stage 21 e o rollback</div></div>
    <div class="tile"><div class="l">R2</div><div class="v">~22:15</div><div class="d">app-dbt, app-ml, app-genai e app-etl</div></div>
    <div class="tile"><div class="l">Última subida</div><div class="v">Qua, 25/11</div><div class="d">as sobras do Sandbox</div></div>
    <div class="tile"><div class="l">Próximo prazo</div><div class="v">18/12</div><div class="d">dbt Core 1.11 · o R2 de hoje o cumpre</div></div>
  </div>
  <h2>A semana</h2>
  {LEGEND}
  {calendar()}
  <div class="cols" style="margin-top:2.5mm">
    <div class="box">
      <h3>Regras de cada sessão com ambiente</h3>
      <ul>
        <li>Começa na sua palavra, porque é medida; cada sessão avisa as outras do laptop antes de qualquer write.</li>
        <li><b>Claude⚡</b> é um write que Claude executa na sua palavra, nomeando o ato, no chat da sessão que o executa.</li>
        <li>Você sobe tudo às 14:00 com um comando só, em série; o hub desce por último, depois de o Sandbox ler zero.</li>
        <li>O Chrome logado como Data Scientist é só da sessão do N.10; o GitLab e qualquer login de persona vão para outro perfil de navegador.</li>
        <li>Termina em custo zero: abas do portal fechadas, <code>make down</code>, <code>make hub-down</code>, <code>make status</code>, §R.</li>
      </ul>
    </div>
    <div class="box">
      <h3>Dependências que fixam a ordem</h3>
      <ul>
        <li>O R2 esperava os applies do 10.5 e a revogação da assinatura do 5.0 do Stage 20: a revogação às 23:20 de domingo, os applies nesta manhã.</li>
        <li>O N.10 e o R2 não esperam um pelo outro: o 8.6 apaga no <code>app-dbt-dev</code> o asset da tabela do pass 5 do Stage 20, e o pass 5 de hoje é o do Stage 21.</li>
        <li>A tag do <code>app-dbt</code> sai depois do 8.6 e antes da execução da fonte do <code>app-dbt-dev</code>, às 23:43.</li>
        <li>As sobras esperam a decisão do <code>SUP-466</code> para a leitura 6, não dependem do R2, e o 6d vem por último.</li>
      </ul>
    </div>
  </div>
  {FOOT.format(p=1)}
</section>"""


def page2():
    return f"""
<section class="page">
  <div class="kicker">Hoje · segunda, 23/11 · 14:00 → ~22:15 (17:00 → ~01:15 UTC)</div>
  <h2>Duas sessões em paralelo sobre uma subida do hub: o resto do N.10 e o R2</h2>
  <p class="sub">Você sobe tudo às 14:00 com um comando só, em série: o hub, o Sandbox, o GitLab com o build runner e
  os dois egress dos alvos; o hub desce por último, depois de o Sandbox ler zero. Os atos de portal do pass 5 são da sessão do
  N.10, no Chrome logado como Data Scientist, cada um na sua palavra; os do R2 no GitLab são seus, entre os legs, num outro
  perfil de navegador, porque um login como outro usuário do Identity Center no perfil do Chrome encerra a sessão do Data
  Scientist no portal.</p>
  {strip()}
  <h3>N.10, o resto · sessão Sandbox, sem warehouse · 14:00 → ~17:10, e os registros até ~18:00</h3>
  {day_table(N10, "sandbox")}
  <h3>R2 · sessão de release · 14:00 → ~22:15</h3>
  {day_table(R2, "release")}
  {FOOT.format(p=2)}
</section>"""


def page3():
    return f"""
<section class="page">
  <div class="kicker">Hoje de manhã, terça e quarta</div>
  <div class="box" style="margin-top:1.6mm">
    <h3>Feito hoje de manhã, sem ambiente <span class="chip">17</span><span class="chip">11</span><span class="chip">5b</span><span class="chip">9</span><span class="chip">21</span></h3>
    <ul>
      <li><b>O 10.5 aplicado nos dois alvos</b>, a partir das 09:50: a retenção <code>none</code> em <code>us-west-2</code>, os slices <code>studio/</code>, <code>chains/</code> e <code>foundation/</code> de Staging e de Production (#391). O <code>TM-36</code> aceito (#389).</li>
      <li><b>Os saldos do free trial</b>, às 12:05: Sandbox 282,94 de 300,00, depois do dia 2 do N.10; Production 299,16, no dia seguinte ao R1.</li>
      <li><b>O registro do dia 2 do N.10</b> (#384) e <b>a preparação do R2</b> (#390): os pins do <code>app-ml</code> e do <code>app-genai</code> em <code>4401f91</code>, a metade de aplicação do 9.11, os comandos dos primeiros pushes.</li>
      <li><b>Sem nada no ar</b>: o produto do pass 2 do Stage 21 apagado; o 6.5 do Stage 21 lido do free trial; o 9.5a e o xxiii do Stage 9.</li>
    </ul>
  </div>
  <h3 style="margin-top:3.4mm">Terça, 24/11 · sem ambiente</h3>
  <p class="sub">Nada sobe: o R2 de hoje leva o que estava na terça, e o PR do 9.11 vem da quarta para cá.</p>
  {day_table(TUE, "none")}
  <h3 style="margin-top:3.4mm">Quarta, 25/11 · sessão Sandbox, as sobras · 09:00 → ~14:40</h3>
  <p class="sub">O que o N.9 dia 3 deixou, por escolha sua; não depende do R2. Cerca de 0,24 USD/h antes dos espaços, mais o
  endpoint do pass 4. A subida leva <code>mwaa</code> com <code>bedrock-base</code>, para os dois workflows da leitura 6
  (§N.12.2).</p>
  {day_table(WED, "sandbox")}
  {FOOT.format(p=3)}
</section>"""


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
        "o release do <code>app-dbt</code> (R2, hoje) vem antes, ou o archive passa para o 1.12",
        ["20"],
    ),
    (
        "19/12/2026",
        "Fim do free trial do Redshift em Sandbox",
        "o N.10 usou o warehouse em 22 e 23/11; as metades de conta do 5b (x) e do 6h (xii) ficam legíveis depois",
        ["5b", "6h", "19", "21"],
    ),
    (
        "23/12/2026",
        "O backup mais novo do GitLab sai do bucket",
        "o backup à mão no fim do R2 de hoje, perto de 01:00 UTC de 24/11, leva o prazo a 25/12",
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


def page4():
    rows_left = [
        (
            "5b · Redshift Serverless",
            "o saldo do free trial no dia seguinte; a metade da conta (x)",
            "24/11; depois de 19/12",
        ),
        (
            "6d · Unified Studio",
            "o restante: a metade monitorada do 7.5, o 7.7, o 6.1 (viii); o <i>Update project</i> da decisão 18 em cinco projetos; as suas tentativas 1.1 e 1.2; o 6.1 (xvii)",
            "24 e 25/11; sem ambiente",
        ),
        (
            "6e · Claude Code no Bedrock",
            "a janela do 6.4; o alerta de orçamento; o sucessor do Sonnet 4.5",
            "25/11; sem data; até 08/01",
        ),
        (
            "6f · Catálogo sobre o lake",
            "o 11.12, o rollback, quando chamado",
            "sob demanda",
        ),
        (
            "6h · Conexão Redshift",
            "x (6.1, um projeto desligado); a conta (xii)",
            "depois de 19/12",
        ),
        (
            "7 · GitLab (operação)",
            "um backup à mão no R2 de hoje; as folhas TLS até 22/09/2027",
            "23/11",
        ),
        (
            "8, 9, 10 · Pipelines, alvos, orquestração",
            "o R2 e o fechamento dos três; a conta do warehouse de Production (9)",
            "23 e 24/11; depois de 21/01",
        ),
        (
            "17 · ML no Sandbox",
            "9.7, 10.6 e 9.11 no R2 de hoje; o PR do 9.11; o pass 4 e a leitura 6 do 10.4",
            "23, 24 e 25/11",
        ),
        (
            "19 · Data product nativo",
            "o xiv, a view sobre um schema externo, numa sessão com o warehouse; o fechamento (a sua sessão 12)",
            "sem data; depois de 19/12",
        ),
        (
            "20 · dbt e linhagem",
            "o pass 8 (8.6 a 8.9) no R2 de hoje, antes de 18/12",
            "23/11",
        ),
        (
            "21 · Redshift e S3 como data products",
            "o pass 5 e o seu rollback hoje; o 6.5 por serviço; o fechamento",
            "23/11; depois da conta",
        ),
    ]
    rows_out = [
        (
            "11 · Proteção de dados",
            "a decisão 12 (o principal filtrado); o <code>TM-17</code>; as decisões 1, 2, 5 e 9 (Macie, repositório, Malware Protection, ECR enhanced, <code>SUP-437</code>); o invocation logging do Bedrock (decisão 11); os controles de rede do Identity Center (D39)",
        ),
        (
            "12 · Observabilidade e FinOps",
            "o 2.4, as provocações dos alarmes, em qualquer sessão com o hub; a decisão due 3; o gatilho do D12 (teto de 50 USD; 53,31 em agosto, 74,48 em setembro); 4.1, 4.2, 7.1; 8.4, os testes de RTO; 8.5, a raiz da CA rotacionada",
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
  {FOOT.format(p=4)}
</section>"""


html = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Cronograma do plano</title><style>{CSS}</style></head><body>
{page1()}{page2()}{page3()}{page4()}
</body></html>"""
OUT.write_text(html, encoding="utf-8")
print(OUT)
