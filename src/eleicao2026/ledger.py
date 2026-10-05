"""Registro de observações (ledger) que só acrescenta.

Cada linha é um valor visto em uma fonte, com a data em que a fonte o **divulgou** e a data em que
**nós o coletamos**. Nunca sobrescreve: se a mesma série/período reaparece com valor diferente, uma
nova linha é acrescentada (isso é uma *revisão*, e é exatamente o que permite medir quanto o dado
errou ao longo do tempo). Se o valor é idêntico ao último visto, nada é gravado.

Esquema (`data/ledger/observacoes.csv`):
  fonte_id      identificador da fonte (ver `data/fontes/`)
  serie         nome da série dentro da fonte (ex.: "sgs_433", "focus_IPCA_2026_mediana")
  periodo_ref   período a que o valor se refere (ISO: AAAA-MM-DD, AAAA-MM ou AAAA)
  valor         valor numérico, como texto (preserva a precisão da fonte)
  unidade       "%", "R$", "índice", ...
  divulgado_em  quando a fonte divulgou (ISO 8601, vazio se desconhecido -> usar `coletado_em` com cautela)
  coletado_em   quando coletamos (ISO 8601, UTC)
  url           de onde veio
  nota          texto livre (ex.: "revisão de 4.20 para 4.22")

Regra anti-vazamento: um backtest "em AAAA-MM-DD" só pode usar linhas com
`divulgado_em <= AAAA-MM-DD` (ou, se vazio, `coletado_em <= ...`).
"""
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from eleicao2026 import config as C

CAMPOS = ["fonte_id", "serie", "periodo_ref", "valor", "unidade",
          "divulgado_em", "coletado_em", "url", "nota"]
CAMINHO = C.DATA / "ledger" / "observacoes.csv"


def agora():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_arquivo(caminho, bloco=1 << 20):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for parte in iter(lambda: f.read(bloco), b""):
            h.update(parte)
    return h.hexdigest()


def ler(caminho=None):
    caminho = Path(caminho or CAMINHO)
    if not caminho.exists():
        return []
    with open(caminho, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ultimos(linhas):
    """Último valor visto por (fonte_id, serie, periodo_ref)."""
    ult = {}
    for r in linhas:
        ult[(r["fonte_id"], r["serie"], r["periodo_ref"])] = r["valor"]
    return ult


def acrescentar(novas, caminho=None):
    """Acrescenta ao ledger só o que é novo ou revisado. Retorna (novas_series, revisoes, iguais)."""
    caminho = Path(caminho or CAMINHO)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    existentes = ler(caminho)
    ult = ultimos(existentes)
    a_gravar, n_novas, n_rev, n_iguais = [], 0, 0, 0
    t = agora()
    for r in novas:
        r = {k: ("" if r.get(k) is None else str(r.get(k))) for k in CAMPOS}
        r["coletado_em"] = r["coletado_em"] or t
        chave = (r["fonte_id"], r["serie"], r["periodo_ref"])
        if chave not in ult:
            n_novas += 1
        elif ult[chave] != r["valor"]:
            n_rev += 1
            r["nota"] = (r["nota"] + " | " if r["nota"] else "") + f"revisão de {ult[chave]} para {r['valor']}"
        else:
            n_iguais += 1
            continue
        ult[chave] = r["valor"]
        a_gravar.append(r)
    if a_gravar:
        novo_arquivo = not caminho.exists()
        with open(caminho, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CAMPOS)
            if novo_arquivo:
                w.writeheader()
            w.writerows(a_gravar)
    return n_novas, n_rev, n_iguais


def ate(linhas, data_corte):
    """Visão 'como era em data_corte' (ISO): só o que já tinha sido divulgado, último valor por chave."""
    vis = {}
    for r in linhas:
        quando = r["divulgado_em"] or r["coletado_em"]
        if quando[:10] <= data_corte:
            vis[(r["fonte_id"], r["serie"], r["periodo_ref"])] = r
    return list(vis.values())
