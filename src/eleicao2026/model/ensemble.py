#!/usr/bin/env python3
"""Segundo turno 2026 (Flávio Bolsonaro × Lula): ensemble de 3 métodos independentes.

 M1  ESTRUTURAL : projeção do 1º turno por município -> votos dos eliminados divididos segundo
                  pesquisas (Quaest + Datafolha) -> retenção/mobilização calibrada em 2022.
 M2  PESQUISAS  : média das pesquisas de 2º turno (Lula × Flávio), corrigida pelo erro que as
                  pesquisas do 1º turno tiveram (medido contra a urna).
 M3  HISTÓRICO  : regressão do share do líder do 1º turno no 2º turno (6 eleições, 2002-2022).
 O ensemble é a mistura ponderada das três distribuições (pesos explícitos, com sensibilidade).

Saídas (data/processed/):
  sims_2turno.csv        uma linha por simulação (componente, parâmetros sorteados, resultado nacional)
  sims_2turno_uf.csv     % de Lula por UF em cada simulação
  tabela_uf_2turno.csv   resumo por UF
  resumo_2turno.json     todas as estatísticas usadas nos gráficos e no relatório
Somente biblioteca padrão.

Uso: python -m eleicao2026.model.ensemble [--n 10000]
"""
import argparse
import csv
import json
import math
import random
import sys
from collections import defaultdict
from datetime import date

from eleicao2026 import config as C
from eleicao2026.config import LULA, FLAV, UF2REG, REG, UFN
from eleicao2026.model import segundo_turno as S
from eleicao2026.model.linalg import expit, logit, wquant
from eleicao2026.model.segundo_turno import coef, runoff, total

SEED = 20261025
N_PER = 10000                                # simulações por componente
W = {"M1": 0.50, "M2": 0.30, "M3": 0.20}     # pesos do ensemble (SUPOSIÇÃO explícita; veja sensibilidade)
N_BOOT = 200
Q = [0.025, 0.05, 0.25, 0.5, 0.75, 0.95, 0.975]

# SUPOSIÇÃO (sem pesquisa): candidatos menores
MINOR_RIGHT = 0.65
MINOR_LEFT = 0.30
LEFT = {"HERTZ DIAS", "EDMILSON COSTA", "RUI COSTA PIMENTA"}
# Pesquisas de 1º turno antes disso não entram no cálculo do erro; idem 2º turno
CORTE_1T = date(2026, 9, 26)
CORTE_2T = date(2026, 9, 20)
MEIA_VIDA_DIAS = 7.0
CARRY_CENTRAL, CARRY_DP = 0.4, 0.2           # SUPOSIÇÃO: quanto do viés do 1º turno persiste no 2º


# ----------------------------------------------------------------------------- insumos
def load_transfer():
    rows = list(csv.DictReader(open(C.EXTERNAL / "transferencia_pesquisas.csv")))
    quaest, datafolha, agg = {}, {}, None
    for r in rows:
        f, l = float(r["flavio"]), float(r["lula"])
        b = float(r["branco_nulo_indeciso"]) if r["branco_nulo_indeciso"] else None
        if r["eleitor_de"].startswith("AGREGADO"):
            agg = (f, l, b)
        elif r["instituto"] == "Quaest":
            quaest[r["eleitor_de"]] = (f, l, b)
        elif r["instituto"] == "Datafolha":
            datafolha[r["eleitor_de"]] = (f, l)
    return quaest, datafolha, agg


def load_hist():
    return {int(r["ano"]): (r["lider_1t"], float(r["pct_lider_1t"]), float(r["pct_segundo_1t"]),
                            float(r["pct_lider_2t"]), r["segundo_1t"])
            for r in csv.DictReader(open(C.EXTERNAL / "historico_2turnos.csv"))}


