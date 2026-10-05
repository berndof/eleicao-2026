"""Geração de gráficos em alta resolução para o Modelo M4 e o Ensemble de 4 Modelos.

Gera as figuras:
  29_m4_fundamentos_historico.png : Relação histórica de aprovação e miséria econômica vs votação
  30_m4_distribuicao_nacional.png  : Densidades de probabilidade Monte Carlo dos 4 pilares (M1, M2, M3, M4)
  31_ensemble_4modelos_comparativo.png : Comparativo de cenários de ensemble e pesos de Markowitz
  32_m4_projecao_uf.png           : Projeção por UF (M1 vs M4 vs Ensemble Balanceado)

Em versões bilíngues (PT e EN).
Somente matplotlib e numpy.
Uso: python -m eleicao2026.viz.figuras_m4
"""
import csv
import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

from eleicao2026 import config as C
from eleicao2026.viz.theme import apply_theme

apply_theme()

COR_LULA = "#e41a1c"
COR_FLAVIO = "#377eb8"
COR_NEUTRO = "#7f7f7f"
COR_M1 = "#ff7f00"
COR_M2 = "#4daf4a"
COR_M3 = "#984ea3"
COR_M4 = "#377eb8"
COR_ENS = "#2ca02c"


def gerar_figura_29(lang="pt"):
    """Figura 29: Fundamentos Macroeconômicos e Avaliação Histórica (2002-2026)."""
    # Carregar dados históricos
    rows = []
    with open(C.EXTERNAL / "fundamentos_macro_historico.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                "ano": int(r["ano"]),
                "cand": r["cand_situacao"],
                "incumbente": r["incumbente"],
                "saldo_aprov": float(r["saldo_aprova_desaprova"]),
                "miseria": float(r["indice_miseria"]),
                "votos_2t": float(r["votos_validos_2t_situacao"]) if r["votos_validos_2t_situacao"] else None,
            })

    treino = [r for r in rows if r["votos_2t"] is not None]
    alvo_26 = [r for r in rows if r["ano"] == 2026][0]

    # Carregar predição de resumo_v2_m4.json
    with open(C.PROCESSED / "resumo_v2_m4.json", encoding="utf-8") as f:
        m4_res = json.load(f)
    pred_26 = m4_res["ajuste_econometrico"]["pred_central_pct"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.8))

    # --- Painel A: Saldo de Aprovação vs Voto 2T
    x_aprov = np.array([r["saldo_aprov"] for r in treino])
    y_votos = np.array([r["votos_2t"] for r in treino])
    p_aprov = np.polyfit(x_aprov, y_votos, 1)
    grid_x1 = np.linspace(-30, 85, 100)

    ax1.plot(grid_x1, np.polyval(p_aprov, grid_x1), color="#555555", linestyle="--", alpha=0.7, label=("Tendência OLS Histórica" if lang == "pt" else "Historical OLS Trend"))
    ax1.axhline(50, color="#999999", linestyle=":", linewidth=1.2)
    ax1.axvline(0, color="#999999", linestyle=":", linewidth=1.2)

    for r in treino:
        cor = COR_LULA if "Lula" in r["cand"] or "Dilma" in r["cand"] else (COR_FLAVIO if "Bolsonaro" in r["cand"] else "#33a02c")
        ax1.scatter(r["saldo_aprov"], r["votos_2t"], s=90, color=cor, edgecolor="black", zorder=4)
        ax1.annotate(f"{r['cand']} ({r['ano']})\n{r['votos_2t']:.1f}%",
                     (r["saldo_aprov"], r["votos_2t"]),
                     textcoords="offset points", xytext=(8, -4 if r['ano'] == 2010 else 6),
                     fontsize=8.5, fontweight="bold", color="#222222")

    # Ponto 2026 projetado
    ax1.scatter(alvo_26["saldo_aprov"], pred_26, s=130, color=COR_LULA, marker="*", edgecolor="black", zorder=5, label=("Lula 2026 (Predição M4)" if lang == "pt" else "Lula 2026 (M4 Prediction)"))
    ax1.annotate(f"Lula 2026 (M4)\nProj: {pred_26:.1f}%\n(Saldo: {alvo_26['saldo_aprov']:.0f} pp)",
                 (alvo_26["saldo_aprov"], pred_26),
                 textcoords="offset points", xytext=(-85, 10),
                 fontsize=8.5, fontweight="bold", color=COR_LULA,
                 arrowprops=dict(arrowstyle="->", color=COR_LULA, lw=1.2))

    ax1.set_xlabel("Saldo Líquido Aprova - Desaprova (pp)" if lang == "pt" else "Net Approval Rating: Approve - Disapprove (pp)", fontsize=10)
    ax1.set_ylabel("Votação 2º Turno da Situação (%)" if lang == "pt" else "Incumbent Runoff Vote Share (%)", fontsize=10)
    ax1.set_title("A. Popularidade do Governo vs Desempenho Eleitoral" if lang == "pt" else "A. Government Approval vs Incumbent Runoff Vote", fontsize=11, fontweight="bold")
    ax1.grid(True, linestyle="--", alpha=0.4)
    ax1.legend(fontsize=8.5, loc="lower right")

    # --- Painel B: Índice de Miséria vs Voto 2T
    x_mis = np.array([r["miseria"] for r in treino])
    p_mis = np.polyfit(x_mis, y_votos, 1)
    grid_x2 = np.linspace(8, 22, 100)

    ax2.plot(grid_x2, np.polyval(p_mis, grid_x2), color="#555555", linestyle="--", alpha=0.7, label=("Tendência OLS Histórica" if lang == "pt" else "Historical OLS Trend"))
    ax2.axhline(50, color="#999999", linestyle=":", linewidth=1.2)

    for r in treino:
        cor = COR_LULA if "Lula" in r["cand"] or "Dilma" in r["cand"] else (COR_FLAVIO if "Bolsonaro" in r["cand"] else "#33a02c")
        ax2.scatter(r["miseria"], r["votos_2t"], s=90, color=cor, edgecolor="black", zorder=4)
        ax2.annotate(f"{r['cand']} ({r['ano']})\n{r['votos_2t']:.1f}%",
                     (r["miseria"], r["votos_2t"]),
                     textcoords="offset points", xytext=(8, 4),
                     fontsize=8.5, fontweight="bold", color="#222222")

    # Ponto 2026 projetado na miséria
    ax2.scatter(alvo_26["miseria"], pred_26, s=130, color=COR_LULA, marker="*", edgecolor="black", zorder=5, label=("2026 (Miséria Recorde 9,52%)" if lang == "pt" else "2026 (Record Misery Index 9.52%)"))
    ax2.annotate(f"2026: IPCA 4.2% + Desemp 5.3%\nMiséria: {alvo_26['miseria']:.2f}%\nProj M4: {pred_26:.1f}%",
                 (alvo_26["miseria"], pred_26),
                 textcoords="offset points", xytext=(12, -20),
                 fontsize=8.5, fontweight="bold", color=COR_LULA,
                 arrowprops=dict(arrowstyle="->", color=COR_LULA, lw=1.2))

    ax2.set_xlabel("Índice de Miséria Econômica (IPCA 12m + Desemprego %)" if lang == "pt" else "Economic Misery Index (12m Inflation + Unemployment %)", fontsize=10)
    ax2.set_ylabel("Votação 2º Turno da Situação (%)" if lang == "pt" else "Incumbent Runoff Vote Share (%)", fontsize=10)
    ax2.set_title("B. Fundamentos Macroeconômicos vs Desempenho Eleitoral" if lang == "pt" else "B. Macroeconomic Fundamentals vs Incumbent Runoff Vote", fontsize=11, fontweight="bold")
    ax2.grid(True, linestyle="--", alpha=0.4)
    ax2.legend(fontsize=8.5, loc="upper right")

    titulo = ("Fundamentos Macroeconômicos e Popularidade no 2º Turno Presidencial (2002-2026)\n"
              "Calibração do Modelo M4: Relação empírica entre aprovação, miséria econômica e urnas") if lang == "pt" else (
              "Macroeconomic Fundamentals & Approval in Brazilian Presidential Runoffs (2002-2026)\n"
              "Model M4 Calibration: Empirical link between approval, economic misery and election outcome")
    fig.suptitle(titulo, fontsize=12, fontweight="bold", y=0.98)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    out_dir = (C.FIGURES / "pt") if lang == "pt" else (C.FIGURES / "en")
    out_file = out_dir / "29_m4_fundamentos_historico.png"
    plt.savefig(out_file, dpi=200)
    plt.close()
    print(f"Figura salva: {out_file}")


