"""Modelo M4 V2: Fundamentos Macroeconômicos e Avaliação Governamental.

Modela a votação do presidente / candidato da situação no 2º turno como função de:
  1. Avaliação e Aprovação Governamental (Datafolha histórico 2002-2026)
  2. Fundamentos Econômicos (Índice de Miséria: Inflação IPCA 12m + Desemprego PNAD)
  3. Diferencial de Rejeição Relativa (Datafolha)

Utiliza regressão Ridge penalizada no espaço logit com validação cruzada leave-one-out
(LOOCV) em todas as eleições com situação no 2º turno (2002, 2006, 2010, 2014, 2022).
Gera distribuição preditiva Monte Carlo nacional e projeção regional por UF.

Somente biblioteca padrão + NumPy.
Uso: python -m eleicao2026.v2.m4_fundamentos [--n 10000]
"""
import argparse
import csv
import json
import math
import sys
from pathlib import Path
import numpy as np

from eleicao2026 import config as C

SEED = 20261025
N_SIM_DEFAULT = 10000


def logit(p):
    p = np.clip(p, 1e-6, 1.0 - 1e-6)
    return np.log(p / (1.0 - p))


def expit(x):
    return 1.0 / (1.0 + np.exp(-x))


def carregar_dados_historicos(csv_path=None):
    """Carrega o histórico de fundamentos macroeconômicos e aprovação de governo."""
    p = Path(csv_path or (C.EXTERNAL / "fundamentos_macro_historico.csv"))
    rows = []
    with open(p, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                "ano": int(r["ano"]),
                "incumbente": r["incumbente"],
                "cand_situacao": r["cand_situacao"],
                "cand_oposicao": r["cand_oposicao"],
                "otimo_bom": float(r["otimo_bom"]),
                "regular": float(r["regular"]),
                "ruim_pessimo": float(r["ruim_pessimo"]),
                "saldo_aprovacao": float(r["saldo_aprovacao"]),
                "aprova": float(r["aprova"]),
                "desaprova": float(r["desaprova"]),
                "saldo_aprova_desaprova": float(r["saldo_aprova_desaprova"]),
                "rejeicao_situacao": float(r["rejeicao_situacao"]),
                "rejeicao_oposicao": float(r["rejeicao_oposicao"]),
                "saldo_rejeicao": float(r["saldo_rejeicao"]),
                "ipca_12m": float(r["ipca_12m"]),
                "desemprego": float(r["desemprego"]),
                "indice_miseria": float(r["indice_miseria"]),
                "pib_ano": float(r["pib_ano"]),
                "votos_validos_2t_situacao": float(r["votos_validos_2t_situacao"]) if r["votos_validos_2t_situacao"] else None,
                "votos_validos_2t_oposicao": float(r["votos_validos_2t_oposicao"]) if r["votos_validos_2t_oposicao"] else None,
            })
    return rows


