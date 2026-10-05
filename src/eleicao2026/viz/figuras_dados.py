#!/usr/bin/env python3
"""Gráficos da ETAPA DE COLETA: um por conjunto de dados coletado.

  d01  apuração 2026            quanto estava apurado às 20h e como isso variava pelo país
  d02  votos de 2022            mapa por UF e relação com o voto de 2026, município a município
  d03  perfil do eleitorado     como o eleitorado mudou (2002-2026) e a relação com o voto
  d04  pesquisas                as pesquisas de 1º turno contra o resultado da urna
  d05  eleições 2002-2026       todos os candidatos de cada eleição presidencial
  d06  eliminados e 2º turno    quanto voto "sobrou" e quanto cada finalista ganhou entre os turnos
  d07  pesquisas de transferência  as 6 linhas feitas à mão de que o M1 depende

Uso: python -m eleicao2026.viz.figuras_dados [--only d01 d05]
Saída: figures/pt/dNN_nome.png  (só em português)
"""
import argparse
import csv
from collections import defaultdict
from datetime import date

import matplotlib
import matplotlib.dates as mdates
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import Patch

from eleicao2026 import config as C
from eleicao2026.config import COR, LULA, FLAV, UF2REG
from eleicao2026.viz.figures import D, draw_map, footer, jload, np, plt, save

CURTO = {"JAIR BOLSONARO": "Bolsonaro", "FLAVIO BOLSONARO": "Flávio", "FERNANDO HADDAD": "Haddad",
         "GERALDO ALCKMIN": "Alckmin", "ESCRITOR AUGUSTO CURY": "Cury", "SIMONE TEBET": "Tebet",
         "CIRO GOMES": "Ciro", "CIRO": "Ciro", "HELOÍSA HELENA": "Heloísa", "AÉCIO NEVES": "Aécio",
         "JOSÉ SERRA": "Serra", "MARINA SILVA": "Marina", "RENAN SANTOS": "Renan", "RONALDO CAIADO": "Caiado",
         "ZEMA": "Zema", "GAROTINHO": "Garotinho", "DILMA": "Dilma", "LULA": "Lula",
         "CRISTOVAM BUARQUE": "Cristovam", "LUCIANA GENRO": "Luciana", "JOÃO AMOÊDO": "Amoêdo",
         "CABO DACIOLO": "Daciolo"}


def curto(nome):
    return CURTO.get(nome, nome.title().split()[-1])

T = dict(fonte="Fonte: TSE (dados abertos e apuração de 04/10/2026), Wikipédia (pesquisas); cálculos do autor.",
         fonte_pesq="Fonte: pesquisas compiladas na Wikipédia; resultado da urna: TSE.",
         fonte_transf="Fonte: Quaest e Datafolha de 02-03/10/2026, via resumos de busca (confiança média-baixa).")
COR_REG = {"Norte": "#2a9d8f", "Nordeste": "#c1272d", "Centro-Oeste": "#e9a23b", "Sudeste": "#7b5ea7",
           "Sul": "#1f5fa8", "Exterior": "#8a8a8a"}
ANOS = (2002, 2006, 2010, 2014, 2018, 2022)


# ----------------------------------------------------------------------------- dados
def rows(p):
    return list(csv.DictReader(open(p)))


def votos_cand(r):
    return {c[2:]: int(v) for c, v in r.items() if c.startswith("v_")}


def corr_pond(x, y, w):
    """Correlação ponderada (peso = votos), para não deixar cidades minúsculas mandarem."""
    x, y, w = map(np.asarray, (x, y, w))
    mx, my = np.average(x, weights=w), np.average(y, weights=w)
    c = np.average((x - mx) * (y - my), weights=w)
    return c / np.sqrt(np.average((x - mx) ** 2, weights=w) * np.average((y - my) ** 2, weights=w))


def reta_pond(x, y, w):
    x, y, w = map(np.asarray, (x, y, w))
    mx, my = np.average(x, weights=w), np.average(y, weights=w)
    b = np.average((x - mx) * (y - my), weights=w) / np.average((x - mx) ** 2, weights=w)
    return b, my - b * mx


