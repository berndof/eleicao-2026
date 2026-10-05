"""Testes unitários das peças numéricas e do parser de pesquisas (não dependem dos dados baixados)."""
import math
import random
from datetime import date

from eleicao2026.collect.pesquisas import data_fim
from eleicao2026.model.ensemble import shift_logit
from eleicao2026.model.linalg import expit, logit, solve, wls, wquant


def test_solve_sistema_2x2():
    x = solve([[2.0, 1.0], [1.0, 3.0]], [5.0, 10.0])
    assert math.isclose(x[0], 1.0, abs_tol=1e-9) and math.isclose(x[1], 3.0, abs_tol=1e-9)


def test_wls_recupera_coeficientes():
    rnd = random.Random(1)
    X = [[1.0, rnd.random()] for _ in range(500)]
    y = [2.0 + 3.0 * x[1] for x in X]
    b = wls(X, y, [1.0] * len(X))
    assert math.isclose(b[0], 2.0, abs_tol=1e-3) and math.isclose(b[1], 3.0, abs_tol=1e-3)


def test_logit_expit_inversas():
    for p in (0.05, 0.3, 0.5, 0.77, 0.99):
        assert math.isclose(expit(logit(p)), p, abs_tol=1e-9)


def test_wquant_mediana_ponderada():
    vals = [1, 2, 3, 4]
    assert wquant(vals, [1, 1, 1, 1], [0.5])[0] == 2
    assert wquant(vals, [0, 0, 0, 1], [0.5])[0] == 4


def test_data_fim_formatos():
    assert data_fim("27–29 Sep") == date(2026, 9, 29).isoformat()
    assert data_fim("30 Sep–3 Oct") == date(2026, 10, 3).isoformat()
    assert data_fim("3 Oct") == date(2026, 10, 3).isoformat()


def test_shift_logit_atinge_alvo():
    base = {"a": (60.0, 40.0), "b": (30.0, 70.0), "c": (50.0, 50.0)}
    vtot = {u: l + b for u, (l, b) in base.items()}
    sh = shift_logit(base, 0.55, vtot)
    tot = sum(vtot.values())
    assert math.isclose(sum(vtot[u] * sh[u] for u in sh) / tot, 0.55, abs_tol=1e-6)
