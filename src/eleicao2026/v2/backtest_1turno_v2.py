#!/usr/bin/env python3
"""Backtest Comparativo da Projeção das 20h (Snapshot 85% do 1º Turno).

Compara o desempenho de:
  (1) Parcial puro às 20h (sem modelo, o que a TV mostrava)
  (2) Projeção V1 das 20h (Baseline publicado: votos 2022 + perfil eleitorado TSE)
  (3) Projeção V2 das 20h (Aprimorado: V1 + Censo 2022 religião/renda/raça + Prefeitos 2024)

Mede o erro contra o resultado 100% final da urna em nível nacional, por UF e por município.
Gera a Figura 28 (PT/EN) e data/processed/backtest_1turno_v2.json.
"""
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

from eleicao2026 import config as C
from eleicao2026.config import LULA, FLAV
from eleicao2026.model.primeiro_turno import load as load_v1, build as build_v1
from eleicao2026.v2.calibrar_shrinkage import carregar_gabarito, ajustar_wls_np
from eleicao2026.v2.m1_v2 import carregar_dados_v2


def carregar_dados_censo_prefeitos():
    """Carrega Censo 2022 e Prefeitos 2024 para cada município."""
    censo = {}
    with open(C.EXTERNAL / "censo2022_mun.csv") as f:
        for r in csv.DictReader(f):
            k = (r["uf"], r["cd_tse"])
            censo[k] = {
                "evang": float(r["pct_evangelica_10mais"]) / 100.0 if r["pct_evangelica_10mais"] else 0.30,
                "catol": float(r["pct_catolica_10mais"]) / 100.0 if r["pct_catolica_10mais"] else 0.50,
                "preta_parda": float(r["pct_preta_parda_2022"]) / 100.0 if r["pct_preta_parda_2022"] else 0.50,
                "urb": float(r["pct_urbana_2022"]) / 100.0 if r["pct_urbana_2022"] else 0.70,
                "renda_med": float(r["renda_mediana_percapita_2022"]) if r["renda_mediana_percapita_2022"] else 600.0,
            }

    prefeitos = {}
    with open(C.EXTERNAL / "prefeitos_2024_mun.csv") as f:
        for r in csv.DictReader(f):
            k = (r["uf"], r["cd_tse"])
            prefeitos[k] = r.get("sg_partido", "").strip().upper()

    return censo, prefeitos


def build_v2_features(cur, h22, prof, ufs, censo, prefeitos):
    """Constrói matriz de features V2 expandida com Censo 2022 e Prefeitos 2024."""
    X_v1, feats = build_v1(cur, h22, prof, ufs)
    X_v2 = {}
    ufidx = {u: i for i, u in enumerate(ufs)}

    for k in cur.keys():
        ft = feats[k]
        p = ft["p"]
        c = censo.get(k, {"evang": 0.30, "catol": 0.50, "preta_parda": 0.50, "urb": 0.70, "renda_med": 600.0})
        pref = prefeitos.get(k, "")

        # Dummies partidárias dos prefeitos de 2024
        is_pl = 1.0 if pref == "PL" else 0.0
        is_pt_psb = 1.0 if pref in ("PT", "PSB", "PC DO B", "PV", "PSOL") else 0.0
        is_centrao = 1.0 if pref in ("PP", "REPUBLICANOS", "PSD", "MDB", "UNIÃO") else 0.0

        # Features base + demografia do Censo 2022 + Prefeitos 2024
        row = [
            1.0, ft["l22"], ft["f22"], p["sup"], p["analf"], p["fund"], p["jovem"], p["idoso"], p["fem"],
            math.log(max(p["tot"], 50)),
            c["evang"], c["catol"], c["preta_parda"], c["urb"], math.log(max(c["renda_med"], 50.0)),
            is_pl, is_pt_psb, is_centrao
        ]
        dummies = [0.0] * len(ufs)
        dummies[ufidx[cur[k]["uf"]]] = 1.0
        X_v2[k] = row + dummies[1:]

    return X_v1, X_v2, feats