def ajustar_ridge_loocv(historico, lambda_grid=None, usar_binario=True):
    """Ajusta regressão Ridge com LOOCV no espaço logit.
    
    Retorna o melhor lambda, erro LOOCV (RMSE e MAE), coeficientes e predição central para 2026.
    """
    if lambda_grid is None:
        lambda_grid = [0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0]

    # Separar treino (2002-2022) e alvo (2026)
    treino = [r for r in historico if r["votos_validos_2t_situacao"] is not None]
    alvo = [r for r in historico if r["ano"] == 2026][0]

    N = len(treino)
    # Matriz de preditores: [Saldo_Aprov, Indice_Miseria, Saldo_Rejeicao]
    if usar_binario:
        X = np.array([[r["saldo_aprova_desaprova"], r["indice_miseria"], r["saldo_rejeicao"]] for r in treino])
        x_26 = np.array([alvo["saldo_aprova_desaprova"], alvo["indice_miseria"], alvo["saldo_rejeicao"]])
    else:
        X = np.array([[r["saldo_aprovacao"], r["indice_miseria"], r["saldo_rejeicao"]] for r in treino])
        x_26 = np.array([alvo["saldo_aprovacao"], alvo["indice_miseria"], alvo["saldo_rejeicao"]])

    Y_pct = np.array([r["votos_validos_2t_situacao"] for r in treino])
    Y_logit = logit(Y_pct / 100.0)

    # Padronização de variáveis explicativas
    mu_X = np.mean(X, axis=0)
    std_X = np.std(X, axis=0)
    # Evitar divisão por zero
    std_X = np.where(std_X < 1e-6, 1.0, std_X)
    X_s = (X - mu_X) / std_X
    x_26_s = (x_26 - mu_X) / std_X

    melhor_lam = None
    melhor_rmse = float("inf")
    melhor_mae = float("inf")
    melhor_erros = []
    tabela_loocv = []

    for lam in lambda_grid:
        erros_cv = []
        for i in range(N):
            idx_tr = [j for j in range(N) if j != i]
            X_tr = X_s[idx_tr]
            Y_tr = Y_logit[idx_tr]

            D_tr = np.column_stack([np.ones(len(idx_tr)), X_tr])
            P = np.diag([0.0, lam, lam, lam])
            beta_tr = np.linalg.solve(D_tr.T @ D_tr + P, D_tr.T @ Y_tr)

            d_val = np.array([1.0, *X_s[i]])
            pred_logit = np.dot(d_val, beta_tr)
            pred_pct = expit(pred_logit) * 100.0
            erros_cv.append(pred_pct - Y_pct[i])

        rmse = float(np.sqrt(np.mean(np.array(erros_cv) ** 2)))
        mae = float(np.mean(np.abs(erros_cv)))
        tabela_loocv.append({"lambda": lam, "rmse": rmse, "mae": mae})

        if rmse < melhor_rmse:
            melhor_rmse = rmse
            melhor_mae = mae
            melhor_lam = lam
            melhor_erros = erros_cv

    # Ajuste final com melhor lambda em todo o dataset de treino
    D_full = np.column_stack([np.ones(N), X_s])
    P_full = np.diag([0.0, melhor_lam, melhor_lam, melhor_lam])
    beta_full = np.linalg.solve(D_full.T @ D_full + P_full, D_full.T @ Y_logit)

    d_26 = np.array([1.0, *x_26_s])
    pred_26_logit = float(np.dot(d_26, beta_full))
    pred_26_pct = float(expit(pred_26_logit) * 100.0)

    # Incerteza do modelo (erro residual out-of-sample)
    sigma_resid = max(melhor_rmse / 100.0, 0.02)  # em escala de proporção (ex: 0.068 -> ~6.8 pp)

    return {
        "melhor_lambda": melhor_lam,
        "loocv_rmse_pp": melhor_rmse,
        "loocv_mae_pp": melhor_mae,
        "erros_por_ano": {r["ano"]: float(e) for r, e in zip(treino, melhor_erros)},
        "beta_intercepto": float(beta_full[0]),
        "beta_aprovacao": float(beta_full[1]),
        "beta_miseria": float(beta_full[2]),
        "beta_rejeicao": float(beta_full[3]),
        "pred_2026_central_pct": pred_26_pct,
        "pred_2026_central_logit": pred_26_logit,
        "sigma_resid": sigma_resid,
        "tabela_loocv": tabela_loocv,
    }


def carregar_pesos_uf():
    """Carrega pesos eleitorais e votação base 2022 por UF."""
    rows = list(csv.DictReader(open(C.INTERIM / "projecao_1turno_uf_snap85.csv")))
    tot_vv = sum(float(r["validos_proj"]) for r in rows)
    ufs = {}
    for r in rows:
        uf = r["uf"]
        vv = float(r["validos_proj"])
        # Share do 1T como âncora espacial
        lula_1t = float(r["lula_proj"]) / vv if vv > 0 else 0.5
        flavio_1t = float(r["flavio_proj"]) / vv if vv > 0 else 0.5
        # Proporção Lula na disputa direta
        share_lula_dir = lula_1t / (lula_1t + flavio_1t) if (lula_1t + flavio_1t) > 0 else 0.5
        ufs[uf] = {
            "vv": vv,
            "peso": vv / tot_vv,
            "share_base": share_lula_dir,
            "lula_1t": lula_1t,
            "flavio_1t": flavio_1t,
        }
    return ufs


