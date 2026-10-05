#!/usr/bin/env python3
"""Exemplos numéricos "passo a passo": mostra, com números reais, o que cada camada faz.

  1. MUNICÍPIO (camadas 1-3): um município com apuração parcial no snapshot das ~20h (85% do país):
     dados brutos -> votos válidos esperados -> regressão -> encolhimento -> projeção -> resultado final.
  2. UF (camadas 5-7): do 1º turno projetado de uma UF ao 2º turno do modelo M1, termo a termo.
  3. DECOMPOSIÇÃO NACIONAL do M1: de onde vem cada voto de Lula e de Flávio no 2º turno.

Saídas (data/processed/): exemplo_municipio.json, exemplo_uf.json, m1_decomposicao.json
Somente biblioteca padrão.

Uso: python -m eleicao2026.model.explicar [--mun ba:36692] [--uf mg]
"""
import argparse
import csv
import json
import sys
from collections import defaultdict

from eleicao2026 import config as C
from eleicao2026.config import LULA, FLAV, UF2REG, UFN
from eleicao2026.model import ensemble as E
from eleicao2026.model import primeiro_turno as P
from eleicao2026.model import segundo_turno as S
from eleicao2026.model.linalg import dot, expit, logit, wls

VARS = ["const", "lula22", "flavio22", "superior", "analf", "fund_inc", "jovem", "idoso", "fem", "log_eleit"]


def exemplo_municipio(key=("pe", "23817"), snap=None):
    snap = snap or C.SNAPSHOT_85 / "mun_2026.csv"
    cur, h22, prof = P.load(snap)
    with open(C.INTERIM / "perfil_2022_mun.csv") as f:
        te22 = {(r["uf"], r["cd"]): int(r["tot"]) for r in csv.DictReader(f)}
    ufs = sorted({c["uf"] for c in cur.values()})
    X, feats = P.build(cur, h22, prof, ufs)
    fit = [k for k in cur if cur[k]["vv"] > 0 and cur[k]["est"] / max(cur[k]["te"], 1) >= 0.5]
    Xa = [X[k] for k in fit]
    wa = [cur[k]["vv"] for k in fit]
    BL = wls(Xa, [cur[k]["cand"].get(LULA, 0) / cur[k]["vv"] for k in fit], wa)
    BF = wls(Xa, [cur[k]["cand"].get(FLAV, 0) / cur[k]["vv"] for k in fit], wa)
    c = cur[key]
    f = c["est"] / c["te"]
    V = c["vv"] / f
    M = V - c["vv"]
    pl, pf = dot(X[key], BL), dot(X[key], BF)
    lam = c["vv"] / (c["vv"] + P.K_SHRINK)
    obs_l, obs_f = c["cand"][LULA] / c["vv"], c["cand"][FLAV] / c["vv"]
    ml, mf = pl + lam * (obs_l - pl), pf + lam * (obs_f - pf)
    proj_l, proj_f = c["cand"][LULA] + M * ml, c["cand"][FLAV] + M * mf
    ft = feats[key]
    fin = {(r["uf"], r["cd"]): r for r in csv.DictReader(open(C.INTERIM / "mun_2026.csv"))}[key]
    out = dict(
        municipio=c["nome"], uf=key[0], secoes_total=c["ts"], secoes_apuradas=c["st"], eleitorado=c["te"],
        eleitorado_apurado=c["est"], frac_apurada=f, validos_apurados=c["vv"], lula_apurado=c["cand"][LULA],
        flavio_apurado=c["cand"][FLAV], lula_share_obs=obs_l, flavio_share_obs=obs_f,
        validos_esperados=V, faltantes=M, lula22=ft["l22"], bolsonaro22=ft["f22"], perfil=ft["p"],
        prev_lula=pl, prev_flavio=pf, lam=lam, falt_share_lula=ml, falt_share_flavio=mf,
        proj_lula=proj_l, proj_flavio=proj_f, proj_lula_share=proj_l / V, proj_flavio_share=proj_f / V,
        final_validos=int(fin["vv"]), final_lula=int(fin["v_LULA"]), final_flavio=int(fin["v_FLAVIO BOLSONARO"]),
        final_lula_share=int(fin["v_LULA"]) / int(fin["vv"]), final_flavio_share=int(fin["v_FLAVIO BOLSONARO"]) / int(fin["vv"]),
        coef=dict(zip(VARS, zip(BL, BF))),
    )
    # confere com a saída publicada do snapshot
    for r in csv.DictReader(open(C.SNAPSHOT_85 / "projecao_mun.csv")):
        if (r["uf"], r["cd"]) == key:
            assert abs(float(r["share_lula_falt"]) - ml) < 1e-4, (r, ml)
    return out


