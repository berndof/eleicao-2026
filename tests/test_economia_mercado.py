import csv
from pathlib import Path
from eleicao2026 import config as C


def test_economia_resumo():
    p = C.EXTERNAL / "economia_resumo.csv"
    assert p.exists()
    with open(p, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) >= 15
    series = {r["serie"] for r in rows}
    assert "selic_meta" in series
    assert "ipca_12m" in series
    assert "usd_ptax_venda" in series
    assert any("focus_ipca" in s for s in series)


def test_polymarket_uf():
    p = C.EXTERNAL / "polymarket_mercados_uf.csv"
    assert p.exists()
    with open(p, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) > 100
    estados = {r["estado"] for r in rows}
    assert "Amapá" in estados or any("Amapá" in e for e in estados)


def test_ledger_economico_e_mercado():
    p = C.DATA / "ledger" / "observacoes.csv"
    assert p.exists()
    with open(p, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) > 1000
    fontes = {r["fonte_id"] for r in rows}
    assert "bcb_sgs" in fontes
    assert "bcb_focus" in fontes
    assert "polymarket" in fontes
