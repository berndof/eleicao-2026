#!/usr/bin/env python3
"""Comparativo Sistemático entre os Modelos V1 (Baseline) e V2 (Novos Dados e Métodos).

Compara lado a lado:
 - V1-M1 (Estrutural com médias regionais) vs V2-M1 (Estrutural + Censo 2022 + Prefeitos 2024).
 - V1-M2 (Pesquisas com pesos homogêneos) vs V2-M2 (Pesquisas ponderadas por acurácia auditada no TSE).
 - V1-M3 (Histórico 2002-2022).
 - Ensembles V1 (pesos fixos 50/30/20) vs V2 (pesos calibrados por variância mínima).

Gera a Figura 27 (PT/EN) e data/processed/comparativo_modelos_v1_v2.json.
"""
import json
import math
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

from eleicao2026 import config as C
from eleicao2026.v2.m1_v2 import simular_m1_v2
from eleicao2026.v2.m2_v2 import simular_m2_v2


def carregar_resumo_v1():
    """Carrega as estatísticas do modelo V1 baseline publicado."""
    with open(C.PROCESSED / "resumo_2turno.json") as f:
        res = json.load(f)
    return res


def resolver_pesos_min_variancia(cov_matrix):
    """Calcula pesos de Markowitz para mínima variância sob restrição w >= 0 e sum(w) = 1."""
    inv_cov = np.linalg.pinv(cov_matrix)
    ones = np.ones(cov_matrix.shape[0])
    w = inv_cov @ ones / (ones.T @ inv_cov @ ones)
    w = np.clip(w, 0.05, 0.80)  # evita concentração total
    w = w / np.sum(w)
    return w


