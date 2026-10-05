#!/usr/bin/env python3
"""Gera todas as figuras do artigo (PT e EN) a partir de data/processed e data/interim.

Uso: python -m eleicao2026.viz.figures [--lang pt en] [--only 03 09]
Saída: figures/<lang>/NN_nome.png
"""
import argparse
import csv
import json
import math
import sys
from datetime import date

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.collections import PatchCollection  # noqa: E402
from matplotlib.colors import TwoSlopeNorm  # noqa: E402
from matplotlib.patches import Polygon as MplPolygon  # noqa: E402

from eleicao2026 import config as C  # noqa: E402
from eleicao2026.config import COR, UFN  # noqa: E402

# ----------------------------------------------------------------------------- textos (i18n)
T = {
    "pt": dict(
        fonte="Fonte: TSE (apuração 04/10/2026, 23h, 99,99% das seções); cálculos do autor.",
        fonte_mod="Fonte: TSE, pesquisas (Wikipédia/institutos); modelo do autor — github.com/berndof/eleicao-2026",
        f1_title="1º turno 2026: Flávio Bolsonaro e Lula vão ao 2º turno",
        f1_x="% dos votos válidos", f1_out="Outros",
        f2_title="A projeção feita com 85% apurado acertou o resultado final?",
        f2_x="% dos votos válidos", f2_part="Parcial (85% apurado)", f2_proj="Projeção do modelo (85%)",
        f2_fin="Resultado final (99,99%)",
        f3_title="Erro por UF na margem Lula − Flávio: projeção × parcial sem projeção",
        f3_x="Erro na margem (pontos percentuais): estimado − final\n(positivo = favorecia Lula)",
        f3_part="Parcial (85% apurado)", f3_proj="Projeção do modelo",
        f4_title="1º turno: margem Lula − Flávio por UF", f4_cb="Margem (p.p. dos votos válidos)\n← Flávio    Lula →",
        f5_title="Pesquisas de 1º turno erraram a favor de Lula (última pesquisa de cada instituto)",
        f5_x="Erro na margem Lula − Flávio, em p.p. de votos válidos (pesquisa − urna)", f5_mean="média",
        f6_title="Pesquisas de 2º turno: Lula × Flávio (votos válidos entre os dois)",
        f6_y="Lula, % dos votos válidos entre os dois", f6_avg="média móvel (7 dias, ponderada)",
        f6_vline="1º turno (04/10)", f6_note="Cada ponto é uma pesquisa; as posteriores a 04/10 ainda não existem.",
        f7_title="Para onde vão os eleitores dos eliminados", f7_votes="Votos válidos no 1º turno (milhões)",
        f7_split="% do voto declarado que vai a Flávio", f7_2022="2022: eliminados → Bolsonaro",
        f7_mean="média ponderada 2026", f7_sup="suposição (sem pesquisa)",
        f8_title="Histórico: quanto o líder do 1º turno ganha no 2º?",
        f8_x="Líder entre os dois no 1º turno (% dos votos dos dois)", f8_y="Líder no 2º turno (% dos válidos)",
        f8_2026="Flávio 2026 (previsão)", f8_fit="regressão (β = {b:.2f})",
        f9_title="Probabilidade de Lula vencer o 2º turno: três métodos e o ensemble",
        f9_x="% de Lula nos votos válidos do 2º turno", f9_y="densidade de simulações",
        f9_win="Lula vence ({p:.0f}%)", f9_lose="Flávio vence ({p:.0f}%)", f9_ens="Ensemble",
        M1="M1 estrutural", M2="M2 pesquisas corrigidas", M3="M3 histórico",
        f10_title="O resultado depende de quanto peso damos a cada método", f10_x="Probabilidade de Lula vencer (%)",
        f11_title="O que mais move o resultado (M1 e M2)", f11_x="Variação na % média de Lula, em p.p. (terço baixo → terço alto de cada parâmetro)",
        f12_title="2º turno (previsão): % de Lula por UF", f12_cb="Lula, % dos votos válidos\n← Flávio    Lula →",
        f13_title="Previsão por UF: mediana e intervalo de 90%", f13_x="Lula, % dos votos válidos do 2º turno",
        f13_swing="IC cruza 50% (UF disputada)", f13_safe="IC não cruza 50%",
        f14_title="M1: cenários determinísticos", f14_x="% de Lula nos votos válidos do 2º turno",
        f15_title="Margem de votos no 2º turno (Lula − Flávio)", f15_x="Margem (milhões de votos)",
        f15_lula="Lula na frente", f15_flavio="Flávio na frente",
        winner_l="Lula", winner_f="Flávio",
        rot=dict(sp="SP", ),
    ),
    "en": dict(
        fonte="Source: TSE (count on 04 Oct 2026, 11pm, 99.99% of polling stations); author's calculations.",
        fonte_mod="Source: TSE, polls (Wikipedia/pollsters); author's model — github.com/berndof/eleicao-2026",
        f1_title="2026 first round: Flávio Bolsonaro and Lula go to the runoff",
        f1_x="% of valid votes", f1_out="Others",
        f2_title="Did the projection made at 85% counted get the final result right?",
        f2_x="% of valid votes", f2_part="Partial count (85%)", f2_proj="Model projection (at 85%)",
        f2_fin="Final result (99.99%)",
        f3_title="State-level error in the Lula − Flávio margin: projection vs. raw partial count",
        f3_x="Margin error (percentage points): estimate − final\n(positive = overstated Lula)",
        f3_part="Partial count (85%)", f3_proj="Model projection",
        f4_title="First round: Lula − Flávio margin by state", f4_cb="Margin (pp of valid votes)\n← Flávio    Lula →",
        f5_title="First-round polls erred in Lula's favor (each pollster's last poll)",
        f5_x="Error in the Lula − Flávio margin, pp of valid votes (poll − ballot box)", f5_mean="mean",
        f6_title="Runoff polls: Lula vs. Flávio (share of the two-candidate vote)",
        f6_y="Lula, % of the two-candidate vote", f6_avg="rolling average (7 days, weighted)",
        f6_vline="First round (Oct 4)", f6_note="Each dot is a poll; polls after Oct 4 do not exist yet.",
        f7_title="Where the eliminated candidates' voters go", f7_votes="Valid votes in the first round (millions)",
        f7_split="% of declared vote going to Flávio", f7_2022="2022: eliminated → Bolsonaro",
        f7_mean="2026 weighted mean", f7_sup="assumption (no poll)",
        f8_title="History: how much does the first-round leader gain in the runoff?",
        f8_x="Leader among the two in round 1 (% of their combined votes)", f8_y="Leader in round 2 (% of valid votes)",
        f8_2026="Flávio 2026 (forecast)", f8_fit="regression (β = {b:.2f})",
        f9_title="Probability that Lula wins the runoff: three methods and the ensemble",
        f9_x="Lula's share of valid runoff votes (%)", f9_y="simulation density",
        f9_win="Lula wins ({p:.0f}%)", f9_lose="Flávio wins ({p:.0f}%)", f9_ens="Ensemble",
        M1="M1 structural", M2="M2 adjusted polls", M3="M3 historical",
        f10_title="The result depends on how much weight each method gets", f10_x="Probability that Lula wins (%)",
        f11_title="What moves the result the most (M1 and M2)", f11_x="Change in mean Lula share, pp (lowest third → highest third of each parameter)",
        f12_title="Runoff (forecast): Lula's share by state", f12_cb="Lula, % of valid votes\n← Flávio    Lula →",
        f13_title="Forecast by state: median and 90% interval", f13_x="Lula, % of valid runoff votes",
        f13_swing="CI crosses 50% (battleground)", f13_safe="CI does not cross 50%",
        f14_title="M1: deterministic scenarios", f14_x="Lula's share of valid runoff votes (%)",
        f15_title="Vote margin in the runoff (Lula − Flávio)", f15_x="Margin (millions of votes)",
        f15_lula="Lula ahead", f15_flavio="Flávio ahead",
        winner_l="Lula", winner_f="Flávio",
        rot=dict(),
    ),
}
SCEN_EN = {
    "M1 base (assimetria 0,5; comparecimento 2022)": "M1 base (asymmetry 0.5; 2022 turnout)",
    "M1: comparecimento dos eliminados = pesquisa literal": "M1: eliminated voters' turnout = poll as stated",
    "M1: bases mantêm 100% (sem mobilização pró-Bolsonaro de 2022)": "M1: bases keep 100% (no 2022 pro-Bolsonaro mobilization)",
    "M1: mobilização de 2022 se repete por inteiro": "M1: 2022 mobilization repeats in full",
    "M1: eliminados 50/50": "M1: eliminated split 50/50",
    "M1: eliminados como em 2022 (48% Bolsonaro)": "M1: eliminated split as in 2022 (48% Bolsonaro)",
    "M1: eliminados 10 pp mais pró-Flávio": "M1: eliminated 10 pp more pro-Flávio",
    "M1: eliminados 10 pp mais pró-Lula": "M1: eliminated 10 pp more pro-Lula",
    "M1: sem inclinação regional": "M1: no regional tilt",
    "M1: todos os eliminados votam em Lula (limite)": "M1: all eliminated vote for Lula (bound)",
}
TORN_EN = {
    "Mobilização de 2022 se repete (0 → 1)": "2022 mobilization repeats (0 → 1)",
    "Comparecimento dos eliminados (pesquisa → 2022)": "Eliminated voters' turnout (poll → 2022)",
    "Inclinação comum das pesquisas de transferência (± logit)": "Common tilt of transfer polls (± logit)",
    "Choque nacional na margem (±1,5 pp)": "National margin shock (±1.5 pp)",
    "M2: quanto do viés do 1º turno persiste (0 → 1)": "M2: how much first-round poll bias persists (0 → 1)",
}
SENS_EN = {
    "Ensemble (base)": "Ensemble (base)", "Só M1 (estrutural)": "M1 only (structural)",
    "Só M2 (pesquisas corrigidas)": "M2 only (adjusted polls)", "Só M3 (histórico)": "M3 only (historical)",
    "Pesos iguais": "Equal weights", "Mais peso nas pesquisas (M2 60%)": "More weight on polls (M2 60%)",
    "Mais peso no estrutural (M1 70%)": "More weight on structural (M1 70%)",
}
CAND_NOME = {"FLAVIO BOLSONARO": "Flávio Bolsonaro", "LULA": "Lula", "RONALDO CAIADO": "Ronaldo Caiado",
             "ESCRITOR AUGUSTO CURY": "Augusto Cury", "RENAN SANTOS": "Renan Santos", "ZEMA": "Romeu Zema",
             "SAMARA": "Samara", "CLARIANA BARAO": "Clariana Barão", "HERTZ DIAS": "Hertz Dias",
             "EDMILSON COSTA": "Edmilson Costa", "VETERINÁRIO WILSON GRASSI": "Wilson Grassi",
             "RUI COSTA PIMENTA": "Rui Costa Pimenta"}