def decompor(N, alfa, split, rho, delta, vote_rate=None, asym=None):
    """Mesma conta de segundo_turno.runoff, separando a origem de cada voto (Lula / Flávio)."""
    w = S.ASYM_BASE if asym is None else asym
    dec = dict(lula=dict(propria=0.0, rival=0.0, elim=defaultdict(float)),
               flavio=dict(propria=0.0, rival=0.0, elim=defaultdict(float)))
    for uf, Nuf in N.items():
        a = S.coef(alfa, UF2REG[uf])
        L1, F1 = Nuf.get(LULA, 0.0), Nuf.get(FLAV, 0.0)
        dec["lula"]["propria"] += L1 * (w * a[0][0] + (1 - w))
        dec["lula"]["rival"] += F1 * (w * a[0][1])
        dec["flavio"]["propria"] += F1 * (w * a[1][1] + (1 - w))
        dec["flavio"]["rival"] += L1 * (w * a[1][0])
        for c, n in Nuf.items():
            if c in (LULA, FLAV):
                continue
            s = expit(logit(split[c]) + delta.get(UF2REG[uf], 0.0))
            r = (vote_rate or {}).get(c, rho)
            dec["flavio"]["elim"][c] += n * r * s
            dec["lula"]["elim"][c] += n * r * (1 - s)
    return dec


def exemplo_uf(uf, cal, N, split, lit):
    reg = UF2REG[uf]
    a = S.coef(cal["alfa"], reg)
    rho0, delta = cal["rho0"], cal["delta"]
    Nuf = N[uf]
    L1, F1 = Nuf.get(LULA, 0.0), Nuf.get(FLAV, 0.0)
    w = S.ASYM_BASE
    tot1 = sum(Nuf.values())
    out = dict(uf=uf, nome=UFN[uf], regiao=reg, validos_1t=tot1, lula_1t=L1, flavio_1t=F1, eliminados_1t=tot1 - L1 - F1,
               coef_lula=a[0], coef_flavio=a[1], regioes_proprias=reg in cal["alfa"], delta_regional=delta.get(reg, 0.0),
               peso_assimetria=w, rho0=rho0)
    out["lula_retem"] = L1 * (w * a[0][0] + (1 - w))
    out["lula_da_base_flavio"] = F1 * w * a[0][1]
    out["flavio_retem"] = F1 * (w * a[1][1] + (1 - w))
    out["flavio_da_base_lula"] = L1 * w * a[1][0]
    elim = []
    lb = fb = 0.0
    for c, n in sorted(Nuf.items(), key=lambda x: -x[1]):
        if c in (LULA, FLAV):
            continue
        s = expit(logit(split[c]) + delta.get(reg, 0.0))
        b, l = n * rho0 * s, n * rho0 * (1 - s)
        fb += b
        lb += l
        elim.append(dict(candidato=c, votos=n, split_nacional=split[c], split_uf=s, comparece=rho0, para_flavio=b, para_lula=l))
    out["eliminados"] = elim
    out["lula_2t"] = out["lula_retem"] + out["lula_da_base_flavio"] + lb
    out["flavio_2t"] = out["flavio_retem"] + out["flavio_da_base_lula"] + fb
    out["lula_2t_pct"] = out["lula_2t"] / (out["lula_2t"] + out["flavio_2t"])
    res = S.runoff(N, cal["alfa"], split, rho0, delta)
    assert abs(res[uf][0] - out["lula_2t"]) < 1e-6 * out["lula_2t"], (res[uf][0], out["lula_2t"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mun", default="pe:23817", help="uf:código TSE do município")
    ap.add_argument("--uf", default="mg")
    a = ap.parse_args()
    uf_, cd_ = a.mun.split(":")
    em = exemplo_municipio((uf_, cd_))
    (C.PROCESSED / "exemplo_municipio.json").write_text(json.dumps(em, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in em.items() if k not in ("coef",)}, indent=1, ensure_ascii=False), file=sys.stderr)

    cal = E.calibrate(lambda *_: None)
    cur, pm = S.load26()
    N, _ = S.first_round(cur, pm)
    elim = sorted({c for u in N.values() for c in u if c not in (LULA, FLAV)})
    split4, lit4, src4, f_agg, lit_agg = E.build_split()
    split = {c: (split4[c] if c in split4 else (E.MINOR_LEFT if c in E.LEFT else E.MINOR_RIGHT)) for c in elim}
    eu = exemplo_uf(a.uf, cal, N, split, None)
    (C.PROCESSED / "exemplo_uf.json").write_text(json.dumps(eu, indent=1, ensure_ascii=False))
    print(json.dumps(eu, indent=1, ensure_ascii=False), file=sys.stderr)

    dec = decompor(N, cal["alfa"], split, cal["rho0"], cal["delta"])
    V1 = sum(sum(v.values()) for v in N.values())
    out = dict(
        lula_1t=sum(v.get(LULA, 0) for v in N.values()), flavio_1t=sum(v.get(FLAV, 0) for v in N.values()), validos_1t=V1,
        peso_assimetria=S.ASYM_BASE, rho0=cal["rho0"], split=split,
        lula=dict(propria=dec["lula"]["propria"], rival=dec["lula"]["rival"], elim=dict(dec["lula"]["elim"])),
        flavio=dict(propria=dec["flavio"]["propria"], rival=dec["flavio"]["rival"], elim=dict(dec["flavio"]["elim"])))
    for k in ("lula", "flavio"):
        out[k]["total"] = out[k]["propria"] + out[k]["rival"] + sum(out[k]["elim"].values())
    (C.PROCESSED / "m1_decomposicao.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps(out, indent=1, ensure_ascii=False), file=sys.stderr)


if __name__ == "__main__":
    main()
