"""Testes de unidade para o Modelo M4 e o Ensemble de 4 Modelos."""
import json
import pytest
import numpy as np

from eleicao2026 import config as C
from eleicao2026.v2.m4_fundamentos import (
    carregar_dados_historicos,
    ajustar_ridge_loocv,
    carregar_pesos_uf,
    simular_monte_carlo,
)
from eleicao2026.v2.ensemble_v2_4m import (
    carregar_modelos,
    calcular_matriz_covariancia,
    otimizar_markowitz,
    avaliar_ensemble,
)


def test_carregar_dados_historicos():
    hist = carregar_dados_historicos()
    assert len(hist) == 6
    anos = [r["ano"] for r in hist]
    assert anos == [2002, 2006, 2010, 2014, 2022, 2026]

    # Verificar 2026 alvo
    r26 = [r for r in hist if r["ano"] == 2026][0]
    assert r26["cand_situacao"] == "Lula"
    assert r26["cand_oposicao"] == "Flávio Bolsonaro"
    assert r26["desemprego"] == 5.3
    assert r26["ipca_12m"] == 4.22
    assert r26["indice_miseria"] == 9.52
    assert r26["votos_validos_2t_situacao"] is None


def test_ajustar_ridge_loocv():
    hist = carregar_dados_historicos()
    res = ajustar_ridge_loocv(hist, lambda_grid=[1.0, 2.0, 3.0, 5.0], usar_binario=True)

    assert res["melhor_lambda"] in [1.0, 2.0, 3.0, 5.0]
    assert res["loocv_rmse_pp"] < 8.0
    assert res["loocv_mae_pp"] < 6.5
    # Sinais econômicos coerentes
    assert res["beta_aprovacao"] > 0.0  # mais aprovação -> mais votos
    assert res["beta_miseria"] < 0.0    # mais miséria -> menos votos
    # Predição central de Lula entre 50% e 55%
    assert 50.0 < res["pred_2026_central_pct"] < 55.0


def test_monte_carlo_m4():
    hist = carregar_dados_historicos()
    ajuste = ajustar_ridge_loocv(hist, usar_binario=True)
    ufs = carregar_pesos_uf()

    mc = simular_monte_carlo(ajuste, ufs, n_sim=500, seed=42)
    assert len(mc["lula_nacional_sims"]) == 500
    assert 0.48 < mc["lula_media"] < 0.56
    assert 0.04 < mc["lula_dp"] < 0.10
    assert 0.50 < mc["p_lula_vence"] < 0.85
    assert len(mc["resumo_ufs"]) >= 27


def test_ensemble_4m_estrutura():
    modelos = carregar_modelos()
    assert set(modelos.keys()) == {"M1", "M2", "M3", "M4"}

    corr, cov, sds = calcular_matriz_covariancia(modelos)
    assert cov.shape == (4, 4)
    # Matriz simétrica e semi-definida positiva
    assert np.allclose(cov, cov.T)
    eigenvals = np.linalg.eigvalsh(cov)
    assert np.all(eigenvals > 0)

    w_uncon, w_mark = otimizar_markowitz(cov)
    assert len(w_mark) == 4
    assert np.all(w_mark >= 0.0)
    assert np.isclose(np.sum(w_mark), 1.0)

    # Avaliar cenário balanceado
    w_bal = np.array([0.40, 0.25, 0.15, 0.20])
    res_bal = avaliar_ensemble(w_bal, modelos, cov)
    assert 0.47 < res_bal["lula_media"] < 0.51
    assert 0.01 < res_bal["lula_dp"] < 0.03
    assert 0.10 < res_bal["p_lula_vence"] < 0.40