plt.rcParams.update({
    "font.size": 10.5, "axes.spines.top": False, "axes.spines.right": False, "axes.titleweight": "bold",
    "axes.titlesize": 13, "figure.dpi": 100, "savefig.dpi": 170, "savefig.bbox": "tight",
    "axes.grid": True, "grid.alpha": 0.25, "axes.axisbelow": True, "font.family": "DejaVu Sans",
})


# ----------------------------------------------------------------------------- dados
def jload(p):
    return json.loads(open(p).read())


def csv_rows(p):
    return list(csv.DictReader(open(p)))


class D:
    """Carrega uma vez os dados usados pelas figuras."""
    def __init__(self):
        self.res = jload(C.PROCESSED / "resumo_2turno.json")
        self.bt = jload(C.PROCESSED / "backtest_1turno.json")
        self.meta = jload(C.PROCESSED / "apuracao_meta.json")
        self.bt_uf = csv_rows(C.PROCESSED / "backtest_1turno_uf.csv")
        self.uf1 = {r["uf"]: r for r in csv_rows(C.PROCESSED / "resultado_1turno_uf.csv")}
        self.tab_uf = {r["uf"]: r for r in csv_rows(C.PROCESSED / "tabela_uf_2turno.csv")}
        self.polls2 = csv_rows(C.INTERIM / "pesquisas_2turno.csv")
        self._sims = None
        self.geo = jload(C.EXTERNAL / "ufs_ibge.geojson")

    @property
    def sims(self):
        if self._sims is None:
            rows = csv_rows(C.PROCESSED / "sims_2turno.csv")
            self._sims = dict(
                comp=np.array([r["componente"] for r in rows]),
                w=np.array([float(r["peso"]) for r in rows]),
                lula=np.array([float(r["lula_pct"]) for r in rows]) * 100,
                margem=np.array([float(r["margem_votos"]) for r in rows]) / 1e6)
        return self._sims


