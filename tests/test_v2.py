"""Testes unitários dos modelos e calibrações da Versão 2 (V2).

Sem chamadas de rede; executa offline e em alta velocidade.
"""
import numpy as np
import pytest

from eleicao2026.v2.m1_v2 import fit_elasticnet, simular_m1_v2
from eleicao2026.v2.m2_v2 import simular_m2_v2, carregar_pesquisas_auditadas
from eleicao2026.v2.calibrar_shrinkage import ajustar_wls_np
from eleicao2026.v2.comparar_modelos import resolver_pesos_min_variancia


def test_fit_elasticnet_convergencia():
    """Testa se a descida de coordenadas do ElasticNet recupera coeficientes aproximados."""
    np.random.seed(42)
    n, p = 100, 5
    X = np.random.randn(n, p)
    X[:, 0] = 1.0  # intercepto
    true_beta = np.array([2.0, 1.5, -1.0, 0.0, 0.0])
    y = X @ true_beta + np.random.normal(0, 0.1, n)
    w = np.ones(n)

    beta_est = fit_elasticnet(X, y, w, l1_ratio=0.5, alpha=1e-4, max_iter=500)
    assert len(beta_est) == p
    assert np.isclose(beta_est[0], 2.0, atol=0.3)
    assert np.isclose(beta_est[1], 1.5, atol=0.3)
    assert np.isclose(beta_est[2], -1.0, atol=0.3)


def test_ajustar_wls_np():
    """Verifica solução de mínimos quadrados ponderados via numpy."""
    X = np.array([[1.0, 2.0], [1.0, 3.0], [1.0, 4.0]])
    y = np.array([5.0, 7.0, 9.0])
    w = np.array([1.0, 1.0, 1.0])
    b = ajustar_wls_np(X, y, w, ridge=0.0)
    assert np.isclose(b[0], 1.0, atol=1e-4)  # intercepto
    assert np.isclose(b[1], 2.0, atol=1e-4)  # inclinação


def test_resolver_pesos_min_variancia():
    """Verifica se os pesos do ensemble somam 1 e respeitam os limites."""
    cov = np.array([
        [0.01, 0.002, 0.001],
        [0.002, 0.04, 0.005],
        [0.001, 0.005, 0.09],
    ])
    w = resolver_pesos_min_variancia(cov)
    assert len(w) == 3
    assert np.isclose(np.sum(w), 1.0)
    assert all(x > 0 for x in w)
    # Modelo com menor variância (índice 0) deve ter maior peso
    assert w[0] > w[1] > w[2]


def test_simular_m1_v2_estrutura():
    """Executa simulação leve do V2-M1 e valida o formato do resumo."""
    res = simular_m1_v2(n_sim=20, seed=123)
    assert "lula_media" in res
    assert 0.40 < res["lula_media"] < 0.60
    assert res["lula_ic90"][0] <= res["lula_media"] <= res["lula_ic90"][1]
    assert "ufs" in res
    assert len(res["ufs"]) >= 27


def test_simular_m2_v2_pesquisas_auditadas():
    """Valida carga e simulação do V2-M2."""
    dados = carregar_pesquisas_auditadas()
    assert len(dados["polls_2t"]) >= 10
    assert "erros_1t" in dados

    res = simular_m2_v2(n_sim=20, seed=123)
    assert "lula_media" in res
    assert 0.40 < res["lula_media"] < 0.60
    assert "institutos" in res
    soma_pesos = sum(i["peso_v2_pct"] for i in res["institutos"])
    assert np.isclose(soma_pesos, 100.0, atol=0.2)


def test_backtest_1turno_v2_execucao():
    """Valida carga e predição do backtest do 1T com features V2."""
    from eleicao2026.v2.backtest_1turno_v2 import build_v2_features, projetar_snapshot
    cur_mock = {
        ("sp", "001"): dict(uf="sp", te=1000, est=850, vv=700, cand={"LULA": 300, "FLAVIO BOLSONARO": 350}),
        ("rj", "002"): dict(uf="rj", te=2000, est=1700, vv=1500, cand={"LULA": 700, "FLAVIO BOLSONARO": 750}),
    }
    h22_mock = {("sp", "001"): {"LULA": 280, "JAIR BOLSONARO": 360}, ("rj", "002"): {"LULA": 680, "JAIR BOLSONARO": 760}}
    prof_mock = {
        ("sp", "001"): dict(tot=1000, fem=0.52, sup=0.15, analf=0.03, fund=0.2, jovem=0.12, idoso=0.2),
        ("rj", "002"): dict(tot=2000, fem=0.53, sup=0.18, analf=0.02, fund=0.18, jovem=0.11, idoso=0.22),
    }
    censo_mock = {
        ("sp", "001"): dict(evang=0.25, catol=0.55, preta_parda=0.35, urb=0.90, renda_med=1200.0),
        ("rj", "002"): dict(evang=0.32, catol=0.45, preta_parda=0.52, urb=0.95, renda_med=1100.0),
    }
    pref_mock = {("sp", "001"): "MDB", ("rj", "002"): "PL"}
    ufs = ["rj", "sp"]

    X_v1, X_v2, feats = build_v2_features(cur_mock, h22_mock, prof_mock, ufs, censo_mock, pref_mock)
    assert len(X_v2[("sp", "001")]) > len(X_v1[("sp", "001")])
    proj = projetar_snapshot(cur_mock, X_v2, feats, te22={("sp", "001"): 1000, ("rj", "002"): 2000}, cutoff=0.5)
    assert 0.0 < proj["lula_pct"] < 1.0
    assert 0.0 < proj["flav_pct"] < 1.0