def cand_hist():
    """pres_candidatos.csv agrupado por (ano, turno) -> lista ordenada por votos."""
    out = defaultdict(list)
    for r in rows(C.INTERIM / "pres_candidatos.csv"):
        out[(int(r["ano"]), int(r["turno"]))].append(
            dict(nome=r["candidato"], partido=r["partido"], votos=int(r["votos"]), pct=float(r["pct_validos"]),
                 sit=r["situacao"]))
    return out


# ----------------------------------------------------------------------------- d01
def d01(d):
    snap = rows(C.SNAPSHOT_85 / "mun_2026.csv")
    frac = [int(r["est"]) / int(r["te"]) for r in snap if int(r["te"]) > 0]
    uf = defaultdict(lambda: [0, 0])
    for r in snap:
        uf[r["uf"]][0] += int(r["est"])
        uf[r["uf"]][1] += int(r["te"])
    nac = sum(v[0] for v in uf.values()) / sum(v[1] for v in uf.values())
    itens = sorted(((u, v[0] / v[1]) for u, v in uf.items()), key=lambda x: x[1])

    fig, (a, b) = plt.subplots(1, 2, figsize=(13, 6), gridspec_kw=dict(width_ratios=[1, 1.15]))
    a.hist(np.array(frac) * 100, bins=np.arange(0, 105, 5), color="#555555", edgecolor="white")
    a.set_xlabel("% do eleitorado do município já apurado às ~20h")
    a.set_ylabel("número de municípios")
    a.set_title("Cada município estava num ponto diferente", loc="left", fontsize=11.5)
    sem = sum(1 for f in frac if f < 0.5)
    a.text(0.03, 0.93, f"{sem} municípios com menos de 50% apurado\n(não entram no ajuste da regressão)",
           transform=a.transAxes, va="top", fontsize=9, color="#444444")

    y = np.arange(len(itens))
    b.barh(y, [100 * v for _, v in itens], color=[COR_REG[UF2REG[u]] for u, _ in itens])
    b.set_yticks(y, [u.upper() for u, _ in itens], fontsize=8.5)
    b.axvline(100 * nac, color="black", ls="--", lw=1)
    b.text(100 * nac, len(itens) - 0.2, f" Brasil {100 * nac:.1f}%", fontsize=9, va="bottom")
    b.set_xlim(40, 103)
    b.set_xlabel("% do eleitorado apurado às ~20h")
    b.set_title("Onde a apuração estava mais atrasada às 20h", loc="left", fontsize=11.5)
    b.legend(handles=[Patch(color=cor, label=reg) for reg, cor in COR_REG.items()], frameon=False,
             loc="lower right", fontsize=9)
    fig.suptitle("Apuração 2026 às 20h: o que faltava contar não era uma amostra do país", x=0.01, ha="left",
                 fontweight="bold", fontsize=13.5)
    footer(fig, T)
    save(fig, "pt", "d01_apuracao_2026")


# ----------------------------------------------------------------------------- d02a
def d02a(d):
    r22 = {(r["uf"], r["cd"]): {c: int(v) for c, v in r.items() if c not in ("uf", "cd", "nome")}
           for r in rows(C.INTERIM / "pres_2022_mun.csv")}
    por_uf = defaultdict(lambda: [0, 0, 0])
    for (uf, _), v in r22.items():
        s = por_uf[uf]
        s[0] += v.get("LULA", 0)
        s[1] += v.get("JAIR BOLSONARO", 0)
        s[2] += sum(v.values())
    marg = {u: 100 * (s[0] - s[1]) / s[2] for u, s in por_uf.items() if u != "zz"}

    fig, a = plt.subplots(figsize=(8, 7.5))
    lim = max(abs(v) for v in marg.values())
    norm = TwoSlopeNorm(vmin=-lim, vcenter=0, vmax=lim)
    cmap = matplotlib.colormaps["RdBu"].reversed()
    draw_map(a, d.geo, marg, cmap, norm)
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=a, shrink=0.6, pad=0.01)
    cb.set_label("Margem Lula − Bolsonaro, 1º turno 2022 (p.p.)")
    a.set_title("Como cada UF votou em 2022", loc="left", fontsize=12)
    fig.suptitle("Votos de 2022", x=0.01, ha="left", fontweight="bold", fontsize=13.5)
    footer(fig, T)
    save(fig, "pt", "d02a_votos_2022_mapa")