def footer(fig, t, key="fonte"):
    fig.text(0.01, -0.02, t[key], fontsize=8, color="#666666", ha="left", va="top")


def save(fig, lang, name):
    out = C.FIGURES / lang
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{name}.png")
    plt.close(fig)
    print("ok", lang, name, file=sys.stderr)


# ----------------------------------------------------------------------------- mapa
UF_CODE = {v: k for k, v in C.UF_IBGE.items()}


def _rings(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    return geom["coordinates"]


def _area(ring):
    r = np.array(ring)
    return abs((r[:-1, 0] * r[1:, 1] - r[1:, 0] * r[:-1, 1]).sum()) / 2


def _centroid(poly):
    ring = np.array(poly[0])
    x, y = ring[:, 0], ring[:, 1]
    a = x[:-1] * y[1:] - x[1:] * y[:-1]
    A = a.sum() / 2
    if abs(A) < 1e-12:
        return x.mean(), y.mean()
    cx = ((x[:-1] + x[1:]) * a).sum() / (6 * A)
    cy = ((y[:-1] + y[1:]) * a).sum() / (6 * A)
    return cx, cy


def draw_map(ax, geo, values, cmap, norm, labels=True, label_fs=7.5):
    patches, colors = [], []
    cents = {}
    for ft in geo["features"]:
        uf = UF_CODE[int(ft["properties"]["codarea"])]
        polys = _rings(ft["geometry"])
        big = max(polys, key=lambda p: _area(p[0]))
        cents[uf] = _centroid(big)
        for p in polys:
            patches.append(MplPolygon(np.array(p[0]), closed=True))
            colors.append(cmap(norm(values[uf])))
    pc = PatchCollection(patches, facecolor=colors, edgecolor="white", linewidth=0.8)
    ax.add_collection(pc)
    ax.set_xlim(-74.5, -33.5)
    ax.set_ylim(-34.5, 5.8)
    ax.set_aspect(1.05)
    ax.axis("off")
    ax.grid(False)
    if labels:
        off = {"go": (-1.6, 0.9), "df": (1.9, -1.1), "se": (1.4, -0.8), "al": (1.9, -0.2), "pe": (0.6, -0.3),
               "rn": (0.9, 0.3), "pb": (1.0, 0.0)}
        for uf, (x, y) in cents.items():
            dx, dy = off.get(uf, (0, 0))
            v = norm(values[uf])
            dark = abs(v - 0.5) > 0.32 and uf not in off
            ax.text(x + dx, y + dy, uf.upper(), ha="center", va="center", fontsize=label_fs, fontweight="bold",
                    color="white" if dark else "#222222")
    return pc


# ----------------------------------------------------------------------------- figuras
def fig01(d, t, lang):
    votes = d.meta["votos_candidatos"]
    vv = d.meta["votos_validos"]
    items = sorted(votes.items(), key=lambda x: -x[1])
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    names = [CAND_NOME.get(k, k.title()) for k, _ in items]
    pcts = [100 * v / vv for _, v in items]
    cols = [COR["lula"] if k == "LULA" else COR["flavio"] if k == "FLAVIO BOLSONARO" else COR["outros"]
            for k, _ in items]
    y = np.arange(len(items))[::-1]
    ax.barh(y, pcts, color=cols)
    for yi, p, (k, v) in zip(y, pcts, items):
        ax.text(p + 0.4, yi, f"{p:.2f}%  ({v/1e6:.2f} M)" if v > 1e5 else f"{p:.2f}%", va="center", fontsize=9)
    ax.set_yticks(y, names)
    ax.set_xlim(0, 56)
    ax.set_xlabel(t["f1_x"])
    ax.set_title(t["f1_title"], loc="left")
    footer(fig, t)
    save(fig, lang, "01_resultado_1turno")


def fig02(d, t, lang):
    b = d.bt
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    for yi, (key, nome, cor) in enumerate([("flavio", "Flávio", COR["flavio"]), ("lula", "Lula", COR["lula"])]):
        pts = [(b["parcial"][key], "o", t["f2_part"]), (b["projetado"][key], "D", t["f2_proj"]),
               (b["final"][key], "*", t["f2_fin"])]
        ax.hlines(yi, min(p[0] for p in pts) * 100, max(p[0] for p in pts) * 100, color=cor, alpha=0.3, lw=3)
        for v, m, lab in pts:
            ax.scatter(v * 100, yi, marker=m, s=170 if m == "*" else 90, color=cor if m != "o" else "white",
                       edgecolor=cor, linewidth=1.8, zorder=3, label=lab if yi == 0 else None)
            dy = 0.22 if m != "D" else -0.28
            ax.text(v * 100, yi + dy, f"{100*v:.2f}%", ha="center", fontsize=9, color=cor)
    ax.set_yticks([0, 1], ["Flávio", "Lula"])
    ax.set_ylim(-0.6, 1.6)
    ax.set_xlabel(t["f2_x"])
    ax.set_title(t["f2_title"], loc="left")
    h, l = ax.get_legend_handles_labels()
    ax.legend(h, l, frameon=False, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.42))
    ep = b["erro_projecao_pp"]
    ax.text(0.99, 0.5, f"Δ = {ep['lula']:+.2f} pp (Lula)\nΔ = {ep['flavio']:+.2f} pp (Flávio)",
            transform=ax.transAxes, ha="right", va="center", fontsize=9, color="#444444")
    footer(fig, t)
    fig.subplots_adjust(bottom=0.3)
    save(fig, lang, "02_backtest_nacional")