def simular_monte_carlo(modelo_ajuste, ufs, n_sim=N_SIM_DEFAULT, seed=SEED):
    """Executa simulação de Monte Carlo para o Modelo M4.
    
    Sorteia choques macroeconômicos nacionais e choques regionais correlacionados por UF.
    """
    rng = np.random.default_rng(seed)

    mu_logit = modelo_ajuste["pred_2026_central_logit"]
    # Converter incerteza de pontos percentuais para a escala logit via Delta method
    p_center = expit(mu_logit)
    sigma_pct = modelo_ajuste["sigma_resid"]
    sigma_logit = sigma_pct / (p_center * (1.0 - p_center))

    # Sorteio do choque nacional de fundamentos
    # 10.000 sorteios do nível nacional
    choques_nat_logit = rng.normal(mu_logit, sigma_logit, size=n_sim)
    lula_nacional_sims = expit(choques_nat_logit)

    uf_list = sorted(ufs.keys())
    uf_pesos = np.array([ufs[u]["peso"] for u in uf_list])
    uf_bases = np.array([ufs[u]["share_base"] for u in uf_list])
    uf_bases_logit = logit(uf_bases)

    # Calibração do deslocamento espacial por simulação
    # logit(UF_sim) = logit(UF_base) + delta_sim + choque_uf
    # Ajusta delta_sim para que sum(peso_u * expit(logit_u)) = lula_nacional_sims[s]
    # Matriz para armazenar projeções por UF: (n_sim, n_ufs)
    sims_ufs = np.zeros((n_sim, len(uf_list)), dtype=np.float32)

    # Choques por UF com variância empírica de 2.0 pp
    tau_uf = 0.020
    tau_uf_logit = tau_uf / (0.5 * 0.5)

    # Simulação vetorizada por blocos
    for s in range(n_sim):
        target = lula_nacional_sims[s]
        # Bisseção rápida para encontrar delta_sim
        lo, hi = -3.0, 3.0
        for _ in range(25):
            mid = (lo + hi) / 2.0
            test_val = np.sum(uf_pesos * expit(uf_bases_logit + mid))
            if test_val < target:
                lo = mid
            else:
                hi = mid
        delta_central = (lo + hi) / 2.0

        # Adicionar ruído idiossincrático por UF mantendo a média nacional
        eps_uf = rng.normal(0.0, tau_uf_logit, size=len(uf_list))
        # Centralizar resíduos ponderados para não enviesar a média nacional
        eps_uf -= np.sum(uf_pesos * eps_uf)
        sims_ufs[s, :] = expit(uf_bases_logit + delta_central + eps_uf)

    # Estatísticas nacionais
    lula_media = float(np.mean(lula_nacional_sims))
    lula_mediana = float(np.median(lula_nacional_sims))
    lula_dp = float(np.std(lula_nacional_sims))
    p_lula_vence = float(np.mean(lula_nacional_sims > 0.50))

    q_vals = [0.025, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.975]
    quantis_nat = {f"{q:.3f}": float(np.quantile(lula_nacional_sims, q)) for q in q_vals}

    # Estatísticas por UF
    resumo_ufs = {}
    for i, uf in enumerate(uf_list):
        vals = sims_ufs[:, i]
        resumo_ufs[uf] = {
            "lula_media": float(np.mean(vals)),
            "lula_dp": float(np.std(vals)),
            "lula_ic90": [float(np.quantile(vals, 0.05)), float(np.quantile(vals, 0.95))],
            "p_lula_vence": float(np.mean(vals > 0.50)),
            "vv": int(ufs[uf]["vv"]),
        }

    return {
        "lula_nacional_sims": lula_nacional_sims,
        "lula_media": lula_media,
        "lula_mediana": lula_mediana,
        "lula_dp": lula_dp,
        "p_lula_vence": p_lula_vence,
        "quantis_nacionais": quantis_nat,
        "resumo_ufs": resumo_ufs,
        "sims_ufs": sims_ufs,
        "uf_list": uf_list,
    }


