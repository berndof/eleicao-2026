import csv
from pathlib import Path
from eleicao2026 import config as C


def test_chaves_municipios():
    p = C.EXTERNAL / "municipios_chaves.csv"
    assert p.exists()
    with open(p, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 5571
    # Verifica que códigos têm formato correto
    for r in rows:
        assert len(r["cd_tse"]) == 5
        assert len(r["uf"]) == 2


def test_censo2022_mun():
    p = C.EXTERNAL / "censo2022_mun.csv"
    assert p.exists()
    with open(p, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 5571
    # Verifica São Paulo (capital)
    sp = [r for r in rows if r["uf"] == "sp" and r["cd_tse"] == "71072"][0]
    assert int(sp["populacao_2022"]) > 10_000_000
    assert float(sp["pct_catolica_10mais"]) > 40
    assert float(sp["pct_evangelica_10mais"]) > 15
    assert float(sp["renda_media_percapita_2022"]) > 2000


def test_prefeitos_2024():
    p = C.EXTERNAL / "prefeitos_2024_mun.csv"
    assert p.exists()
    with open(p, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) >= 5500
    for r in rows:
        assert len(r["cd_tse"]) == 5
        assert len(r["sg_partido"]) > 0
