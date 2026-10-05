"""Testes da camada de influência das pesquisas e dos exemplos passo a passo (usam os dados versionados)."""
import csv
import json
import math

from eleicao2026 import config as C
from eleicao2026.model import influencia as I
from eleicao2026.model import ensemble as E


def test_results_nao_e_pesquisa():
    rows = list(csv.DictReader(open(C.INTERIM / "pesquisas_1turno.csv")))
    assert rows and all(r["pollster"] != "Results" for r in rows)


def test_t4_cdf_simetrica():
    assert abs(I.t4_cdf(0) - 0.5) < 1e-12
    assert abs(I.t4_cdf(1.3) + I.t4_cdf(-1.3) - 1) < 1e-12


def test_forma_fechada_m2_bate_com_simulacao():
    res = json.loads((C.PROCESSED / "resumo_2turno.json").read_text())
    inf = json.loads((C.PROCESSED / "influencia.json").read_text())
    assert abs(inf["m2_fechada"]["media"] - res["componentes"]["M2"]["media"]) < 0.002
    assert abs(inf["m2_fechada"]["p"] - res["componentes"]["M2"]["p_lula"]) < 0.01
    assert abs(inf["m3_fechada"]["p"] - res["componentes"]["M3"]["p_lula"]) < 0.01


def test_selecao_de_pesquisas_igual_ao_ensemble():
    p = json.loads((C.PROCESSED / "resumo_2turno.json").read_text())
    L1, F1 = p["primeiro_turno_proj"]["lula"], p["primeiro_turno_proj"]["flavio"]
    ps = E.poll_stats(L1, F1)
    in1 = [o for o in I.polls_1t(L1, F1) if o["status"] == "entra"]
    in2 = [o for o in I.polls_2t() if o["status"] == "entra"]
    assert len(in1) == len(ps["err"]) and len(in2) == len(ps["rows"])
    d = I.m2_dist([o["err"] for o in in1], in2, L1, F1)
    assert abs(d["avg"] - ps["avg"]) < 1e-12 and abs(d["b1"] - ps["b1"]) < 1e-12


def test_decomposicao_m1_soma_o_total():
    m = json.loads((C.PROCESSED / "m1_decomposicao.json").read_text())
    res = json.loads((C.PROCESSED / "resumo_2turno.json").read_text())
    for k in ("lula", "flavio"):
        parts = m[k]["propria"] + m[k]["rival"] + sum(m[k]["elim"].values())
        assert math.isclose(parts, m[k]["total"], rel_tol=1e-9)
    assert abs(m["lula"]["total"] / (m["lula"]["total"] + m["flavio"]["total"]) - res["m1_deterministico"]["lula_pct"]) < 1e-9