# ----------------------------------------------------------------------------- d02b
def d02b(d):
    import matplotlib.patheffects as pe
    r22 = {(r["uf"], r["cd"]): {c: int(v) for c, v in r.items() if c not in ("uf", "cd", "nome")}
           for r in rows(C.INTERIM / "pres_2022_mun.csv")}
    capitais = ["SÃO PAULO", "RIO DE JANEIRO", "SALVADOR", "FORTALEZA", "BELO HORIZONTE", "MANAUS", "CURITIBA", "PORTO ALEGRE", "FLORIANÓPOLIS", "VITÓRIA"]
    outliers = ["FARTURA DO PIAUÍ", "NOVA PÁDUA", "SÃO CAETANO DO SUL", "ÁGUAS DE SÃO PEDRO", "BALNEÁRIO CAMBORIÚ", "NITERÓI", "SINGAPURA", "MONTREAL", "VANCOUVER"]
    caps_x, caps_y, caps_n = [], [], []
    xs, ys, ws, cs = [], [], [], []
    for r in rows(C.INTERIM / "mun_2026.csv"):
        p = perf.get((r["uf"], r["cd"]))
        vv = int(r["vv"])
        if not p or vv < 200 or int(p["tot"]) == 0:
            continue
        px = 100 * int(p["sup"]) / int(p["tot"])
        py = 100 * int(r["v_LULA"]) / vv
        xs.append(px)
        ys.append(py)
        ws.append(vv)
        cs.append(COR_REG.get(UF2REG.get(r["uf"].lower()), "#444444"))
        
        nm = r["nome"]
        if nm in capitais or nm in outliers:
            caps_x.append(px)
            caps_y.append(py)
            label = nm.title()
            if r["uf"] == "zz":
                label = f"{label} (Ext.)"
            caps_n.append(label)

    xs, ys, ws = np.array(xs), np.array(ys), np.array(ws)
    rr = corr_pond(xs, ys, ws)
    bb, aa = reta_pond(xs, ys, ws)

    fig, b = plt.subplots(figsize=(9, 8))
    b.scatter(xs, ys, s=np.sqrt(ws) / 5, alpha=0.55, color=cs, edgecolor="none")
    
    g = np.array([0, 100])
    b.plot(g, g, color="#888888", ls="--", lw=1.5)
    b.plot(g, aa + bb * g, color="#c1272d", lw=2.5)

    for cx, cy, cn in zip(caps_x, caps_y, caps_n):
        txt = b.annotate(cn, (cx, cy), xytext=(4, -4), textcoords="offset points", fontsize=9.5, color="#111111", weight="bold")
        txt.set_path_effects([pe.withStroke(linewidth=2.5, foreground="white")])

    b.set_xlim(0, 100)
    b.set_ylim(0, 100)
    b.set_xlabel("% de Lula no município em 2022 (1º turno)", fontsize=11)
    b.set_ylabel("% de Lula no município em 2026 (1º turno)", fontsize=11)
    b.set_title("Onde o PT foi bem em 2022, continuou bem em 2026", loc="left", fontsize=12)

    cx_box = dict(facecolor='white', alpha=0.85, edgecolor='none', pad=3)
    b.text(0.03, 0.96, f"Cada bolinha = 1 município (tamanho = total de votos)\nCorrelação r = {rr:.2f}\n"\
           f"Reta vermelha: tendência real (cada +10% em 2022 → +{10 * bb:.1f}% em 2026)".replace(".", ","),
           transform=b.transAxes, va="top", fontsize=10, bbox=cx_box)

    b.text(85, 78, "Linha tracejada cinza:\nse a votação de 2026\nfosse idêntica à de 2022", color="#666666", fontsize=9, ha="right", va="bottom", bbox=cx_box)
    handles = [Patch(color=c, label=n) for n, c in COR_REG.items() if n != "Exterior"]
    b.legend(handles=handles, frameon=True, fontsize=10, loc="lower right", title="Região", facecolor="white", framealpha=0.9, edgecolor="none")

    fig.suptitle("Votos de 2022: o melhor ponto de partida para prever 2026", x=0.01, ha="left", fontweight="bold", fontsize=14)
    footer(fig, T)
    save(fig, "pt", "d02b_votos_2022_dispersao")




