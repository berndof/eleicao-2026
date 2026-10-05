import csv
from pathlib import Path

from eleicao2026 import config as C
from eleicao2026.audit_pesquisas import SAIDA, auditar


def test_auditoria_todas_casadas():
    linhas = auditar()
    assert len(linhas) == 112
    # Nenhuma pesquisa pode estar sem registro
    sem_reg = [r for r in linhas if r["status_auditoria"] == "sem_registro"]
    assert len(sem_reg) == 0, f"Pesquisas sem registro: {sem_reg}"

    # Conferir se os campos essenciais estão preenchidos
    for r in linhas:
        assert r["protocolo_tse"].startswith("BR")
        assert len(r["empresa_tse"]) > 0
        assert float(r["custo_declarado_rs"]) > 0