def build_split():
    """Fração do voto VÁLIDO de cada eliminado que vai a Flávio, e % que declara voto (literal)."""
    quaest, datafolha, agg = load_transfer()
    split, lit, src = {}, {}, {}
    f_agg = agg[0] / (agg[0] + agg[1])
    lit_agg = (agg[0] + agg[1]) / 100
    for c in ("RENAN SANTOS", "RONALDO CAIADO", "ESCRITOR AUGUSTO CURY", "ZEMA"):
        parts, notes = [], []
        if c in quaest:
            f, l, _ = quaest[c]
            parts.append(f / (f + l))
            notes.append(f"Quaest {f:.0f}/{l:.0f}")
            lit[c] = (f + l) / 100
        if c in datafolha:
            f, l = datafolha[c]
            parts.append(f / (f + l))
            notes.append(f"Datafolha {f:.0f}/{l:.0f}")
        else:  # sem número individual do Datafolha: usa o agregado dos 4
            parts.append(f_agg)
            notes.append(f"Datafolha agregado {agg[0]:.0f}/{agg[1]:.0f}")
        split[c] = sum(parts) / len(parts)
        lit.setdefault(c, lit_agg)
        src[c] = " + ".join(notes)
    return split, lit, src, f_agg, lit_agg


# ----------------------------------------------------------------------------- pesquisas
def poll_stats(L1, F1):
    """Erro das pesquisas de 1º turno e média das pesquisas de 2º turno (último por instituto)."""
    p1 = list(csv.DictReader(open(C.INTERIM / "pesquisas_1turno.csv")))
    last1 = {}
    for r in p1:
        d = date.fromisoformat(r["data_fim"])
        if d < CORTE_1T:
            continue
        tot = sum(float(r[k] or 0) for k in ("lula", "flavio", "caiado", "zema", "santos", "cury", "outros"))
        l, f = float(r["lula"]) / tot, float(r["flavio"]) / tot
        last1.setdefault(r["pollster"], []).append((d, l, f, r["data"]))
    err = {}
    for p, v in last1.items():
        v.sort()
        _, l, f, dt = v[-1]
        err[p] = dict(data=dt, l=l, f=f, err_margem=(l - f) - (L1 - F1), err_l=l - L1, err_f=f - F1)
    errs = [e["err_margem"] for e in err.values()]
    b1 = sum(errs) / len(errs)
    sd_b = math.sqrt(sum((e - b1) ** 2 for e in errs) / (len(errs) - 1))

    p2 = list(csv.DictReader(open(C.INTERIM / "pesquisas_2turno.csv")))
    last2 = {}
    for r in p2:
        d = date.fromisoformat(r["data_fim"])
        if d < CORTE_2T:
            continue
        l, f = float(r["lula"]), float(r["flavio"])
        last2.setdefault(r["pollster"], []).append((d, l, f, r["data"], float(r["branco_nao_sabe"] or 0)))
    rows = []
    for p, v in last2.items():
        v.sort()
        d, l, f, dt, bl = v[-1]
        rows.append(dict(pollster=p, data=dt, data_fim=d.isoformat(), l=l, f=f, branco=bl,
                         lula_valido=l / (l + f)))
    ref = max(date.fromisoformat(r["data_fim"]) for r in rows)
    ws = [0.5 ** ((ref - date.fromisoformat(r["data_fim"])).days / MEIA_VIDA_DIAS) for r in rows]
    avg = sum(w * r["lula_valido"] for w, r in zip(ws, rows)) / sum(ws)
    raw = [r["lula_valido"] for r in rows]
    sd_poll = math.sqrt(sum((x - sum(raw) / len(raw)) ** 2 for x in raw) / (len(raw) - 1))
    return dict(err=err, b1=b1, sd_b=sd_b, rows=sorted(rows, key=lambda r: r["data_fim"], reverse=True),
                avg=avg, sd_poll=sd_poll)


# ----------------------------------------------------------------------------- histórico
def hist_model(hist, f1, l1):
    """s2 - 0,5 = beta (s1 - 0,5), s = share do líder do 1º turno entre os dois primeiros."""
    xs, ys = [], []
    for a, (nm, s1, s2, r2, _) in hist.items():
        xs.append(s1 / (s1 + s2) - 0.5)
        ys.append(r2 / 100 - 0.5)
    beta = sum(x * y for x, y in zip(xs, ys)) / sum(x * x for x in xs)
    res = [y - beta * x for x, y in zip(xs, ys)]
    sd = math.sqrt(sum(r * r for r in res) / (len(res) - 1))
    lead = f1 / (f1 + l1)  # Flávio é o líder
    return beta, sd, res, lead, 0.5 + beta * (lead - 0.5)