# ----------------------------------------------------------------------------- d03a
def d03a(d):
    anos = [2002, 2006, 2010, 2014, 2018, 2022, 2026]
    serie = defaultdict(list)
    for a in anos:
        r = rows(C.INTERIM / f"perfil_{a}_mun.csv")
        tot = sum(int(x["tot"]) for x in r)
        for k in ("fem", "sup", "analf", "fund_inc", "jovem", "idoso"):
            s = sum(int(x[k]) for x in r)
            serie[k].append(100 * s / tot if (s > 0) else np.nan)
    rot = dict(fem="Mulheres", sup="Superior completo", analf="Analfabetos / lê e escreve",
               fund_inc="Fundamental incompleto", jovem="16-24 anos", idoso="60+ anos")
    cor = dict(fem="#8a8a8a", sup="#2a9d8f", analf="#c1272d", fund_inc="#e9a23b", jovem="#1f5fa8", idoso="#7b5ea7")

    fig, a = plt.subplots(figsize=(8, 6))
    for k in ("fem", "sup", "analf", "fund_inc", "jovem", "idoso"):
        a.plot(anos, serie[k], marker="o", color=cor[k], lw=2, label=rot[k])
        ult = [(x, y) for x, y in zip(anos, serie[k]) if not np.isnan(y)][-1]
        dy = {"jovem": 1.2, "idoso": -1.2}.get(k, 0)
        a.text(ult[0] + 0.4, ult[1] + dy, f"{ult[1]:.0f}%", va="center", fontsize=9, color=cor[k])
    a.set_xticks(anos)
    a.set_xlim(2001, 2029)
    a.set_ylabel("% do eleitorado")
    a.legend(frameon=False, fontsize=9, loc="center left", bbox_to_anchor=(1.05, 0.5))
    a.set_title("O eleitorado mudou muito em 24 anos", loc="left", fontsize=12)
    a.text(0.99, 0.02, "faixa etária não informada pelo TSE em 2002 e 2006", transform=a.transAxes, ha="right",
           fontsize=8, color="#888888")
    fig.subplots_adjust(right=0.75)
    footer(fig, T)
    save(fig, "pt", "d03a_perfil_tempo")


# ----------------------------------------------------------------------------- d03b
def d03b(d):
    perf = {(r["uf"], r["cd"]): r for r in rows(C.INTERIM / "perfil_2026_mun.csv")}
    xs, ys, ws, cs = [], [], [], []
    capitais = ["SÃO PAULO", "RIO DE JANEIRO", "SALVADOR", "FORTALEZA", "BELO HORIZONTE", "MANAUS", "CURITIBA", "PORTO ALEGRE", "FLORIANÓPOLIS", "VITÓRIA"]
    outliers = ["FARTURA DO PIAUÍ", "NOVA PÁDUA", "SÃO CAETANO DO SUL", "ÁGUAS DE SÃO PEDRO", "BALNEÁRIO CAMBORIÚ", "NITERÓI", "SINGAPURA", "MONTREAL", "VANCOUVER"]
    caps_x, caps_y, caps_n = [], [], []
    xs, ys, ws, cs = [], [], [], []
    for r in rows(C.INTERIM / "mun_2026.csv"):
        p = perf.get((r["uf"], r["cd"]))
        vv = int(r["vv"])
        if not p or vv < 200 or int(p["tot"]) == 0:
            continue
        px = 100 * int(p["sup"]) / int(p["tot"])
        py = 100 * int(r["v_LULA"]) / vv
        xs.append(px)
        ys.append(py)
        ws.append(vv)
        cs.append(COR_REG.get(UF2REG.get(r["uf"].lower()), "#444444"))
        
        nm = r["nome"]
        if nm in capitais or nm in outliers:
            caps_x.append(px)
            caps_y.append(py)
            label = nm.title()
            if r["uf"] == "zz":
                label = f"{label} (Ext.)"
            caps_n.append(label)
    xs, ys, ws = np.array(xs), np.array(ys), np.array(ws)
    rr = corr_pond(xs, ys, ws)

    fig, b = plt.subplots(figsize=(8, 6))
    b.scatter(xs, ys, s=np.sqrt(ws) / 6, alpha=0.4, color=cs, edgecolor="none")
    bb, aa = reta_pond(xs, ys, ws)
    g = np.array([0, xs.max()])
    b.plot(g, aa + bb * g, color="black", lw=1.6, ls="--")
    for cx, cy, cn in zip(caps_x, caps_y, caps_n):
        b.annotate(cn, (cx, cy), xytext=(4, -4), textcoords="offset points", fontsize=8, color="#222222")
    b.set_ylim(0, 100)
    b.legend(handles=[Patch(color=c, label=n) for n, c in COR_REG.items() if n != "Exterior"], frameon=False,
             fontsize=9, loc="upper right", ncol=2)
    b.set_xlabel("% do eleitorado com superior completo (2026)")
    b.set_ylabel("% de Lula no município (1º turno 2026)")
    b.set_title("Escolaridade e voto, município a município", loc="left", fontsize=12)
    b.text(0.97, 0.04, f"r = {rr:.2f} (ponderada por votos)\nassociação, não causa: escolaridade e região\nandam juntas, então a reta mistura as duas", transform=b.transAxes, va="bottom", ha="right", fontsize=9)
    footer(fig, T)
    save(fig, "pt", "d03b_perfil_voto")



