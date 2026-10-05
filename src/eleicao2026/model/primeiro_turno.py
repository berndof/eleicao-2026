#!/usr/bin/env python3
"""Projeção do 1º turno presidencial 2026 a partir da apuração parcial do TSE.

Método (por município, depois agregado por UF e Brasil):
 1. Votos válidos esperados = votos apurados / fração do eleitorado apurado
    (municípios sem nenhuma seção apurada: votos válidos de 2022 × crescimento do eleitorado).
 2. Share de cada bloco (Lula / Flávio / outros) na parte FALTANTE =
    previsão de uma regressão ponderada (share 2022 + perfil do eleitorado + efeito UF)
    + correção parcial pelo desvio observado no próprio município (encolhimento).
 3. Incerteza por Monte Carlo, com ruído calibrado por validação cruzada (5 folds)
    e choques sistemáticos por UF e nacional.
Somente biblioteca padrão.

Uso: python -m eleicao2026.model.primeiro_turno [--cur CSV] [--tag NOME]
"""
import argparse
import csv
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

from eleicao2026 import config as C
from eleicao2026.config import LULA, FLAV
from eleicao2026.model.linalg import dot, wls

K_SHRINK = 3000.0  # votos "equivalentes" do prior vs. observação no município
N_SIM = 4000
SEED = 2026


# ----------------------------------------------------------------- carga
def load(cur_csv):
    cur = {}
    with open(cur_csv) as f:
        for r in csv.DictReader(f):
            k = (r["uf"], r["cd"])
            cand = {c[2:]: int(v) for c, v in r.items() if c.startswith("v_")}
            cur[k] = dict(
                uf=r["uf"], nome=r["nome"], ts=int(r["ts"]), st=int(r["st"]),
                te=int(r["te"]), est=int(r["est"]), vv=int(r["vv"]), cand=cand,
            )
    h22 = {}
    with open(C.INTERIM / "pres_2022_mun.csv") as f:
        for r in csv.DictReader(f):
            v = {c: int(x) for c, x in r.items() if c not in ("uf", "cd", "nome")}
            h22[(r["uf"], r["cd"])] = v
    prof = {}
    with open(C.INTERIM / "perfil_2026_mun.csv") as f:
        for r in csv.DictReader(f):
            t = int(r["tot"]) or 1
            prof[(r["uf"], r["cd"])] = dict(
                tot=t, fem=int(r["fem"]) / t, sup=int(r["sup"]) / t, analf=int(r["analf"]) / t,
                fund=int(r["fund_inc"]) / t, jovem=int(r["jovem"]) / t, idoso=int(r["idoso"]) / t)
    return cur, h22, prof


# ------------------------------------------------------------- features
def build(cur, h22, prof, ufs):
    feats = {}
    ufidx = {u: i for i, u in enumerate(ufs)}
    for k, c in cur.items():
        p = prof.get(k)
        if p is None:
            p = dict(tot=c["te"], fem=.52, sup=.1, analf=.07, fund=.3, jovem=.12, idoso=.2)
        v22 = h22.get(k)
        if v22:
            tot22 = sum(v22.values())  # inclui todos os candidatos
            l22 = v22.get("LULA", 0) / max(tot22, 1)
            f22 = v22.get(C.BOLSONARO_2022, 0) / max(tot22, 1)
            vv22 = tot22
        else:
            l22 = f22 = None
            vv22 = None
        feats[k] = dict(p=p, l22=l22, f22=f22, vv22=vv22)
    # preenche l22/f22 ausentes com média da UF
    acc = defaultdict(lambda: [0.0, 0.0, 0])
    for k, ft in feats.items():
        if ft["l22"] is not None:
            a = acc[cur[k]["uf"]]
            a[0] += ft["l22"]; a[1] += ft["f22"]; a[2] += 1
    for k, ft in feats.items():
        if ft["l22"] is None:
            a = acc[cur[k]["uf"]]
            n = max(a[2], 1)
            ft["l22"], ft["f22"] = a[0] / n, a[1] / n
    X = {}
    for k, ft in feats.items():
        p = ft["p"]
        row = [1.0, ft["l22"], ft["f22"], p["sup"], p["analf"], p["fund"], p["jovem"], p["idoso"],
               p["fem"], math.log(max(p["tot"], 50))]
        dummies = [0.0] * len(ufs)
        dummies[ufidx[cur[k]["uf"]]] = 1.0
        X[k] = row + dummies[1:]
    return X, feats


