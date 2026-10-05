"""Utilitários dos coletores de economia (`economia.py`) e de mercados (`mercado.py`).

Só biblioteca padrão. Reúne o que se repete em toda coleta de fonte externa:
  * `baixar`        GET com tentativas e pausa educada, devolvendo os bytes originais;
  * `salvar_bruto`  grava os bytes tal como recebidos em data/raw/<fonte_id>/ e devolve sha256 + tamanho;
  * `escrever_entrada`  grava o catálogo da fonte em data/fontes/entradas/<fonte_id>.json.

Nada aqui guarda dado pessoal; os coletores só persistem séries agregadas e metadados de mercados.
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from eleicao2026 import config as C
from eleicao2026 import ledger as L

ENTRADAS = C.DATA / "fontes" / "entradas"
CHAVES_ENTRADA = ["id", "nome", "publicador", "url_origem", "url_landing", "coletado_em", "sha256",
                  "tamanho_bytes", "licenca", "granularidade", "periodo", "confianca", "status",
                  "usado_em", "limitacoes"]
USADO_EM_INICIAL = "catalogado, nao usado no modelo"


class FalhaHTTP(Exception):
    """Falha definitiva de rede/HTTP (depois das tentativas)."""


def agora_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def hoje_utc():
    return datetime.now(timezone.utc).date()


def baixar(url, tries=3, pausa=1.0, timeout=60, cabecalhos=None):
    """GET que devolve os bytes originais. Não tenta de novo em 403/404/400 (não contornar bloqueios)."""
    ultimo = None
    for i in range(tries):
        try:
            with urlopen(Request(url, headers=cabecalhos or C.UA), timeout=timeout) as r:
                return r.read()
        except HTTPError as e:
            ultimo = f"HTTP {e.code}"
            if e.code in (400, 401, 403, 404):
                break
        except (URLError, TimeoutError, OSError) as e:
            ultimo = f"{type(e).__name__}: {e}"
        time.sleep(pausa * (i + 1))
    raise FalhaHTTP(f"{url} -> {ultimo}")


def salvar_bruto(fonte_id, nome, corpo, url, coletado_em):
    """Grava `corpo` (bytes originais) em data/raw/<fonte_id>/<nome>. Devolve o registro de proveniência."""
    pasta = C.RAW / fonte_id
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / nome).write_bytes(corpo)
    return {"arquivo": f"data/raw/{fonte_id}/{nome}", "url": url, "coletado_em": coletado_em,
            "sha256": L.sha256_bytes(corpo), "tamanho_bytes": len(corpo)}


def escrever_entrada(entrada, caminho=None):
    """Grava o catálogo da fonte. `entrada` precisa ter todas as chaves de CHAVES_ENTRADA."""
    faltam = [k for k in CHAVES_ENTRADA if k not in entrada]
    if faltam:
        raise ValueError(f"entrada de catálogo sem chaves: {faltam}")
    caminho = Path(caminho or ENTRADAS / f"{entrada['id']}.json")
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(entrada, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return caminho


def resumo_proveniencia(registros):
    """(lista de sha256, soma dos tamanhos) para os campos `sha256` e `tamanho_bytes` do catálogo."""
    return [r["sha256"] for r in registros], sum(r["tamanho_bytes"] for r in registros)


def gravar_manifesto(fonte_id, registros):
    """data/raw/<fonte_id>/MANIFESTO.json: url, sha256, tamanho e instante de cada arquivo bruto."""
    pasta = C.RAW / fonte_id
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "MANIFESTO.json").write_text(json.dumps(registros, ensure_ascii=False, indent=2) + "\n",
                                          encoding="utf-8")