def executar_m4(n_sim=N_SIM_DEFAULT, log=print):
    """Executa o pipeline completo do Modelo M4 e grava outputs."""
    log("=== Executando Modelo M4 (Fundamentos Macroeconômicos e Popularidade) ===")
    historico = carregar_dados_historicos()
    log(f"Histórico carregado: {len(historico)} registros (2002 a 2026)")

    # 1. Ajuste Ridge com validação cruzada
    ajuste = ajustar_ridge_loocv(historico, usar_binario=True)
    log(f"Ajuste Ridge LOOCV: lambda ótimo = {ajuste['melhor_lambda']}")
    log(f"LOOCV RMSE = {ajuste['loocv_rmse_pp']:.2f} pp | MAE = {ajuste['loocv_mae_pp']:.2f} pp")
    log(f"Coeficientes padronizados: Aprov={ajuste['beta_aprovacao']:+.3f}, Miséria={ajuste['beta_miseria']:+.3f}, Rejeição={ajuste['beta_rejeicao']:+.3f}")
    log(f"Predição Central M4 para 2026: Lula = {ajuste['pred_2026_central_pct']:.2f}% | Flávio = {100.0 - ajuste['pred_2026_central_pct']:.2f}%")

    # 2. Carregar dados regionais e executar Monte Carlo
    ufs = carregar_pesos_uf()
    log(f"Carregadas {len(ufs)} UFs para desagregação espacial.")
    log(f"Iniciando simulação de Monte Carlo com {n_sim} iterações...")
    mc = simular_monte_carlo(ajuste, ufs, n_sim=n_sim)

    log(f"Resultado Monte Carlo M4:")
    log(f"  Média Lula: {mc['lula_media']*100:.2f}% (DP: {mc['lula_dp']*100:.2f} pp)")
    log(f"  IC 90%: [{mc['quantis_nacionais']['0.050']*100:.2f}%, {mc['quantis_nacionais']['0.950']*100:.2f}%]")
    log(f"  Probabilidade de vitória de Lula: {mc['p_lula_vence']*100:.1f}%")
    log(f"  Probabilidade de vitória de Flávio: {(1.0 - mc['p_lula_vence'])*100:.1f}%")

    # 3. Salvar resumo em JSON
    C.PROCESSED.mkdir(parents=True, exist_ok=True)
    output_json = {
        "modelo": "M4_FUNDAMENTOS_V2",
        "n_sim": n_sim,
        "lula_media": round(mc["lula_media"], 4),
        "lula_mediana": round(mc["lula_mediana"], 4),
        "lula_dp": round(mc["lula_dp"], 4),
        "flavio_media": round(1.0 - mc["lula_media"], 4),
        "p_lula_vence": round(mc["p_lula_vence"], 4),
        "p_flavio_vence": round(1.0 - mc["p_lula_vence"], 4),
        "quantis_nacionais": mc["quantis_nacionais"],
        "ajuste_econometrico": {
            "melhor_lambda": ajuste["melhor_lambda"],
            "loocv_rmse_pp": round(ajuste["loocv_rmse_pp"], 2),
            "loocv_mae_pp": round(ajuste["loocv_mae_pp"], 2),
            "erros_por_ano": {str(k): round(v, 2) for k, v in ajuste["erros_por_ano"].items()},
            "coeficientes": {
                "intercepto": round(ajuste["beta_intercepto"], 4),
                "aprovacao": round(ajuste["beta_aprovacao"], 4),
                "miseria": round(ajuste["beta_miseria"], 4),
                "rejeicao": round(ajuste["beta_rejeicao"], 4),
            },
            "pred_central_pct": round(ajuste["pred_2026_central_pct"], 2),
        },
        "ufs": mc["resumo_ufs"],
    }

    dst_json = C.PROCESSED / "resumo_v2_m4.json"
    with open(dst_json, "w", encoding="utf-8") as f:
        json.dump(output_json, f, indent=2, ensure_ascii=False)
    log(f"Salvo resumo em: {dst_json}")

    return output_json, mc


def main():
    parser = argparse.ArgumentParser(description="Modelo M4 V2: Fundamentos Macroeconômicos")
    parser.add_argument("--n", type=int, default=N_SIM_DEFAULT, help="Número de simulações Monte Carlo")
    args = parser.parse_args()
    executar_m4(n_sim=args.n)


if __name__ == "__main__":
    main()