def run(cur_csv=None, out_mun=None, out_uf=None, out_nat=None, out_coef=None, log=print):
    cur_csv = Path(cur_csv or C.INTERIM / "mun_2026.csv")
    out_mun = Path(out_mun or C.INTERIM / "projecao_mun.csv")
    out_uf = Path(out_uf or C.PROCESSED / "projecao_1turno_uf.csv")
    out_nat = Path(out_nat or C.PROCESSED / "projecao_1turno_nacional.json")
    out_coef = Path(out_coef or C.PROCESSED / "projecao_1turno_coeficientes.csv")
    for p in (out_mun, out_uf, out_nat, out_coef):
        p.parent.mkdir(parents=True, exist_ok=True)

    cur, h22, prof = load(cur_csv)
    with open(C.INTERIM / "perfil_2022_mun.csv") as f:
        te22 = {(r["uf"], r["cd"]): int(r["tot"]) for r in csv.DictReader(f)}
    ufs = sorted({c["uf"] for c in cur.values()})
    X, feats = build(cur, h22, prof, ufs)

    keys = list(cur)
    fit = [k for k in keys if cur[k]["vv"] > 0 and cur[k]["est"] / max(cur[k]["te"], 1) >= 0.5]
    log(f"municípios no ajuste: {len(fit)} / {len(keys)}")

    def share(k, name):
        c = cur[k]
        return c["cand"].get(name, 0) / c["vv"]

    def targets(k):
        return share(k, LULA), share(k, FLAV)

    rnd = random.Random(SEED)
    folds = {k: rnd.randrange(5) for k in fit}
    cv = {}  # resíduos CV (l, f)
    for fo in range(5):
        tr = [k for k in fit if folds[k] != fo]
        te = [k for k in fit if folds[k] == fo]
        Xt = [X[k] for k in tr]
        w = [cur[k]["vv"] for k in tr]
        bl = wls(Xt, [targets(k)[0] for k in tr], w)
        bf = wls(Xt, [targets(k)[1] for k in tr], w)
        for k in te:
            tl, tf = targets(k)
            cv[k] = (tl - dot(X[k], bl), tf - dot(X[k], bf))
    Xa = [X[k] for k in fit]
    wa = [cur[k]["vv"] for k in fit]
    BL = wls(Xa, [targets(k)[0] for k in fit], wa)
    BF = wls(Xa, [targets(k)[1] for k in fit], wa)

    sw = sum(wa)
    rmse_l = math.sqrt(sum(cur[k]["vv"] * cv[k][0] ** 2 for k in fit) / sw)
    rmse_f = math.sqrt(sum(cur[k]["vv"] * cv[k][1] ** 2 for k in fit) / sw)
    log(f"CV RMSE ponderado (pp): Lula {100*rmse_l:.2f}  Flávio {100*rmse_f:.2f}")

    # variância do resíduo da margem (L-F) em função de 1/vv:  s² = a + b/vv
    xs = [1 / cur[k]["vv"] for k in fit]
    ys = [(cv[k][0] - cv[k][1]) ** 2 for k in fit]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    a = max(my - b * mx, 0.0004)
    b = max(b, 0.0)

    # viés médio por UF (para calibrar choque sistemático)
    ufm = defaultdict(lambda: [0.0, 0.0])
    for k in fit:
        u = cur[k]["uf"]
        ufm[u][0] += cur[k]["vv"] * (cv[k][0] - cv[k][1])
        ufm[u][1] += cur[k]["vv"]
    ufbias = [v[0] / v[1] for v in ufm.values()]
    tau_uf = max(math.sqrt(sum(x * x for x in ufbias) / len(ufbias)), 0.01)
    tau_nat = 0.01
    log(f"choque UF (margem) tau={100*tau_uf:.2f}pp  nacional={100*tau_nat:.2f}pp")

    # --------------------------------------------- projeção por município
    proj = {}
    for k in keys:
        c = cur[k]
        f = c["est"] / c["te"] if c["te"] else 0.0
        if c["vv"] > 0 and f > 0.02:
            V = c["vv"] / f
        else:
            vv22 = feats[k]["vv22"] or c["te"] * 0.75
            V = vv22 * (c["te"] / max(te22.get(k, c["te"]), 1))
        M = max(V - c["vv"], 0.0)
        pl = min(max(dot(X[k], BL), 0.0), 1.0)
        pf = min(max(dot(X[k], BF), 0.0), 1.0)
        if c["vv"] > 0:
            lam = c["vv"] / (c["vv"] + K_SHRINK)
            ml = pl + lam * (c["cand"].get(LULA, 0) / c["vv"] - pl)
            mf = pf + lam * (c["cand"].get(FLAV, 0) / c["vv"] - pf)
        else:
            ml, mf = pl, pf
        s = ml + mf
        if s > 1:
            ml, mf = ml / s, mf / s
        proj[k] = dict(uf=c["uf"], M=M, ml=ml, mf=mf, vv=c["vv"],
                       vl=c["cand"].get(LULA, 0), vf=c["cand"].get(FLAV, 0),
                       sd=math.sqrt(a + b / max(M + c["vv"], 1.0)), f=f)

    with open(out_mun, "w", newline="") as f_:
        w_ = csv.writer(f_)
        w_.writerow(["uf", "cd", "vv_apurado", "faltantes", "share_lula_falt", "share_flavio_falt"])
        for k, p in proj.items():
            w_.writerow([k[0], k[1], p["vv"], f"{p['M']:.1f}", f"{p['ml']:.5f}", f"{p['mf']:.5f}"])

    def totals(shock_nat, shock_uf, noise):
        agg = defaultdict(lambda: [0.0, 0.0, 0.0])  # L, F, total
        for k, p in proj.items():
            M = p["M"]
            e = 0.0
            if noise:
                e = shock_nat + shock_uf[p["uf"]] + rnd.gauss(0, p["sd"])
            ml = min(max(p["ml"] + e / 2, 0), 1)
            mf = min(max(p["mf"] - e / 2, 0), 1)
            s = ml + mf
            if s > 1:
                ml, mf = ml / s, mf / s
            g = agg[p["uf"]]
            g[0] += p["vl"] + M * ml
            g[1] += p["vf"] + M * mf
            g[2] += p["vv"] + M
        return agg

    pt = totals(0, defaultdict(float), False)
    L = sum(v[0] for v in pt.values()); F = sum(v[1] for v in pt.values()); T = sum(v[2] for v in pt.values())
    cur_L = sum(c["cand"].get(LULA, 0) for c in cur.values())
    cur_F = sum(c["cand"].get(FLAV, 0) for c in cur.values())
    cur_T = sum(c["vv"] for c in cur.values())
    log(f"ATUAL    : Lula {100*cur_L/cur_T:.2f}%  Flávio {100*cur_F/cur_T:.2f}%  (válidos {cur_T:,})")
    log(f"PROJETADO: Lula {100*L/T:.2f}%  Flávio {100*F/T:.2f}%  Outros {100*(T-L-F)/T:.2f}%  (válidos {T:,.0f})")

    # Monte Carlo
    wins, noruns, shares = 0, 0, []
    ufwin = defaultdict(int)
    for _ in range(N_SIM):
        sn = rnd.gauss(0, tau_nat)
        su = {u: rnd.gauss(0, tau_uf) for u in ufs}
        ag = totals(sn, su, True)
        l = sum(v[0] for v in ag.values()); f = sum(v[1] for v in ag.values()); t = sum(v[2] for v in ag.values())
        shares.append((l / t, f / t))
        wins += l > f
        noruns += (l / t > 0.5) or (f / t > 0.5)
        for u, v in ag.items():
            ufwin[u] += v[0] > v[1]
    shares.sort(key=lambda x: x[0] - x[1])
    lo, hi = shares[int(0.05 * N_SIM)], shares[int(0.95 * N_SIM)]
    log(f"P(Lula à frente no 1º turno) = {100*wins/N_SIM:.1f}%  |  P(>50% válidos) = {100*noruns/N_SIM:.1f}%")
    log(f"margem Lula-Flávio, IC90%: {100*(lo[0]-lo[1]):+.2f}pp a {100*(hi[0]-hi[1]):+.2f}pp")

    out = [["uf", "apur_eleit", "lula_pct", "flavio_pct", "outros_pct", "p_lula_lidera",
            "validos_proj", "validos_atual", "lula_proj", "flavio_proj"]]
    for u in ufs:
        v = pt[u]
        cc = [c for c in cur.values() if c["uf"] == u]
        ap = sum(c["est"] for c in cc) / sum(c["te"] for c in cc)
        pl_, pf_ = v[0] / v[2], v[1] / v[2]
        out.append([u, f"{ap:.4f}", f"{pl_:.4f}", f"{pf_:.4f}", f"{1-pl_-pf_:.4f}", f"{ufwin[u]/N_SIM:.3f}",
                    f"{v[2]:.0f}", sum(c["vv"] for c in cc), f"{v[0]:.0f}", f"{v[1]:.0f}"])
    with open(out_uf, "w", newline="") as f_:
        csv.writer(f_).writerows(out)

    names = ["const", "lula22", "flavio22", "superior", "analf", "fund_inc", "jovem", "idoso", "fem", "log_eleit"]
    with open(out_coef, "w", newline="") as f_:
        w_ = csv.writer(f_)
        w_.writerow(["variavel", "coef_share_lula", "coef_share_flavio"])
        for n_, bl, bf in zip(names, BL, BF):
            w_.writerow([n_, f"{bl:.4f}", f"{bf:.4f}"])
    nat = dict(
        lula=L / T, flavio=F / T, outros=(T - L - F) / T, validos_proj=T,
        lula_atual=cur_L / cur_T, flavio_atual=cur_F / cur_T, validos_atual=cur_T,
        pct_eleitorado_apurado=sum(c["est"] for c in cur.values()) / sum(c["te"] for c in cur.values()),
        p_lula_lidera=wins / N_SIM, p_vencedor_1t=noruns / N_SIM,
        margem_ic90=[lo[0] - lo[1], hi[0] - hi[1]], cv_rmse_pp=dict(lula=100 * rmse_l, flavio=100 * rmse_f),
        tau_uf_pp=100 * tau_uf, tau_nacional_pp=100 * tau_nat, n_municipios=len(keys), n_ajuste=len(fit),
    )
    out_nat.write_text(json.dumps(nat, indent=1, ensure_ascii=False))
    return nat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cur", help="CSV de apuração por município (padrão: data/interim/mun_2026.csv)")
    ap.add_argument("--tag", help="sufixo para as saídas (ex.: snap85), para não sobrescrever as principais")
    a = ap.parse_args()
    kw = {}
    if a.tag:
        kw = dict(out_mun=C.INTERIM / f"projecao_mun_{a.tag}.csv",
                  out_uf=C.INTERIM / f"projecao_1turno_uf_{a.tag}.csv",
                  out_nat=C.INTERIM / f"projecao_1turno_nacional_{a.tag}.json",
                  out_coef=C.INTERIM / f"projecao_1turno_coef_{a.tag}.csv")
    run(a.cur, log=lambda s: print(s, file=sys.stderr), **kw)


if __name__ == "__main__":
    main()