def fig03(d, t, lang):
    rows = sorted(d.bt_uf, key=lambda r: float(r["validos_final"]))
    fig, ax = plt.subplots(figsize=(8, 8.3))
    y = np.arange(len(rows))
    for yi, r in zip(y, rows):
        a, p = float(r["erro_margem_parcial_pp"]), float(r["erro_margem_proj_pp"])
        ax.plot([a, p], [yi, yi], color="#bbbbbb", lw=1.5, zorder=1)
    ax.scatter([float(r["erro_margem_proj_pp"]) for r in rows], y, color=COR["M1"], s=75, zorder=2,
               label=t["f3_proj"])
    ax.scatter([float(r["erro_margem_parcial_pp"]) for r in rows], y, color="white", edgecolor="#555555",
               s=26, zorder=3, linewidth=1.3, label=t["f3_part"])
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(y, [r["uf"].upper() for r in rows])
    ax.set_xlabel(t["f3_x"])
    ax.set_title(t["f3_title"], loc="left", fontsize=11.5)
    ax.legend(frameon=False, loc="lower right")
    ax.text(0.01, 0.995, "↑ " + ("maiores eleitorados" if lang == "pt" else "largest electorates"),
            transform=ax.transAxes, fontsize=8.5, color="#666666", va="top")
    footer(fig, t)
    save(fig, lang, "03_backtest_por_uf")


def fig04(d, t, lang):
    vals = {u: float(r["margem_lula_flavio_pp"]) for u, r in d.uf1.items() if u != "zz"}
    fig, ax = plt.subplots(figsize=(7.4, 6.3))
    lim = max(abs(v) for v in vals.values())
    norm = TwoSlopeNorm(vmin=-lim, vcenter=0, vmax=lim)
    cmap = matplotlib.colormaps["RdBu"]  # vermelho = Lula? RdBu: baixo=vermelho; invertemos
    cmap = cmap.reversed()               # alto (Lula) = vermelho, baixo (Flávio) = azul
    pc = draw_map(ax, d.geo, vals, cmap, norm)
    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    cb = fig.colorbar(sm, ax=ax, shrink=0.6, pad=0.01)
    cb.set_label(t["f4_cb"])
    ax.set_title(t["f4_title"], loc="left")
    footer(fig, t)
    save(fig, lang, "04_mapa_margem_1turno")


def fig05(d, t, lang):
    err = d.res["erro_pesquisas_1t"]
    items = sorted(err.items(), key=lambda x: x[1]["err_margem"])
    fig, ax = plt.subplots(figsize=(8, 5.2))
    y = np.arange(len(items))
    vals = [100 * e["err_margem"] for _, e in items]
    ax.barh(y, vals, color=[COR["lula"] if v > 0 else COR["flavio"] for v in vals])
    for yi, v in zip(y, vals):
        ax.text(v + (0.15 if v >= 0 else -0.15), yi, f"{v:+.1f}", va="center", ha="left" if v >= 0 else "right",
                fontsize=9)
    ax.set_yticks(y, [p for p, _ in items])
    m = 100 * d.res["vies_pesquisas_1t"]
    ax.axvline(m, color="black", ls="--", lw=1)
    ax.text(m, len(items) - 0.35, f"{t['f5_mean']} {m:+.1f}", ha="center", fontsize=9)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_xlim(-3.6, 9.2)
    ax.set_xlabel(t["f5_x"])
    ax.set_title(t["f5_title"], loc="left", fontsize=11.5)
    footer(fig, t, "fonte_mod")
    save(fig, lang, "05_erro_pesquisas_1turno")


def fig06(d, t, lang):
    pts = []
    for r in d.polls2:
        dt = date.fromisoformat(r["data_fim"])
        if dt < date(2026, 8, 15):
            continue
        l, f = float(r["lula"]), float(r["flavio"])
        pts.append((dt, 100 * l / (l + f), r["pollster"]))
    pts.sort()
    x = np.array([p[0].toordinal() for p in pts])
    y = np.array([p[1] for p in pts])
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.axhline(50, color="black", lw=0.8)
    ax.scatter([date.fromordinal(i) for i in x], y, color=COR["lula"], alpha=0.55, s=28)
    # média móvel ponderada por recência (meia-vida 7 dias), avaliada por dia
    days = np.arange(x.min(), x.max() + 1)
    avg = []
    for dd in days:
        mask = x <= dd
        if mask.sum() < 3:
            avg.append(np.nan)
            continue
        w = 0.5 ** ((dd - x[mask]) / 7.0)
        avg.append((w * y[mask]).sum() / w.sum())
    ax.plot([date.fromordinal(int(i)) for i in days], avg, color=COR["ens"], lw=2.2, label=t["f6_avg"])
    ax.axvline(date(2026, 10, 4), color="#888888", ls="--", lw=1)
    ax.text(date(2026, 10, 3), 53.6, t["f6_vline"], ha="right", fontsize=9, color="#666666")
    ax.set_ylabel(t["f6_y"])
    ax.set_ylim(43, 57)
    ax.set_title(t["f6_title"], loc="left")
    ax.legend(frameon=False, loc="upper left")
    ax.text(0.01, 0.02, t["f6_note"], transform=ax.transAxes, fontsize=8.5, color="#666666")
    ax.text(0.01, 0.93, ("↑ Lula à frente" if lang == "pt" else "↑ Lula ahead"), transform=ax.transAxes,
            fontsize=8.5, color=COR["lula"], va="top", alpha=0)
    import matplotlib.dates as mdates
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m" if lang == "pt" else "%b %d"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    footer(fig, t, "fonte_mod")
    save(fig, lang, "06_pesquisas_2turno")


