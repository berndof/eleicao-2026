from eleicao2026 import ledger as L


def _r(valor, **kw):
    base = dict(fonte_id="x", serie="s", periodo_ref="2026-08", valor=valor, divulgado_em="2026-09-10T00:00:00Z")
    return base | kw


def test_novo_igual_e_revisao(tmp_path):
    f = tmp_path / "o.csv"
    assert L.acrescentar([_r("4.20")], f) == (1, 0, 0)
    assert L.acrescentar([_r("4.20")], f) == (0, 0, 1)          # idêntico: nada gravado
    assert L.acrescentar([_r("4.22")], f) == (0, 1, 0)          # revisado: nova linha
    linhas = L.ler(f)
    assert [r["valor"] for r in linhas] == ["4.20", "4.22"]
    assert "revisão de 4.20 para 4.22" in linhas[1]["nota"]


def test_ate_nao_vaza_futuro(tmp_path):
    f = tmp_path / "o.csv"
    L.acrescentar([_r("4.20", divulgado_em="2026-09-10T00:00:00Z")], f)
    L.acrescentar([_r("4.22", divulgado_em="2026-10-10T00:00:00Z")], f)
    vis = L.ate(L.ler(f), "2026-09-30")
    assert [r["valor"] for r in vis] == ["4.20"]