# ----------------------------------------------------------------------------- d04
def d04(d):
    polls = rows(C.INTERIM / "pesquisas_1turno.csv")
    L, F, dt, nomes = [], [], [], []
    for r in polls:
        tot = sum(float(r[k] or 0) for k in ("lula", "flavio", "caiado", "zema", "santos", "cury", "outros"))
        L.append(100 * float(r["lula"]) / tot)
        F.append(100 * float(r["flavio"]) / tot)
        dt.append(date.fromisoformat(r["data_fim"]))
        nomes.append(r["pollster"])
    vv = d.meta["votos_validos"]
    rl, rf = 100 * d.meta["votos_candidatos"][LULA] / vv, 100 * d.meta["votos_candidatos"][FLAV] / vv

    fig, (a, b) = plt.subplots(1, 2, figsize=(13, 5.6), gridspec_kw=dict(width_ratios=[1.6, 1]))
    a.scatter(dt, F, color=COR["flavio"], alpha=0.65, s=28, label="Flávio (pesquisas)")
    a.scatter(dt, L, color=COR["lula"], alpha=0.65, s=28, label="Lula (pesquisas)")
    
    # Add institute names as tiny text labels
    for x, y_l, y_f, n in zip(dt, L, F, nomes):
        a.annotate(n, (x, y_l), xytext=(4, 0), textcoords="offset points", fontsize=6, color="#555555", va="center")
        a.annotate(n, (x, y_f), xytext=(4, 0), textcoords="offset points", fontsize=6, color="#555555", va="center")
    a.axhline(rf, color=COR["flavio"], ls="--", lw=1.4)
    a.axhline(rl, color=COR["lula"], ls="--", lw=1.4)
    a.text(min(dt), rf + 0.25, f"urna: Flávio {rf:.1f}%", color=COR["flavio"], fontsize=9, va="bottom")
    a.text(min(dt), rl - 0.25, f"urna: Lula {rl:.1f}%", color=COR["lula"], fontsize=9, va="top")
    a.set_ylabel("% dos votos válidos (pesquisa reescalada sem indecisos)")
    a.legend(frameon=False, loc="lower right", fontsize=9)
    a.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    a.tick_params(axis="x", rotation=30)
    a.set_title(f"{len(polls)} pesquisas de 1º turno coletadas (set-out/2026)", loc="left", fontsize=11.5)

    cont = defaultdict(int)
    for n in nomes:
        cont[n] += 1
    it = sorted(cont.items(), key=lambda x: x[1])
    y = np.arange(len(it))
    b.barh(y, [v for _, v in it], color="#555555")
    b.set_yticks(y, [n for n, _ in it])
    for yi, (_, v) in zip(y, it):
        b.text(v + 0.1, yi, str(v), va="center", fontsize=9)
    fig.subplots_adjust(wspace=0.3)
    b.set_xlabel("pesquisas por instituto")
    b.set_title("Quem publicou", loc="left", fontsize=11.5)
    fig.suptitle("Pesquisas: o que cada instituto dizia antes da urna", x=0.01, ha="left", fontweight="bold",
                 fontsize=13.5)
    footer(fig, T, "fonte_pesq")
    save(fig, "pt", "d04_pesquisas")


