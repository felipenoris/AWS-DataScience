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
CAL_START, CAL_END = 8.0, 25.0  # 08:00 to 01:00
CAL_H = 128.0  # mm of the time grid
NOW = 22 + 20 / 60  # the revision's reading time, drawn on day 0
DAYS = ["Dom 22/11", "Seg 23/11", "Ter 24/11", "Qua 25/11"]
CAL_BLOCKS = [
    # day index, start, end, kind, title, line, stages
    (0, 10.5, 12.5, "done", "Sem ambiente", "", ["19", "20", "6f"]),
    (
        0,
        15 + 16 / 60,
        NOW,
        "done",
        "Feito hoje",
        "uma subida para o N.9 dia 3, o N.10 dia 1 e o começo do dia 2: Stage 17 C e pass 5; 5b; 6h; passes 5 dos Stages 19 e 20; passes 2 e 3 do Stage 21. O TM-28 aplicado às 21:46. O R1 rodou de madrugada",
        ["17", "5b", "6h", "19", "20", "21", "11"],
    ),
    (
        0,
        NOW,
        24.0,
        "warehouse",
        "Descida e atos",
        "",
        ["21", "6d", "17"],
    ),
    (
        1,
        9.0,
        12.5,
        "none",
        "Sem ambiente",
        "saldos, PRs, SUP-466 · 09:30 os applies do 10.5",
        ["17", "11", "5b", "9"],
    ),
    (
        1,
        13.5,
        18.5,
        "warehouse",
        "N.10 · dia 2, o resto",
        "hub + Sandbox: redshift · pass 4 e pass 5 do Stage 21, 5.4 do Stage 19, as revogações",
        ["21", "19", "6h", "20"],
    ),
    (1, 18.5, 19.5, "none", "Registros", "", ["6d"]),
    (
        2,
        9.0,
        17.25,
        "release",
        "R2 · releases",
        "hub + GitLab BUILD=1 + egress de Staging e Production com bedrock-base · app-dbt, app-ml, app-genai, app-etl",
        ["8", "9", "10", "17", "20", "7"],
    ),
    (
        3,
        9.0,
        14 + 40 / 60,
        "sandbox",
        "Sandbox · as sobras",
        "hub + Sandbox: bedrock-base · pass 4 do Stage 17, janela do 6e 6.4 e leitura 6 do 10.4, restante do 6d por último",
        ["17", "6e", "6d"],
    ),
    (
        3,
        15.0,
        17.0,
        "none",
        "PR do 9.11",
        "",
        ["17", "8", "9", "10"],
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
    for day, s, e, kind, title, line, stg in CAL_BLOCKS:
        x = rail_w + day * col_w + gap / 2
        h = (e - s) / (CAL_END - CAL_START) * CAL_H
        border, fill = HUE[kind]
        small = " small" if h < 12 or not line else ""
        done = " done" if kind == "done" else ""
        parts.append(
            f'<div class="blk{small}{done}" style="left:{x:.2f}mm;top:{y(s) + 0.3:.2f}mm;width:{col_w - gap:.2f}mm;'
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


# ---------------------------------------------------------------- page 2: tonight
TODAY = [
    # start, end, short, block text, stages, who, kind
    (
        21 + 37 / 60,
        22 + 6 / 60,
        "1",
        "<b>Feito: o pass 3 do Stage 21, a linhagem do warehouse</b>, das 21:37 às 22:06 (00:37 a 01:06 UTC, #384). O <code>lineage_reader</code>, o secret, a conexão por secret e a fonte com <i>Import data lineage</i>; o pull leu sete dias e terminou <code>PARTIALLY_SUCCEEDED</code>: <code>CREATE TABLE … AS</code>, <code>INSERT … SELECT</code> e <code>CREATE VIEW</code> viraram arestas, <code>UPDATE</code> e <code>MERGE</code> não, e o CTAS de <code>awsdatacatalog</code> falhou; o grafo não chega ao lake. O 3.5 removeu a fonte, a conexão, o usuário e o secret; os nós ficam.",
        ["21"],
        "você · Claude⚡",
        "done",
    ),
    (
        21.75,
        22 + 6 / 60,
        "A",
        "<b>Feito: o TM-28, pelo orquestrador.</b> Os três applies às 21:46 (00:46 UTC), cada um re-planejado <i>No changes</i>: o SCP do OU <code>Interactive</code> com <code>DenyAgentCoreBuiltInTools</code>, e <code>agent-registry</code> na cerca de <code>staging/studio/</code> e de <code>production/studio/</code>. A bateria <code>--phase ou</code> leu 62 esperados, 0 inesperados, 5 não medidos; a simulação, as seis ações em <code>explicitDeny</code>. O PR #385 entrou no <code>main</code> às 22:06.",
        ["11", "6d"],
        "Claude⚡",
        "done",
    ),
    (
        21.75,
        24.0,
        "B",
        "<b>Em paralelo, os subagentes.</b> Um escreve e planeja o 10.5 do Stage 17: o <code>TM-36</code>, o <code>genai.tf</code> dos dois <code>&lt;env&gt;/studio/</code>, <code>&lt;env&gt;/chains/</code>, os <code>state_read_keys</code> de <code>&lt;env&gt;/foundation/</code> e a variável de <code>staging/egress/</code>. Um plano de <code>&lt;env&gt;/studio/</code> tirado antes das 21:46 leva a cerca do TM-28 também (Lesson 69). Os applies são seus, na segunda, depois da revisão do PR. O outro abriu o PR #386: o <code>--help</code> dos scripts de <code>aws/</code>, sem chamada à AWS.",
        ["17", "11"],
        "Claude",
        "none",
    ),
    (
        NOW,
        22.5,
        "2",
        "<b>Leituras de fechamento do Stage 21.</b> <code>list-workgroups</code> só com <code>awsds-sandbox-warehouse</code>, nenhum cluster em <code>describe-clusters</code>, <code>WH-8</code> verde no <code>./aws/warehouse.py</code>: o workgroup do consumidor, removido no 2.9, fica fora do <code>make down</code> e do <code>make status</code>.",
        ["21"],
        "Claude",
        "warehouse",
    ),
    (
        22.5,
        22 + 50 / 60,
        "3",
        "<b>Descida.</b> Todo espaço parado e toda aba do portal fechada, de todas as sessões; Claude avisa as outras sessões; <code>make down ENV=sandbox</code>, <code>make hub-down</code>, <code>make status</code> e as leituras do §R. Começa no máximo às 23:40.",
        ["infra"],
        "você · Claude",
        "warehouse",
    ),
    (
        22 + 50 / 60,
        23.5,
        "4",
        "<b>Sem ambiente, os seus atos.</b> <i>Update project</i>, como dono, no <code>app-ml-dev</code>, no <code>app-genai-dev</code> e no <code>app-dbt-dev</code>, livres desde o fim do N.9 dia 3; o espaço de teste <code>jup8h</code> apagado no <code>app-etl-dev</code>. Se quiser adiantar: o PR #386 lido e a decisão do <code>SUP-466</code>.",
        ["6d", "17"],
        "você",
        "none",
    ),
    (
        23.5,
        24.0,
        "5",
        "<b>Folga</b> até o fim da sessão. O saldo do free trial do Sandbox se lê depois que fecha o último intervalo de meia hora, ou amanhã cedo.",
        ["5b"],
        "você",
        "none",
    ),
]
STRIP_START, STRIP_END = NOW, 24.0
STRIP_LABEL_W, STRIP_W = 22.0, 162.0
STRIP_TRACKS = [
    # track label, then (start, end, segment label, kind); a start before NOW is drawn from NOW
    (
        "Você e o N.10",
        [
            (NOW, 22.5, "2", "warehouse"),
            (22.5, 22 + 50 / 60, "3 · descida", "warehouse"),
            (22 + 50 / 60, 23.5, "4 · atos sem ambiente", "none"),
            (23.5, 24.0, "5 · folga", "none"),
        ],
    ),
    (
        "Subagentes",
        [(21.75, 24.0, "B · o 10.5 escrito e planejado; o --help já no PR #386", "none")],
    ),
]


def strip():
    def x(t):
        return STRIP_LABEL_W + (t - STRIP_START) / (STRIP_END - STRIP_START) * STRIP_W

    row_h, row_gap = 6.0, 1.4
    bottom = len(STRIP_TRACKS) * (row_h + row_gap) - row_gap
    parts = [f'<div class="strip" style="height:{bottom + 5.2:.1f}mm">']
    for t, lab in [(NOW, hm(NOW)), (22.5, "22:30"), (23.0, "23h"), (23.5, "23:30"), (24.0, "24h")]:
        parts.append(
            f'<div class="tline" style="left:{x(t):.2f}mm;height:{bottom + 0.8:.2f}mm"></div>'
        )
        parts.append(
            f'<div class="tick" style="left:{x(t):.2f}mm;top:{bottom + 1.2:.2f}mm">{lab}</div>'
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
MON = [
    (
        13.5,
        13 + 55 / 60,
        "",
        "<b>Subida.</b> Avisos e <code>make status</code>; você: <code>make hub-up</code>, <code>make up ENV=sandbox GROUPS=redshift</code>; <code>make status</code>. JupyterLab em <code>ml.t3.medium</code> no <code>eighth-experimentation</code> e no <code>test-experimentation</code>.",
        ["infra"],
        "você · Claude",
    ),
    (
        13 + 55 / 60,
        15 + 10 / 60,
        "",
        "<b>Stage 21, pass 4: o namespace no Glue Data Catalog.</b> 4.1 e 4.2, Claude⚡: o registro, o catálogo federado e os grants; 4.3 e 4.4, você: a leitura pelo editor e uma fonte Glue sobre o catálogo; 4.5: o transfer role e o statement da chave em <code>sandbox/data/</code> (decisão 4 (b)), Claude⚡; 4.6, você: o Athena; 4.8 na mesma sessão, o statement saindo antes do role. A 128 RPU, cada consulta do compute gerenciado custa ao menos 0,77 USD.",
        ["21"],
        "você · Claude⚡",
    ),
    (
        15 + 10 / 60,
        15 + 20 / 60,
        "",
        "<b>Leituras de fechamento.</b> <code>list-workgroups</code>, <code>describe-clusters</code> e <code>WH-8</code>: o compute gerenciado fica fora do <code>make down</code>, do <code>make status</code> e do limite de uso.",
        ["21"],
        "Claude",
    ),
    (
        15 + 20 / 60,
        17 + 20 / 60,
        "",
        "<b>Stage 21, pass 5: imagens como S3 Object Collection.</b> O prefixo publicado do espaço do <code>eighth-experimentation</code>; o produto pedido de um notebook do <code>test-experimentation</code>, aprovado, lido e revogado, com a espera de 5 minutos da revogação. Não usa o warehouse.",
        ["21"],
        "você · Claude",
    ),
    (
        17 + 20 / 60,
        18 + 5 / 60,
        "",
        "<b>Stage 19 5.4 com o item 5 do rollback do Stage 21.</b> Os grants do 5.1 revogados; a view <code>lab.trades_hot_by_desk</code> e as tabelas removidas, o <code>lab</code> mantido (6h 6.4); depois as assinaturas revogadas, a do 4.12 pelo 2.5 e a do 5.0 do Stage 20, cada uma lida dos dois lados. É o que o R2 espera.",
        ["19", "21", "6h", "20"],
        "você · Claude",
    ),
    (
        18 + 5 / 60,
        18.5,
        "",
        "<b>Descida.</b> Espaços parados e abas fechadas; <code>make down ENV=sandbox</code>, <code>make hub-down</code>, <code>make status</code>, §R. O <code>make status</code> não lê workgroups; as leituras de fechamento valem por ele.",
        ["infra"],
        "você · Claude",
    ),
    (
        18.5,
        19.5,
        "",
        "<b>Registros, sem ambiente.</b> O saldo do Sandbox depois da descida; o PR do <code>CLAUDE.md</code> do orquestrador (Current position, as chaves das Lessons 89 e 90), com o N.10 fechado; <i>Update project</i> no <code>eighth-experimentation</code> e no <code>test-experimentation</code>.",
        ["6d", "5b"],
        "você · Claude",
        "none",
    ),
]
R2 = [
    (
        8.5,
        9.0,
        "",
        "<b>Antes, sem nada no ar.</b> Claude: o <code>pip-audit</code> dos locks no laptop (Lesson 77), os avisos e <code>make status</code>. Você: o saldo do Sandbox; o 8.6, os assets do link do 5.0 e da tabela do pass 5 apagados no <code>app-dbt-dev</code> depois da execução da fonte das 23:43 de segunda.",
        ["20", "8", "5b"],
        "você · Claude",
        "none",
    ),
    (
        9.0,
        9 + 40 / 60,
        "",
        "<b>Subida.</b> Você: <code>make hub-up</code>, <code>make gitlab-up BUILD=1</code>, o túnel.",
        ["infra", "7"],
        "você · Claude",
    ),
    (
        9 + 40 / 60,
        10 + 20 / 60,
        "",
        "<b>O que o R1 deixou.</b> A entrada <code>gitlab.awsds.internal</code> do keychain apagada, se guardar a senha de antes da rotação; <code>git pull</code> e <code>git push gitlab main</code>, o mirror de onde os legs clonam os scripts do #321; o merge request da linha <code>default-v0.10.1</code> no README do <code>awsds/dev-env</code> e o seu mirror (Claude). O build runner é lido rodando antes de cada tag.",
        ["7", "8"],
        "você · Claude",
    ),
    (
        10 + 20 / 60,
        12 + 20 / 60,
        "",
        "<b><code>app-dbt</code> <code>v0.1.0</code></b> (Stage 20 8.7 a 8.9). O primeiro push, o pipeline do branch, o merge request e a tag. <code>make up ENV=staging ONLY=egress GROUPS=bedrock-base</code> antes da primeira tag, o grupo servindo aos legs do <code>app-genai</code>; <code>make up ENV=production ONLY=workloads-egress GROUPS=bedrock-base</code> antes do primeiro <code>production-gate</code>; as leituras por alvo.",
        ["20", "8", "9", "10"],
        "você · Claude",
    ),
    (
        12 + 20 / 60,
        14 + 20 / 60,
        "",
        "<b><code>app-ml</code></b> (Stage 17 9.7). O bundle leva o candidato que o <code>app-ml-dev</code> publicou por último (9.6). Claude⚡ inicia a cadeia de score de Production na sua palavra, antes e depois do seu <code>production-approve</code>.",
        ["17", "8", "10"],
        "você · Claude⚡",
    ),
    (
        14 + 20 / 60,
        16.0,
        "",
        "<b><code>app-genai</code></b> (Stage 17 10.6), se o 10.5 aplicou nos dois alvos. O pipeline não roda <code>pip-audit</code>. Claude⚡ inicia <code>awsds-prod-chain-app-genai-triage</code> na sua palavra.",
        ["17", "8", "10"],
        "você · Claude⚡",
    ),
    (
        16.0,
        16 + 40 / 60,
        "",
        "<b><code>app-etl</code></b>, o release que aposenta a metade do modelo (Stage 17 9.11), depois que o <code>app-ml</code> tem o modelo nos dois alvos; o pin do lint vai para <code>4401f91</code> (§N.12.5).",
        ["17", "8"],
        "você",
    ),
    (
        16 + 40 / 60,
        17.25,
        "",
        "<b>Descida.</b> <code>make down ENV=staging</code> depois do último leg de Staging, <code>make down ENV=production ONLY=workloads-egress</code>; antes do <code>make gitlab-down</code>, um backup à mão (<code>gitlab-backup create</code> numa sessão SSM), já que o mais novo sai do bucket em 23/12; o túnel, <code>make hub-down</code>; <code>make status</code>, §R.",
        ["infra", "7"],
        "você · Claude",
    ),
]
WED = [
    (
        9.0,
        9.5,
        "",
        "<b>Subida.</b> Avisos e <code>make status</code>; você: <code>make hub-up</code>, <code>make up ENV=sandbox GROUPS=bedrock-base</code>; <code>make status</code>. Os espaços: o <code>jup</code> do <code>eighth-experimentation</code>, e o <code>code</code>, que espera o 6d.",
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
        "<b>Stage 17 10.4, leitura 6</b>, fora da janela: o guardrail da conta pela decisão do <code>SUP-466</code>, escrito e planejado antes sem nada no ar; cada apply de <code>sandbox/bedrock/</code> é Claude⚡ na sua palavra, e as duas chaves voltam a <code>false</code> no fim.",
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
    (
        15.0,
        17.0,
        "",
        "<b>Sem ambiente, depois do R2.</b> Claude: o PR do estado do 9.11, planejado de um <code>main</code> que já tenha o release (item 11). Você: fechar os Stages 8, 9 e 10 como o Stage 4 fechou, o que espera indo para o seu gatilho (item 12).",
        ["17", "8", "9", "10"],
        "você · Claude",
        "none",
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
.warn { border-left: 1mm solid #1b1b1a; background: #f6f5f2; padding: 1.8mm 2.4mm; border-radius: 0 1.2mm 1.2mm 0; }
.footer { position: absolute; left: 13mm; right: 13mm; bottom: 6.5mm; font-size: 6.6pt; color: #8a8984;
  display: flex; justify-content: space-between; border-top: .2mm solid #ecebe6; padding-top: 1.2mm; }
.left-table td:first-child { font-weight: 700; white-space: nowrap; width: 31mm; }
.left-table td { font-size: 7.6pt; }
"""

FOOT = '<div class="footer"><span>AWS Data Science · cronograma do que falta no plano · gerado em 22/11/2026, 22:20 BRT, do main em <code>a42e4c9d</code>, com os PRs #384 e #386 abertos</span><span>{p}/5</span></div>'

LEGEND = (
    '<div class="legend">'
    + "".join(
        f'<span><span class="sw" style="background:{HUE[k][1]};border-left-color:{HUE[k][0]}"></span>{t}</span>'
        for k, t in [
            ("sandbox", "Sandbox: hub + grupos"),
            ("warehouse", "Warehouse: hub + <code>redshift</code>"),
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
  <p class="sub">Revisto às 22:20 de domingo, 22/11, com a sessão de hoje indo até 24:00 (03:00 UTC). Horários em BRT
  (UTC−3); o plano registra UTC. A ordem e os prazos são do plano (<code>promotion.md</code> §N.6 e §N.12); os horários dos
  dias seguintes partem das 09:00 por convenção deste relatório, e você pode deslocá-los.</p>
  <div class="tiles">
    <div class="tile"><div class="l">Descida de hoje</div><div class="v">22:30</div><div class="d">no máximo às 23:40</div></div>
    <div class="tile"><div class="l">Próxima subida</div><div class="v">Seg, 13:30</div><div class="d">o resto do N.10 dia 2</div></div>
    <div class="tile"><div class="l">R2</div><div class="v">Ter, 24/11</div><div class="d">app-dbt, app-ml, app-genai e app-etl</div></div>
    <div class="tile"><div class="l">Última subida</div><div class="v">Qua, 25/11</div><div class="d">as sobras do Sandbox</div></div>
    <div class="tile"><div class="l">Próximo prazo</div><div class="v">18/12</div><div class="d">dbt Core 1.11 · <code>app-dbt</code></div></div>
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
        <li>Cada subida tem a sua sessão do Claude e o seu branch; o resto do N.10 dia 2 pode seguir na sessão do #384 enquanto o PR estiver aberto.</li>
      </ul>
    </div>
    <div class="box">
      <h3>Dependências que fixam a ordem</h3>
      <ul>
        <li>O 10.5 aplica sobre o TM-28, aplicado hoje às 21:46; o apply de Staging lê primeiro a forma do guardrail da conta (<code>SUP-466</code>), e o de Production espera por ele.</li>
        <li>O R2 espera os applies do 10.5 e o fim do N.10 dia 2, cujas revogações vêm antes do 8.6 no <code>app-dbt-dev</code>.</li>
        <li>As sobras esperam a decisão do <code>SUP-466</code> para a leitura 6, não dependem do R2, e o 6d vem por último.</li>
      </ul>
    </div>
  </div>
  {FOOT.format(p=1)}
</section>"""


def page2():
    return f"""
<section class="page">
  <div class="kicker">Hoje · domingo, 22/11 · 22:20 → 24:00 (01:20 → 03:00 UTC)</div>
  <h2>O que cabe até a meia-noite: as leituras de fechamento, a descida e os seus atos</h2>
  <p class="sub">No ar desde 15:16 (18:16 UTC): o hub e o Sandbox com <code>mwaa,mlflow,bedrock-base,bedrock-agent,redshift</code>,
  a subida que o N.9 dia 3 e o N.10 dividiram. O N.10 dia 2 fez os passes 2 e 3 do Stage 21 (#384), e nada mais da lista do
  dia cabe antes do limite da descida. As trilhas correm juntas, e só a primeira usa o portal e o Sandbox.</p>
  {strip()}
  {day_table(TODAY, "none", numbered=True)}
  <div class="warn" style="margin:2.6mm 0 0">
    <b>O pass 4 do Stage 21 e o restante do 6d ficam fora da noite.</b> O pass 4 leva cerca de 75 min, com quatro applies e um
    compute gerenciado fora do <code>make down</code>; começado às 22:20, as suas leituras de fechamento terminariam às 23:45,
    depois do limite da descida. O pass 5, cerca de 2 h, vem depois dele. O 6d pede os terminais das outras sessões quietos durante o 7.5, e o seu 7.7 fecha
    todas as abas do portal; vai para quarta.
  </div>
  <div class="cols" style="margin-top:2.6mm">
    <div class="box">
      <h3>O que termina antes da descida</h3>
      <ul>
        <li>As leituras de fechamento: o workgroup do consumidor ausente, nenhum cluster, <code>WH-8</code> verde.</li>
        <li>Todo espaço parado e toda aba do portal fechada, de todas as sessões; o <code>make down</code> varre os apps que sobrarem.</li>
        <li>O subagente do 10.5 não usa o Sandbox e segue depois dela; o TM-28 terminou às 22:06.</li>
      </ul>
    </div>
    <div class="box">
      <h3>O que fica para segunda, sem cobrar parado</h3>
      <ul>
        <li>Os grants do 5.1 no Lake Formation e o <code>USAGE ON DATABASE awsdatacatalog</code> do usuário 103.</li>
        <li>A cópia <code>lab.trades_hot</code>, as tabelas do pass 2 e do 3.3, a view <code>lab.trades_hot_by_desk</code>; o produto <code>sandbox-trades-hot</code>.</li>
        <li>As assinaturas do 4.12 (<code>eighth-experimentation</code>) e do 5.0 (<code>app-dbt-dev</code>), revogadas no fim do resto do dia 2.</li>
        <li>Custo até a descida: cerca de 0,34 USD/h, mais 1,44 USD por hora de consulta do warehouse, que o free trial absorve.</li>
      </ul>
    </div>
  </div>
  {FOOT.format(p=2)}
</section>"""


def page3():
    return f"""
<section class="page">
  <div class="kicker">Segunda, 23/11 · sem ambiente de manhã, sessão warehouse à tarde</div>
  <h2>Os applies do 10.5 e o resto do N.10 dia 2</h2>
  <div class="cols" style="margin-top:2mm">
    <div class="box">
      <h3>09:00 · os seus atos <span class="chip">5b</span><span class="chip">9</span><span class="chip">17</span><span class="chip">6e</span></h3>
      <ul>
        <li><b>Saldo do free trial do Redshift em Production</b>, no dia seguinte ao R1. Console; infrastructure user; conta Production; <code>InfrastructureAccess</code>. Última leitura: 299,16 de 300,00 (22/11, depois do R1).</li>
        <li><b>Saldo em Sandbox</b>, no dia seguinte. Mesmo usuário; conta Sandbox; <code>InfrastructureAccess</code>. Última: 286,16 (22/11, depois do dia 1).</li>
        <li><b>Revisões e merges</b>: o #386 (o <code>--help</code>) e o deste cronograma; o #384 quando o dia 2 fechar. O merge é sempre seu.</li>
        <li><b>A decisão do <code>SUP-466</code></b>: como o guardrail da conta é aplicado no Sandbox (<code>ALL</code> sem os embeddings, outro mecanismo, ou nenhum). A leitura 6 de quarta espera por ela; o apply de Staging do 10.5 lê nesta manhã a forma sem lista de modelos.</li>
        <li>Opcional: o <b>alerta de orçamento</b> (6e, decisão 6; Stage 12 2.1), no console da Management, usuário AWS Control Tower Admin, <code>AWSAdministratorAccess</code>; as tentativas 1.1 e 1.2 do 6d como Data Scientist User.</li>
      </ul>
    </div>
    <div class="box">
      <h3>09:30 → ~12:30 · Stage 17 10.5 <span class="chip">17</span><span class="chip">11</span></h3>
      <ul>
        <li><b>Você</b> revisa o PR do 10.5 e aceita o resíduo do <code>TM-36</code>, ou as decisões 22 e 24 voltam à mesa.</li>
        <li><b>Claude</b>: a tag do módulo (Recipe B).</li>
        <li><b>Os applies</b>, cada um na sua palavra: <code>staging/studio/</code>, que cria o guardrail da conta e a sua configuração; a retenção <code>none</code> em <code>us-west-2</code> em Staging, ato seu no console; <code>production/studio/</code>; a retenção em Production; <code>&lt;env&gt;/chains/</code>; <code>&lt;env&gt;/foundation/</code> com o var-file de alerts.</li>
        <li><b>Claude</b>: a simulação do 10.1 na boundary aplicada e <code>./aws/deploytargets.py</code>. A variável de <code>staging/egress/</code> nasce na subida do R2.</li>
        <li>Se Staging recusar a configuração, o <code>app-genai</code> sai do R2; <code>app-dbt</code> e <code>app-ml</code> seguem.</li>
      </ul>
    </div>
  </div>
  <h3 style="margin-top:3.4mm">13:30 → ~18:30 · N.10 dia 2, o resto · sessão warehouse, e os registros até ~19:30</h3>
  <p class="sub">Os passes 4 e 5 do Stage 21, o passo 7 do Stage 19 com o item 5 do rollback, e as
  assinaturas revogadas. O plano estima cerca de 5 h. Cada <code>make up</code> cria um limite de uso novo, de 10 RPU-h no dia;
  num estouro, os passos do warehouse esperam a sua palavra, e o pass 5 segue.</p>
  {day_table(MON, "warehouse")}
  {FOOT.format(p=3)}
</section>"""


def page4():
    return f"""
<section class="page">
  <div class="kicker">Terça, 24/11 · sessão de release · 09:00 → ~17:15</div>
  <h2>R2: os primeiros releases de <code>app-dbt</code>, <code>app-ml</code> e <code>app-genai</code>, e a metade do modelo do <code>app-etl</code></h2>
  <p class="sub">Depois dos applies do 10.5 e do fim do N.10 dia 2. O plano estima de 6 a 8 h e cerca de 0,48 USD/h antes do
  egress dos alvos (mais 0,080 USD/h por egress no ar), de 4 a 6 USD no total. Cada leg leva uma hora ou mais; os atos sem leg
  cabem nas esperas.</p>
  {day_table(R2, "release")}
  <h3 style="margin-top:3.2mm">Quarta, 25/11 · sessão Sandbox, as sobras · 09:00 → ~14:40, e o PR do 9.11 à tarde</h3>
  <p class="sub">O que o N.9 dia 3 deixou, por escolha sua; não depende do R2. Cerca de 0,24 USD/h antes dos espaços, mais o
  endpoint do pass 4.</p>
  {day_table(WED, "sandbox")}
  {FOOT.format(p=4)}
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
        "o release do <code>app-dbt</code> (R2, 24/11) vem antes, ou o archive passa para o 1.12",
        ["20"],
    ),
    (
        "19/12/2026",
        "Fim do free trial do Redshift em Sandbox",
        "o resto do N.10 (23/11) vem antes; as metades de conta do 5b (x) e do 6h (xii) ficam legíveis depois",
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
            "o saldo do free trial no dia seguinte; a metade da conta (x)",
            "23/11; depois de 19/12",
        ),
        (
            "6d · Unified Studio",
            "o restante: a metade monitorada do 7.5, o 7.7, o 6.1 (viii); o <i>Update project</i> da decisão 18 em cinco projetos; as suas tentativas 1.1 e 1.2; o 6.1 (xvii)",
            "22, 23 e 25/11; sem ambiente",
        ),
        (
            "6e · Claude Code no Bedrock",
            "a janela do 6.4; o alerta de orçamento; o sucessor do Sonnet 4.5",
            "25/11; 23/11; até 08/01",
        ),
        (
            "6f · Catálogo sobre o lake",
            "o 11.12, o rollback, quando chamado",
            "sob demanda",
        ),
        (
            "6h · Conexão Redshift",
            "o <code>lab</code> mantido (6.4); x (6.1, um projeto desligado); a conta (xii)",
            "23/11; depois de 19/12",
        ),
        (
            "7 · GitLab (operação)",
            "um backup antes de 23/12, no R2; as folhas TLS até 22/09/2027",
            "24/11",
        ),
        (
            "8, 9, 10 · Pipelines, alvos, orquestração",
            "o R2 e o fechamento dos três; a conta do warehouse de Production (9)",
            "24 e 25/11; depois de 21/01",
        ),
        (
            "11 · Proteção de dados",
            "o <code>TM-36</code> do 10.5, aceito antes dos applies; o TM-28 controlado em 22/11, às 21:46",
            "23/11",
        ),
        (
            "17 · ML no Sandbox",
            "os applies do 10.5; 9.7, 10.6 e 9.11 no R2; o pass 4; a leitura 6 do 10.4; o PR do 9.11",
            "23, 24 e 25/11",
        ),
        (
            "19 · Data product nativo",
            "o passo 7 (5.4) e a revogação do 4.12; o fechamento (a sua sessão 12)",
            "23/11; depois de 19/12",
        ),
        (
            "20 · dbt e linhagem",
            "a revogação do 5.0; o pass 8 (8.6 a 8.9) no R2, antes de 18/12",
            "23 e 24/11",
        ),
        (
            "21 · Redshift e S3 como data products",
            "o pass 4, o pass 5 e o item 5 do rollback; o fechamento",
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
  {FOOT.format(p=5)}
</section>"""


html = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Cronograma do plano</title><style>{CSS}</style></head><body>
{page1()}{page2()}{page3()}{page4()}{page5()}
</body></html>"""
OUT.write_text(html, encoding="utf-8")
print(OUT)