def main():
    print("=== Comparativo Sistemático V1 (Baseline) vs V2 (Aprimorado) ===")
    v1 = carregar_resumo_v1()

    # Executa ou carrega V2-M1 e V2-M2
    m1_v2_res = simular_m1_v2(n_sim=10000, seed=20261025)
    m2_v2_res = simular_m2_v2(n_sim=10000, seed=20261025)

    # Estatísticas de M3 (Histórico 2002-2022) do V1
    m3_media = v1["componentes"]["M3"]["media"]
    m3_q05 = v1["componentes"]["M3"]["quantis"]["0.05"]
    m3_q95 = v1["componentes"]["M3"]["quantis"]["0.95"]
    m3_p_lula = v1["componentes"]["M3"]["p_lula"]

    # Simulações V2-Ensemble com pesos 50/30/20 e com pesos ótimos
    n_sim = 10000
    np.random.seed(20261025)
    sims_m1_v2 = np.random.normal(m1_v2_res["lula_media"], (m1_v2_res["lula_ic90"][1] - m1_v2_res["lula_ic90"][0]) / 3.29, n_sim)
    sims_m2_v2 = np.random.normal(m2_v2_res["lula_media"], (m2_v2_res["lula_ic90"][1] - m2_v2_res["lula_ic90"][0]) / 3.29, n_sim)
    sims_m3 = np.random.normal(m3_media, (m3_q95 - m3_q05) / 3.29, n_sim)

    # Matriz de covariância empírica dos modelos
    cov_mat = np.cov([sims_m1_v2, sims_m2_v2, sims_m3])
    pesos_otimos = resolver_pesos_min_variancia(cov_mat)

    # Ensemble V2 com 50/30/20
    ens_v2_503020 = 0.50 * sims_m1_v2 + 0.30 * sims_m2_v2 + 0.20 * sims_m3
    # Ensemble V2 com pesos ótimos
    ens_v2_otimo = pesos_otimos[0] * sims_m1_v2 + pesos_otimos[1] * sims_m2_v2 + pesos_otimos[2] * sims_m3

    tabela_comparativa = [
        {
            "modelo": "M1 (Estrutural)",
            "v1_media": v1["componentes"]["M1"]["media"],
            "v1_ic90": [v1["componentes"]["M1"]["quantis"]["0.05"], v1["componentes"]["M1"]["quantis"]["0.95"]],
            "v1_p_lula": v1["componentes"]["M1"]["p_lula"],
            "v2_media": m1_v2_res["lula_media"],
            "v2_ic90": m1_v2_res["lula_ic90"],
            "v2_p_lula": m1_v2_res["p_lula_vence"],
            "diferenca_pp": round(100 * (m1_v2_res["lula_media"] - v1["componentes"]["M1"]["media"]), 2),
            "o_que_mudou": "Adição de Censo 2022 (religião/renda) e Prefeitos 2024 (máquina local)",
        },
        {
            "modelo": "M2 (Pesquisas)",
            "v1_media": v1["componentes"]["M2"]["media"],
            "v1_ic90": [v1["componentes"]["M2"]["quantis"]["0.05"], v1["componentes"]["M2"]["quantis"]["0.95"]],
            "v1_p_lula": v1["componentes"]["M2"]["p_lula"],
            "v2_media": m2_v2_res["lula_media"],
            "v2_ic90": m2_v2_res["lula_ic90"],
            "v2_p_lula": m2_v2_res["p_lula_vence"],
            "diferenca_pp": round(100 * (m2_v2_res["lula_media"] - v1["componentes"]["M2"]["media"]), 2),
            "o_que_mudou": "Pesos individuais calibrados pelo erro do 1T auditado no TSE e amostra",
        },
        {
            "modelo": "M3 (Histórico 2002-22)",
            "v1_media": m3_media,
            "v1_ic90": [m3_q05, m3_q95],
            "v1_p_lula": m3_p_lula,
            "v2_media": m3_media,
            "v2_ic90": [m3_q05, m3_q95],
            "v2_p_lula": m3_p_lula,
            "diferenca_pp": 0.0,
            "o_que_mudou": "Mantido como controle histórico puro",
        },
        {
            "modelo": "Ensemble (50/30/20)",
            "v1_media": v1["share_lula_media"],
            "v1_ic90": [v1["share_lula_quantis"]["0.05"], v1["share_lula_quantis"]["0.95"]],
            "v1_p_lula": v1["p_lula_vence"],
            "v2_media": round(float(np.mean(ens_v2_503020)), 4),
            "v2_ic90": [round(float(np.percentile(ens_v2_503020, 5)), 4), round(float(np.percentile(ens_v2_503020, 95)), 4)],
            "v2_p_lula": round(float(np.mean(ens_v2_503020 > 0.5)), 4),
            "diferenca_pp": round(100 * (float(np.mean(ens_v2_503020)) - v1["share_lula_media"]), 2),
            "o_que_mudou": "Mistura ponderada tradicional com M1 e M2 aprimorados",
        },
        {
            "modelo": "Ensemble V2 Otimizado",
            "v1_media": v1["share_lula_media"],
            "v1_ic90": [v1["share_lula_quantis"]["0.05"], v1["share_lula_quantis"]["0.95"]],
            "v1_p_lula": v1["p_lula_vence"],
            "v2_media": round(float(np.mean(ens_v2_otimo)), 4),
            "v2_ic90": [round(float(np.percentile(ens_v2_otimo, 5)), 4), round(float(np.percentile(ens_v2_otimo, 95)), 4)],
            "v2_p_lula": round(float(np.mean(ens_v2_otimo > 0.5)), 4),
            "diferenca_pp": round(100 * (float(np.mean(ens_v2_otimo)) - v1["share_lula_media"]), 2),
            "o_que_mudou": f"Pesos de mínima variância: M1 {100*pesos_otimos[0]:.0f}% / M2 {100*pesos_otimos[1]:.0f}% / M3 {100*pesos_otimos[2]:.0f}%",
        },
    ]

    out_data = {
        "pesos_otimos": {
            "M1": round(float(pesos_otimos[0]), 3),
            "M2": round(float(pesos_otimos[1]), 3),
            "M3": round(float(pesos_otimos[2]), 3),
        },
        "comparativo": tabela_comparativa,
    }

    out_json = C.PROCESSED / "comparativo_modelos_v1_v2.json"
    with open(out_json, "w") as f:
        json.dump(out_data, f, indent=2)
    print(f"Salvo comparativo em {out_json}")

    gerar_grafico_comparativo(tabela_comparativa, lang="pt")
    gerar_grafico_comparativo(tabela_comparativa, lang="en")


