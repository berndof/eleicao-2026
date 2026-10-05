#!/usr/bin/env python3
"""Calibração empírica do hiperparâmetro de encolhimento K_SHRINK e corte de apuração.

Avalia o impacto do ponto de corte (fração apurada para entrar no ajuste) e
do peso de encolhimento bayesiano K_SHRINK sobre o erro da projeção do 1º turno,
usando o snapshot de ~20h (85% apurado) contra o resultado final da urna.
Gera a Figura 26 (PT/EN) e data/processed/calibracao_shrinkage.json.
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
from eleicao2026.model.primeiro_turno import load, build


def ajustar_wls_np(Xa, y, w, ridge=1e-6):
    """WLS rápido vetorizado via numpy."""
    X = np.asarray(Xa, dtype=float)
    y = np.asarray(y, dtype=float)
    W = np.asarray(w, dtype=float)
    p = X.shape[1]
    XTW = X.T * W
    A = XTW @ X + np.eye(p) * (ridge * np.mean(W) + 1e-9)
    b = XTW @ y
    return np.linalg.solve(A, b)


def carregar_gabarito():
    """Carrega o resultado final 100% da urna para calcular o erro exato."""
    with open(C.INTERIM / "mun_2026.csv") as f:
        rows = list(csv.DictReader(f))
    tot_l = sum(int(r.get("v_LULA", 0)) for r in rows)
    tot_f = sum(int(r.get("v_FLAVIO BOLSONARO", 0)) for r in rows)
    tot_vv = sum(int(r.get("vv", 0)) for r in rows)

    uf_tot = defaultdict(lambda: [0, 0, 0])
    for r in rows:
        u = r["uf"]
        uf_tot[u][0] += int(r.get("v_LULA", 0))
        uf_tot[u][1] += int(r.get("v_FLAVIO BOLSONARO", 0))
        uf_tot[u][2] += int(r.get("vv", 0))

    uf_margem_real = {u: (l - f) / max(v, 1) for u, (l, f, v) in uf_tot.items()}
    return {
        "lula_pct": tot_l / tot_vv,
        "flav_pct": tot_f / tot_vv,
        "margem_nat": (tot_l - tot_f) / tot_vv,
        "uf_margens": uf_margem_real,
    }


def main():
    print("=== Calibração Empírica de K_SHRINK e Cutoff de Apuração ===")
    snap_path = C.SNAPSHOTS / "20261004_2005_apuracao85" / "mun_2026.csv"
    cur, h22, prof = load(snap_path)
    with open(C.INTERIM / "perfil_2022_mun.csv") as f:
        te22 = {(r["uf"], r["cd"]): int(r["tot"]) for r in csv.DictReader(f)}
    ufs = sorted({c["uf"] for c in cur.values()})
    X_dict, feats = build(cur, h22, prof, ufs)
    keys = list(cur)

    gabarito = carregar_gabarito()
    real_margem = gabarito["margem_nat"]

    ks = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 5000, 6000, 7500, 10000]
    cutoffs = [0.30, 0.40, 0.50, 0.60]

    grade = defaultdict(dict)

    # Pré-calcula V e M para todos os municípios
    V_dict, M_dict = {}, {}
    for k in keys:
        c = cur[k]
        f = c["est"] / c["te"] if c["te"] else 0.0
        if c["vv"] > 0 and f > 0.02:
            V = c["vv"] / f
        else:
            vv22 = feats[k]["vv22"] or c["te"] * 0.75
            V = vv22 * (c["te"] / max(te22.get(k, c["te"]), 1))
        V_dict[k] = V
        M_dict[k] = max(V - c["vv"], 0.0)

    for cut in cutoffs:
        fit = [k for k in keys if cur[k]["vv"] > 0 and cur[k]["est"] / max(cur[k]["te"], 1) >= cut]
        if len(fit) < 100:
            continue

        Xa = [X_dict[k] for k in fit]
        wa = [cur[k]["vv"] for k in fit]
        yl = [cur[k]["cand"].get(LULA, 0) / cur[k]["vv"] for k in fit]
        yf = [cur[k]["cand"].get(FLAV, 0) / cur[k]["vv"] for k in fit]

        bl = ajustar_wls_np(Xa, yl, wa)
        bf = ajustar_wls_np(Xa, yf, wa)

        # Pré-calcula predições da regressão
        X_all = np.array([X_dict[k] for k in keys])
        preds_l = np.clip(X_all @ bl, 0.0, 1.0)
        preds_f = np.clip(X_all @ bf, 0.0, 1.0)
        pl_dict = {k: float(preds_l[i]) for i, k in enumerate(keys)}
        pf_dict = {k: float(preds_f[i]) for i, k in enumerate(keys)}

        for k_shrink in ks:
            tot_lula = 0.0
            tot_flav = 0.0
            tot_vv = 0.0
            uf_tot = defaultdict(lambda: [0.0, 0.0, 0.0])

            for k in keys:
                c = cur[k]
                M = M_dict[k]
                pl = pl_dict[k]
                pf = pf_dict[k]

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

            pct_lula_nat = tot_lula / max(tot_vv, 1.0)
            pct_flav_nat = tot_flav / max(tot_vv, 1.0)
            margem_nat = pct_lula_nat - pct_flav_nat

            uf_margens = {u: (vl - vf) / max(vv, 1.0) for u, (vl, vf, vv) in uf_tot.items()}
            erro_nat_pp = 100.0 * abs(margem_nat - real_margem)
            uf_diffs = [abs(uf_margens[u] - gabarito["uf_margens"][u]) for u in ufs if u in uf_margens and u in gabarito["uf_margens"]]
            mae_uf_pp = 100.0 * sum(uf_diffs) / len(uf_diffs)

            grade[cut][k_shrink] = {
                "erro_nat_pp": erro_nat_pp,
                "mae_uf_pp": mae_uf_pp,
                "margem_proj": margem_nat,
                "lula_proj": pct_lula_nat,
                "flav_proj": pct_flav_nat,
                "n_fit": len(fit),
            }

    otimo_k_050 = min(ks, key=lambda k: grade[0.50][k]["mae_uf_pp"])
    menor_mae_uf = grade[0.50][otimo_k_050]["mae_uf_pp"]
    erro_nat_otimo = grade[0.50][otimo_k_050]["erro_nat_pp"]

    print(f"Resultado real da margem nacional: {100*real_margem:+.2f} pp (Lula {100*gabarito['lula_pct']:.2f}% vs Flávio {100*gabarito['flav_pct']:.2f}%)")
    print("Para cutoff=0.50:")
    print(f"  K = 3.000 (V1 fixo): MAE UF = {grade[0.50][3000]['mae_uf_pp']:.3f} pp, Erro Nat = {grade[0.50][3000]['erro_nat_pp']:.3f} pp")
    print(f"  K ótimo empírico: {otimo_k_050} (MAE UF = {menor_mae_uf:.3f} pp, Erro Nat = {erro_nat_otimo:.3f} pp)")

    # Cálculo analítico do Bayes empírico: K = sigma^2 / tau^2
    fit50 = [k for k in cur if cur[k]["vv"] > 0 and cur[k]["est"] / max(cur[k]["te"], 1) >= 0.5]
    Xa50 = np.array([X_dict[k] for k in fit50])
    w50 = np.array([cur[k]["vv"] for k in fit50])
    y_diff = np.array([(cur[k]["cand"].get(LULA, 0) - cur[k]["cand"].get(FLAV, 0)) / cur[k]["vv"] for k in fit50])
    b_diff = ajustar_wls_np(Xa50, y_diff, w50)
    res_diff = y_diff - Xa50 @ b_diff
    tau2 = np.average(res_diff**2, weights=w50)
    # sigma2 amostral médio ponderado na margem ~ 4 * p * (1-p) com p=0.46
    sigma2_amostral = 4.0 * 0.46 * 0.54  # ~ 0.99
    k_bayes_teorico = sigma2_amostral / max(tau2, 1e-4)

    relatorio = {
        "real_margem_nat_pct": round(100 * real_margem, 3),
        "real_lula_pct": round(100 * gabarito["lula_pct"], 3),
        "real_flav_pct": round(100 * gabarito["flav_pct"], 3),
        "k_v1": 3000,
        "k_v1_mae_uf_pp": round(grade[0.50][3000]["mae_uf_pp"], 3),
        "k_v1_erro_nat_pp": round(grade[0.50][3000]["erro_nat_pp"], 3),
        "k_otimo_empirico": otimo_k_050,
        "k_otimo_mae_uf_pp": round(menor_mae_uf, 3),
        "k_otimo_erro_nat_pp": round(erro_nat_otimo, 3),
        "tau2_prior_residuo": round(float(tau2), 6),
        "k_bayes_teorico_estimado": round(float(k_bayes_teorico), 1),
        "grade_completa": {str(cut): {str(k): v for k, v in grade[cut].items()} for cut in grade},
    }

    out_json = C.PROCESSED / "calibracao_shrinkage.json"
    with open(out_json, "w") as f:
        json.dump(relatorio, f, indent=2)
    print(f"Salvo resumo em {out_json}")

    gerar_grafico(grade, ks, cutoffs, otimo_k_050, real_margem, lang="pt")
    gerar_grafico(grade, ks, cutoffs, otimo_k_050, real_margem, lang="en")


def gerar_grafico(grade, ks, cutoffs, otimo_k, real_margem, lang="pt"):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2), dpi=200)

    cores = {0.30: "#888888", 0.40: "#2b5c8f", 0.50: "#1b9e77", 0.60: "#d95f02"}

    for cut in cutoffs:
        maes = [grade[cut][k]["mae_uf_pp"] for k in ks]
        lbl = f"Corte ≥ {int(cut*100)}% apurado" if lang == "pt" else f"Cutoff ≥ {int(cut*100)}% tallied"
        ax1.plot(ks, maes, marker="o", markersize=4, label=lbl, color=cores[cut], linewidth=2.2 if cut == 0.50 else 1.2)

    ax1.axvline(3000, color="#e41a1c", linestyle="--", linewidth=1.5, label="K = 3.000 (V1 fixo)" if lang == "pt" else "K = 3,000 (V1 fixed)")
    ax1.axvline(otimo_k, color="#1b9e77", linestyle=":", linewidth=1.5, label=f"K ótimo ({otimo_k})" if lang == "pt" else f"Optimal K ({otimo_k})")

    ax1.set_xlabel("Hiperparâmetro K_SHRINK (votos virtuais do prior)" if lang == "pt" else "Hyperparameter K_SHRINK (prior virtual votes)", fontsize=10)
    ax1.set_ylabel("Erro Médio Absoluto por UF (p.p. na margem)" if lang == "pt" else "Mean Absolute Error by State (pp in margin)", fontsize=10)
    ax1.set_title("A. Erro por UF em função de K e do Corte" if lang == "pt" else "A. State-Level Error by K and Count Cutoff", fontsize=11, fontweight="bold")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(fontsize=8.5, loc="upper right")

    for cut in cutoffs:
        erros_nat = [grade[cut][k]["erro_nat_pp"] for k in ks]
        lbl = f"Corte ≥ {int(cut*100)}%" if lang == "pt" else f"Cutoff ≥ {int(cut*100)}%"
        ax2.plot(ks, erros_nat, marker="s", markersize=4, label=lbl, color=cores[cut], linewidth=2.2 if cut == 0.50 else 1.2)

    ax2.axvline(3000, color="#e41a1c", linestyle="--", linewidth=1.5, label="K = 3.000 (V1)")
    ax2.set_xlabel("Hiperparâmetro K_SHRINK" if lang == "pt" else "Hyperparameter K_SHRINK", fontsize=10)
    ax2.set_ylabel("Erro Absoluto Nacional (p.p.)" if lang == "pt" else "National Absolute Error (pp)", fontsize=10)
    ax2.set_title("B. Erro Nacional da Projeção vs Real" if lang == "pt" else "B. National Projection Error vs Real Count", fontsize=11, fontweight="bold")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(fontsize=8.5, loc="upper right")

    titulo = ("Calibração Empírica do Encolhimento (Shrinkage) no 1º Turno 2026\n"
              "Avaliando K_SHRINK e corte sobre o snapshot de 85% contra a apuração final 100%") if lang == "pt" else (
              "Empirical Calibration of Shrinkage in the 2026 First Round\n"
              "Evaluating K_SHRINK and tally cutoff on the 85% snapshot against 100% final count")
    fig.suptitle(titulo, fontsize=12, fontweight="bold", y=0.98)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    out_dir = (C.FIGURES / "pt") if lang == "pt" else (C.FIGURES / "en")
    out_file = out_dir / "26_calibracao_shrinkage_k.png"
    plt.savefig(out_file, dpi=200)
    plt.close()
    print(f"Figura salva: {out_file}")


if __name__ == "__main__":
    main()