def gerar_figura_30(lang="pt"):
    """Figura 30: Densidades de Probabilidade Monte Carlo dos 4 Modelos."""
    with open(C.PROCESSED / "resumo_ensemble_4m.json", encoding="utf-8") as f:
        ens = json.load(f)

    comps = ens["componentes"]
    cores = {"M1": COR_M1, "M2": COR_M2, "M3": COR_M3, "M4": COR_M4}
    labels_pt = {
        "M1": f"M1 Estrutural V2 (Urnas 1T + Censo + Prefeitos)\nMédia: {comps['M1']['lula_media']*100:.1f}% | DP: {comps['M1']['lula_dp']*100:.2f}pp | P(Lula): {comps['M1']['p_lula']*100:.0f}%",
        "M2": f"M2 Pesquisas V2 (Auditoria TSE 1T)\nMédia: {comps['M2']['lula_media']*100:.1f}% | DP: {comps['M2']['lula_dp']*100:.2f}pp | P(Lula): {comps['M2']['p_lula']*100:.0f}%",
        "M3": f"M3 Histórico (Líder 1T 2002-2022)\nMédia: {comps['M3']['lula_media']*100:.1f}% | DP: {comps['M3']['lula_dp']*100:.2f}pp | P(Lula): {comps['M3']['p_lula']*100:.0f}%",
        "M4": f"M4 Fundamentos V2 (Macro + Aprovação)\nMédia: {comps['M4']['lula_media']*100:.1f}% | DP: {comps['M4']['lula_dp']*100:.2f}pp | P(Lula): {comps['M4']['p_lula']*100:.0f}%",
    }
    labels_en = {
        "M1": f"M1 Structural V2 (1T Ballots + Census + Mayors)\nMean: {comps['M1']['lula_media']*100:.1f}% | SD: {comps['M1']['lula_dp']*100:.2f}pp | P(Lula): {comps['M1']['p_lula']*100:.0f}%",
        "M2": f"M2 Polls V2 (TSE 1T Error Audit)\nMean: {comps['M2']['lula_media']*100:.1f}% | SD: {comps['M2']['lula_dp']*100:.2f}pp | P(Lula): {comps['M2']['p_lula']*100:.0f}%",
        "M3": f"M3 Historical (1T Leader 2002-2022)\nMean: {comps['M3']['lula_media']*100:.1f}% | SD: {comps['M3']['lula_dp']*100:.2f}pp | P(Lula): {comps['M3']['p_lula']*100:.0f}%",
        "M4": f"M4 Fundamentals V2 (Macro + Approval)\nMean: {comps['M4']['lula_media']*100:.1f}% | SD: {comps['M4']['lula_dp']*100:.2f}pp | P(Lula): {comps['M4']['p_lula']*100:.0f}%",
    }
    labels = labels_pt if lang == "pt" else labels_en

    x_grid = np.linspace(0.40, 0.65, 500)
    fig, ax = plt.subplots(figsize=(10.5, 5.8))

    for k in ["M1", "M2", "M3", "M4"]:
        mu = comps[k]["lula_media"]
        sigma = comps[k]["lula_dp"]
        pdf = (1.0 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_grid - mu) / sigma) ** 2)
        ax.plot(x_grid * 100, pdf, label=labels[k], color=cores[k], linewidth=2.2)
        ax.fill_between(x_grid * 100, pdf, alpha=0.15, color=cores[k])

    ax.axvline(50, color="black", linestyle="--", linewidth=1.5, label=("Linha de 50% (Maioria Válida)" if lang == "pt" else "50% Threshold (Valid Majority)"))
    ax.axvspan(40, 50, color=COR_FLAVIO, alpha=0.04)
    ax.axvspan(50, 65, color=COR_LULA, alpha=0.04)

    ax.text(45.0, ax.get_ylim()[1] * 0.90, ("ZONA DE VITÓRIA\nDE FLÁVIO" if lang == "pt" else "FLÁVIO VICTORY\nZONE"),
            color=COR_FLAVIO, fontweight="bold", fontsize=11, ha="center", alpha=0.7)
    ax.text(57.5, ax.get_ylim()[1] * 0.90, ("ZONA DE VITÓRIA\nDE LULA" if lang == "pt" else "LULA VICTORY\nZONE"),
            color=COR_LULA, fontweight="bold", fontsize=11, ha="center", alpha=0.7)

    ax.set_xlim(42, 63)
    ax.set_xlabel("Votos Válidos de Lula no 2º Turno (%)" if lang == "pt" else "Lula Valid Vote Share in Runoff (%)", fontsize=10)
    ax.set_ylabel("Densidade de Probabilidade" if lang == "pt" else "Probability Density", fontsize=10)
    
    titulo = ("Distribuição de Probabilidade dos 4 Pilares Metodológicos Independentes (2026)\n"
              "Contraste entre Microdados Eleitorais (M1/M2) e Fundamentos Macroeconômicos (M4)") if lang == "pt" else (
              "Probability Density of the 4 Independent Methodological Pillars (2026)\n"
              "Contrast between Electoral Microdata (M1/M2) and Macroeconomic Fundamentals (M4)")
    ax.set_title(titulo, fontsize=11, fontweight="bold", pad=12)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(fontsize=8.5, loc="upper right")

    plt.tight_layout()
    out_dir = (C.FIGURES / "pt") if lang == "pt" else (C.FIGURES / "en")
    out_file = out_dir / "30_m4_distribuicao_nacional.png"
    plt.savefig(out_file, dpi=200)
    plt.close()
    print(f"Figura salva: {out_file}")


