#!/usr/bin/env python3
"""Resultado do 1º turno por UF e backtest da projeção feita com ~85% apurado.

Compara, contra a apuração atual (data/interim/mun_2026.csv):
  (a) parcial: share de Lula/Flávio entre os votos já apurados no snapshot (sem projetar)
  (b) projeção do modelo no snapshot (data/snapshots/20261004_2005_apuracao85)
com o resultado final, por UF e por município.

Saídas (data/processed/): resultado_1turno_uf.csv, resultado_1turno_uf_candidato.csv,
                          backtest_1turno_uf.csv, backtest_1turno.json
Somente biblioteca padrão.
"""
import csv
import json
import math
from collections import defaultdict

from eleicao2026 import config as C
from eleicao2026.config import LULA, FLAV


def read_cur(path):
    out = {}
    for r in csv.DictReader(open(path)):
        out[(r["uf"], r["cd"])] = dict(
            uf=r["uf"], vv=int(r["vv"]), te=int(r["te"]), est=int(r["est"]),
            cand={c[2:]: int(v) for c, v in r.items() if c.startswith("v_")})
    return out


def run(log=print):
    C.PROCESSED.mkdir(parents=True, exist_ok=True)
    fin = read_cur(C.INTERIM / "mun_2026.csv")
    snap = read_cur(C.SNAPSHOT_85 / "mun_2026.csv")
    proj = {(r["uf"], r["cd"]): dict(M=float(r["faltantes"]), ml=float(r["share_lula_falt"]),
                                     mf=float(r["share_flavio_falt"]))
            for r in csv.DictReader(open(C.SNAPSHOT_85 / "projecao_mun.csv"))}

    # ---- resultado final por UF (e por candidato)
    uf = defaultdict(lambda: defaultdict(int))
    for k, c in fin.items():
        u = uf[c["uf"]]
        u["vv"] += c["vv"]; u["te"] += c["te"]; u["est"] += c["est"]
        for n, v in c["cand"].items():
            u["c:" + n] += v
    ufs = sorted(uf)
    cands = sorted({n[2:] for u in uf.values() for n in u if n.startswith("c:")})
    with open(C.PROCESSED / "resultado_1turno_uf_candidato.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["uf", "candidato", "votos", "pct_validos"])
        for u in ufs:
            for n in cands:
                v = uf[u]["c:" + n]
                w.writerow([u, n, v, f"{v/uf[u]['vv']:.5f}"])
    with open(C.PROCESSED / "resultado_1turno_uf.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["uf", "validos", "eleitorado", "eleitorado_apurado", "lula", "flavio", "outros", "lula_pct",
                    "flavio_pct", "outros_pct", "margem_lula_flavio_pp"])
        for u in ufs:
            d = uf[u]
            l, fl = d["c:" + LULA], d["c:" + FLAV]
            w.writerow([u, d["vv"], d["te"], d["est"], l, fl, d["vv"] - l - fl, f"{l/d['vv']:.5f}",
                        f"{fl/d['vv']:.5f}", f"{(d['vv']-l-fl)/d['vv']:.5f}", f"{100*(l-fl)/d['vv']:.3f}"])

    # ---- backtest por município e UF
    agg = defaultdict(lambda: defaultdict(float))
    mun_err = []  # (peso, erro share Lula, erro share Flávio, erro margem)
    for k, s in snap.items():
        f = fin.get(k)
        p = proj.get(k)
        if f is None or p is None:
            continue
        a = agg[s["uf"]]
        a["apur_snap"] += s["est"]; a["te"] += s["te"]
        a["vv_part"] += s["vv"]
        a["l_part"] += s["cand"].get(LULA, 0); a["f_part"] += s["cand"].get(FLAV, 0)
        Lp = s["cand"].get(LULA, 0) + p["M"] * p["ml"]
        Fp = s["cand"].get(FLAV, 0) + p["M"] * p["mf"]
        Vp = s["vv"] + p["M"]
        a["vv_proj"] += Vp; a["l_proj"] += Lp; a["f_proj"] += Fp
        a["vv_fin"] += f["vv"]; a["l_fin"] += f["cand"].get(LULA, 0); a["f_fin"] += f["cand"].get(FLAV, 0)
        if f["vv"] > 0 and Vp > 0:
            el = Lp / Vp - f["cand"].get(LULA, 0) / f["vv"]
            ef = Fp / Vp - f["cand"].get(FLAV, 0) / f["vv"]
            mun_err.append((f["vv"], el, ef, (Lp - Fp) / Vp - (f["cand"].get(LULA, 0) - f["cand"].get(FLAV, 0)) / f["vv"],
                            s["est"] / max(s["te"], 1)))

    rows, tot = [], defaultdict(float)
    for u in ufs:
        a = agg[u]
        for k, v in a.items():
            tot[k] += v
        row = dict(
            uf=u, apur_snapshot=a["apur_snap"] / a["te"],
            lula_parcial=a["l_part"] / a["vv_part"], flavio_parcial=a["f_part"] / a["vv_part"],
            lula_proj=a["l_proj"] / a["vv_proj"], flavio_proj=a["f_proj"] / a["vv_proj"],
            lula_final=a["l_fin"] / a["vv_fin"], flavio_final=a["f_fin"] / a["vv_fin"],
            validos_proj=a["vv_proj"], validos_final=a["vv_fin"])
        row["erro_lula_proj_pp"] = 100 * (row["lula_proj"] - row["lula_final"])
        row["erro_flavio_proj_pp"] = 100 * (row["flavio_proj"] - row["flavio_final"])
        row["erro_margem_proj_pp"] = row["erro_lula_proj_pp"] - row["erro_flavio_proj_pp"]
        row["erro_margem_parcial_pp"] = 100 * ((row["lula_parcial"] - row["flavio_parcial"])
                                               - (row["lula_final"] - row["flavio_final"]))
        row["erro_validos_pct"] = 100 * (row["validos_proj"] / row["validos_final"] - 1)
        rows.append(row)
    cols = list(rows[0].keys())
    with open(C.PROCESSED / "backtest_1turno_uf.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow([r[c] if isinstance(r[c], str) else f"{r[c]:.5f}" for c in cols])

    def wrms(i):
        sw = sum(e[0] for e in mun_err)
        return math.sqrt(sum(e[0] * e[i] ** 2 for e in mun_err) / sw)

    def wmae(i):
        sw = sum(e[0] for e in mun_err)
        return sum(e[0] * abs(e[i]) for e in mun_err) / sw
    uf_w = {r["uf"]: r["validos_final"] for r in rows}
    sw = sum(uf_w.values())
    nat = dict(
        apuracao_snapshot=tot["apur_snap"] / tot["te"],
        parcial=dict(lula=tot["l_part"] / tot["vv_part"], flavio=tot["f_part"] / tot["vv_part"]),
        projetado=dict(lula=tot["l_proj"] / tot["vv_proj"], flavio=tot["f_proj"] / tot["vv_proj"],
                       validos=tot["vv_proj"]),
        final=dict(lula=tot["l_fin"] / tot["vv_fin"], flavio=tot["f_fin"] / tot["vv_fin"], validos=tot["vv_fin"]),
        erro_projecao_pp=dict(
            lula=100 * (tot["l_proj"] / tot["vv_proj"] - tot["l_fin"] / tot["vv_fin"]),
            flavio=100 * (tot["f_proj"] / tot["vv_proj"] - tot["f_fin"] / tot["vv_fin"]),
            validos_pct=100 * (tot["vv_proj"] / tot["vv_fin"] - 1)),
        erro_parcial_pp=dict(
            lula=100 * (tot["l_part"] / tot["vv_part"] - tot["l_fin"] / tot["vv_fin"]),
            flavio=100 * (tot["f_part"] / tot["vv_part"] - tot["f_fin"] / tot["vv_fin"])),
        uf=dict(
            mae_margem_proj_pp=sum(uf_w[r["uf"]] * abs(r["erro_margem_proj_pp"]) for r in rows) / sw,
            mae_margem_parcial_pp=sum(uf_w[r["uf"]] * abs(r["erro_margem_parcial_pp"]) for r in rows) / sw,
            max_abs_erro_margem_proj_pp=max(abs(r["erro_margem_proj_pp"]) for r in rows),
            pior_uf=max(rows, key=lambda r: abs(r["erro_margem_proj_pp"]))["uf"],
            vencedor_correto=sum((r["lula_proj"] > r["flavio_proj"]) == (r["lula_final"] > r["flavio_final"])
                                 for r in rows), n=len(rows)),
        municipio=dict(n=len(mun_err), rmse_lula_pp=100 * wrms(1), rmse_flavio_pp=100 * wrms(2),
                       mae_lula_pp=100 * wmae(1), mae_flavio_pp=100 * wmae(2), mae_margem_pp=100 * wmae(3)),
    )
    (C.PROCESSED / "backtest_1turno.json").write_text(json.dumps(nat, indent=1, ensure_ascii=False))
    log(f"backtest: parcial L {100*nat['parcial']['lula']:.2f} F {100*nat['parcial']['flavio']:.2f} | "
        f"proj L {100*nat['projetado']['lula']:.2f} F {100*nat['projetado']['flavio']:.2f} | "
        f"final L {100*nat['final']['lula']:.2f} F {100*nat['final']['flavio']:.2f}")
    return nat


def main():
    run()


if __name__ == "__main__":
    main()