def projetar_snapshot(cur, X_dict, feats, te22, k_shrink=3000.0, cutoff=0.50):
    """Executa a projeção sobre o snapshot com uma matriz de features X."""
    keys = list(cur)
    fit = [k for k in keys if cur[k]["vv"] > 0 and cur[k]["est"] / max(cur[k]["te"], 1) >= cutoff]

    yl = [cur[k]["cand"].get(LULA, 0) / cur[k]["vv"] for k in fit]
    yf = [cur[k]["cand"].get(FLAV, 0) / cur[k]["vv"] for k in fit]
    wa = [cur[k]["vv"] for k in fit]
    Xa = [X_dict[k] for k in fit]

    bl = ajustar_wls_np(Xa, yl, wa)
    bf = ajustar_wls_np(Xa, yf, wa)

    X_all = np.array([X_dict[k] for k in keys])
    preds_l = np.clip(X_all @ bl, 0.0, 1.0)
    preds_f = np.clip(X_all @ bf, 0.0, 1.0)

    tot_lula = 0.0
    tot_flav = 0.0
    tot_vv = 0.0
    uf_tot = defaultdict(lambda: [0.0, 0.0, 0.0])

    for i, k in enumerate(keys):
        c = cur[k]
        f = c["est"] / c["te"] if c["te"] else 0.0
        if c["vv"] > 0 and f > 0.02:
            V = c["vv"] / f
        else:
            vv22 = feats[k]["vv22"] or c["te"] * 0.75
            V = vv22 * (c["te"] / max(te22.get(k, c["te"]), 1))
        M = max(V - c["vv"], 0.0)

        pl = preds_l[i]
        pf = preds_f[i]

        if c["vv"] > 0:
            lam = c["vv"] / (c["vv"] + k_shrink)
            ml = pl + lam * (c["cand"].get(LULA, 0) / c["vv"] - pl)
            mf = pf + lam * (c["cand"].get(FLAV, 0) / c["vv"] - pf)
        else:
            ml, mf = pl, pf

        s = ml + mf
        if s > 1.0:
            ml, mf = ml / s, mf / s

        vl_exp = c["cand"].get(LULA, 0) + M * ml
        vf_exp = c["cand"].get(FLAV, 0) + M * mf
        vv_exp = c["vv"] + M

        tot_lula += vl_exp
        tot_flav += vf_exp
        tot_vv += vv_exp

        u = c["uf"]
        uf_tot[u][0] += vl_exp
        uf_tot[u][1] += vf_exp
        uf_tot[u][2] += vv_exp

    lula_pct = tot_lula / max(tot_vv, 1.0)
    flav_pct = tot_flav / max(tot_vv, 1.0)
    margem = lula_pct - flav_pct

    uf_margens = {u: (vl - vf) / max(vv, 1.0) for u, (vl, vf, vv) in uf_tot.items()}
    uf_lula = {u: vl / max(vv, 1.0) for u, (vl, vf, vv) in uf_tot.items()}

    return {
        "lula_pct": lula_pct,
        "flav_pct": flav_pct,
        "margem": margem,
        "uf_margens": uf_margens,
        "uf_lula": uf_lula,
    }