def gerar_figura_31(lang="pt"):
    """Figura 31: Comparativo dos 4 Modelos e Cenários de Ensemble."""
    with open(C.PROCESSED / "resumo_ensemble_4m.json", encoding="utf-8") as f:
        ens = json.load(f)

    modelos = [
        ("M1 Estrutural V2", ens["componentes"]["M1"]["lula_media"] * 100, ens["componentes"]["M1"]["ic90"], ens["componentes"]["M1"]["p_lula"] * 100, COR_M1),
        ("M2 Pesquisas V2", ens["componentes"]["M2"]["lula_media"] * 100, ens["componentes"]["M2"]["ic90"], ens["componentes"]["M2"]["p_lula"] * 100, COR_M2),
        ("M3 Histórico 1T", ens["componentes"]["M3"]["lula_media"] * 100, ens["componentes"]["M3"]["ic90"], ens["componentes"]["M3"]["p_lula"] * 100, COR_M3),
        ("M4 Fundamentos V2", ens["componentes"]["M4"]["lula_media"] * 100, ens["componentes"]["M4"]["ic90"], ens["componentes"]["M4"]["p_lula"] * 100, COR_M4),
        ("Ensemble Markowitz (Mín. Var.)", ens["cenarios"]["markowitz_min_var"]["lula_media"] * 100, ens["cenarios"]["markowitz_min_var"]["lula_ic90"], ens["cenarios"]["markowitz_min_var"]["p_lula_vence"] * 100, "#1f77b4"),
        ("Ensemble Pragmático (60/20/10/10)", ens["cenarios"]["pragmatico_1t"]["lula_media"] * 100, ens["cenarios"]["pragmatico_1t"]["lula_ic90"], ens["cenarios"]["pragmatico_1t"]["p_lula_vence"] * 100, "#ff7f0e"),
        ("Ensemble Informado (40/25/15/20)", ens["cenarios"]["informado_balanceado"]["lula_media"] * 100, ens["cenarios"]["informado_balanceado"]["lula_ic90"], ens["cenarios"]["informado_balanceado"]["p_lula_vence"] * 100, COR_ENS),
        ("Ensemble Equiponderado (25% cada)", ens["cenarios"]["equiponderado"]["lula_media"] * 100, ens["cenarios"]["equiponderado"]["lula_ic90"], ens["cenarios"]["equiponderado"]["p_lula_vence"] * 100, "#9467bd"),
    ]

    if lang == "en":
        modelos = [
            ("M1 Structural V2", m[1], m[2], m[3], m[4]) if "M1" in m[0] else
            ("M2 Polls V2", m[1], m[2], m[3], m[4]) if "M2" in m[0] else
            ("M3 Historical 1T", m[1], m[2], m[3], m[4]) if "M3" in m[0] else
            ("M4 Fundamentals V2", m[1], m[2], m[3], m[4]) if "M4" in m[0] else
            ("Ensemble Markowitz (Min. Var.)", m[1], m[2], m[3], m[4]) if "Markowitz" in m[0] else
            ("Ensemble Pragmatic (60/20/10/10)", m[1], m[2], m[3], m[4]) if "Pragmático" in m[0] else
            ("Ensemble Informed (40/25/15/20)", m[1], m[2], m[3], m[4]) if "Informado" in m[0] else
            ("Ensemble Equal Weights (25% each)", m[1], m[2], m[3], m[4])
            for m in modelos
        ]

    nomes = [m[0] for m in modelos]
    medias = [m[1] for m in modelos]
    erros_lo = [m[1] - m[2][0] * 100 for m in modelos]
    erros_hi = [m[2][1] * 100 - m[1] for m in modelos]
    probs = [m[3] for m in modelos]
    cores_bar = [m[4] for m in modelos]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 6.0))
    y = np.arange(len(modelos))

    # --- Painel A: Votação Esperada
    ax1.barh(y, medias, xerr=[erros_lo, erros_hi], color=cores_bar, alpha=0.85, capsize=4, edgecolor="black", linewidth=0.8)
    for yi, v in zip(y, medias):
        ax1.text(v + 0.35, yi, f"{v:.2f}%", va="center", fontsize=9, fontweight="bold")
    ax1.axvline(50, color="black", linestyle="--", linewidth=1.2, label=("Maioria 50%" if lang == "pt" else "50% Majority"))
    ax1.set_yticks(y, nomes, fontsize=9.5)
    ax1.set_xlim(42, 57)
    ax1.set_xlabel("Voto Válido Esperado de Lula (%) [IC 90%]" if lang == "pt" else "Lula Expected Valid Vote (%) [90% CI]", fontsize=10)
    ax1.set_title("A. Votação Nacional Esperada por Modelo / Ensemble" if lang == "pt" else "A. Expected National Vote Share by Model / Ensemble", fontsize=11, fontweight="bold")
    ax1.grid(True, linestyle="--", alpha=0.4)
    ax1.invert_yaxis()

    # --- Painel B: Probabilidade de Vitória
    bars = ax2.barh(y, probs, color=[COR_LULA if p > 50 else COR_FLAVIO for p in probs], alpha=0.85, edgecolor="black", linewidth=0.8)
    for yi, p in zip(y, probs):
        rot = f"Lula {p:.1f}%\n(Flávio {100-p:.1f}%)" if lang == "pt" else f"Lula {p:.1f}%\n(Flávio {100-p:.1f}%)"
        ax2.text(p + 1.2, yi, rot, va="center", fontsize=8.5, fontweight="bold")
    ax2.axvline(50, color="black", linestyle="--", linewidth=1.2)
    ax2.set_yticks(y, nomes, fontsize=9.5)
    ax2.set_xlim(0, 85)
    ax2.set_xlabel("Probabilidade de Vitória de Lula P(Lula > 50%)" if lang == "pt" else "Probability of Lula Victory P(Lula > 50%)", fontsize=10)
    ax2.set_title("B. Probabilidade de Vitória Estimada" if lang == "pt" else "B. Estimated Victory Probability", fontsize=11, fontweight="bold")
    ax2.grid(True, linestyle="--", alpha=0.4)
    ax2.invert_yaxis()

    titulo = ("Síntese Comparativa do Ensemble V2 de 4 Modelos (2º Turno 2026)\n"
              "Mapeamento da incerteza entre M1 (Urnas), M2 (Pesquisas), M3 (Histórico) e M4 (Fundamentos)") if lang == "pt" else (
              "Comparative Synthesis of the 4-Model V2 Ensemble (2026 Runoff)\n"
              "Uncertainty mapping across M1 (Ballots), M2 (Polls), M3 (History) and M4 (Fundamentals)")
    fig.suptitle(titulo, fontsize=12, fontweight="bold", y=0.98)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    out_dir = (C.FIGURES / "pt") if lang == "pt" else (C.FIGURES / "en")
    out_file = out_dir / "31_ensemble_4modelos_comparativo.png"
    plt.savefig(out_file, dpi=200)
    plt.close()
    print(f"Figura salva: {out_file}")