def fig07(d, t, lang):
    tr = d.res["transferencia"]
    sp22 = 100 * d.res["calibracao_2022"]["eliminados_para_bolsonaro_2022"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.8), sharey=True, gridspec_kw=dict(width_ratios=[1, 1.3]))
    tr = tr[::-1]
    y = np.arange(len(tr))
    names = [CAND_NOME.get(r["candidato"], r["candidato"].title()) for r in tr]
    a1.barh(y, [r["votos_validos_1t"] / 1e6 for r in tr], color=COR["outros"])
    a1.set_yticks(y, names)
    a1.set_xlabel(t["f7_votes"])
    a2.barh(y, [100 * r["para_flavio"] for r in tr],
            color=[COR["flavio"] if "suposição" not in r["fonte"] else "#9db8d8" for r in tr])
    for yi, r in zip(y, tr):
        a2.text(100 * r["para_flavio"] + 1, yi, f"{100*r['para_flavio']:.0f}%" + ("*" if "suposição" in r["fonte"] else ""),
                va="center", fontsize=9)
    a2.axvline(sp22, color=COR["lula"], ls="--", lw=1.3)
    a2.text(sp22 - 1, len(tr) - 0.4, t["f7_2022"] + f" ({sp22:.0f}%)", color=COR["lula"], fontsize=8.5, ha="right")
    mw = 100 * d.res["transferencia_media_flavio"]
    a2.axvline(mw, color="black", ls=":", lw=1.3)
    a2.text(mw + 1, len(tr) - 0.4, f"{t['f7_mean']}: {mw:.0f}%", fontsize=8.5, ha="left")
    a2.set_xlim(0, 100)
    a2.set_xlabel(t["f7_split"])
    a2.text(0.99, 0.045, "* " + t["f7_sup"], transform=a2.transAxes, ha="right", fontsize=8, color="#666666")
    fig.suptitle(t["f7_title"], x=0.01, ha="left", fontweight="bold", fontsize=13, y=1.0)
    footer(fig, t, "fonte_mod")
    save(fig, lang, "07_transferencia_eliminados")


def fig08(d, t, lang):
    h = d.res["historico"]
    xs = np.array([x["pct_lider_1t"] / (x["pct_lider_1t"] + x["pct_segundo_1t"]) * 100 for x in h])
    ys = np.array([x["pct_lider_2t"] for x in h])
    beta = d.res["beta_hist"]
    fig, ax = plt.subplots(figsize=(7.6, 5.4))
    grid = np.linspace(50, 70, 50)
    ax.plot(grid, 50 + beta * (grid - 50), color="#666666", label=t["f8_fit"].format(b=beta))
    ax.plot(grid, grid, color="#cccccc", ls="--", lw=1)
    ax.scatter(xs, ys, s=60, color=COR["M3"], zorder=3)
    for x, y, r in zip(xs, ys, h):
        ax.annotate(f"{r['ano']}\n{r['lider']}", (x, y), textcoords="offset points", xytext=(6, -14), fontsize=8.5)
    lead = 100 * d.res["lider_entre_dois_1t"]
    pred = 50 + beta * (lead - 50)
    ax.errorbar([lead], [pred], yerr=[[100 * d.res["hist_sd"]], [100 * d.res["hist_sd"]]], fmt="*", ms=17,
                color=COR["flavio"], capsize=4, zorder=4, label=t["f8_2026"])
    ax.annotate(f"{pred:.1f}%", (lead, pred), textcoords="offset points", xytext=(12, 10), fontsize=10, fontweight="bold",
                color=COR["flavio"])
    ax.set_xlabel(t["f8_x"])
    ax.set_ylabel(t["f8_y"])
    ax.set_title(t["f8_title"], loc="left", fontsize=12)
    ax.legend(frameon=False, loc="upper left")
    footer(fig, t, "fonte_mod")
    save(fig, lang, "08_historico_2turnos")


def _hist_lines(s, comp, bins):
    m = s["comp"] == comp if comp else np.ones_like(s["w"], bool)
    h, _ = np.histogram(s["lula"][m], bins=bins, weights=s["w"][m], density=True)
    return h


def fig09(d, t, lang):
    s = d.sims
    bins = np.arange(38, 60.01, 0.4)
    ctr = (bins[:-1] + bins[1:]) / 2
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    he = _hist_lines(s, None, bins)
    ax.fill_between(ctr, he, step="mid", color=COR["ens"], alpha=0.18, label=t["f9_ens"])
    ax.fill_between(ctr, np.where(ctr >= 50, he, 0), step="mid", color=COR["lula"], alpha=0.45)
    ax.step(ctr, he, where="mid", color=COR["ens"], lw=2)
    for c in ("M1", "M2", "M3"):
        ax.step(ctr, _hist_lines(s, c, bins), where="mid", color=COR[c], lw=1.6, label=t[c])
    ax.axvline(50, color="black", lw=1)
    p = 100 * d.res["p_lula_vence"]
    ax.set_ylim(0, ax.get_ylim()[1] * 1.12)
    ymax = ax.get_ylim()[1]
    ax.text(50.4, ymax * 0.93, t["f9_win"].format(p=p), color=COR["lula"], fontweight="bold")
    ax.text(49.6, ymax * 0.93, t["f9_lose"].format(p=100 - p), color=COR["flavio"], fontweight="bold", ha="right")
    ax.set_xlabel(t["f9_x"])
    ax.set_ylabel(t["f9_y"])
    ax.set_yticks([])
    ax.set_title(t["f9_title"], loc="left")
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0.0, 0.85))
    footer(fig, t, "fonte_mod")
    save(fig, lang, "09_distribuicao_ensemble")