def main():
    print("=== Backtest das 20h: Parcial vs Projeção V1 vs Projeção V2 ===")
    snap_path = C.SNAPSHOTS / "20261004_2005_apuracao85" / "mun_2026.csv"
    cur, h22, prof = load_v1(snap_path)
    with open(C.INTERIM / "perfil_2022_mun.csv") as f:
        te22 = {(r["uf"], r["cd"]): int(r["tot"]) for r in csv.DictReader(f)}
    ufs = sorted({c["uf"] for c in cur.values()})

    censo, prefeitos = carregar_dados_censo_prefeitos()
    X_v1, X_v2, feats = build_v2_features(cur, h22, prof, ufs, censo, prefeitos)

    gabarito = carregar_gabarito()
    lula_real = gabarito["lula_pct"]
    flav_real = gabarito["flav_pct"]
    margem_real = gabarito["margem_nat"]

    # 1. Parcial puro às 20h
    tot_l_snap = sum(c["cand"].get(LULA, 0) for c in cur.values())
    tot_f_snap = sum(c["cand"].get(FLAV, 0) for c in cur.values())
    tot_vv_snap = sum(c["vv"] for c in cur.values())
    parcial_lula = tot_l_snap / tot_vv_snap
    parcial_flav = tot_f_snap / tot_vv_snap
    parcial_margem = parcial_lula - parcial_flav

    uf_snap_tot = defaultdict(lambda: [0, 0, 0])
    for c in cur.values():
        u = c["uf"]
        uf_snap_tot[u][0] += c["cand"].get(LULA, 0)
        uf_snap_tot[u][1] += c["cand"].get(FLAV, 0)
        uf_snap_tot[u][2] += c["vv"]
    parcial_uf_margens = {u: (vl - vf) / max(vv, 1) for u, (vl, vf, vv) in uf_snap_tot.items()}

    # 2. Projeção V1 (Baseline com K=3000)
    proj_v1 = projetar_snapshot(cur, X_v1, feats, te22, k_shrink=3000.0, cutoff=0.50)

    # 3. Projeção V2 (com Censo 2022 + Prefeitos 2024 e K calibrado)
    proj_v2 = projetar_snapshot(cur, X_v2, feats, te22, k_shrink=1500.0, cutoff=0.50)

    # Cálculo dos erros
    mae_uf_parcial = 100 * np.mean([abs(parcial_uf_margens[u] - gabarito["uf_margens"][u]) for u in ufs if u in parcial_uf_margens])
    mae_uf_v1 = 100 * np.mean([abs(proj_v1["uf_margens"][u] - gabarito["uf_margens"][u]) for u in ufs if u in proj_v1["uf_margens"]])
    mae_uf_v2 = 100 * np.mean([abs(proj_v2["uf_margens"][u] - gabarito["uf_margens"][u]) for u in ufs if u in proj_v2["uf_margens"]])

    tabela = [
        {
            "metodo": "Parcial Puro (85% às 20h)",
            "lula": round(100 * parcial_lula, 2),
            "flavio": round(100 * parcial_flav, 2),
            "margem": round(100 * parcial_margem, 2),
            "erro_lula_pp": round(100 * (parcial_lula - lula_real), 2),
            "erro_flavio_pp": round(100 * (parcial_flav - flav_real), 2),
            "erro_margem_pp": round(100 * (parcial_margem - margem_real), 2),
            "mae_uf_pp": round(mae_uf_parcial, 3),
        },
        {
            "metodo": "Projeção V1 (Baseline 2022 + Perfil)",
            "lula": round(100 * proj_v1["lula_pct"], 2),
            "flavio": round(100 * proj_v1["flav_pct"], 2),
            "margem": round(100 * proj_v1["margem"], 2),
            "erro_lula_pp": round(100 * (proj_v1["lula_pct"] - lula_real), 2),
            "erro_flavio_pp": round(100 * (proj_v1["flav_pct"] - flav_real), 2),
            "erro_margem_pp": round(100 * (proj_v1["margem"] - margem_real), 2),
            "mae_uf_pp": round(mae_uf_v1, 3),
        },
        {
            "metodo": "Projeção V2 (+ Censo 2022, Prefeitos 2024)",
            "lula": round(100 * proj_v2["lula_pct"], 2),
            "flavio": round(100 * proj_v2["flav_pct"], 2),
            "margem": round(100 * proj_v2["margem"], 2),
            "erro_lula_pp": round(100 * (proj_v2["lula_pct"] - lula_real), 2),
            "erro_flavio_pp": round(100 * (proj_v2["flav_pct"] - flav_real), 2),
            "erro_margem_pp": round(100 * (proj_v2["margem"] - margem_real), 2),
            "mae_uf_pp": round(mae_uf_v2, 3),
        },
        {
            "metodo": "Resultado Final da Urna (100%)",
            "lula": round(100 * lula_real, 2),
            "flavio": round(100 * flav_real, 2),
            "margem": round(100 * margem_real, 2),
            "erro_lula_pp": 0.0,
            "erro_flavio_pp": 0.0,
            "erro_margem_pp": 0.0,
            "mae_uf_pp": 0.0,
        },
    ]

    print("\n--- Resultados do Backtest das 20h ---")
    for r in tabela:
        print(f"{r['metodo']:42} | Lula {r['lula']:5.2f}% | Flávio {r['flavio']:5.2f}% | Margem {r['margem']:+6.2f} pp | Erro Margem: {r['erro_margem_pp']:+5.2f} pp | MAE UF: {r['mae_uf_pp']:5.3f} pp")

    relatorio = {
        "snapshot": "20261004_2005_apuracao85",
        "tabela": tabela,
    }

    out_json = C.PROCESSED / "backtest_1turno_v2.json"
    with open(out_json, "w") as f:
        json.dump(relatorio, f, indent=2)
    print(f"\nSalvo resumo em {out_json}")

    gerar_grafico_backtest(tabela, proj_v1, proj_v2, parcial_uf_margens, gabarito["uf_margens"], ufs, lang="pt")
    gerar_grafico_backtest(tabela, proj_v1, proj_v2, parcial_uf_margens, gabarito["uf_margens"], ufs, lang="en")