def gerar_grafico_comparativo(tabela, lang="pt"):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5), dpi=200)

    modelos = [t["modelo"] for t in tabela]
    v1_medias = [100 * t["v1_media"] for t in tabela]
    v2_medias = [100 * t["v2_media"] for t in tabela]
    v1_err_lo = [100 * (t["v1_media"] - t["v1_ic90"][0]) for t in tabela]
    v1_err_hi = [100 * (t["v1_ic90"][1] - t["v1_media"]) for t in tabela]
    v2_err_lo = [100 * (t["v2_media"] - t["v2_ic90"][0]) for t in tabela]
    v2_err_hi = [100 * (t["v2_ic90"][1] - t["v2_media"]) for t in tabela]

    y_pos = np.arange(len(modelos))
    bar_height = 0.35

    # Painel 1: % Projetada de Lula (Votos Válidos) com IC 90%
    ax1.errorbar(v1_medias, y_pos - bar_height / 2, xerr=[v1_err_lo, v1_err_hi],
                 fmt='o', color='#2b5c8f', label='V1 Baseline (Publicado)' if lang == 'pt' else 'V1 Baseline (Published)',
                 capsize=4, capthick=1.5, elinewidth=1.5, markersize=6)
    ax1.errorbar(v2_medias, y_pos + bar_height / 2, xerr=[v2_err_lo, v2_err_hi],
                 fmt='s', color='#d95f02', label='V2 Aprimorado (Novos Dados)' if lang == 'pt' else 'V2 Enhanced (New Data)',
                 capsize=4, capthick=1.5, elinewidth=1.5, markersize=6)

    ax1.axvline(50.0, color='#888888', linestyle='--', linewidth=1.2, label='Linha de 50% (Vitória)' if lang == 'pt' else '50% Threshold')
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(modelos, fontsize=9.5)
    ax1.set_xlabel('% dos Votos Válidos em Lula (com IC 90%)' if lang == 'pt' else '% Valid Votes for Lula (with 90% CI)', fontsize=10)
    ax1.set_title('A. Projeção Média e Incerteza (IC 90%)' if lang == 'pt' else 'A. Mean Projection and 90% CI', fontsize=11, fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(fontsize=8.5, loc='upper right')
    ax1.invert_yaxis()

    # Painel 2: Probabilidade de Vitória de Lula (%)
    v1_probs = [100 * t["v1_p_lula"] for t in tabela]
    v2_probs = [100 * t["v2_p_lula"] for t in tabela]

    ax2.barh(y_pos - bar_height / 2, v1_probs, height=bar_height, color='#2b5c8f', alpha=0.85, label='V1 Baseline')
    ax2.barh(y_pos + bar_height / 2, v2_probs, height=bar_height, color='#d95f02', alpha=0.85, label='V2 Aprimorado')

    for i in range(len(modelos)):
        ax2.text(v1_probs[i] + 0.8, y_pos[i] - bar_height / 2, f"{v1_probs[i]:.1f}%", va='center', fontsize=8.5, color='#2b5c8f', fontweight='bold')
        ax2.text(v2_probs[i] + 0.8, y_pos[i] + bar_height / 2, f"{v2_probs[i]:.1f}%", va='center', fontsize=8.5, color='#d95f02', fontweight='bold')

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels([])
    ax2.set_xlabel('Probabilidade de Vitória de Lula P(Lula > 50%)' if lang == 'pt' else 'Probability of Lula Victory P(Lula > 50%)', fontsize=10)
    ax2.set_title('B. Probabilidade Estimada de Vitória' if lang == 'pt' else 'B. Estimated Victory Probability', fontsize=11, fontweight='bold')
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.set_xlim(0, 50)
    ax2.legend(fontsize=8.5, loc='upper right')
    ax2.invert_yaxis()

    titulo = ("Comparativo dos Modelos: V1 Baseline vs V2 (Censo, Prefeitos, Auditoria TSE)\n"
              "Efeito das novas camadas de dados sobre a projeção do 2º turno 2026") if lang == 'pt' else (
              "Model Comparison: V1 Baseline vs V2 (Census, Mayors, TSE Audit)\n"
              "Impact of new data layers on 2026 runoff projection")
    fig.suptitle(titulo, fontsize=12, fontweight='bold', y=0.98)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    out_dir = (C.FIGURES / "pt") if lang == "pt" else (C.FIGURES / "en")
    out_file = out_dir / "27_comparativo_v1_v2.png"
    plt.savefig(out_file, dpi=200)
    plt.close()
    print(f"Figura salva: {out_file}")


if __name__ == "__main__":
    main()