def fig10(d, t, lang):
    sens = d.res["sensibilidade_pesos"][::-1]
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    y = np.arange(len(sens))
    vals = [100 * r["p_lula"] for r in sens]
    cols = [COR["ens"] if r["rotulo"].startswith("Ensemble") else
            COR[r["rotulo"][3:5]] if r["rotulo"].startswith("Só M") else "#9a9a9a" for r in sens]
    ax.barh(y, vals, color=cols)
    for yi, v in zip(y, vals):
        ax.text(v + 0.8, yi, f"{v:.1f}%", va="center", fontsize=9.5)
    lab = [(SENS_EN.get(r["rotulo"], r["rotulo"]) if lang == "en" else r["rotulo"]) for r in sens]
    ax.set_yticks(y, lab)
    ax.axvline(50, color="black", lw=0.8, ls=":")
    ax.set_xlim(0, 60)
    ax.set_xlabel(t["f10_x"])
    ax.set_title(t["f10_title"], loc="left")
    footer(fig, t, "fonte_mod")
    save(fig, lang, "10_sensibilidade_pesos")


def fig11(d, t, lang):
    tn = sorted(d.res["tornado"], key=lambda r: abs(r["alto"] - r["baixo"]))
    mean = {c: 100 * d.res["componentes"][c]["media"] for c in ("M1", "M2")}
    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    y = np.arange(len(tn))
    for yi, r in zip(y, tn):
        base = mean["M2"] if r["rotulo"].startswith("M2") else mean["M1"]
        lo, hi = 100 * r["baixo"] - base, 100 * r["alto"] - base
        ax.barh(yi, hi - lo, left=lo, color=COR["lula"] if hi > lo else COR["flavio"], alpha=0.85)
        ax.text(max(lo, hi) + 0.05, yi, f"{hi-lo:+.2f} pp", va="center", fontsize=9)
    ax.set_yticks(y, [(TORN_EN.get(r["rotulo"], r["rotulo"]) if lang == "en" else r["rotulo"]) for r in tn])
    ax.axvline(0, color="black", lw=1)
    ax.set_xlim(-1.5, 2.2)
    ax.set_xlabel(t["f11_x"])
    ax.set_title(t["f11_title"], loc="left")
    footer(fig, t, "fonte_mod")
    save(fig, lang, "11_tornado_m1")


def fig12(d, t, lang):
    vals = {u: 100 * float(r["lula_2t_mediana"]) for u, r in d.tab_uf.items() if u != "zz"}
    fig, ax = plt.subplots(figsize=(7.4, 6.3))
    norm = TwoSlopeNorm(vmin=20, vcenter=50, vmax=80)
    cmap = matplotlib.colormaps["RdBu"].reversed()
    draw_map(ax, d.geo, vals, cmap, norm)
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, shrink=0.6, pad=0.01)
    cb.set_label(t["f12_cb"])
    ax.set_title(t["f12_title"], loc="left")
    footer(fig, t, "fonte_mod")
    save(fig, lang, "12_mapa_previsao_2turno")


def fig13(d, t, lang):
    rows = sorted(d.tab_uf.values(), key=lambda r: float(r["lula_2t_mediana"]))
    fig, ax = plt.subplots(figsize=(8, 8.3))
    y = np.arange(len(rows))
    for yi, r in zip(y, rows):
        lo, md, hi = (100 * float(r[k]) for k in ("lula_2t_p05", "lula_2t_mediana", "lula_2t_p95"))
        swing = lo < 50 < hi
        c = COR["M2"] if swing else (COR["lula"] if md > 50 else COR["flavio"])
        ax.plot([lo, hi], [yi, yi], color=c, lw=3, solid_capstyle="round", alpha=0.85)
        ax.scatter(md, yi, color="white", edgecolor=c, s=36, zorder=3, linewidth=1.6)
    ax.axvline(50, color="black", lw=0.9)
    ax.set_yticks(y, [r["uf"].upper() for r in rows])
    ax.set_xlabel(t["f13_x"])
    ax.set_title(t["f13_title"], loc="left")
    ax.plot([], [], color=COR["M2"], lw=3, label=t["f13_swing"])
    ax.plot([], [], color="#888888", lw=3, label=t["f13_safe"])
    ax.legend(frameon=False, loc="lower right")
    footer(fig, t, "fonte_mod")
    save(fig, lang, "13_previsao_por_uf")


def fig14(d, t, lang):
    sc = d.res["cenarios_m1"][::-1]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    y = np.arange(len(sc))
    vals = [100 * r["lula_pct"] for r in sc]
    ax.barh(y, vals, color=[COR["lula"] if v > 50 else COR["flavio"] for v in vals], alpha=0.85)
    for yi, v in zip(y, vals):
        ax.text(v + 0.15, yi, f"{v:.1f}%", va="center", fontsize=9)
    ax.set_yticks(y, [(SCEN_EN.get(r["rotulo"], r["rotulo"]) if lang == "en" else r["rotulo"]) for r in sc], fontsize=9)
    ax.axvline(50, color="black", lw=1)
    ax.set_xlim(40, 56)
    ax.set_xlabel(t["f14_x"])
    ax.set_title(t["f14_title"], loc="left")
    footer(fig, t, "fonte_mod")
    save(fig, lang, "14_cenarios_m1")


def fig15(d, t, lang):
    s = d.sims
    bins = np.arange(-22, 14.01, 0.5)
    ctr = (bins[:-1] + bins[1:]) / 2
    h, _ = np.histogram(s["margem"], bins=bins, weights=s["w"], density=True)
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    ax.fill_between(ctr, np.where(ctr >= 0, h, 0), step="mid", color=COR["lula"], alpha=0.6, label=t["f15_lula"])
    ax.fill_between(ctr, np.where(ctr < 0, h, 0), step="mid", color=COR["flavio"], alpha=0.6, label=t["f15_flavio"])
    q = d.res["margem_quantis"]
    for k in ("0.05", "0.5", "0.95"):
        v = q[k] / 1e6
        ax.axvline(v, color="black", ls="--" if k != "0.5" else "-", lw=1)
        ax.text(v, ax.get_ylim()[1] * (0.97 if k == "0.5" else 0.86),
                f" {({'0.05': 'P5', '0.5': 'P50', '0.95': 'P95'})[k]}: {v:+.1f} M", fontsize=9, ha="left")
    ax.axvline(0, color="black", lw=1.2)
    ax.set_xlabel(t["f15_x"])
    ax.set_yticks([])
    ax.set_title(t["f15_title"], loc="left")
    ax.legend(frameon=False, loc="upper left")
    footer(fig, t, "fonte_mod")
    save(fig, lang, "15_margem_votos")