def gerar_grafico_backtest(tabela, proj_v1, proj_v2, parcial_ufs, gabarito_ufs, ufs, lang="pt"):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5), dpi=200)

    # Painel 1: Erro Absoluto da Margem Nacional e por UF
    metodos = [t["metodo"].split("(")[0].strip() for t in tabela[:3]]
    erros_nat = [abs(t["erro_margem_pp"]) for t in tabela[:3]]
    maes_uf = [t["mae_uf_pp"] for t in tabela[:3]]

    x = np.arange(len(metodos))
    w = 0.35

    cores1 = ["#d95f02", "#2b5c8f", "#1b9e77"]

    b1 = ax1.bar(x - w / 2, erros_nat, width=w, color=cores1, alpha=0.85, label="Erro Nacional (p.p.)" if lang == "pt" else "National Error (pp)")
    b2 = ax1.bar(x + w / 2, maes_uf, width=w, color=cores1, alpha=0.45, hatch="//", label="Erro Médio por UF (MAE p.p.)" if lang == "pt" else "Mean State Error (MAE pp)")

    for bar in b1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2, yval + 0.03, f"{yval:.2f}", ha='center', va='bottom', fontsize=9, fontweight='bold')
    for bar in b2:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2, yval + 0.03, f"{yval:.2f}", ha='center', va='bottom', fontsize=9)

    ax1.set_xticks(x)
    ax1.set_xticklabels(metodos, fontsize=9.5)
    ax1.set_ylabel("Erro Absoluto (pontos percentuais)" if lang == "pt" else "Absolute Error (percentage points)", fontsize=10)
    ax1.set_title("A. Comparação de Precisão às 20h (85% apurado)" if lang == "pt" else "A. Accuracy Comparison at 8pm (85% tallied)", fontsize=11, fontweight="bold")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(fontsize=9, loc="upper right")
    ax1.set_ylim(0, 3.5)

    # Painel 2: Erro por UF na V1 vs V2
    diff_v1 = [100 * (proj_v1["uf_margens"][u] - gabarito_ufs[u]) for u in ufs if u in proj_v1["uf_margens"] and u in gabarito_ufs]
    diff_v2 = [100 * (proj_v2["uf_margens"][u] - gabarito_ufs[u]) for u in ufs if u in proj_v2["uf_margens"] and u in gabarito_ufs]
    uf_labels = [u.upper() for u in ufs if u in proj_v1["uf_margens"] and u in gabarito_ufs]

    idx = np.arange(len(uf_labels))
    ax2.axhline(0, color="#888888", linestyle="-", linewidth=1.0)
    ax2.plot(idx, diff_v1, marker="o", markersize=4, linestyle="--", color="#2b5c8f", label="Erro Projeção V1 (p.p.)" if lang == "pt" else "V1 Error (pp)")
    ax2.plot(idx, diff_v2, marker="s", markersize=4, linestyle="-", color="#1b9e77", label="Erro Projeção V2 (p.p.)" if lang == "pt" else "V2 Error (pp)")

    ax2.set_xticks(idx[::2])
    ax2.set_xticklabels(uf_labels[::2], fontsize=8)
    ax2.set_ylabel("Erro na Margem (Lula - Flávio) em p.p." if lang == "pt" else "Margin Error (Lula - Flávio) in pp", fontsize=10)
    ax2.set_title("B. Erro Residual por UF: V1 vs V2" if lang == "pt" else "B. State Residual Error: V1 vs V2", fontsize=11, fontweight="bold")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(fontsize=9, loc="upper right")

    titulo = ("Backtest das 20h: Testando as Alterações da V2 no Modelo do 1º Turno\n"
              "Desempenho no snapshot de 85% contra o resultado final da urna") if lang == "pt" else (
              "8pm Backtest: Testing V2 Changes on the First-Round Model\n"
              "Performance on 85% snapshot against final election outcome")
    fig.suptitle(titulo, fontsize=12, fontweight="bold", y=0.98)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    out_dir = (C.FIGURES / "pt") if lang == "pt" else (C.FIGURES / "en")
    out_file = out_dir / "28_backtest_1turno_v2.png"
    plt.savefig(out_file, dpi=200)
    plt.close()
    print(f"Figura salva: {out_file}")


if __name__ == "__main__":
    main()
