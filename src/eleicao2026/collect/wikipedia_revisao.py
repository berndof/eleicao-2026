#!/usr/bin/env python3
"""Descobre e registra QUAL revisão da Wikipédia (EN) é o wikitext salvo em data/external/.

A página 'Opinion polling for the 2026 Brazilian presidential election' muda várias vezes por dia.
Sem o `oldid` não dá para reproduzir a leitura nem auditar cada linha. Como a Wikipédia NÃO é fonte
primária (cada linha cita o instituto/veículo), o `oldid` serve só para a proveniência do ponto de
partida; os números devem ser conferidos nas fontes primárias (ver audit_pesquisas.py).

Método: lista as revisões via API do MediaWiki (prop=revisions: ids|timestamp|sha1), compara o SHA-1 do
texto salvo (normalizando só o \\n final) com o de cada revisão e, havendo casamento, baixa o conteúdo
dessa revisão (rvslots=main) e confere o SHA-256. Sem casamento exato, informa a revisão mais próxima
(por diferença de linhas, via difflib), sem fingir exatidão.

Gera data/external/wikipedia_pesquisas_2026.revisao.json:
  oldid, timestamp, sha256 do arquivo, permalink, status ('casado_exato' | 'aproximado' | 'nao_encontrado').

Uso: python -m eleicao2026.collect.wikipedia_revisao [--arquivo caminho] [--saida caminho]
Somente biblioteca padrão. Também é chamado por collect.pesquisas.baixar() nas próximas coletas.
"""
import argparse
import difflib
import hashlib
import json
import sys
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from eleicao2026 import config as C

TITULO = "Opinion polling for the 2026 Brazilian presidential election"
API = "https://en.wikipedia.org/w/api.php"
ARQUIVO = C.EXTERNAL / "wikipedia_pesquisas_2026.wikitext"
SAIDA = C.EXTERNAL / "wikipedia_pesquisas_2026.revisao.json"


def permalink(oldid):
    return "https://en.wikipedia.org/w/index.php?" + urlencode({"title": TITULO.replace(" ", "_"), "oldid": oldid})


def _api(**params):
    q = urlencode(dict(action="query", format="json", formatversion="2", **params))
    with urlopen(Request(f"{API}?{q}", headers=C.UA), timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def sha1_texto(b):
    """SHA-1 do texto sem o(s) \\n finais (a API do MediaWiki não devolve quebra de linha final)."""
    return hashlib.sha1(b.rstrip(b"\n")).hexdigest()


def sha256_arquivo(b):
    return hashlib.sha256(b).hexdigest()


def listar_revisoes(max_rev=200):
    """Revisões mais recentes (mais nova primeiro): dicts com revid, timestamp, sha1, size."""
    revs, cont = [], {}
    while len(revs) < max_rev:
        d = _api(prop="revisions", titles=TITULO, rvprop="ids|timestamp|sha1|size", rvlimit=50, **cont)
        revs += d["query"]["pages"][0].get("revisions", [])
        if "continue" not in d:
            break
        cont = d["continue"]
    return revs


def conteudo_revisao(revid):
    d = _api(prop="revisions", revids=revid, rvprop="content", rvslots="main")
    return d["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"].encode("utf-8")


def diferenca_linhas(a, b):
    """Nº de linhas acrescentadas+removidas entre dois textos (bytes)."""
    sm = difflib.unified_diff(a.decode("utf-8").splitlines(), b.decode("utf-8").splitlines(), lineterm="", n=0)
    return sum(1 for l in sm if l[:1] in "+-" and l[:3] not in ("+++", "---"))


def casar(corpo, revisoes, buscar=conteudo_revisao):
    """Procura em `revisoes` a que tem o SHA-1 de `corpo`. Devolve dict com status/oldid/timestamp/..."""
    alvo = sha1_texto(corpo)
    for r in revisoes:
        if r["sha1"] == alvo:
            conf = sha256_arquivo(buscar(r["revid"]).rstrip(b"\n")) == sha256_arquivo(corpo.rstrip(b"\n"))
            return dict(status="casado_exato", oldid=r["revid"], timestamp=r["timestamp"],
                        sha256_conteudo_revisao_confere=conf, diferenca_linhas=0)
    # sem casamento: a revisão com menor diferença de linhas entre as mais recentes
    melhor = None
    for r in revisoes[:15]:
        dl = diferenca_linhas(corpo, buscar(r["revid"]))
        if melhor is None or dl < melhor[0]:
            melhor = (dl, r)
    if melhor is None:
        return dict(status="nao_encontrado", oldid=None, timestamp=None, diferenca_linhas=None)
    return dict(status="aproximado", oldid=melhor[1]["revid"], timestamp=melhor[1]["timestamp"],
                diferenca_linhas=melhor[0])


def registrar(arquivo=ARQUIVO, saida=SAIDA):
    """Casa `arquivo` com uma revisão e grava o JSON de proveniência. Devolve o dict gravado."""
    corpo = arquivo.read_bytes()
    res = casar(corpo, listar_revisoes())
    out = dict(
        titulo=TITULO, arquivo=str(arquivo.relative_to(C.ROOT)) if arquivo.is_relative_to(C.ROOT) else str(arquivo),
        sha256_arquivo=sha256_arquivo(corpo), sha1_arquivo=sha1_texto(corpo), tamanho_bytes=len(corpo),
        arquivo_mtime=datetime.fromtimestamp(arquivo.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        oldid=res["oldid"], timestamp_revisao=res["timestamp"],
        permalink=permalink(res["oldid"]) if res["oldid"] else None, status_casamento=res["status"],
        diferenca_linhas=res.get("diferenca_linhas"),
        conteudo_revisao_confere_sha256=res.get("sha256_conteudo_revisao_confere"),
        verificado_em=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        nota="Wikipédia não é fonte primária: o oldid só fixa o ponto de partida; números a validar nos institutos/TSE.")
    saida.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arquivo", default=str(ARQUIVO))
    ap.add_argument("--saida", default=str(SAIDA))
    a = ap.parse_args()
    from pathlib import Path
    out = registrar(Path(a.arquivo), Path(a.saida))
    print(f"{out['status_casamento']}: oldid={out['oldid']} ({out['timestamp_revisao']}) {out['permalink']}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