# ----------------------------------------------------------------------------- figuras de insumos (16-19)
T["pt"].update(
    f16_title="Quais pesquisas de 2º turno entram no M2, e com que peso",
    f16_x="Peso na média (%): cada 7 dias de atraso corta o peso pela metade",
    f16_lab="Lula {v:.1f}% dos válidos",
    f16_note="{n} das {tot} pesquisas do arquivo não entram: são anteriores a 20/09 ou foram substituídas\n"
             "por uma pesquisa mais recente do mesmo instituto.",
    f17_title="Nenhuma pesquisa sozinha move a probabilidade de Lula em mais de ~1 p.p.",
    f17_x="Variação na probabilidade de Lula vencer, em pontos percentuais (ensemble)",
    f17_1t="Pesquisas de 1º turno\n(entram só pelo erro medido na urna)",
    f17_2t="Pesquisas de 2º turno\n(entram pelo valor e pela data)",
    f17_foot="Efeito de tirar cada pesquisa e recalcular o M2 (peso do M2 no ensemble: 30%).",
    f18_title="O que mais pesa nos dados: quanto do viés das pesquisas corrigimos",
    f18_x="Variação na probabilidade de Lula vencer, em pontos percentuais (ensemble)",
    f18_m2="M2 (pesquisas)", f18_m1="M1 (transferência)",
    f19_title="M1: de onde vêm os votos do 2º turno",
    f19_x="Votos válidos (milhões; eixo começa em 50)",
    f19_start="1º turno (projetado)", f19_base="Bases: retenção e mobilização\n(calibradas em 2022, peso 0,5)",
    f19_voters="Eleitores de {n} que votam nele", f19_rest="Demais eliminados", f19_end="2º turno (M1)",
)
T["en"].update(
    f16_title="Which runoff polls enter M2, and with what weight",
    f16_x="Weight in the average (%): each 7 days of age halves the weight",
    f16_lab="Lula {v:.1f}% of valid",
    f16_note="{n} of the {tot} polls in the file do not enter: they predate 20 Sep or were superseded\n"
             "by a more recent poll from the same pollster.",
    f17_title="No single poll moves the probability of a Lula win by more than ~1 pp",
    f17_x="Change in the probability that Lula wins, in percentage points (ensemble)",
    f17_1t="First-round polls\n(enter only through their error against the ballot box)",
    f17_2t="Runoff polls\n(enter through their value and date)",
    f17_foot="Effect of dropping each poll and recomputing M2 (M2 weight in the ensemble: 30%).",
    f18_title="What weighs most in the data: how much poll bias we correct for",
    f18_x="Change in the probability that Lula wins, in percentage points (ensemble)",
    f18_m2="M2 (polls)", f18_m1="M1 (transfer)",
    f19_title="M1: where the runoff votes come from",
    f19_x="Valid votes (millions; axis starts at 50)",
    f19_start="First round (projected)", f19_base="Bases: retention and mobilization\n(calibrated on 2022, weight 0.5)",
    f19_voters="{n} voters who vote for him", f19_rest="Other eliminated candidates", f19_end="Runoff (M1)",
)
SCEN2_EN = {
    "M2 base (média das pesquisas corrigida pelo viés do 1º turno × 0,4)": "M2 base",
    "Sem correção do 1º turno (só a média das pesquisas de 2º turno)": "No first-round correction (runoff polls only)",
    "Correção total do viés do 1º turno (fator 1,0)": "Full first-round bias correction (factor 1.0)",
    "Média simples (sem peso por recência)": "Plain average (no recency weighting)",
    "Sem os 3 institutos que mais erraram no 1º turno (Indexa, MDA, Nexus)": "Without the 3 worst first-round pollsters (Indexa, MDA, Nexus)",
    "Só Quaest (sem Datafolha)": "Quaest only (no Datafolha)",
    "Só Datafolha (sem Quaest)": "Datafolha only (no Quaest)",
    "Sem nenhuma pesquisa de transferência (todos por suposição)": "No transfer poll at all (all assumed)",
}


def _inf(name):
    return csv_rows(C.PROCESSED / name)


def fig16(d, t, lang):
    rows = [r for r in _inf("influencia_2turno.csv") if r["status"] == "entra"]
    rows.sort(key=lambda r: r["data_fim"])
    tot = len(_inf("influencia_2turno.csv"))
    fig, ax = plt.subplots(figsize=(9, 5.4))
    y = np.arange(len(rows))
    w = [100 * float(r["peso_normalizado"]) for r in rows]
    cols = [COR["lula"] if float(r["lula_valido"]) > 0.5 else COR["flavio"] for r in rows]
    ax.barh(y, w, color=cols, alpha=0.85)
    for yi, r, wi in zip(y, rows, w):
        ax.text(wi + 0.15, yi, t["f16_lab"].format(v=100 * float(r["lula_valido"])), va="center", fontsize=8.5)
    ax.set_yticks(y, [f"{r['pollster']} ({r['data']})" for r in rows], fontsize=9)
    ax.set_xlim(0, max(w) * 1.45)
    ax.set_xlabel(t["f16_x"])
    ax.set_title(t["f16_title"], loc="left", fontsize=12)
    fig.text(0.01, -0.07, t["f16_note"].format(n=tot - len(rows), tot=tot), fontsize=8.5, color="#555555",
             ha="left", va="top")
    footer(fig, t, "fonte_mod")
    save(fig, lang, "16_peso_pesquisas_2turno")