def gerar_figura_32(lang="pt"):
    """Figura 32: Projeção por UF comparando M1 V2, M4 V2 e Ensemble Balanceado."""
    with open(C.PROCESSED / "resumo_ensemble_4m.json", encoding="utf-8") as f:
        ens = json.load(f)

    with open(C.PROCESSED / "resumo_v2_m1.json", encoding="utf-8") as f:
        m1 = json.load(f)

    with open(C.PROCESSED / "resumo_v2_m4.json", encoding="utf-8") as f:
        m4 = json.load(f)

    ufs_ens = ens["ufs_cenario_balanceado"]
    ufs_keys = sorted(ufs_ens.keys(), key=lambda u: ufs_ens[u]["lula_media"])

    # Filtrar ZZ para visualização limpa
    ufs_plot = [u for u in ufs_keys if u != "zz"]
    y = np.arange(len(ufs_plot))

    v_m1 = [float(m1["ufs"][u].get("lula_media", m1["ufs"][u].get("media", 0.5))) * 100 for u in ufs_plot]
    v_m4 = [float(m4["ufs"][u]["lula_media"]) * 100 for u in ufs_plot]
    v_ens = [float(ufs_ens[u]["lula_media"]) * 100 for u in ufs_plot]

    fig, ax = plt.subplots(figsize=(9.0, 9.5))

    # Conectar M1 e M4 com linha
    for yi, m1_val, m4_val in zip(y, v_m1, v_m4):
        ax.plot([min(m1_val, m4_val), max(m1_val, m4_val)], [yi, yi], color="#bbbbbb", linewidth=1.5, zorder=1)

    ax.scatter(v_m1, y, color=COR_M1, s=45, label=("M1 Estrutural V2" if lang == "pt" else "M1 Structural V2"), zorder=3)
    ax.scatter(v_m4, y, color=COR_M4, s=45, label=("M4 Fundamentos V2" if lang == "pt" else "M4 Fundamentals V2"), zorder=3)
    ax.scatter(v_ens, y, color=COR_ENS, s=70, marker="D", edgecolor="black", linewidth=0.8,
               label=("Ensemble Balanceado (40/25/15/20)" if lang == "pt" else "Informed Ensemble (40/25/15/20)"), zorder=4)

    ax.axvline(50, color="black", linestyle="--", linewidth=1.2)
    ax.set_yticks(y, [u.upper() for u in ufs_plot], fontsize=9)
    ax.set_xlim(25, 75)
    ax.set_xlabel("Votação Projetada de Lula no 2º Turno (%)" if lang == "pt" else "Lula Projected Runoff Vote (%)", fontsize=10)
    ax.set_title("Projeção por Estado (UF): M1 Estrutural vs M4 Fundamentos vs Ensemble" if lang == "pt" else
                 "State-by-State (UF) Projection: M1 Structural vs M4 Fundamentals vs Ensemble",
                 fontsize=11, fontweight="bold", pad=12)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(fontsize=9, loc="lower right")

    plt.tight_layout()
    out_dir = (C.FIGURES / "pt") if lang == "pt" else (C.FIGURES / "en")
    out_file = out_dir / "32_m4_projecao_uf.png"
    plt.savefig(out_file, dpi=200)
    plt.close()
    print(f"Figura salva: {out_file}")


def main():
    for lang in ["pt", "en"]:
        print(f"Gerando gráficos M4 em {lang.upper()}...")
        gerar_figura_29(lang)
        gerar_figura_30(lang)
        gerar_figura_31(lang)
        gerar_figura_32(lang)


if __name__ == "__main__":
    main()
