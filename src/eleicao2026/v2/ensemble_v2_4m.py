"""Ensemble V2 de 4 Modelos (M1, M2, M3, M4).

Combina quatro metodologias independentes para o 2º Turno de 2026:
  M1 Estrutural V2   : Urnas 1T + Transferências + Censo 2022 + Prefeitos 2024 (ElasticNet)
  M2 Pesquisas V2    : Intenções de Voto Ponderadas por Auditoria de Erro 1T TSE
  M3 Histórico       : Regressão Empírica do Líder de 1T no 2T (2002-2022)
  M4 Fundamentos V2  : Macroeconomia (IPCA + Desemprego recorde) + Avaliação de Governo

Executa otimização de portfólio de Markowitz (mínima variância), compara cenários de
ponderação e gera síntese nacional e por Unidade da Federação.

Somente biblioteca padrão + NumPy.
Uso: python -m eleicao2026.v2.ensemble_v2_4m
"""
import json
import math
from pathlib import Path
import numpy as np

from eleicao2026 import config as C


def normal_cdf(z):
    """CDF da distribuição normal padrão usando math.erf."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def carregar_modelos():
    """Carrega os resultados processados dos quatro modelos."""
    with open(C.PROCESSED / "resumo_v2_m1.json", encoding="utf-8") as f:
        m1 = json.load(f)
    with open(C.PROCESSED / "resumo_v2_m2.json", encoding="utf-8") as f:
        m2 = json.load(f)
    with open(C.PROCESSED / "resumo_2turno.json", encoding="utf-8") as f:
        r2 = json.load(f)
        m3_comp = r2["componentes"]["M3"]
    with open(C.PROCESSED / "resumo_v2_m4.json", encoding="utf-8") as f:
        m4 = json.load(f)

    # Extrair médias e desvios padrão
    # M1 V2
    m1_media = float(m1["lula_media"])
    m1_dp = (float(m1["lula_ic90"][1]) - float(m1["lula_ic90"][0])) / (2.0 * 1.645)

    # M2 V2
    m2_media = float(m2["lula_media"])
    m2_dp = (float(m2["lula_ic90"][1]) - float(m2["lula_ic90"][0])) / (2.0 * 1.645)

    # M3
    m3_media = float(m3_comp["media"])
    m3_q05 = float(m3_comp["quantis"]["0.05"])
    m3_q95 = float(m3_comp["quantis"]["0.95"])
    m3_dp = (m3_q95 - m3_q05) / (2.0 * 1.645)

    # M4 V2
    m4_media = float(m4["lula_media"])
    m4_dp = float(m4["lula_dp"])

    modelos = {
        "M1": {
            "nome": "Estrutural V2 (Censo + Prefeitos + 1T)",
            "lula_media": m1_media,
            "lula_dp": m1_dp,
            "p_lula": float(m1["p_lula_vence"]),
            "ic90": m1["lula_ic90"],
            "raw": m1,
        },
        "M2": {
            "nome": "Pesquisas V2 (Auditoria TSE)",
            "lula_media": m2_media,
            "lula_dp": m2_dp,
            "p_lula": float(m2["p_lula_vence"]),
            "ic90": m2["lula_ic90"],
            "raw": m2,
        },
        "M3": {
            "nome": "Histórico Líder 1T (2002-2022)",
            "lula_media": m3_media,
            "lula_dp": m3_dp,
            "p_lula": float(m3_comp["p_lula"]),
            "ic90": [m3_q05, m3_q95],
            "raw": m3_comp,
        },
        "M4": {
            "nome": "Fundamentos V2 (Macro + Avaliação)",
            "lula_media": m4_media,
            "lula_dp": m4_dp,
            "p_lula": float(m4["p_lula_vence"]),
            "ic90": [float(m4["quantis_nacionais"]["0.050"]), float(m4["quantis_nacionais"]["0.950"])],
            "raw": m4,
        },
    }
    return modelos


def calcular_matriz_covariancia(modelos):
    """Estima a matriz de covariância entre os quatro modelos baseando-se em correlações teóricas e empíricas."""
    sds = np.array([modelos["M1"]["lula_dp"], modelos["M2"]["lula_dp"], modelos["M3"]["lula_dp"], modelos["M4"]["lula_dp"]])

    # Matriz de correlação justificada:
    # M1 x M2: 0.50 (pesquisas refletem em parte as inclinações de transferência)
    # M1 x M3: 0.20 (ambos ancoram na votação do 1º turno)
    # M1 x M4: -0.10 (fundamentos macro apontam em direção oposta à máquina política municipal de 2024)
    # M2 x M3: 0.30 (inércia do 1T x intenção declarada)
    # M2 x M4: 0.35 (aprovação de governo e pesquisas eleitorais compartilham sinal de opinião pública)
    # M3 x M4: 0.10 (baixa correlação)
    corr = np.array([
        [ 1.00,  0.50,  0.20, -0.10],
        [ 0.50,  1.00,  0.30,  0.35],
        [ 0.20,  0.30,  1.00,  0.10],
        [-0.10,  0.35,  0.10,  1.00],
    ])

    cov = np.outer(sds, sds) * corr
    return corr, cov, sds


def otimizar_markowitz(cov):
    """Calcula pesos de mínima variância de Markowitz irrestritos e no simplex não-negativo."""
    inv_cov = np.linalg.pinv(cov)
    ones = np.ones(4)
    w_unconstrained = inv_cov @ ones / (ones.T @ inv_cov @ ones)

    # Projeção no simplex não-negativo via otimização quadrática simples
    w_pos = np.maximum(w_unconstrained, 0.0)
    w_simplex = w_pos / np.sum(w_pos)

    # Refinamento por busca em grade fina no simplex para garantir mínimo absoluto não-negativo
    best_w = w_simplex
    best_var = best_w.T @ cov @ best_w

    # Grade de refinamento
    steps = 40
    for i in range(steps + 1):
        for j in range(steps + 1 - i):
            for k in range(steps + 1 - i - j):
                l = steps - i - j - k
                w = np.array([i, j, k, l], dtype=float) / steps
                var = w.T @ cov @ w
                if var < best_var:
                    best_var = var
                    best_w = w

    return w_unconstrained, best_w


def avaliar_ensemble(pesos, modelos, cov):
    """Calcula estatísticas de um ensemble dado um vetor de pesos."""
    means = np.array([modelos["M1"]["lula_media"], modelos["M2"]["lula_media"], modelos["M3"]["lula_media"], modelos["M4"]["lula_media"]])
    mean_lula = float(np.dot(pesos, means))
    var_lula = float(pesos.T @ cov @ pesos)
    sd_lula = float(math.sqrt(var_lula))

    z = (0.50 - mean_lula) / sd_lula if sd_lula > 0 else 0.0
    p_lula = float(1.0 - normal_cdf(z))
    ic90 = [float(mean_lula - 1.645 * sd_lula), float(mean_lula + 1.645 * sd_lula)]

    return {
        "pesos": [round(float(w), 4) for w in pesos],
        "lula_media": round(mean_lula, 4),
        "lula_dp": round(sd_lula, 4),
        "flavio_media": round(1.0 - mean_lula, 4),
        "p_lula_vence": round(p_lula, 4),
        "p_flavio_vence": round(1.0 - p_lula, 4),
        "lula_ic90": [round(ic90[0], 4), round(ic90[1], 4)],
    }


def sintetizar_ufs_ensemble(pesos, modelos):
    """Combina projeções por UF de M1 e M4 ponderadas."""
    m1_ufs = modelos["M1"]["raw"]["ufs"]
    m4_ufs = modelos["M4"]["raw"]["ufs"]
    uf_keys = sorted(m1_ufs.keys())

    # Pesos normalizados entre M1 e M4 para projeção espacial
    w1, _, _, w4 = pesos
    s_w = w1 + w4
    if s_w <= 0:
        w1_s, w4_s = 0.5, 0.5
    else:
        w1_s, w4_s = w1 / s_w, w4 / s_w

    ufs_resumo = {}
    for uf in uf_keys:
        m1_u = m1_ufs[uf]
        m4_u = m4_ufs.get(uf, m1_u)

        m1_val = float(m1_u.get("lula_media", m1_u.get("media", 0.5)))
        m1_p = float(m1_u.get("p_lula_vence", m1_u.get("p_lula", 0.0)))

        m4_val = float(m4_u.get("lula_media", m4_u.get("media", 0.5)))
        m4_p = float(m4_u.get("p_lula_vence", m4_u.get("p_lula", 0.0)))

        lula_uf_media = w1_s * m1_val + w4_s * m4_val
        p_lula_uf = w1_s * m1_p + w4_s * m4_p

        ufs_resumo[uf] = {
            "lula_media": round(lula_uf_media, 4),
            "flavio_media": round(1.0 - lula_uf_media, 4),
            "p_lula_vence": round(p_lula_uf, 4),
            "p_flavio_vence": round(1.0 - p_lula_uf, 4),
            "vv": m1_u.get("vv", m4_u.get("vv", 0)),
        }
    return ufs_resumo


def executar_ensemble_4m(log=print):
    """Executa a síntese completa do Ensemble de 4 Modelos."""
    log("=== Executando Ensemble V2 de 4 Modelos (M1, M2, M3, M4) ===")
    modelos = carregar_modelos()
    for k, m in modelos.items():
        log(f"  {k} ({m['nome']}): Lula = {m['lula_media']*100:.2f}% | DP = {m['lula_dp']*100:.2f}pp | P(Lula) = {m['p_lula']*100:.1f}%")

    corr, cov, sds = calcular_matriz_covariancia(modelos)
    w_unconstrained, w_markowitz = otimizar_markowitz(cov)

    log(f"\nPesos de Markowitz (Mínima Variância):")
    log(f"  Irrestritos: M1={w_unconstrained[0]:.3f}, M2={w_unconstrained[1]:.3f}, M3={w_unconstrained[2]:.3f}, M4={w_unconstrained[3]:.3f}")
    log(f"  Restritos (>=0): M1={w_markowitz[0]:.3f}, M2={w_markowitz[1]:.3f}, M3={w_markowitz[2]:.3f}, M4={w_markowitz[3]:.3f}")

    # Cenários de Alocação
    cenarios = {
        "markowitz_min_var": {
            "nome": "Mínima Variância de Markowitz",
            "descricao": "Pesos ótimos que minimizam a variância total da carteira",
            "pesos": w_markowitz,
        },
        "informado_balanceado": {
            "nome": "Ensemble Informado e Balanceado",
            "descricao": "Ponderação diversificada (40% M1, 25% M2, 15% M3, 20% M4)",
            "pesos": np.array([0.40, 0.25, 0.15, 0.20]),
        },
        "equiponderado": {
            "nome": "Equiponderado (25% cada)",
            "descricao": "Pesos iguais entre os 4 pilares metodológicos",
            "pesos": np.array([0.25, 0.25, 0.25, 0.25]),
        },
        "pragmatico_1t": {
            "nome": "Pragmático Foco em Urna (60/20/10/10)",
            "descricao": "Foco na apuração do 1T e transferências (60% M1, 20% M2, 10% M3, 10% M4)",
            "pesos": np.array([0.60, 0.20, 0.10, 0.10]),
        },
    }

    resultados_cenarios = {}
    for c_id, c_info in cenarios.items():
        res = avaliar_ensemble(c_info["pesos"], modelos, cov)
        res["nome"] = c_info["nome"]
        res["descricao"] = c_info["descricao"]
        resultados_cenarios[c_id] = res
        log(f"\nCenário: {c_info['nome']}")
        log(f"  Pesos [M1, M2, M3, M4]: {res['pesos']}")
        log(f"  Lula: {res['lula_media']*100:.2f}% | Flávio: {res['flavio_media']*100:.2f}% | DP: {res['lula_dp']*100:.2f}pp")
        log(f"  P(Lula vence): {res['p_lula_vence']*100:.1f}% | P(Flávio vence): {res['p_flavio_vence']*100:.1f}%")
        log(f"  IC 90%: [{res['lula_ic90'][0]*100:.2f}%, {res['lula_ic90'][1]*100:.2f}%]")

    # Síntese espacial por UF para o cenário balanceado e markowitz
    ufs_balanceado = sintetizar_ufs_ensemble(cenarios["informado_balanceado"]["pesos"], modelos)
    ufs_markowitz = sintetizar_ufs_ensemble(cenarios["markowitz_min_var"]["pesos"], modelos)

    saida = {
        "modelo": "ENSEMBLE_V2_4M",
        "componentes": {k: {"nome": v["nome"], "lula_media": round(v["lula_media"], 4), "lula_dp": round(v["lula_dp"], 4), "p_lula": round(v["p_lula"], 4), "ic90": [round(v["ic90"][0], 4), round(v["ic90"][1], 4)]} for k, v in modelos.items()},
        "matriz_correlacao": [[round(float(c), 2) for c in row] for row in corr],
        "pesos_markowitz_irrestritos": [round(float(w), 4) for w in w_unconstrained],
        "pesos_markowitz_restritos": [round(float(w), 4) for w in w_markowitz],
        "cenarios": resultados_cenarios,
        "ufs_cenario_balanceado": ufs_balanceado,
        "ufs_cenario_markowitz": ufs_markowitz,
    }

    dst = C.PROCESSED / "resumo_ensemble_4m.json"
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(saida, f, indent=2, ensure_ascii=False)
    log(f"\nSalvo resumo completo do ensemble 4M em: {dst}")

    return saida


def main():
    executar_ensemble_4m()


if __name__ == "__main__":
    main()