def fig17(d, t, lang):
    fig, axs = plt.subplots(1, 2, figsize=(11, 5.6), sharex=True)
    for ax, fn, key, ttl in ((axs[0], "influencia_1turno.csv", "f17_1t", None), (axs[1], "influencia_2turno.csv", "f17_2t", None)):
        rows = [r for r in _inf(fn) if r["status"] == "entra"]
        rows.sort(key=lambda r: float(r["d_ens_p_pp"]))
        y = np.arange(len(rows))
        v = [float(r["d_ens_p_pp"]) for r in rows]
        ax.hlines(y, 0, v, color="#999999", lw=1.5)
        ax.scatter(v, y, color=[COR["lula"] if x > 0 else COR["flavio"] for x in v], zorder=3, s=45)
        ax.set_yticks(y, [r["pollster"] for r in rows], fontsize=9)
        ax.axvline(0, color="black", lw=0.8)
        ax.set_title(t[key], fontsize=10.5, loc="left")
        for yi, x in zip(y, v):
            ax.text(x + (0.04 if x >= 0 else -0.04), yi, f"{x:+.2f}", va="center", ha="left" if x >= 0 else "right", fontsize=8)
    lim = max(abs(float(r["d_ens_p_pp"])) for fn in ("influencia_1turno.csv", "influencia_2turno.csv")
              for r in _inf(fn) if r["status"] == "entra") * 1.35
    axs[0].set_xlim(-lim, lim)
    fig.supxlabel(t["f17_x"], fontsize=10)
    fig.suptitle(t["f17_title"], x=0.01, ha="left", fontweight="bold", fontsize=13)
    fig.text(0.01, -0.02, t["f17_foot"], fontsize=8.5, color="#555555")
    fig.text(0.01, -0.055, t["fonte_mod"], fontsize=8, color="#666666")
    fig.tight_layout(rect=(0, 0.02, 1, 0.95))
    save(fig, lang, "17_efeito_remover_pesquisa")


def fig18(d, t, lang):
    inf = jload(C.PROCESSED / "influencia.json")
    items = [(s["rotulo"], s["ens_p_delta_pp"], "M2") for s in inf["cenarios_m2"][1:]]
    fig, ax = plt.subplots(figsize=(10, 4.2))
    y = np.arange(len(items))[::-1]
    lab = [(SCEN2_EN.get(r, r) if lang == "en" else r) for r, _, _ in items]
    ax.barh(y, [v for _, v, _ in items], color=[COR["lula"] if v > 0 else COR["flavio"] for _, v, _ in items], alpha=0.85)
    for yi, (_, v, _) in zip(y, items):
        ax.text(v + (0.1 if v >= 0 else -0.1), yi, f"{v:+.1f}", va="center", ha="left" if v >= 0 else "right", fontsize=9)
    ax.set_yticks(y, lab, fontsize=9)
    ax.axvline(0, color="black", lw=0.8)
    lim = max(abs(v) for _, v, _ in items) * 1.3
    ax.set_xlim(-lim, lim)
    ax.set_xlabel(t["f18_x"])
    ax.set_title(t["f18_title"], loc="left", fontsize=11.5)
    footer(fig, t, "fonte_mod")
    save(fig, lang, "18_cenarios_de_insumo")


def fig19(d, t, lang):
    m = jload(C.PROCESSED / "m1_decomposicao.json")
    nm = {"RONALDO CAIADO": "Caiado", "RENAN SANTOS": "Renan Santos", "ESCRITOR AUGUSTO CURY": "Cury", "ZEMA": "Zema"}
    fig, axs = plt.subplots(2, 1, figsize=(9.5, 8.4))
    for ax, k, col, v1, title in ((axs[0], "lula", COR["lula"], m["lula_1t"], "Lula"),
                                  (axs[1], "flavio", COR["flavio"], m["flavio_1t"], "Flávio")):
        e = m[k]["elim"]
        big = sorted(nm, key=lambda c: -e[c])
        steps = [(t["f19_start"], v1 / 1e6, None),
                 (t["f19_base"], (m[k]["propria"] + m[k]["rival"] - v1) / 1e6, "d")]
        steps += [(t["f19_voters"].format(n=nm[c]), e[c] / 1e6, "d") for c in big]
        steps += [(t["f19_rest"], sum(v for c, v in e.items() if c not in big) / 1e6, "d")]
        cum = 0.0
        ys = np.arange(len(steps) + 1)[::-1]
        for yi, (lab, v, kind) in zip(ys, steps):
            if kind is None:
                ax.barh(yi, v, color=col, alpha=0.4)
                ax.text(v + 0.1, yi, f"{v:.1f}", va="center", fontsize=9)
                cum = v
            else:
                c_ = col if v >= 0 else "#444444"
                ax.barh(yi, v, left=cum, color=c_, alpha=0.85)
                ax.text(max(cum, cum + v) + 0.1, yi, f"{v:+.2f}", va="center", fontsize=9)
                cum += v
        ax.barh(ys[-1], cum, color=col)
        ax.text(cum + 0.1, ys[-1], f"{cum:.1f}", va="center", fontsize=10, fontweight="bold")
        ax.set_yticks(ys, [s_[0] for s_ in steps] + [t["f19_end"]], fontsize=9)
        ax.set_xlim(50, 66)
        ax.set_title(title, loc="left", fontsize=11, color=col)
        ax.set_xlabel(t["f19_x"] if k == "flavio" else "")
        ax.grid(axis="y", visible=False)
    fig.suptitle(t["f19_title"], x=0.01, ha="left", fontweight="bold", fontsize=13)
    fig.tight_layout(rect=(0, 0.02, 1, 0.96))
    fig.text(0.01, -0.01, t["fonte_mod"], fontsize=8, color="#666666")
    save(fig, lang, "19_decomposicao_m1")


FIGS = {"01": fig01, "02": fig02, "03": fig03, "04": fig04, "05": fig05, "06": fig06, "07": fig07, "08": fig08,
        "09": fig09, "10": fig10, "11": fig11, "12": fig12, "13": fig13, "14": fig14, "15": fig15,
        "16": fig16, "17": fig17, "18": fig18, "19": fig19}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", nargs="+", default=["pt", "en"])
    ap.add_argument("--only", nargs="*", default=None, help="números das figuras (ex.: 03 09)")
    a = ap.parse_args()
    d = D()
    for lang in a.lang:
        for k, fn in FIGS.items():
            if a.only and k not in a.only:
                continue
            fn(d, T[lang], lang)


if __name__ == "__main__":
    main()