# ----------------------------------------------------------------------------- d05
def _cor_partido(nome, partido):
    if partido == "PT":
        return COR["lula"]
    if nome in ("JAIR BOLSONARO", "FLAVIO BOLSONARO") or partido in ("PL", "PSL"):
        return COR["flavio"]
    if partido == "PSDB":
        return "#7fb2e5"
    return None


def d05(d):
    h = cand_hist()
    linhas = []
    for a in ANOS:
        linhas.append((str(a), [(c["nome"], c["partido"], c["pct"]) for c in h[(a, 1)]]))
    vv = d.meta["votos_validos"]
    c26 = sorted(d.meta["votos_candidatos"].items(), key=lambda x: -x[1])
    part = {LULA: "PT", FLAV: "PL"}
    linhas.append(("2026", [(k, part.get(k, ""), 100 * v / vv) for k, v in c26]))

    cinzas = ["#9a9a9a", "#b5b5b5", "#848484", "#c9c9c9"]
    fig, ax = plt.subplots(figsize=(13, 6.2))
    for yi, (ano, cs) in enumerate(linhas[::-1]):
        esq = 0
        i = 0
        for nome, partido, pct in cs:
            cor = _cor_partido(nome, partido)
            if cor is None:
                cor = cinzas[i % len(cinzas)]
                i += 1
            ax.barh(yi, pct, left=esq, color=cor, edgecolor="white", linewidth=0.8)
            if pct >= 2.8:
                rot = curto(nome)
                ax.text(esq + pct / 2, yi, f"{rot}\n{pct:.1f}%", ha="center", va="center", fontsize=8,
                        color="white" if cor in (COR["lula"], COR["flavio"]) else "#222222")
            esq += pct
    ax.set_yticks(range(len(linhas)), [a for a, _ in linhas[::-1]])
    ax.set_xlim(0, 100)
    ax.set_xlabel("% dos votos válidos no 1º turno (cada candidato é um bloco; sem rótulo = menos de 2,8%, ex.: Renan e Caiado, 2,2% cada, em 2026)")
    ax.grid(False)
    ax.set_title("Todos os candidatos de cada eleição presidencial: o tamanho do 'resto' muda muito", loc="left")
    footer(fig, T)
    save(fig, "pt", "d05_candidatos_2002_2026")