# ----------------------------------------------------------------------------- geografia
def shift_logit(base, target, vtot):
    """Aplica o mesmo deslocamento de logit ao share de Lula de cada UF até o total nacional = target."""
    sh = {u: l / (l + b) for u, (l, b) in base.items()}
    lo, hi = -2.0, 2.0
    for _ in range(50):
        mid = (lo + hi) / 2
        s = sum(vtot[u] * expit(logit(sh[u]) + mid) for u in sh) / sum(vtot.values())
        if s < target:
            lo = mid
        else:
            hi = mid
    return {u: expit(logit(sh[u]) + (lo + hi) / 2) for u in sh}


def run(n_per=N_PER, log=print):
    rnd = random.Random(SEED)
    C.PROCESSED.mkdir(parents=True, exist_ok=True)

    # ---------- calibração 2022 (retenção das bases e comparecimento dos eliminados)
    rows = S.load22()
    rm_g, _ = S.cv_eval(rows, False, random.Random(1))
    rm_r, cvres = S.cv_eval(rows, True, random.Random(1))
    naive = math.sqrt(sum(r["V1"] * (r["x"][0] / (r["x"][0] + r["x"][1]) - r["L2"] / (r["L2"] + r["B2"])) ** 2
                          for r in rows) / sum(r["V1"] for r in rows))
    regional = rm_r < rm_g
    alfa = S.fit(rows, regional)
    a0 = S.fit(rows, False)[None]
    rho0 = a0[0][2] + a0[1][2]
    sp22 = a0[1][2] / rho0
    delta = {}
    for reg in REG:
        a = coef(alfa, reg)
        s = a[1][2] / (a[0][2] + a[1][2]) if a[0][2] + a[1][2] > 0 else sp22
        delta[reg] = logit(s) - logit(sp22)
    xs = [1 / r["V1"] for r, _ in cvres]
    ys = [(2 * e) ** 2 for _, e in cvres]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    bb = max(sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs), 0.0)
    aa = max(my - bb * mx, 0.0004)
    ufb = defaultdict(lambda: [0.0, 0.0])
    for r, e in cvres:
        ufb[r["k"][0]][0] += r["V1"] * 2 * e
        ufb[r["k"][0]][1] += r["V1"]
    tau_uf = max(math.sqrt(sum((v[0] / v[1]) ** 2 for v in ufb.values()) / len(ufb)), 0.01)
    log(f"calibração 2022: {len(rows)} municípios; RMSE global {100*rm_g:.2f}pp, regional {100*rm_r:.2f}pp, "
        f"ingênuo {100*naive:.2f}pp")

    # ---------- 1º turno projetado (município -> UF)
    cur, pm = S.load26()
    N, muni = S.first_round(cur, pm)
    V1 = sum(sum(v.values()) for v in N.values())
    L1 = sum(v.get(LULA, 0) for v in N.values()) / V1
    F1 = sum(v.get(FLAV, 0) for v in N.values()) / V1
    elim = sorted({c for u in N.values() for c in u if c not in (LULA, FLAV)})
    elim_votes = {c: sum(N[u].get(c, 0.0) for u in N) for c in elim}

    split4, lit4, src4, f_agg, lit_agg = build_split()
    split, lit = {}, {}
    for c in elim:
        if c in split4:
            split[c], lit[c] = split4[c], lit4[c]
        else:
            split[c] = MINOR_LEFT if c in LEFT else MINOR_RIGHT
            lit[c] = lit_agg
    others = sum(elim_votes.values())
    w_split = sum(elim_votes[c] * split[c] for c in elim) / others

    # ---------- componentes M2 / M3
    hist = load_hist()
    ps = poll_stats(L1, F1)
    beta, sd_h, res_h, lead_s, m3_f = hist_model(hist, F1, L1)
    margin2p_err = ps["b1"] / (L1 + F1)       # erro de margem das pesquisas, base dois candidatos
    m2_center = ps["avg"] - CARRY_CENTRAL * margin2p_err / 2

    # ---------- M1: base e estrutura para simulação
    base = runoff(N, alfa, split, rho0, delta)  # asym padrão (0,5)
    L2b, B2b = total(base)
    vtot = {u: l + b for u, (l, b) in base.items()}
    mv = defaultdict(float)
    ratio = {u: (base[u][0] + base[u][1]) / max(sum(N[u].values()), 1) for u in N}
    for u, V in muni:
        mv[u] += (math.sqrt(aa + bb / max(V, 1)) * V * ratio[u]) ** 2
    boots = []
    for _ in range(N_BOOT):
        samp = [rows[rnd.randrange(len(rows))] for _ in rows]
        boots.append(S.fit(samp, regional))
    ufs = sorted(N)

    sims, sims_uf = [], []

    def record(comp, i, params, uf_l, uf_b):
        Lt = sum(uf_l.values())
        Bt = sum(uf_b.values())
        row = dict(sim=f"{comp}-{i}", componente=comp, lula_pct=Lt / (Lt + Bt), flavio_pct=Bt / (Lt + Bt),
                   lula_votos=Lt, flavio_votos=Bt, margem_votos=Lt - Bt, vencedor="Lula" if Lt > Bt else "Flávio")
        row.update(params)
        sims.append(row)
        sims_uf.append([f"{comp}-{i}", comp] + [uf_l[u] / (uf_l[u] + uf_b[u]) for u in ufs])

    # ---------- M1
    for i in range(n_per):
        al = boots[rnd.randrange(N_BOOT)]
        asym = rnd.random()
        u_rho = rnd.random()
        rho_noise = rnd.gauss(0, 0.03)
        common = rnd.gauss(0, 0.30)                    # inclinação comum das pesquisas de transferência
        sp, vr = {}, {}
        for c in elim:
            sp[c] = expit(logit(split[c]) + common + rnd.gauss(0, 0.30))
            vr[c] = min(max(lit[c] + u_rho * (rho0 - lit[c]) + rho_noise, 0.3), 1.05)
        res = runoff(N, al, sp, rho0, delta, vr, asym)
        sn = rnd.gauss(0, S.TAU_NAT)
        ul, ub = {}, {}
        for u, (l, b) in res.items():
            v2 = l + b
            dm = (rnd.gauss(0, tau_uf) + sn) * v2 + rnd.gauss(0, math.sqrt(mv[u]))
            ul[u], ub[u] = l + dm / 2, b - dm / 2
        record("M1", i, dict(asym=asym, comparecimento_elim=u_rho, desl_transf=common, choque_nac=sn), ul, ub)

    # ---------- M2 / M3 (share nacional sorteado; geografia = M1 deslocada)
    def geo(target, comp, i, params):
        sh = shift_logit(base, target, vtot)
        eps = rnd.gauss(0, 0.012)
        ul, ub = {}, {}
        for u in ufs:
            v2 = vtot[u] * (1 + eps)
            s = min(max(sh[u] + rnd.gauss(0, tau_uf / 2), 0.02), 0.98)
            ul[u], ub[u] = v2 * s, v2 * (1 - s)
        # reescala para o alvo nacional exato (o ruído por UF não deve deslocar o total)
        Lt, Bt = sum(ul.values()), sum(ub.values())
        k = target / (Lt / (Lt + Bt))
        for u in ufs:
            v2 = ul[u] + ub[u]
            s = min(max(ul[u] / v2 * k, 0.01), 0.99)
            ul[u], ub[u] = v2 * s, v2 * (1 - s)
        record(comp, i, params, ul, ub)

    sd_m2 = math.sqrt(0.018 ** 2 + 0.015 ** 2 + (ps["sd_poll"] / math.sqrt(len(ps["rows"]))) ** 2)
    for i in range(n_per):
        k = min(max(rnd.gauss(CARRY_CENTRAL, CARRY_DP), 0.0), 1.0)
        bias = rnd.gauss(ps["b1"], ps["sd_b"] / math.sqrt(len(ps["err"]))) / (L1 + F1)
        tgt = ps["avg"] - k * bias / 2 + rnd.gauss(0, sd_m2)
        geo(min(max(tgt, 0.3), 0.7), "M2", i, dict(carry_viés=k, viés_1T=bias, meta_share_lula=tgt))
    for i in range(n_per):
        chi = rnd.gammavariate(2, 2)  # t com 4 g.l., escala p/ dp ~ sd_h
        e = rnd.gauss(0, 1) / math.sqrt(chi / 4) * sd_h / math.sqrt(2)
        tgt = 1 - (0.5 + beta * (lead_s - 0.5) + e)
        geo(min(max(tgt, 0.3), 0.7), "M3", i, dict(meta_share_lula=tgt))

    # ---------- agregação ponderada
    cnt = defaultdict(int)
    for s in sims:
        cnt[s["componente"]] += 1
    for s in sims:
        s["peso"] = W[s["componente"]] / cnt[s["componente"]]
    wts = [s["peso"] for s in sims]
    sh = [s["lula_pct"] for s in sims]
    mg = [s["margem_votos"] for s in sims]

    def comp_stats(name):
        sub = [s for s in sims if s["componente"] == name]
        v = [s["lula_pct"] for s in sub]
        m = [s["margem_votos"] for s in sub]
        return dict(mean=sum(v) / len(v), p_lula=sum(1 for s in sub if s["vencedor"] == "Lula") / len(sub),
                    q=wquant(v, [1] * len(v), Q), margem_med=wquant(m, [1] * len(m), [0.5])[0],
                    margem_q=wquant(m, [1] * len(m), [0.05, 0.95]))
    cs = {c: comp_stats(c) for c in W}
    p_lula = sum(s["peso"] for s in sims if s["vencedor"] == "Lula")
    qs = wquant(sh, wts, Q)
    mq = wquant(mg, wts, Q)
    mean_sh = sum(a * b for a, b in zip(sh, wts))

    # ---------- escrita de dados
    keys = ["sim", "componente", "peso", "lula_pct", "flavio_pct", "lula_votos", "flavio_votos", "margem_votos",
            "vencedor", "asym", "comparecimento_elim", "desl_transf", "choque_nac", "carry_viés", "viés_1T",
            "meta_share_lula"]
    with open(C.PROCESSED / "sims_2turno.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for s in sims:
            r = dict(s)
            for k in ("lula_pct", "flavio_pct"):
                r[k] = f"{r[k]:.5f}"
            for k in ("lula_votos", "flavio_votos", "margem_votos"):
                r[k] = f"{r[k]:.0f}"
            r["peso"] = f"{r['peso']:.3e}"
            for k in ("asym", "comparecimento_elim", "desl_transf", "choque_nac", "carry_viés", "viés_1T",
                      "meta_share_lula"):
                if isinstance(r.get(k), float):
                    r[k] = f"{r[k]:.4f}"
            w.writerow(r)
    with open(C.PROCESSED / "sims_2turno_uf.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sim", "componente"] + ufs)
        for r in sims_uf:
            w.writerow(r[:2] + [f"{x:.4f}" for x in r[2:]])

    # ---------- tabela por UF
    uf_rows = []
    idx = {u: i for i, u in enumerate(ufs)}
    for u in ufs:
        v = [r[2 + idx[u]] for r in sims_uf]
        q = wquant(v, wts, [0.05, 0.5, 0.95])
        pl = sum(wt for r, wt in zip(sims_uf, wts) if r[2 + idx[u]] > 0.5)
        l1 = N[u].get(LULA, 0) / sum(N[u].values())
        f1 = N[u].get(FLAV, 0) / sum(N[u].values())
        l2, b2 = base[u]
        uf_rows.append(dict(uf=u, nome=UFN[u], regiao=UF2REG[u], v1=sum(N[u].values()), l1=l1, f1=f1,
                            l2=q[1], lo=q[0], hi=q[2], p=pl, v2=l2 + b2, m1=(l2 - b2) / (l2 + b2)))
    with open(C.PROCESSED / "tabela_uf_2turno.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["uf", "nome", "regiao", "validos_1t_proj", "lula_1t", "flavio_1t", "lula_2t_mediana",
                    "lula_2t_p05", "lula_2t_p95", "p_lula_vence_uf", "validos_2t_M1"])
        for r in uf_rows:
            w.writerow([r["uf"], r["nome"], r["regiao"], f"{r['v1']:.0f}", f"{r['l1']:.4f}", f"{r['f1']:.4f}",
                        f"{r['l2']:.4f}", f"{r['lo']:.4f}", f"{r['hi']:.4f}", f"{r['p']:.3f}", f"{r['v2']:.0f}"])

    # ---------- sensibilidade: pesos e cenários M1 determinísticos
    weight_sets = [("Ensemble (base)", W), ("Só M1 (estrutural)", {"M1": 1, "M2": 0, "M3": 0}),
                   ("Só M2 (pesquisas corrigidas)", {"M1": 0, "M2": 1, "M3": 0}),
                   ("Só M3 (histórico)", {"M1": 0, "M2": 0, "M3": 1}),
                   ("Pesos iguais", {"M1": 1 / 3, "M2": 1 / 3, "M3": 1 / 3}),
                   ("Mais peso nas pesquisas (M2 60%)", {"M1": 0.3, "M2": 0.6, "M3": 0.1}),
                   ("Mais peso no estrutural (M1 70%)", {"M1": 0.7, "M2": 0.2, "M3": 0.1})]
    sens = [dict(rotulo=lab, pesos=wd, lula_media=sum(wd[c] * cs[c]["mean"] for c in wd),
                 p_lula=sum(wd[c] * cs[c]["p_lula"] for c in wd)) for lab, wd in weight_sets]
    scen = []

    def sc(label, **kw):
        sp_ = kw.pop("sp", split)
        r = runoff(N, alfa, sp_, rho0, kw.pop("d", delta), kw.pop("vr", None), kw.pop("asym", None))
        l, b = total(r)
        scen.append(dict(rotulo=label, lula_pct=l / (l + b), margem=l - b))
    sc("M1 base (assimetria 0,5; comparecimento 2022)")
    sc("M1: comparecimento dos eliminados = pesquisa literal", vr=lit)
    sc("M1: bases mantêm 100% (sem mobilização pró-Bolsonaro de 2022)", asym=0.0)
    sc("M1: mobilização de 2022 se repete por inteiro", asym=1.0)
    sc("M1: eliminados 50/50", sp={c: 0.5 for c in elim})
    sc("M1: eliminados como em 2022 (48% Bolsonaro)", sp={c: sp22 for c in elim})
    sc("M1: eliminados 10 pp mais pró-Flávio", sp={c: expit(logit(s) + 0.4) for c, s in split.items()})
    sc("M1: eliminados 10 pp mais pró-Lula", sp={c: expit(logit(s) - 0.4) for c, s in split.items()})
    sc("M1: sem inclinação regional", d={r: 0.0 for r in REG})
    sc("M1: todos os eliminados votam em Lula (limite)", sp={c: 0.0 for c in elim})

    # ---------- tornado (M1): efeito de cada parâmetro no share de Lula
    m1 = [s for s in sims if s["componente"] == "M1"]

    def tercile_effect(key, pool):
        v = sorted(pool, key=lambda s: s[key])
        n = len(v) // 3
        return sum(s["lula_pct"] for s in v[:n]) / n, sum(s["lula_pct"] for s in v[-n:]) / n
    tornado = [("Mobilização de 2022 se repete (0 → 1)", "asym"),
               ("Comparecimento dos eliminados (pesquisa → 2022)", "comparecimento_elim"),
               ("Inclinação comum das pesquisas de transferência (± logit)", "desl_transf"),
               ("Choque nacional na margem (±1,5 pp)", "choque_nac")]
    torn = [dict(rotulo=lab, baixo=lo, alto=hi) for lab, k in tornado for lo, hi in [tercile_effect(k, m1)]]
    lo, hi = tercile_effect("carry_viés", [s for s in sims if s["componente"] == "M2"])
    torn.append(dict(rotulo="M2: quanto do viés do 1º turno persiste (0 → 1)", baixo=lo, alto=hi))

    # ---------- histograma e limiares
    bins = [(0.40 + 0.01 * i, 0.41 + 0.01 * i) for i in range(0, 16)]
    hist_bins = [dict(lo=lo_, hi=hi_, ens=sum(w_ for s, w_ in zip(sims, wts) if lo_ <= s["lula_pct"] < hi_),
                      **{c: sum(1 for s in sims if s["componente"] == c and lo_ <= s["lula_pct"] < hi_) / n_per
                         for c in W}) for lo_, hi_ in bins]
    thr = [dict(limiar=t, ens=sum(w_ for s, w_ in zip(sims, wts) if s["lula_pct"] > t),
                **{c: sum(1 for s in sims if s["componente"] == c and s["lula_pct"] > t) / n_per for c in W})
           for t in (0.50, 0.49, 0.48, 0.47, 0.46, 0.45)]
    mthr = [dict(margem=m_, ens=sum(w_ for s, w_ in zip(sims, wts) if s["margem_votos"] < -m_),
                 **{c: sum(1 for s in sims if s["componente"] == c and s["margem_votos"] < -m_) / n_per for c in W})
            for m_ in (0, 1e6, 2e6, 4e6, 6e6, 8e6, 10e6)]

    rg = defaultdict(lambda: [0.0, 0.0])
    for u, (l, b) in base.items():
        rg[UF2REG[u]][0] += l
        rg[UF2REG[u]][1] += b
    regioes = [dict(regiao=r_, lula=l / (l + b), flavio=b / (l + b), margem_pp=(l - b) / (l + b) * 100,
                    peso=(l + b) / (L2b + B2b)) for r_, (l, b) in
               sorted(rg.items(), key=lambda x: -(x[1][0] + x[1][1]))]

    summary = dict(
        gerado_em=date.today().isoformat(), n_por_componente=n_per, pesos=W,
        p_lula_vence=p_lula, share_lula_media=mean_sh,
        share_lula_quantis=dict(zip(map(str, Q), qs)), margem_quantis=dict(zip(map(str, Q), mq)),
        componentes={c: dict(media=cs[c]["mean"], p_lula=cs[c]["p_lula"], quantis=dict(zip(map(str, Q), cs[c]["q"])),
                             margem_mediana=cs[c]["margem_med"], margem_p05_p95=cs[c]["margem_q"]) for c in cs},
        primeiro_turno_proj=dict(lula=L1, flavio=F1, validos=V1),
        vies_pesquisas_1t=ps["b1"], vies_pesquisas_1t_dp=ps["sd_b"], carry_central=CARRY_CENTRAL,
        m2_central=m2_center, m2_media_bruta_pesquisas=ps["avg"], beta_hist=beta, hist_sd=sd_h,
        m3_central_lula=1 - m3_f, lider_entre_dois_1t=lead_s,
        calibracao_2022=dict(n_municipios=len(rows), rmse_global_pp=100 * rm_g, rmse_regional_pp=100 * rm_r,
                             rmse_ingenuo_pp=100 * naive, comparecimento_eliminados=rho0,
                             eliminados_para_bolsonaro_2022=sp22, retencao_lula=a0[0][0],
                             lula_para_bolsonaro=a0[1][0], bolsonaro_para_bolsonaro=a0[1][1],
                             bolsonaro_para_lula=a0[0][1], delta_regional=delta, tau_uf_pp=100 * tau_uf),
        transferencia=[dict(candidato=c, votos_validos_1t=elim_votes[c], fonte=src4.get(
            c, "suposição: " + ("esquerda minoritária" if c in LEFT else "direita/menor")),
            para_flavio=split[c], declara_voto=lit[c]) for c in sorted(elim, key=lambda c: -elim_votes[c])],
        transferencia_media_flavio=w_split,
        pesquisas_2t=ps["rows"],
        erro_pesquisas_1t={p: e for p, e in ps["err"].items()},
        historico=[dict(ano=a, lider=v[0], segundo=v[4], pct_lider_1t=v[1], pct_segundo_1t=v[2], pct_lider_2t=v[3])
                   for a, v in hist.items()],
        residuos_historico=res_h, uf=uf_rows, regioes=regioes, histograma=hist_bins, limiares=thr,
        margens_flavio=mthr, tornado=torn, sensibilidade_pesos=sens, cenarios_m1=scen,
        m1_deterministico=dict(lula_pct=L2b / (L2b + B2b), margem=L2b - B2b),
    )
    (C.PROCESSED / "resumo_2turno.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))
    log(f"P(Lula vence) = {100*p_lula:.1f}% | Lula {100*mean_sh:.2f}% | M1 {100*cs['M1']['mean']:.2f}% "
        f"M2 {100*cs['M2']['mean']:.2f}% M3 {100*cs['M3']['mean']:.2f}%")
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=N_PER, help="simulações por componente")
    a = ap.parse_args()
    run(a.n, log=lambda s: print(s, file=sys.stderr))


if __name__ == "__main__":
    main()