# ----------------------------------------------------------------------------- d06
def d06(d):
    h = cand_hist()
    dados = []
    for a in ANOS:
        t1 = {c["nome"]: c for c in h[(a, 1)]}
        t2 = h[(a, 2)]
        tot1 = sum(c["votos"] for c in t1.values())
        fin = [c for c in t2[:2]]
        pool = tot1 - sum(t1[c["nome"]]["votos"] for c in fin)
        ganhos = []
        for c in fin:
            ganhos.append((c["nome"], c["votos"] - t1[c["nome"]]["votos"], c["sit"].startswith("ELEITO")))
        dados.append((a, pool, ganhos))
    pool26 = d.meta["votos_validos"] - d.meta["votos_candidatos"][LULA] - d.meta["votos_candidatos"][FLAV]

    fig, ax = plt.subplots(figsize=(13, 6.4))
    x = np.arange(len(dados) + 1)
    larg = 0.27
    ax.bar(x[:-1] - larg, [p / 1e6 for _, p, _ in dados], larg, color="#9a9a9a", label="votos dos eliminados no 1º turno")
    ax.bar(x[-1] - larg, pool26 / 1e6, larg, color="#9a9a9a", hatch="//", edgecolor="white")
    ax.text(x[-1] - larg, pool26 / 1e6 + 0.2, f"{pool26 / 1e6:.1f}", ha="center", fontsize=8.5)
    for i, (a, pool, g) in enumerate(dados):
        venc, perd = g[0], g[1]  # pres_candidatos vem ordenado por votos; 'situação' é vazia em 2006 e 2010
        ax.bar(i, venc[1] / 1e6, larg, color="#2a9d8f", label="ganho do vencedor (2º turno − 1º turno)" if i == 0 else None)
        ax.bar(i + larg, perd[1] / 1e6, larg, color="#e9a23b", label="ganho do derrotado" if i == 0 else None)
        ax.text(i, venc[1] / 1e6 + 0.2, f"{venc[1] / 1e6:.1f}\n{curto(venc[0])}", ha="center", fontsize=7.5)
        ax.text(i + larg, perd[1] / 1e6 + 0.2, f"{perd[1] / 1e6:.1f}\n{curto(perd[0])}", ha="center", fontsize=7.5)
        ax.text(i - larg, pool / 1e6 + 0.2, f"{pool / 1e6:.1f}", ha="center", fontsize=8.5)
    ax.set_xticks(x, [str(a) for a, _, _ in dados] + ["2026"])
    ax.set_ylim(-4, 34)
    ax.set_xlim(-0.6, len(dados) + 0.9)
    ax.text(x[-1] + 0.5, 6.3, "2º turno: a\ndescobrir", ha="center", fontsize=9, color="#666666")
    ax.set_ylabel("milhões de votos")
    ax.legend(frameon=False, loc="upper left", fontsize=9, ncol=3)
    ax.set_title("Quanto voto 'sobra' dos eliminados e quanto cada finalista ganhou entre os turnos", loc="left")
    ax.set_xlabel("ganho = votos no 2º turno − votos no 1º turno (líquido; não diz de quem vieram). "
                  "Pode superar o 'resto' porque o comparecimento muda entre os turnos.", fontsize=8.5)
    footer(fig, T)
    save(fig, "pt", "d06_eliminados_e_ganhos")


# ----------------------------------------------------------------------------- d07
def d07(d):
    r = rows(C.EXTERNAL / "transferencia_pesquisas.csv")
    nomes = {"RENAN SANTOS": "Renan Santos", "RONALDO CAIADO": "Ronaldo Caiado", "ESCRITOR AUGUSTO CURY": "Augusto Cury",
             "ZEMA": "Romeu Zema", "AGREGADO(ZEMA+CAIADO+RENAN+CURY)": "Agregado dos quatro"}
    r = sorted(r, key=lambda x: (x["instituto"], -float(x["flavio"])))
    fig, ax = plt.subplots(figsize=(11, 4.8))
    y = np.arange(len(r))[::-1]
    for yi, x in zip(y, r):
        f, l = float(x["flavio"]), float(x["lula"])
        resto = 100 - f - l
        ax.barh(yi, f, color=COR["flavio"])
        ax.barh(yi, l, left=f, color=COR["lula"])
        ax.barh(yi, resto, left=f + l, color="#d4d4d4")
        ax.text(f / 2, yi, f"{f:.0f}", ha="center", va="center", color="white", fontsize=9)
        ax.text(f + l / 2, yi, f"{l:.0f}", ha="center", va="center", color="white", fontsize=9)
        ax.text(f + l + resto / 2, yi, f"{resto:.0f}", ha="center", va="center", fontsize=8.5, color="#444444")
    ax.set_yticks(y, [f"{nomes.get(x['eleitor_de'], x['eleitor_de'])}  ·  {x['instituto']}" for x in r])
    ax.set_xlim(0, 100)
    ax.set_xlabel("% dos eleitores desse candidato  (azul = Flávio, vermelho = Lula, cinza = branco/nulo/indeciso)")
    ax.grid(False)
    ax.set_title("As 6 linhas feitas à mão de que o M1 depende: Quaest e Datafolha divergem", loc="left")
    footer(fig, T, "fonte_transf")
    save(fig, "pt", "d07_pesquisas_transferencia")


FIGS = dict(d01=d01, d02a=d02a, d02b=d02b, d03a=d03a, d03b=d03b,  d04=d04, d05=d05, d06=d06, d07=d07)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None, help="ex.: d01 d05")
    a = ap.parse_args()
    d = D()
    for k, fn in FIGS.items():
        if a.only and k not in a.only:
            continue
        fn(d)
    d03a(d)
    d03b(d)


if __name__ == "__main__":
    main()
